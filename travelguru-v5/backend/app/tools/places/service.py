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

from backend.app.core.logging import get_logger
from backend.app.shared.schemas import PlaceOption
from backend.app.tools.places.adapters.google_api import search_places_google_api
from backend.app.tools.places.normalize import normalize_places

logger = get_logger(__name__)


class PlacesSearchError(RuntimeError):
    """
    Custom exception raised when places search orchestration fails.
    
    This exception wraps all service-layer errors that are not validation errors.
    """
    pass


def search_places(
    city: str,
    radius_km: int = 10,
    limit: int = 10,
    min_rating: float = 4.0,
) -> list[PlaceOption]:
    """
    Search for tourist places in a city with filtering and sorting.
    
    This is the main business orchestrator that:
    1. Validates input parameters
    2. Calls Google Places API adapter
    3. Normalizes raw data into PlaceOption schema
    4. Applies business rules (rating filtering, sorting by rating, limiting)
    
    Args:
        city: City name to search places in (e.g., "Paris", "New Delhi").
        radius_km: Search radius in kilometers from city center.
                   Must be between 1 and 50. Defaults to 10.
        limit: Maximum number of results to return.
               Must be between 1 and 50. Defaults to 10.
        min_rating: Minimum rating filter (0-5 scale).
                    Places below this rating are excluded.
                    Must be between 0 and 5. Defaults to 4.0.
    
    Returns:
        List of PlaceOption objects, sorted by rating (descending).
        Empty list if no places found or all filtered out.
    
    Raises:
        ValueError: If inputs are invalid.
        PlacesSearchError: If any orchestration step fails.
    
    Example:
        >>> places = search_places("Paris", radius_km=5, limit=5, min_rating=4.5)
        >>> len(places)
        5
        >>> places[0].rating >= 4.5
        True
        >>> places[0].rating >= places[1].rating
        True
    """
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
    
    logger.info(
        f"Starting places search for city='{city}', "
        f"radius={radius_km}km, limit={limit}, min_rating={min_rating}"
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
        
        # Early return if all filtered out
        if not places:
            logger.info(
                f"No places meet min_rating={min_rating} for city '{city}'"
            )
            return []
        
        # Sort by rating (descending - highest rated first)
        places.sort(key=lambda p: p.rating, reverse=True)
        logger.debug("Sorted places by rating (descending)")
        
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
