"""
API Adapter for Hotel Search (STUB)

This module will provide hotel search functionality using external APIs.
Currently, this is a stub implementation to be completed in the future.

When implemented, this module should:
- Call external hotel search APIs
- Handle API authentication and rate limiting
- Convert API responses to raw dictionaries
- Return data in the same format as dataset_adapter
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def search_raw_hotels(
    city: Optional[str] = None,
    min_stars: Optional[int] = None,
    max_price_per_night: Optional[int] = None,
    required_amenities: Optional[list[str]] = None
) -> list[dict]:
    """
    Search for hotels using external API (NOT IMPLEMENTED).
    
    This is a stub function that will be implemented when API integration
    is required. The function signature matches dataset_adapter.search_raw_hotels
    to maintain a consistent interface.
    
    Args:
        city: City name to filter by (optional)
        min_stars: Minimum star rating (1-5, optional)
        max_price_per_night: Maximum price per night in INR (optional)
        required_amenities: List of required amenities (optional)
    
    Returns:
        list[dict]: List of raw hotel dictionaries (when implemented)
    
    Raises:
        NotImplementedError: This function is not yet implemented
    
    TODO:
        - Integrate with hotel search API (e.g., Booking.com, Hotels.com)
        - Add API key configuration
        - Implement error handling and retry logic
        - Convert API response format to dataset-compatible format
        - Add support for check-in/check-out dates
        - Add support for room type and guest count
    """
    logger.warning(
        "API adapter called but not implemented. "
        "Set DATA_SOURCE='dataset' in config to use the dataset adapter."
    )
    
    raise NotImplementedError(
        "API adapter for hotel search is not implemented yet. "
        "Please use DATA_SOURCE='dataset' in your configuration."
    )
