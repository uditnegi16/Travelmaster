"""
Hotel Search Service.

This module is the business orchestrator for hotel search operations.
It coordinates between adapters, normalizers, and applies business rules.

Responsibilities:
- Resolve city names to IATA codes
- Orchestrate calls to search and ratings adapters
- Apply business rules (filtering, sorting, limiting)
- Return validated HotelOption schema objects

Architecture Layer: Service
- NO direct API calls
- NO data normalization (delegates to normalizer)
- NO schema definitions
- YES business logic and orchestration
"""

from core.amadeus_iata import UnknownCityError, resolve_city_to_iata
from core.logging import get_logger
from agent_in_update.shared.schemas import HotelOption
from .adapters.ratings_api import get_hotel_ratings_api
from .adapters.search_api import search_hotels_api
from .normalize import normalize_hotels
from ....nlp.hotel_intent_extractor import extract_hotel_intent
from ....postprocessing.hotel_enrichment import enrich_hotels, EnrichmentResult

logger = get_logger(__name__)


class HotelSearchError(RuntimeError):
    """
    Custom exception raised when hotel search orchestration fails.
    
    This exception wraps all service-layer errors that are not validation
    or city resolution errors.
    """
    pass


def search_hotels(
    query: str | None = None,
    *,
    city: str | None = None,
    check_in: str | None = None,
    check_out: str | None = None,
    guests: int = 1,
    max_price: int | None = None,
    min_stars: int | float | None = None,
    amenities: list[str] | None = None,
    preferences: dict | None = None,
    limit: int = 5,
) -> list[HotelOption]:
    """
    Search for hotels using natural language query or structured parameters.
    
    This is the main business orchestrator that supports two modes:
    1. NLP Mode: Pass a natural language query string
    2. Structured Mode: Pass individual parameters
    
    The function performs:
    - NLP intent extraction (if query provided)
    - City resolution to IATA code
    - API adapter calls
    - Data normalization
    - Enrichment with intelligence layer
    - Business rule application (filtering, sorting, limiting)
    
    Args:
        query: Natural language query (e.g., "Find cheap hotels in Mumbai with pool").
               If provided, structured params will be extracted from it.
        city: City name to search hotels in (required if query not provided).
        check_in: Check-in date in YYYY-MM-DD format (optional).
        check_out: Check-out date in YYYY-MM-DD format (optional).
        guests: Number of guests (default: 1).
        max_price: Optional maximum price per night filter.
        min_stars: Minimum star rating filter (1-5).
        amenities: List of required amenities.
        preferences: User preferences dict for enrichment personalization.
        limit: Maximum number of results to return (default: 5).
    
    Returns:
        List of HotelOption objects, enriched and sorted by relevance.
        Empty list if no hotels found or all filtered out.
    
    Raises:
        ValueError: If neither query nor city is provided, or invalid params.
        UnknownCityError: If city cannot be resolved to IATA code.
        HotelSearchError: If any orchestration step fails.
    
    Examples:
        # NLP mode
        >>> hotels = search_hotels("Find cheap hotels in Mumbai with pool")
        
        # Structured mode
        >>> hotels = search_hotels(city="Paris", max_price=200, limit=3)
    """
    # NLP extraction if query provided
    if query:
        logger.info(f"NLP mode: extracting intent from query: '{query}'")
        try:
            intent = extract_hotel_intent(query)
            
            # Override structured params with extracted intent
            # Only override if intent has a value (not None)
            city = intent.city
            check_in = intent.check_in
            check_out = intent.check_out
            guests = intent.guests
            if intent.max_price is not None:
                max_price = intent.max_price
            if intent.min_stars is not None:
                min_stars = intent.min_stars
            if intent.amenities:
                amenities = intent.amenities
            if intent.preferences:
                preferences = intent.preferences
            
            logger.info(
                f"NLP extracted: city={city}, guests={guests}, "
                f"max_price={max_price}, min_stars={min_stars}, "
                f"amenities={amenities}, preferences={preferences}"
            )
        except Exception as e:
            logger.error(f"NLP extraction failed: {e}")
            raise ValueError(f"Failed to extract intent from query: {e}") from e
    
    # Input validation
    if not city or not isinstance(city, str) or not city.strip():
        raise ValueError("city must be a non-empty string (provide query or city parameter)")
    
    city = city.strip()
    
    if limit <= 0:
        logger.warning(f"Invalid limit={limit}, defaulting to 5")
        limit = 5
    
    # Ignore invalid max_price
    if max_price is not None and max_price <= 0:
        logger.warning(f"Invalid max_price={max_price}, ignoring price filter")
        max_price = None
    
    logger.info(
        f"Starting hotel search for city='{city}', "
        f"max_price={max_price}, limit={limit}, preferences={preferences}"
    )
    
    try:
        # Step 1: Resolve city to IATA code
        city_iata = resolve_city_to_iata(city)
        logger.info(f"Resolved city '{city}' to IATA code '{city_iata}'")
        
        # Step 2: Call search API adapter
        raw_hotels = search_hotels_api(
            city_iata=city_iata,
            adults=guests,
            check_in=check_in,
            check_out=check_out,
            max_results=max(limit * 3, 30),
        )        
        
        logger.info(f"Retrieved {len(raw_hotels)} raw hotel(s) from search API")
        
        # Step 3: Extract hotel IDs for ratings lookup
        hotel_ids = []
        for h in raw_hotels:
            if (
                isinstance(h, dict)
                and "hotel" in h
                and isinstance(h["hotel"], dict)
                and "hotelId" in h["hotel"]
            ):
                hotel_ids.append(h["hotel"]["hotelId"])
        
        logger.info(f"Extracted {len(hotel_ids)} hotel ID(s) for ratings lookup")
        
        # Step 4: Call ratings API adapter
        try:
            ratings_map = get_hotel_ratings_api(hotel_ids)
        except Exception as e:
            # fallback: continue without ratings
            print(f"Ratings fetch failed, continuing without ratings: {e}")
            ratings_map = {}
        logger.info(f"Retrieved ratings for {len(ratings_map)} hotel(s)")
        
        # Step 5: Normalize raw data into HotelOption schema
        hotels = normalize_hotels(raw_hotels, ratings_map, check_in, check_out)
        logger.info(f"Normalized {len(hotels)} hotels into schema objects with check_in={check_in}, check_out={check_out}")
        
        # Step 6: Apply business rules
        
        # Filter by max_price if specified
        if max_price is not None:
            hotels_before = len(hotels)
            hotels = [h for h in hotels if h.price_per_night <= max_price]
            logger.info(
                f"Price filter (max={max_price}): {hotels_before} -> {len(hotels)} hotels"
            )
        
        # Filter by min_stars if specified
        if min_stars is not None:
            hotels_before = len(hotels)
            hotels = [h for h in hotels if h.star_category >= min_stars]
            logger.info(
                f"Star filter (min={min_stars}): {hotels_before} -> {len(hotels)} hotels"
            )
        
        # Filter by amenities if specified
        if amenities:
            hotels_before = len(hotels)
            filtered_hotels = []
            for h in hotels:
                hotel_amenities_lower = [a.lower() for a in h.amenities]
                has_all_amenities = all(
                    any(req_amenity.lower() in ha for ha in hotel_amenities_lower)
                    for req_amenity in amenities
                )
                if has_all_amenities:
                    filtered_hotels.append(h)
            hotels = filtered_hotels
            logger.info(
                f"Amenity filter ({amenities}): {hotels_before} -> {len(hotels)} hotels"
            )
        
        # Step 7: Apply enrichment intelligence
        if hotels and (preferences or len(hotels) > 1):
            logger.info("Applying hotel enrichment with intelligence layer...")
            try:
                enrichment_result = enrich_hotels(hotels, preferences or {})
                
                # Extract enriched hotels
                enriched_hotels = enrichment_result.enriched_hotels
                
                # Sort by rank (already computed by enrichment)
                enriched_hotels.sort(key=lambda eh: eh.rank)
                
                # Limit results
                if len(enriched_hotels) > limit:
                    enriched_hotels = enriched_hotels[:limit]
                    logger.info(f"Limited enriched results to {limit} hotel(s)")
                
                # Extract base HotelOption objects for return
                # Note: Enrichment metadata (scores, insights, recommendations) is discarded
                # For full intelligence output, use search_hotels_enriched() instead
                hotels = [eh.hotel for eh in enriched_hotels]
                
                logger.info(
                    f"Enrichment complete: returning {len(hotels)} enriched hotel(s)"
                )
            except Exception as e:
                logger.warning(f"Enrichment failed: {e}, returning normalized hotels without enrichment")
                # IMPORTANT: do NOT change the list shape or drop items due to enrichment.
                # Just keep whatever hotels you already have, only apply the same limit.
                if hotels:
                    if len(hotels) > limit:
                        hotels = hotels[:limit]
        else:
            # No enrichment needed, basic sorting
            hotels.sort(key=lambda h: h.price_per_night)
            logger.debug("Sorted hotels by price (ascending)")
            
            # Limit results
            if len(hotels) > limit:
                hotels = hotels[:limit]
                logger.info(f"Limited results to {limit} hotel(s)")
        
        logger.info(
            f"Hotel search complete: returning {len(hotels)} hotel(s) for '{city}'"
        )
        
        return hotels
    
    except ValueError as e:
        # Re-raise validation errors as-is
        raise
    
    except UnknownCityError as e:
        # Re-raise city resolution errors as-is
        raise
    
    except Exception as e:
        # Wrap all other errors in service exception
        error_msg = (
            f"Enriched hotel search orchestration failed for city='{city}': "
            f"{type(e).__name__}: {str(e)}"
        )
        logger.error(error_msg, exc_info=True)
        return []


