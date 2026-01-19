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

from backend.app.core.amadeus_iata import UnknownCityError, resolve_city_to_iata
from backend.app.core.logging import get_logger
from backend.app.shared.schemas import HotelOption
from backend.app.tools.hotel.adapters.ratings_api import get_hotel_ratings_api
from backend.app.tools.hotel.adapters.search_api import search_hotels_api
from backend.app.tools.hotel.normalize import normalize_hotels

logger = get_logger(__name__)


class HotelSearchError(RuntimeError):
    """
    Custom exception raised when hotel search orchestration fails.
    
    This exception wraps all service-layer errors that are not validation
    or city resolution errors.
    """
    pass


def search_hotels(
    city: str,
    max_price: int | None = None,
    limit: int = 5,
) -> list[HotelOption]:
    """
    Search for hotels in a city with optional filtering and limiting.
    
    This is the main business orchestrator that:
    1. Resolves city name to IATA code
    2. Calls hotel search API adapter
    3. Extracts hotel IDs from results
    4. Calls ratings API adapter to enrich data
    5. Normalizes raw data into HotelOption schema
    6. Applies business rules (price filtering, sorting, limiting)
    
    Args:
        city: City name to search hotels in (e.g., "Paris", "New York").
              Will be resolved to IATA code internally.
        max_price: Optional maximum price per night filter.
                  Hotels above this price will be excluded.
                  If <= 0 or None, no price filtering applied.
        limit: Maximum number of results to return.
               Must be > 0, defaults to 5.
    
    Returns:
        List of HotelOption objects, sorted by price (ascending).
        Empty list if no hotels found or all filtered out.
    
    Raises:
        ValueError: If city is empty or not a string, or limit <= 0.
        UnknownCityError: If city cannot be resolved to IATA code.
        HotelSearchError: If any orchestration step fails.
    
    Example:
        >>> hotels = search_hotels("Paris", max_price=200, limit=3)
        >>> len(hotels)
        3
        >>> hotels[0].city
        "PAR"
        >>> hotels[0].price_per_night <= 200
        True
    """
    # Input validation
    if not isinstance(city, str) or not city.strip():
        raise ValueError("city must be a non-empty string")
    
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
        f"max_price={max_price}, limit={limit}"
    )
    
    try:
        # Step 1: Resolve city to IATA code
        city_iata = resolve_city_to_iata(city)
        logger.info(f"Resolved city '{city}' to IATA code '{city_iata}'")
        
        # Step 2: Call search API adapter
        raw_hotels = search_hotels_api(city_iata=city_iata, adults=1)
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
        hotels = normalize_hotels(raw_hotels, ratings_map)
        logger.info(f"Normalized {len(hotels)} hotel(s) into schema objects")
        
        # Step 6: Apply business rules
        
        # Filter by max_price if specified
        if max_price is not None:
            hotels_before = len(hotels)
            hotels = [h for h in hotels if h.price_per_night <= max_price]
            logger.info(
                f"Price filter (max={max_price}): {hotels_before} -> {len(hotels)} hotels"
            )
        
        # Sort by price (ascending)
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
            f"Hotel search orchestration failed for city='{city}': "
            f"{type(e).__name__}: {str(e)}"
        )
        logger.error(error_msg, exc_info=True)
        raise HotelSearchError(error_msg) from e
