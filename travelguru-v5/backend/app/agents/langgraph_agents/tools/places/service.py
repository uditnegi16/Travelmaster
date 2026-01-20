"""
Places Search Service.

This module is the business orchestrator for places search operations.
It coordinates between adapters, normalizers, and applies business rules.

Responsibilities:
- Validate search parameters
- Orchestrate calls to Google Places API adapter
- Call normalizer to convert raw data to schema
- Apply business rules (rating filtering, sorting, limiting)
- Return validated PlaceOption schema objects

Architecture Layer: Service
- NO direct API calls
- NO data normalization (delegates to normalizer)
- NO schema definitions
- YES business logic and orchestration
"""

from app.core.logging import get_logger
from app.shared.schemas import PlaceOption
from app.agents.langgraph_agents.tools.places.adapters.google_api import search_places_google_api
from app.agents.langgraph_agents.tools.places.normalize import normalize_places
from app.agents.nlp.places_intent_extractor import extract_places_intent
from app.agents.postprocessing.places_enrichment import enrich_places, EnrichmentResult

logger = get_logger(__name__)


class PlacesSearchError(RuntimeError):
    """
    Custom exception raised when places search orchestration fails.
    
    This exception wraps all service-layer errors that are not validation errors.
    """
    pass


def search_places(
    query: str | None = None,
    *,
    city: str | None = None,
    radius_km: int = 10,
    limit: int = 10,
    min_rating: float = 4.0,
    max_entry_fee: int | None = None,
    categories: list[str] | None = None,
    preferences: dict | None = None,
) -> list[PlaceOption]:
    """
    Search for tourist places using natural language query or structured parameters.
    
    This is the main business orchestrator that supports two modes:
    1. NLP Mode: Pass a natural language query string
    2. Structured Mode: Pass individual parameters
    
    The function performs:
    - NLP intent extraction (if query provided)
    - API adapter calls
    - Data normalization
    - Enrichment with intelligence layer
    - Business rule application (filtering, sorting, limiting)
    
    Args:
        query: Natural language query (e.g., "Find free museums in Delhi").
               If provided, structured params will be extracted from it.
        city: City name to search places in (required if query not provided).
        radius_km: Search radius in kilometers from city center.
                   Must be between 1 and 50. Defaults to 10.
        limit: Maximum number of results to return.
               Must be between 1 and 50. Defaults to 10.
        min_rating: Minimum rating filter (0-5 scale).
                    Places below this rating are excluded.
                    Must be between 0 and 5. Defaults to 4.0.
        max_entry_fee: Optional maximum entry fee filter in INR.
        categories: Optional list of place categories to filter by.
        preferences: User preferences dict for enrichment personalization.
    
    Returns:
        List of PlaceOption objects, enriched and sorted by relevance.
        Empty list if no places found or all filtered out.
    
    Raises:
        ValueError: If neither query nor city is provided, or invalid params.
        PlacesSearchError: If any orchestration step fails.
    
    Examples:
        # NLP mode
        >>> places = search_places("Find free museums in Delhi")
        
        # Structured mode
        >>> places = search_places(city="Paris", max_entry_fee=500, limit=5)
    """
    # NLP extraction if query provided
    if query:
        logger.info(f"Extracting intent from natural language query: '{query}'")
        try:
            intent = extract_places_intent(query)
            logger.info(f"Extracted intent: city={intent.city}, categories={intent.categories}, "
                       f"max_fee={intent.max_entry_fee}, min_rating={intent.min_rating}")
            
            # Override parameters with extracted intent
            city = intent.city
            if intent.categories:
                categories = intent.categories
            if intent.max_entry_fee is not None:
                max_entry_fee = intent.max_entry_fee
            if intent.min_rating is not None:
                min_rating = intent.min_rating
            if intent.radius_km != 10:  # If not default
                radius_km = intent.radius_km
            if intent.limit != 10:  # If not default
                limit = intent.limit
            if intent.preferences:
                # Merge extracted preferences with provided ones
                preferences = {**(preferences or {}), **intent.preferences}
        except Exception as e:
            logger.warning(f"NLP extraction failed: {e}. Falling back to structured parameters.")
    
    # Validate that we have a city
    if not city:
        raise ValueError("Either 'query' or 'city' parameter must be provided")
    
    # Input validation
    if not isinstance(city, str) or not city.strip():
        raise ValueError("city must be a non-empty string")
    
    city = city.strip()
    
    if not isinstance(radius_km, int) or radius_km < 1 or radius_km > 50:
        raise ValueError("radius_km must be between 1 and 50")
    
    if not isinstance(limit, int) or limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")
    
    if not isinstance(min_rating, (int, float)) or min_rating < 0 or min_rating > 5:
        raise ValueError("min_rating must be between 0 and 5")
    
    if max_entry_fee is not None and (not isinstance(max_entry_fee, int) or max_entry_fee < 0):
        raise ValueError("max_entry_fee must be a non-negative integer")
    
    logger.info(
        f"Starting places search for city='{city}', "
        f"radius={radius_km}km, limit={limit}, min_rating={min_rating}, "
        f"max_fee={max_entry_fee}, categories={categories}"
    )
    
    try:
        # Convert radius to meters
        radius_m = radius_km * 1000
        
        # Call Google API adapter with 3x limit to allow for filtering
        # (Many places may be filtered out by rating or normalizer filters)
        adapter_limit = min(limit * 3, 60)  # Cap at Google API max
        
        logger.debug(
            f"Calling Google adapter with radius={radius_m}m, "
            f"adapter_limit={adapter_limit}"
        )
        
        raw_places = search_places_google_api(
            city=city,
            radius_m=radius_m,
            limit=adapter_limit
        )
        
        logger.info(f"Retrieved {len(raw_places)} raw place(s) from Google API")
        
        # Early return if no raw places
        if not raw_places:
            logger.info(f"No raw places found for city '{city}'")
            return []
        
        # Normalize raw data into PlaceOption schema
        places = normalize_places(raw_places, city=city)
        
        logger.info(f"Normalized {len(places)} place(s) from {len(raw_places)} raw places")
        
        # Early return if normalization produced no results
        if not places:
            logger.info(f"No places survived normalization for city '{city}'")
            return []
        
        # Apply business rules
        
        # Filter by minimum rating
        places_before_filter = len(places)
        places = [p for p in places if p.rating >= min_rating]
        
        logger.info(
            f"Rating filter (min={min_rating}): "
            f"{places_before_filter} -> {len(places)} places"
        )
        
        # Filter by max entry fee if specified
        if max_entry_fee is not None:
            places_before_fee_filter = len(places)
            places = [p for p in places if p.entry_fee <= max_entry_fee]
            logger.info(
                f"Entry fee filter (max={max_entry_fee}): "
                f"{places_before_fee_filter} -> {len(places)} places"
            )
        
        # Filter by categories if specified
        if categories:
            places_before_category_filter = len(places)
            categories_lower = [c.lower() for c in categories]
            places = [p for p in places if p.category.lower() in categories_lower]
            logger.info(
                f"Category filter ({categories}): "
                f"{places_before_category_filter} -> {len(places)} places"
            )
        
        # Early return if all filtered out
        if not places:
            logger.info(
                f"No places meet all filter criteria for city '{city}'"
            )
            return []
        
        # Apply enrichment with intelligence layer
        logger.info("Applying places enrichment with intelligence layer...")
        try:
            enrichment_result = enrich_places(places, preferences)
            
            # Extract enriched places (already ranked and sorted by match_score)
            enriched_places = enrichment_result.enriched_places
            
            # Log enrichment results for debugging
            logger.info(
                f"Enrichment complete. Market analysis: "
                f"{enrichment_result.market_analysis.get('total_options', 0)} options analyzed."
            )
            logger.info(f"Best place: {enrichment_result.best_choice}")
            
            # Extract the original PlaceOption from enriched results
            # They are already sorted by rank (best first)
            # TODO: Later, return EnrichedPlace objects for rich itinerary composition
            # (with insights, tags, scores, reasoning) instead of just PlaceOption
            places = [ep.place for ep in enriched_places]
            
        except Exception as e:
            logger.warning(f"Enrichment failed: {e}. Continuing with basic sorting.")
            # Fallback to simple rating-based sorting
            places.sort(key=lambda p: p.rating, reverse=True)
        
        # Limit results
        if len(places) > limit:
            places = places[:limit]
            logger.info(f"Limited results to {limit} place(s)")
        
        logger.info(
            f"Places search complete: returning {len(places)} place(s) for '{city}'"
        )
        
        return places
    
    except ValueError as e:
        # Re-raise validation errors as-is
        raise
    
    except Exception as e:
        # Wrap all other errors in service exception
        error_msg = (
            f"Places search orchestration failed for city='{city}': "
            f"{type(e).__name__}: {str(e)}"
        )
        logger.error(error_msg, exc_info=True)
        raise PlacesSearchError(error_msg) from e
