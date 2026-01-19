"""
Hotel Tool Service Layer

This is the public entry point for hotel search functionality.
It orchestrates data retrieval, normalization, sorting, and filtering.

Architecture:
- Uses dataset_adapter or api_adapter based on DATA_SOURCE config
- Normalizes all raw data using normalize module
- Applies sorting and limiting
- Returns normalized HotelOption objects
- Optionally returns pagination metadata for UI/API consumption
"""

import logging
from dataclasses import dataclass
from typing import Optional, Union

from backend.travel_agent.config import DATA_SOURCE
from backend.travel_agent.schemas import HotelOption

from . import dataset_adapter, api_adapter
from .normalize import raw_to_hoteloption

logger = logging.getLogger(__name__)


@dataclass
class HotelSearchResult:
    """
    Hotel search result with pagination metadata.
    
    This is used when return_metadata=True to provide additional
    information about the search results for UI/API pagination.
    
    Attributes:
        hotels: List of matching hotel options
        total_found: Total number of hotels matching the filters (before limit)
        returned: Number of hotels actually returned (after limit)
        skipped: Number of malformed hotels that were skipped
        limit: The limit that was applied (None if no limit)
        has_more: Whether there are more results available beyond the limit
    """
    hotels: list[HotelOption]
    total_found: int
    returned: int
    skipped: int
    limit: Optional[int]
    has_more: bool


def search_hotels(
    city: Optional[str] = None,
    min_stars: Optional[int] = None,
    max_price_per_night: Optional[int] = None,
    required_amenities: Optional[list[str]] = None,
    limit: Optional[int] = 5,
    sort_by_price: bool = True,
    return_metadata: bool = False
) -> Union[list[HotelOption], HotelSearchResult]:
    """
    Search for hotels based on filter criteria.
    
    This is the main public API for hotel search. It handles:
    - Adapter selection based on DATA_SOURCE configuration
    - Input validation
    - Raw data retrieval from the appropriate adapter
    - Normalization of raw data to HotelOption objects
    - Sorting by price (if requested)
    - Limiting results
    - Error handling for malformed data
    
    Args:
        city: City name to filter by (case-insensitive, optional)
        min_stars: Minimum star rating (1-5, inclusive, optional)
        max_price_per_night: Maximum price per night in INR (inclusive, optional)
        required_amenities: List of required amenities (all must be present, optional)
        limit: Maximum number of results to return (default: 5, None = return all)
        sort_by_price: Whether to sort results by price ascending (default: True)
        return_metadata: If True, return HotelSearchResult with pagination metadata.
                        If False (default), return only list[HotelOption] for backward compatibility.
    
    Returns:
        Union[list[HotelOption], HotelSearchResult]: 
            - If return_metadata=False: List of normalized hotel options
            - If return_metadata=True: HotelSearchResult with hotels and pagination metadata
    
    Raises:
        ValueError: If input validation fails (e.g., negative limit, invalid star rating)
        NotImplementedError: If DATA_SOURCE is "api" and API adapter is not implemented
    
    Example:
        >>> hotels = search_hotels(
        ...     city="Mumbai",
        ...     min_stars=4,
        ...     max_price_per_night=5000,
        ...     required_amenities=["wifi", "pool"],
        ...     limit=3
        ... )
        >>> for hotel in hotels:
        ...     print(f"{hotel.name}: ₹{hotel.price_per_night}/night")
        Seaside Retreat: ₹3500/night
        Grand Plaza: ₹4200/night
        Ocean View Hotel: ₹4800/night
    """
    # Input validation
    if limit is not None and limit < 0:
        raise ValueError(f"limit must be non-negative or None, got {limit}")
    
    if max_price_per_night is not None and max_price_per_night < 0:
        raise ValueError(f"max_price_per_night must be non-negative, got {max_price_per_night}")
    
    if min_stars is not None and not (1 <= min_stars <= 5):
        raise ValueError(f"min_stars must be between 1 and 5, got {min_stars}")
    
    # Log search request
    logger.info(
        f"Hotel search requested: city={city}, min_stars={min_stars}, "
        f"max_price_per_night={max_price_per_night}, required_amenities={required_amenities}, "
        f"limit={limit}, sort_by_price={sort_by_price}, data_source={DATA_SOURCE}"
    )
    
    # Select appropriate adapter based on configuration
    if DATA_SOURCE == "dataset":
        raw_hotels = dataset_adapter.search_raw_hotels(
            city=city,
            min_stars=min_stars,
            max_price_per_night=max_price_per_night,
            required_amenities=required_amenities
        )
    elif DATA_SOURCE == "api":
        raw_hotels = api_adapter.search_raw_hotels(
            city=city,
            min_stars=min_stars,
            max_price_per_night=max_price_per_night,
            required_amenities=required_amenities
        )
    else:
        raise ValueError(f"Invalid DATA_SOURCE: {DATA_SOURCE}")
    
    # Normalize raw hotels to HotelOption objects
    normalized_hotels: list[HotelOption] = []
    skipped_count = 0
    
    for raw_hotel in raw_hotels:
        try:
            hotel_option = raw_to_hoteloption(raw_hotel)
            normalized_hotels.append(hotel_option)
        except (ValueError, KeyError) as e:
            # Skip malformed rows but log them
            skipped_count += 1
            hotel_id = raw_hotel.get("hotel_id", "UNKNOWN")
            logger.warning(
                f"Skipped malformed hotel {hotel_id}: {e}"
            )
    
    if skipped_count > 0:
        logger.warning(
            f"Skipped {skipped_count} malformed hotel(s) during normalization"
        )
    
    # Sort by price if requested
    if sort_by_price:
        normalized_hotels.sort(key=lambda h: h.price_per_night)
        logger.debug("Sorted hotels by price (ascending)")
    
    # Apply limit (None means return all)
    total_found = len(normalized_hotels)
    if limit is None:
        results = normalized_hotels
        logger.debug("No limit applied, returning all results")
    else:
        results = normalized_hotels[:limit]
    
    has_more = limit is not None and total_found > limit
    
    logger.info(
        f"Returning {len(results)} hotel(s) "
        f"(total_found={total_found}, skipped={skipped_count}, limit={limit})"
    )
    
    # Return with metadata if requested, otherwise just the hotel list
    if return_metadata:
        return HotelSearchResult(
            hotels=results,
            total_found=total_found,
            returned=len(results),
            skipped=skipped_count,
            limit=limit,
            has_more=has_more
        )
    else:
        return results
