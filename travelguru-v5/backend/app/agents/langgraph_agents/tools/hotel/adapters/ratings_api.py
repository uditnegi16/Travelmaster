"""
Hotel Ratings API Adapter.

This module is a pure API adapter for the Amadeus Hotel Ratings / Sentiment API
(also known as E-Reputation / Hotel Sentiments API).
It handles direct communication with the Amadeus API and returns raw JSON data.

Responsibilities:
- Call Amadeus Hotel Sentiments API using the official SDK
- Validate and sanitize input parameters
- Handle API errors gracefully
- Return raw JSON dictionaries (no normalization or schema validation)

Architecture Layer: Adapter
- NO business logic
- NO data normalization
- NO schema validation
- NO rating mapping or merging
- ONLY raw API calls and error handling
"""

from app.core.amadeus_client import call_amadeus, get_amadeus_client
from app.core.logging import get_logger

logger = get_logger(__name__)


class HotelRatingsAPIError(RuntimeError):
    """
    Custom exception raised when the Amadeus Hotel Ratings API call fails.
    
    This exception wraps all API-related errors including network issues,
    authentication failures, rate limiting, and invalid responses.
    """
    pass


def get_hotel_ratings_api(
    hotel_ids: list[str],
) -> dict[str, dict]:
    """
    Fetch hotel ratings and sentiment data from Amadeus API.
    
    This function is a pure API adapter that calls the Amadeus Hotel Sentiments API
    and returns raw JSON data without any transformation or validation.
    
    Args:
        hotel_ids: List of Amadeus hotel IDs to fetch ratings for.
                   Empty, None, or non-string values will be filtered out.
    
    Returns:
        Dictionary mapping hotel IDs to their raw rating objects.
        Returns empty dict if no valid hotel IDs provided or no results found.
        
        Example:
        {
            "HOTEL_ID_1": {"hotelId": "HOTEL_ID_1", "overallRating": "87", ...},
            "HOTEL_ID_2": {"hotelId": "HOTEL_ID_2", "overallRating": "92", ...}
        }
    
    Raises:
        ValueError: If hotel_ids is not a list.
        HotelRatingsAPIError: If the Amadeus API call fails for any reason.
    
    Example:
        >>> ratings = get_hotel_ratings_api(["HILTON123", "TAJ456"])
        >>> ratings["HILTON123"]["overallRating"]
        "87"
    """
    # Input validation
    if not isinstance(hotel_ids, list):
        raise ValueError("hotel_ids must be a list")
    
    # Filter out empty, None, or non-string hotel IDs
    valid_ids = [
        str(hotel_id).strip()
        for hotel_id in hotel_ids
        if hotel_id and isinstance(hotel_id, str) and str(hotel_id).strip()
    ]
    
    # Cap to Amadeus API limit (typically 50 hotels per request)
    valid_ids = valid_ids[:50]
    
    # Early return if no valid IDs
    if not valid_ids:
        logger.info("No valid hotel IDs provided, returning empty dict")
        return {}
    
    logger.info(f"Fetching ratings for {len(valid_ids)} hotel(s)")
    
    try:
        # Get Amadeus client
        client = get_amadeus_client()
        
        # Prepare API parameters - Amadeus expects comma-separated string
        hotel_ids_param = ",".join(valid_ids)
        
        logger.debug(f"Calling Amadeus Hotel Sentiments API for hotels: {hotel_ids_param}")
        
        # Call Amadeus API using the centralized wrapper
        response = call_amadeus(
            fn=client.e_reputation.hotel_sentiments.get,
            hotelIds=hotel_ids_param
        )
        
        # Extract data from response
        if not hasattr(response, "data"):
            logger.warning("Amadeus response has no 'data' attribute")
            return {}
        
        ratings_list = response.data
        
        # Handle empty results
        if not ratings_list:
            logger.info(f"No ratings found for {len(valid_ids)} hotel(s)")
            return {}
        
        # Convert list to dict mapping hotelId -> rating object
        ratings_dict = {}
        for rating in ratings_list:
            # Each rating object should have a hotelId field
            if hasattr(rating, "hotelId"):
                hotel_id = rating.hotelId
                # Normalize SDK object to dict
                rating_dict = rating if isinstance(rating, dict) else vars(rating)
            elif isinstance(rating, dict) and "hotelId" in rating:
                hotel_id = rating["hotelId"]
                rating_dict = rating
            else:
                logger.warning(f"Rating object missing hotelId field: {rating}")
                continue
            
            ratings_dict[hotel_id] = rating_dict
        
        logger.info(
            f"Successfully retrieved {len(ratings_dict)} rating(s) for "
            f"{len(valid_ids)} hotel(s)"
        )
        
        return ratings_dict
    
    except ValueError as e:
        # Re-raise validation errors as-is
        raise
    
    except Exception as e:
        # Catch all API errors and wrap in custom exception
        error_msg = (
            f"Failed to fetch hotel ratings for {len(valid_ids)} hotel(s): "
            f"{type(e).__name__}: {str(e)}"
        )
        logger.error(error_msg, exc_info=True)
        raise HotelRatingsAPIError(error_msg) from e
