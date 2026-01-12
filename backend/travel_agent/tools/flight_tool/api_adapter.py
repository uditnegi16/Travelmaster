"""
API Adapter for Flight Search (STUB)

This module will provide flight search functionality using external APIs.
Currently, this is a stub implementation to be completed in the future.

When implemented, this module should:
- Call external flight search APIs
- Handle API authentication and rate limiting
- Convert API responses to raw dictionaries
- Return data in the same format as dataset_adapter
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def search_raw_flights(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    max_price: Optional[int] = None
) -> list[dict]:
    """
    Search for flights using external API (NOT IMPLEMENTED).
    
    This is a stub function that will be implemented when API integration
    is required. The function signature matches dataset_adapter.search_raw_flights
    to maintain a consistent interface.
    
    Args:
        origin: Origin city to filter by (optional)
        destination: Destination city to filter by (optional)
        max_price: Maximum price in INR to filter by (optional)
    
    Returns:
        list[dict]: List of raw flight dictionaries (when implemented)
    
    Raises:
        NotImplementedError: This function is not yet implemented
    
    TODO:
        - Integrate with flight search API (e.g., Amadeus, Skyscanner)
        - Add API key configuration
        - Implement error handling and retry logic
        - Convert API response format to dataset-compatible format
    """
    logger.warning(
        "API adapter called but not implemented. "
        "Set DATA_SOURCE='dataset' in config to use the dataset adapter."
    )
    
    raise NotImplementedError(
        "API adapter for flight search is not implemented yet. "
        "Please use DATA_SOURCE='dataset' in your configuration."
    )
