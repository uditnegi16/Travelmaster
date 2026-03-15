"""
Hotel Booking API Adapter.

This module is a pure API adapter for the Amadeus Hotel Booking API
(Hotel Orders / Booking endpoint).
It handles direct communication with the Amadeus API and returns raw JSON data.

Responsibilities:
- Call Amadeus Hotel Booking API using the official SDK
- Validate input payload structure
- Handle API errors gracefully
- Return raw JSON dictionaries (no normalization or schema validation)

Architecture Layer: Adapter
- NO business logic
- NO data normalization
- NO schema validation
- NO guest validation or payment processing
- NO database operations
- ONLY raw API calls and error handling

Note:
- Amadeus Self-Service accounts typically do not support actual bookings
- This adapter will likely receive 401/403/501 errors in sandbox environments
- The implementation is production-ready for when booking access is enabled
"""

from core.amadeus_client import call_amadeus, get_amadeus_client
from core.logging import get_logger

logger = get_logger(__name__)


class HotelBookingAPIError(RuntimeError):
    """
    Custom exception raised when the Amadeus Hotel Booking API call fails.
    
    This exception wraps all API-related errors including network issues,
    authentication failures, authorization errors, rate limiting, and invalid responses.
    
    Note: Self-Service Amadeus accounts typically receive 403/501 errors for booking operations.
    """
    pass


def book_hotel_api(
    hotel_offer_payload: dict,
) -> dict:
    """
    Book a hotel using the Amadeus Hotel Booking API.
    
    This function is a pure API adapter that calls the Amadeus Hotel Orders API
    and returns raw JSON data without any transformation or validation.
    
    Args:
        hotel_offer_payload: Dictionary containing the complete booking request payload.
                           Must include fields like 'data' with guest information,
                           room associations, and payment details according to
                           Amadeus API specification.
    
    Returns:
        Raw booking confirmation dictionary from Amadeus API.
        Contains booking confirmation details, reservation IDs, and status.
    
    Raises:
        ValueError: If hotel_offer_payload is not a dict or is empty.
        HotelBookingAPIError: If the Amadeus API call fails for any reason.
                             Common causes include:
                             - 401/403: Authentication/authorization failures
                             - 501: Not Implemented (booking not supported in sandbox)
                             - 400: Invalid payload structure
                             - Network errors
    
    Example:
        >>> payload = {
        ...     "data": {
        ...         "type": "hotel-order",
        ...         "guests": [{"name": {"firstName": "John", "lastName": "Doe"}}],
        ...         "roomAssociations": [{"guestReferences": [{"guestReference": "1"}]}],
        ...         "payment": {"method": "CREDIT_CARD", ...}
        ...     }
        ... }
        >>> result = book_hotel_api(payload)
        >>> result["data"]["id"]
        "BOOKING_CONFIRMATION_123"
    
    Note:
        This function does NOT validate guest details, payment information, or business rules.
        Input validation is the responsibility of higher layers (Service/Tool).
        This adapter only ensures the payload is a non-empty dictionary.
    """
    # Input validation
    if not isinstance(hotel_offer_payload, dict):
        raise ValueError("hotel_offer_payload must be a dictionary")
    
    if not hotel_offer_payload:
        raise ValueError("hotel_offer_payload cannot be empty")
    
    # Log non-sensitive payload information
    payload_keys = list(hotel_offer_payload.keys())
    payload_size = len(str(hotel_offer_payload))
    
    logger.info(
        f"Starting hotel booking request with payload keys: {payload_keys}, "
        f"size: {payload_size} bytes"
    )
    
    try:
        # Get Amadeus client
        client = get_amadeus_client()
        
        logger.debug("Calling Amadeus Hotel Booking API (hotel_orders.post)")
        
        # Call Amadeus API using the centralized wrapper
        # The payload is passed as the body of the POST request
        response = call_amadeus(
            fn=client.booking.hotel_orders.post,
            body=hotel_offer_payload
        )
        
        # Extract data from response
        if hasattr(response, "data"):
            result = response.data
            logger.info("Hotel booking successful - received confirmation data")
        else:
            # Fallback: return entire response if no .data attribute
            result = response
            logger.warning("Amadeus response has no 'data' attribute, returning full response")
        
        logger.info(
            f"Successfully completed hotel booking request - "
            f"response type: {type(result).__name__}"
        )
        
        return result
    
    except ValueError as e:
        # Re-raise validation errors as-is
        raise
    
    except Exception as e:
        # Catch all API errors and wrap in custom exception
        error_msg = (
            f"Failed to book hotel: {type(e).__name__}: {str(e)}"
        )
        
        # Provide helpful context for common sandbox errors
        if "403" in str(e) or "Forbidden" in str(e):
            logger.error(
                f"{error_msg} - Note: Self-Service Amadeus accounts typically "
                "do not have booking permissions in sandbox",
                exc_info=True
            )
        elif "501" in str(e) or "Not Implemented" in str(e):
            logger.error(
                f"{error_msg} - Note: Booking endpoint may not be implemented "
                "in sandbox environment",
                exc_info=True
            )
        else:
            logger.error(error_msg, exc_info=True)
        
        raise HotelBookingAPIError(error_msg) from e