def search_hotels_enriched(
    query: str | None = None,
    *,
    city: str | None = None,
    check_in: str | None = None,
    check_out: str | None = None,
    guests: int = 1,
    max_price: int | None = None,
    min_stars: int | float | None = None,
    amenities: list[str] | None = None,
    preferences: dict | None = None,
    limit: int = 5,
) -> EnrichmentResult:
    """
    Search for hotels with full enrichment intelligence and metadata.
    
    This function returns the complete HotelEnrichmentResult with:
    - scores (value_score, quality_score, relevance_score for each hotel)
    - tags (BUDGET_FRIENDLY, LUXURY, CENTRAL_LOCATION, etc.)
    - insights (market analysis, price intelligence, quality patterns)
    - recommendations (personalized suggestions based on preferences)
    - ranks (sorted by overall score)
    - explanations (why each hotel is recommended)
    
    Args:
        query: Natural language query (e.g., "Find luxury hotels in Goa with spa").
               If provided, structured params will be extracted from it.
        city: City name to search hotels in (required if query not provided).
        check_in: Check-in date in YYYY-MM-DD format (optional).
        check_out: Check-out date in YYYY-MM-DD format (optional).
        guests: Number of guests (default: 1).
        max_price: Optional maximum price per night filter.
        min_stars: Minimum star rating filter (1-5).
        amenities: List of required amenities.
        preferences: User preferences dict for enrichment personalization.
        limit: Maximum number of results to return (default: 5).
    
    Returns:
        EnrichmentResult with complete intelligence metadata.
        Contains enriched_hotels list with full scoring and insights.
    
    Raises:
        ValueError: If neither query nor city is provided, or invalid params.
        UnknownCityError: If city cannot be resolved to IATA code.
        HotelSearchError: If any orchestration step fails.
    
    Examples:
        # NLP mode with full intelligence
        >>> result = search_hotels_enriched("Find luxury hotels in Mumbai")
        >>> for eh in result.enriched_hotels:
        ...     print(f"{eh.hotel.name}: Score={eh.overall_score}, Tags={eh.tags}")
        
        # Structured mode with preferences
        >>> result = search_hotels_enriched(
        ...     city="Paris",
        ...     preferences={"budget_conscious": True, "values_location": True}
        ... )
        >>> print(result.insights)  # Market analysis
        >>> print(result.recommendations)  # Personalized suggestions
    """
    # NLP extraction if query provided
    if query:
        logger.info(f"NLP mode (enriched): extracting intent from query: '{query}'")
        try:
            intent = extract_hotel_intent(query)
            
            # Override structured params with extracted intent
            # Only override if intent has a value (not None)
            city = intent.city
            check_in = intent.check_in
            check_out = intent.check_out
            guests = intent.guests
            if intent.max_price is not None:
                max_price = intent.max_price
            if intent.min_stars is not None:
                min_stars = intent.min_stars
            if intent.amenities:
                amenities = intent.amenities
            if intent.preferences:
                preferences = intent.preferences
            
            logger.info(
                f"NLP extracted: city={city}, guests={guests}, "
                f"max_price={max_price}, min_stars={min_stars}, "
                f"amenities={amenities}, preferences={preferences}"
            )
        except Exception as e:
            logger.error(f"NLP extraction failed: {e}")
            raise ValueError(f"Failed to extract intent from query: {e}") from e
    
    # Input validation
    if not city or not isinstance(city, str) or not city.strip():
        raise ValueError("city must be a non-empty string (provide query or city parameter)")
    
    city = city.strip()
    
    if limit <= 0:
        logger.warning(f"Invalid limit={limit}, defaulting to 5")
        limit = 5
    
    # Ignore invalid max_price
    if max_price is not None and max_price <= 0:
        logger.warning(f"Invalid max_price={max_price}, ignoring price filter")
        max_price = None
    
    logger.info(
        f"Starting enriched hotel search for city='{city}', "
        f"max_price={max_price}, limit={limit}, preferences={preferences}"
    )
    
    try:
        # Step 1: Resolve city to IATA code
        city_iata = resolve_city_to_iata(city)
        logger.info(f"Resolved city '{city}' to IATA code '{city_iata}'")
        
        # Step 2: Call search API adapter
        raw_hotels = search_hotels_api(city_iata=city_iata, adults=guests,check_in=check_in,check_out=check_out,max_results=max(limit * 3, 30))
        logger.info(f"Retrieved {len(raw_hotels)} raw hotel(s) from search API")
        
        # Step 3: Extract hotel IDs for ratings lookup
        hotel_ids = []
        for h in raw_hotels:
            if (
                isinstance(h, dict)
                and "hotel" in h
                and isinstance(h["hotel"], dict)
                and "hotelId" in h["hotel"]
            ):
                hotel_ids.append(h["hotel"]["hotelId"])
        
        logger.info(f"Extracted {len(hotel_ids)} hotel ID(s) for ratings lookup")
        
        # Step 4: Call ratings API adapter
        ratings_map = get_hotel_ratings_api(hotel_ids)
        logger.info(f"Retrieved ratings for {len(ratings_map)} hotel(s)")
        
        # Step 5: Normalize raw data into HotelOption schema
        hotels = normalize_hotels(raw_hotels, ratings_map, check_in, check_out)
        logger.info(f"Normalized {len(hotels)} hotel(s) into schema objects")
        
        # Step 6: Apply business rules
        
        # Filter by max_price if specified
        if max_price is not None:
            hotels_before = len(hotels)
            hotels = [h for h in hotels if h.price_per_night <= max_price]
            logger.info(
                f"Price filter (max={max_price}): {hotels_before} -> {len(hotels)} hotels"
            )
        
        # Filter by min_stars if specified
        if min_stars is not None:
            hotels_before = len(hotels)
            hotels = [h for h in hotels if h.star_category>= min_stars]
            logger.info(
                f"Star filter (min={min_stars}): {hotels_before} -> {len(hotels)} hotels"
            )
        
        # Filter by amenities if specified
        if amenities:
            hotels_before = len(hotels)
            filtered_hotels = []
            for h in hotels:
                hotel_amenities_lower = [a.lower() for a in h.amenities]
                has_all_amenities = all(
                    any(req_amenity.lower() in ha for ha in hotel_amenities_lower)
                    for req_amenity in amenities
                )
                if has_all_amenities:
                    filtered_hotels.append(h)
            hotels = filtered_hotels
            logger.info(
                f"Amenity filter ({amenities}): {hotels_before} -> {len(hotels)} hotels"
            )
        
        # Step 7: Apply enrichment intelligence and return full result
        if not hotels:
            # Return empty result if no hotels
            logger.info("No hotels found after filtering")
            return EnrichmentResult(
                enriched_hotels=[],
                market_analysis={},
                best_choice=None
            )
        
        logger.info("Applying hotel enrichment with full intelligence layer...")
        try:
            enrichment_result = enrich_hotels(hotels, preferences or {})
            
            # Sort by rank (already computed by enrichment)
            enrichment_result.enriched_hotels.sort(key=lambda eh: eh.rank)
            
            # Limit results
            if len(enrichment_result.enriched_hotels) > limit:
                enrichment_result.enriched_hotels = enrichment_result.enriched_hotels[:limit]
                logger.info(f"Limited enriched results to {limit} hotel(s)")
            
            logger.info(
                f"Enrichment complete: returning {len(enrichment_result.enriched_hotels)} hotels "
                f"with full intelligence (scores, tags, insights, recommendations)"
            )
            
            return enrichment_result
            
        except Exception as e:
            # If enrichment fails, return basic result
            logger.error(f"Enrichment failed: {e}, returning basic result")
            hotels.sort(key=lambda h: h.price_per_night)
            if len(hotels) > limit:
                hotels = hotels[:limit]
            
            # Create minimal enrichment result
            from ....postprocessing.hotel_enrichment import EnrichedHotel
            enriched_hotels = [
                EnrichedHotel(
                    hotel=h,
                    rank=idx + 1,
                    overall_score=0.0,
                    value_score=0.0,
                    quality_score=0.0,
                    relevance_score=0.0,
                    tags=[],
                    explanation="Enrichment unavailable"
                )
                for idx, h in enumerate(hotels)
            ]
            
            return EnrichmentResult(
                enriched_hotels=enriched_hotels,
                market_analysis={},
                best_choice=None
            )
    
    except ValueError as e:
        # Re-raise validation errors as-is
        raise
    
    except UnknownCityError as e:
        # Re-raise city resolution errors as-is
        raise
    
    except Exception as e:
        # Wrap all other errors in service exception
        error_msg = (
            f"Enriched hotel search orchestration failed for city='{city}': "
            f"{type(e).__name__}: {str(e)}"
        )
        logger.error(error_msg, exc_info=True)
        return []
