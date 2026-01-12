"""
Flight Tool Service Layer

This is the public entry point for flight search functionality.
It orchestrates data retrieval, normalization, sorting, and filtering.

Architecture:
- Uses dataset_adapter or api_adapter based on DATA_SOURCE config
- Normalizes all raw data using normalize module
- Applies sorting and limiting
- Returns normalized FlightOption objects
- Optionally returns pagination metadata for UI/API consumption
"""

import logging
from dataclasses import dataclass
from typing import Optional, Union

from backend.travel_agent.config import DATA_SOURCE
from backend.travel_agent.schemas import FlightOption

from . import dataset_adapter, api_adapter
from .normalize import raw_to_flightoption

logger = logging.getLogger(__name__)


@dataclass
class FlightSearchResult:
    """
    Flight search result with pagination metadata.
    
    This is used when return_metadata=True to provide additional
    information about the search results for UI/API pagination.
    
    Attributes:
        flights: List of matching flight options
        total_found: Total number of flights matching the filters (before limit)
        returned: Number of flights actually returned (after limit)
        skipped: Number of malformed flights that were skipped
        limit: The limit that was applied (None if no limit)
        has_more: Whether there are more results available beyond the limit
    """
    flights: list[FlightOption]
    total_found: int
    returned: int
    skipped: int
    limit: Optional[int]
    has_more: bool


def search_flights(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    max_price: Optional[int] = None,
    limit: Optional[int] = 5,
    sort_by_price: bool = True,
    return_metadata: bool = False
) -> Union[list[FlightOption], FlightSearchResult]:
    """
    Search for flights based on filter criteria.
    
    This is the main public API for flight search. It handles:
    - Adapter selection based on DATA_SOURCE configuration
    - Input validation
    - Raw data retrieval from the appropriate adapter
    - Normalization of raw data to FlightOption objects
    - Sorting by price (if requested)
    - Limiting results
    - Error handling for malformed data
    
    Args:
        origin: Origin city, IATA code, or alias (case-insensitive, optional)
        destination: Destination city, IATA code, or alias (case-insensitive, optional)
        max_price: Maximum price in INR to filter by (inclusive, optional)
        limit: Maximum number of results to return (default: 5, None = return all)
        sort_by_price: Whether to sort results by price ascending (default: True)
        return_metadata: If True, return FlightSearchResult with pagination metadata.
                        If False (default), return only list[FlightOption] for backward compatibility.
    
    Returns:
        Union[list[FlightOption], FlightSearchResult]: 
            - If return_metadata=False: List of normalized flight options
            - If return_metadata=True: FlightSearchResult with flights and pagination metadata
    
    Raises:
        ValueError: If input validation fails (e.g., negative limit or max_price)
        NotImplementedError: If DATA_SOURCE is "api" and API adapter is not implemented
    
    Example:
        >>> flights = search_flights(
        ...     origin="Delhi",
        ...     destination="Mumbai",
        ...     max_price=5000,
        ...     limit=3
        ... )
        >>> for flight in flights:
        ...     print(f"{flight.airline}: ₹{flight.price}")
        IndiGo: ₹2907
        Air India: ₹3200
        SpiceJet: ₹4500
    """
    # Input validation
    if limit is not None and limit < 0:
        raise ValueError(f"limit must be non-negative or None, got {limit}")
    
    if max_price is not None and max_price < 0:
        raise ValueError(f"max_price must be non-negative, got {max_price}")
    
    # Log search request
    logger.info(
        f"Flight search requested: origin={origin}, destination={destination}, "
        f"max_price={max_price}, limit={limit}, sort_by_price={sort_by_price}, "
        f"data_source={DATA_SOURCE}"
    )
    
    # Select appropriate adapter based on configuration
    if DATA_SOURCE == "dataset":
        raw_flights = dataset_adapter.search_raw_flights(
            origin=origin,
            destination=destination,
            max_price=max_price
        )
    elif DATA_SOURCE == "api":
        raw_flights = api_adapter.search_raw_flights(
            origin=origin,
            destination=destination,
            max_price=max_price
        )
    else:
        raise ValueError(f"Invalid DATA_SOURCE: {DATA_SOURCE}")
    
    # Normalize raw flights to FlightOption objects
    normalized_flights: list[FlightOption] = []
    skipped_count = 0
    
    for raw_flight in raw_flights:
        try:
            flight_option = raw_to_flightoption(raw_flight)
            normalized_flights.append(flight_option)
        except (ValueError, KeyError) as e:
            # Skip malformed rows but log them
            skipped_count += 1
            flight_id = raw_flight.get("flight_id", "UNKNOWN")
            logger.warning(
                f"Skipped malformed flight {flight_id}: {e}"
            )
    
    if skipped_count > 0:
        logger.warning(
            f"Skipped {skipped_count} malformed flight(s) during normalization"
        )
    
    # Sort by price if requested
    if sort_by_price:
        normalized_flights.sort(key=lambda f: f.price)
        logger.debug("Sorted flights by price (ascending)")
    
    # Apply limit (None means return all)
    total_found = len(normalized_flights)
    if limit is None:
        results = normalized_flights
        logger.debug("No limit applied, returning all results")
    else:
        results = normalized_flights[:limit]
    
    has_more = limit is not None and total_found > limit
    
    logger.info(
        f"Returning {len(results)} flight(s) "
        f"(total_found={total_found}, skipped={skipped_count}, limit={limit})"
    )
    
    # Return with metadata if requested, otherwise just the flight list
    if return_metadata:
        return FlightSearchResult(
            flights=results,
            total_found=total_found,
            returned=len(results),
            skipped=skipped_count,
            limit=limit,
            has_more=has_more
        )
    else:
        return results
