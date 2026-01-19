"""
Places Tool Service Layer

This is the public entry point for places of interest search functionality.
It orchestrates data retrieval, normalization, sorting, and filtering.

Architecture:
- Uses dataset_adapter or api_adapter based on DATA_SOURCE config
- Normalizes all raw data using normalize module
- Applies sorting and limiting
- Returns normalized PlaceOption objects
- Optionally returns pagination metadata for UI/API consumption
"""

import logging
from dataclasses import dataclass
from typing import Optional, Union

from travel_agent.config import DATA_SOURCE
from travel_agent.schemas import PlaceOption

from . import dataset_adapter, api_adapter
from .normalize import raw_to_placeoption

logger = logging.getLogger(__name__)


@dataclass
class PlaceSearchResult:
    """
    Place search result with pagination metadata.
    
    This is used when return_metadata=True to provide additional
    information about the search results for UI/API pagination.
    
    Attributes:
        places: List of matching place options
        total_found: Total number of places matching the filters (before limit)
        returned: Number of places actually returned (after limit)
        skipped: Number of malformed places that were skipped
        limit: The limit that was applied (None if no limit)
        has_more: Whether there are more results available beyond the limit
    """
    places: list[PlaceOption]
    total_found: int
    returned: int
    skipped: int
    limit: Optional[int]
    has_more: bool


def search_places(
    city: Optional[str] = None,
    category: Optional[str] = None,
    min_rating: Optional[float] = None,
    limit: Optional[int] = 5,
    sort_by_rating: bool = True,
    return_metadata: bool = False
) -> Union[list[PlaceOption], PlaceSearchResult]:
    """
    Search for places of interest based on filter criteria.
    
    This is the main public API for places search. It handles:
    - Adapter selection based on DATA_SOURCE configuration
    - Input validation
    - Raw data retrieval from the appropriate adapter
    - Normalization of raw data to PlaceOption objects
    - Sorting by rating (if requested)
    - Limiting results
    - Error handling for malformed data
    
    Args:
        city: City name to filter by (case-insensitive, supports fuzzy matching, optional)
        category: Place category/type to filter by (e.g., museum, park, temple, optional)
        min_rating: Minimum rating (0.0-5.0, inclusive, optional)
        limit: Maximum number of results to return (default: 5, None = return all)
        sort_by_rating: Whether to sort results by rating descending (default: True)
        return_metadata: If True, return PlaceSearchResult with pagination metadata.
                        If False (default), return only list[PlaceOption] for backward compatibility.
    
    Returns:
        Union[list[PlaceOption], PlaceSearchResult]: 
            - If return_metadata=False: List of normalized place options
            - If return_metadata=True: PlaceSearchResult with places and pagination metadata
    
    Raises:
        ValueError: If input validation fails (e.g., negative limit, invalid rating)
        NotImplementedError: If DATA_SOURCE is "api" and API adapter is not implemented
    
    Example:
        >>> places = search_places(
        ...     city="Delhi",
        ...     category="museum",
        ...     min_rating=4.0,
        ...     limit=5
        ... )
        >>> for place in places:
        ...     print(f"{place.name}: {place.rating}★")
        Historic Fort: 4.2★
        Popular Museum: 4.5★
        Famous Fort: 4.6★
    """
    # Input validation
    if limit is not None and limit < 0:
        raise ValueError(f"limit must be non-negative or None, got {limit}")
    
    if min_rating is not None and not (0.0 <= min_rating <= 5.0):
        raise ValueError(f"min_rating must be between 0.0 and 5.0, got {min_rating}")
    
    # Log search request
    logger.info(
        f"Place search requested: city={city}, category={category}, "
        f"min_rating={min_rating}, limit={limit}, sort_by_rating={sort_by_rating}, "
        f"data_source={DATA_SOURCE}"
    )
    
    # Select appropriate adapter based on configuration
    if DATA_SOURCE == "dataset":
        raw_places = dataset_adapter.search_raw_places(
            city=city,
            category=category,
            min_rating=min_rating
        )
    elif DATA_SOURCE == "api":
        raw_places = api_adapter.search_raw_places(
            city=city,
            category=category,
            min_rating=min_rating
        )
    else:
        raise ValueError(f"Invalid DATA_SOURCE: {DATA_SOURCE}")
    
    # Normalize raw places to PlaceOption objects
    normalized_places: list[PlaceOption] = []
    skipped_count = 0
    
    for raw_place in raw_places:
        try:
            place_option = raw_to_placeoption(raw_place)
            normalized_places.append(place_option)
        except (ValueError, KeyError) as e:
            # Skip malformed rows but log them
            skipped_count += 1
            place_id = raw_place.get("place_id", "UNKNOWN")
            logger.warning(
                f"Skipped malformed place {place_id}: {e}"
            )
    
    if skipped_count > 0:
        logger.warning(
            f"Skipped {skipped_count} malformed place(s) during normalization"
        )
    
    # Sort by rating if requested (descending - highest rated first)
    if sort_by_rating:
        normalized_places.sort(key=lambda p: p.rating, reverse=True)
        logger.debug("Sorted places by rating (descending)")
    
    # Apply limit (None means return all)
    total_found = len(normalized_places)
    if limit is None:
        results = normalized_places
        logger.debug("No limit applied, returning all results")
    else:
        results = normalized_places[:limit]
    
    has_more = limit is not None and total_found > limit
    
    logger.info(
        f"Returning {len(results)} place(s) "
        f"(total_found={total_found}, skipped={skipped_count}, limit={limit})"
    )
    
    # Return with metadata if requested, otherwise just the place list
    if return_metadata:
        return PlaceSearchResult(
            places=results,
            total_found=total_found,
            returned=len(results),
            skipped=skipped_count,
            limit=limit,
            has_more=has_more
        )
    else:
        return results
