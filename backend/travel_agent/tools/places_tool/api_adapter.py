"""
API Adapter for Places Search (STUB)

This module will provide places of interest search functionality using external APIs.
Currently, this is a stub implementation to be completed in the future.

When implemented, this module should:
- Call external places/attractions search APIs
- Handle API authentication and rate limiting
- Convert API responses to raw dictionaries
- Return data in the same format as dataset_adapter
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def search_raw_places(
    city: Optional[str] = None,
    category: Optional[str] = None,
    min_rating: Optional[float] = None
) -> list[dict]:
    """
    Search for places using external API (NOT IMPLEMENTED).
    
    This is a stub function that will be implemented when API integration
    is required. The function signature matches dataset_adapter.search_raw_places
    to maintain a consistent interface.
    
    Args:
        city: City name to filter by (optional)
        category: Place category/type to filter by (optional)
        min_rating: Minimum rating (0.0-5.0, optional)
    
    Returns:
        list[dict]: List of raw place dictionaries (when implemented)
    
    Raises:
        NotImplementedError: This function is not yet implemented
    
    TODO:
        - Integrate with places/attractions API (e.g., Google Places, TripAdvisor)
        - Add API key configuration
        - Implement error handling and retry logic
        - Convert API response format to dataset-compatible format
        - Add support for geolocation and radius search
        - Add support for opening hours and pricing information
    """
    logger.warning(
        "API adapter called but not implemented. "
        "Set DATA_SOURCE='dataset' in config to use the dataset adapter."
    )
    
    raise NotImplementedError(
        "API adapter for places search is not implemented yet. "
        "Please use DATA_SOURCE='dataset' in your configuration."
    )
