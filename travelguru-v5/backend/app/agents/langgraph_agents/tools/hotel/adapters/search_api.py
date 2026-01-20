"""
Hotel Search API Adapter.

This module is a pure API adapter for the Amadeus Hotel Search using the correct 2-step flow.
It handles direct communication with the Amadeus API and returns raw JSON data.

IMPORTANT: Amadeus hotel search requires two steps:
1. Get hotel IDs by city (reference-data/locations/hotels/by-city)
2. Get offers for those hotel IDs (shopping/hotel-offers)

Responsibilities:
- Execute 2-step Amadeus hotel search flow
- Validate and sanitize input parameters
- Handle API errors gracefully
- Return raw JSON dictionaries (no normalization or schema validation)

Architecture Layer: Adapter
- NO business logic
- NO data normalization
- NO schema validation
- NO filtering or sorting
- ONLY raw API calls and error handling
"""

from backend.app.core.amadeus_client import call_amadeus, get_amadeus_client
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class HotelSearchAPIError(RuntimeError):
    """
    Custom exception raised when the Amadeus Hotel Search API call fails.
    
    This exception wraps all API-related errors including network issues,
    authentication failures, rate limiting, and invalid responses.
    """
    pass


def search_hotels_api(
    city_iata: str,
    adults: int = 1,
    radius_km: int = 50,
    max_results: int = 50,
) -> list[dict]:
    """
    Search for hotels using the Amadeus 2-step Hotel Search flow.
    
    This function implements the correct Amadeus hotel search flow:
    Step 1: Get hotel IDs by city using reference-data API
    Step 2: Get offers for those hotels using shopping API
    
    This is a pure API adapter that returns raw JSON data without any
    transformation or validation.
    
    Args:
        city_iata: IATA code of the city (e.g., 'DEL' for Delhi).
                   Must be a non-empty string.
        adults: Number of adult guests. Minimum 1. Defaults to 1.
        radius_km: Search radius parameter (currently not used in 2-step flow).
                   Kept for API compatibility. Defaults to 50.
        max_results: Maximum number of hotel offers to return.
                     Will be clamped to 200 (Amadeus limit). Defaults to 50.
    
    Returns:
        List of raw hotel offer dictionaries from Amadeus API.
        Returns empty list if no hotels found or no offers available.
    
    Raises:
        ValueError: If city_iata is empty or not a string.
        HotelSearchAPIError: If any Amadeus API call fails.
    
    Example:
        >>> offers = search_hotels_api(city_iata="DEL", adults=2, max_results=10)
        >>> len(offers)
        10
    
    Note:
        Amadeus Self-Service accounts often return 0 hotels. This is normal
        and expected behavior in sandbox environments.
    """
    # Input validation
    if not isinstance(city_iata, str) or not city_iata.strip():
        raise ValueError("city_iata must be a non-empty string")
    
    # Sanitize and clamp parameters
    city_iata = city_iata.strip().upper()
    adults = max(1, int(adults))
    max_results = min(200, max(1, int(max_results)))  # Amadeus limit
    
    logger.info(
        f"Starting 2-step hotel search for city={city_iata}, "
        f"adults={adults}, max_results={max_results}"
    )
    
    try:
        # Get Amadeus client
        client = get_amadeus_client()
        
        # ============================================================
        # STEP 1: Get hotel IDs by city
        # ============================================================
        logger.debug(f"Step 1: Fetching hotel IDs for city={city_iata}")
        
        hotels_by_city_response = call_amadeus(
            fn=client.reference_data.locations.hotels.by_city.get,
            cityCode=city_iata
        )
        
        # Extract hotel IDs from response
        if not hasattr(hotels_by_city_response, "data"):
            logger.warning(
                f"Step 1: Response has no 'data' attribute for city={city_iata}"
            )
            return []
        
        hotel_data = hotels_by_city_response.data
        
        if not hotel_data:
            logger.info(f"Step 1: No hotels found in city={city_iata}")
            return []
        
        # Extract hotel IDs
        hotel_ids = []
        for item in hotel_data:
            # Handle both dict and object responses
            if hasattr(item, "hotelId"):
                hotel_ids.append(item.hotelId)
            elif isinstance(item, dict) and "hotelId" in item:
                hotel_ids.append(item["hotelId"])
        
        if not hotel_ids:
            logger.warning(
                f"Step 1: No valid hotel IDs found in {len(hotel_data)} items "
                f"for city={city_iata}"
            )
            return []
        
        logger.info(
            f"Step 1: Found {len(hotel_ids)} hotel ID(s) for city={city_iata}"
        )
        
        # ============================================================
        # STEP 2: Get offers for hotel IDs
        # ============================================================
        # Limit hotel IDs to prevent oversized requests
        # Use min of max_results and 50 (Amadeus best practice)
        hotel_ids_limit = min(max_results, 50)
        hotel_ids_to_fetch = hotel_ids[:hotel_ids_limit]
        
        logger.debug(
            f"Step 2: Fetching offers for {len(hotel_ids_to_fetch)} hotel(s)"
        )
        
        # Build comma-separated hotel IDs string
        hotel_ids_param = ",".join(str(hid) for hid in hotel_ids_to_fetch)
        
        offers_response = call_amadeus(
            fn=client.shopping.hotel_offers_search.get,
            hotelIds=hotel_ids_param,
            adults=adults
        )
        
        # Extract offers from response
        if not hasattr(offers_response, "data"):
            logger.warning("Step 2: Response has no 'data' attribute")
            return []
        
        offers = offers_response.data
        
        if not offers:
            logger.info(
                f"Step 2: No offers found for {len(hotel_ids_to_fetch)} hotel(s)"
            )
            return []
        
        logger.info(
            f"Step 2: Successfully retrieved {len(offers)} offer(s) "
            f"for city={city_iata}"
        )
        
        return offers
    
    except ValueError as e:
        # Re-raise validation errors as-is
        raise
    
    except Exception as e:
        # Catch all API errors and wrap in custom exception
        error_msg = (
            f"Failed to search hotels for city={city_iata}: "
            f"{type(e).__name__}: {str(e)}"
        )
        logger.error(error_msg, exc_info=True)
        raise HotelSearchAPIError(error_msg) from e