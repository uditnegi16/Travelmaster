"""
Dataset Adapter for Flight Search

This module loads and searches flights from the local JSON dataset.
It returns raw dictionaries without normalization.

Responsibilities:
- Load flights.json from configured path
- Cache data in-memory for performance
- Filter by origin, destination, and max_price
- Return raw dictionaries (NOT FlightOption objects)
"""

import json
import logging
from functools import lru_cache
from typing import Optional

from backend.travel_agent.config import FLIGHTS_DATASET_PATH

logger = logging.getLogger(__name__)

# City name to IATA code mapping for common Indian cities
# This allows searching by either city name or IATA code
CITY_ALIASES = {
    # Delhi variations
    "del": "delhi",
    "new delhi": "delhi",
    "ndls": "delhi",
    
    # Mumbai variations
    "bom": "mumbai",
    "bombay": "mumbai",
    
    # Bangalore variations
    "blr": "bangalore",
    "bengaluru": "bangalore",
    
    # Chennai variations
    "maa": "chennai",
    "madras": "chennai",
    
    # Hyderabad variations
    "hyd": "hyderabad",
    
    # Kolkata variations
    "ccu": "kolkata",
    "calcutta": "kolkata",
    
    # Other cities
    "goi": "goa",
    "cok": "kochi",
    "cochin": "kochi",
}


def _normalize_city_name(city: str) -> str:
    """
    Normalize city name by resolving aliases and IATA codes.
    
    Args:
        city: City name or IATA code (case-insensitive)
    
    Returns:
        str: Normalized city name in lowercase
    
    Example:
        >>> _normalize_city_name("DEL")
        'delhi'
        >>> _normalize_city_name("Bengaluru")
        'bangalore'
        >>> _normalize_city_name("Mumbai")
        'mumbai'
    """
    normalized = city.strip().lower()
    return CITY_ALIASES.get(normalized, normalized)


# NOTE: TTL Cache Strategy
# ========================
# Current implementation uses @lru_cache(maxsize=1) which caches forever.
# This is PERFECT for dataset mode (static data that never changes).
#
# For future API mode, consider using TTL-based caching:
# Option 1: cachetools.TTLCache(maxsize=1, ttl=3600)  # 1 hour TTL
# Option 2: functools.lru_cache with manual invalidation
# Option 3: Redis/memcached for distributed caching
#
# For MVP dataset mode, the current implementation is optimal.
# ========================

@lru_cache(maxsize=1)
def _load_flights_dataset() -> list[dict]:
    """
    Load flights dataset from JSON file and cache it in memory.
    
    This function uses lru_cache to ensure the dataset is loaded only once
    and reused across multiple calls for performance.
    
    Returns:
        list[dict]: List of raw flight dictionaries from the dataset
        
    Raises:
        FileNotFoundError: If the dataset file doesn't exist
        json.JSONDecodeError: If the dataset file is not valid JSON
    """
    logger.info(f"Loading flights dataset from: {FLIGHTS_DATASET_PATH}")
    
    try:
        with open(FLIGHTS_DATASET_PATH, "r", encoding="utf-8") as f:
            flights = json.load(f)
        
        logger.info(f"Successfully loaded {len(flights)} flights from dataset")
        return flights
    
    except FileNotFoundError:
        logger.error(f"Flights dataset not found at {FLIGHTS_DATASET_PATH}")
        raise
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in flights dataset: {e}")
        raise


def search_raw_flights(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    max_price: Optional[int] = None
) -> list[dict]:
    """
    Search for flights in the dataset based on filter criteria.
    
    This function performs case-insensitive, trimmed matching on city names
    and filters by price if specified. It returns raw dictionaries that need
    to be normalized by the normalize module.
    
    Args:
        origin: Origin city to filter by (case-insensitive, optional)
        destination: Destination city to filter by (case-insensitive, optional)
        max_price: Maximum price in INR to filter by (inclusive, optional)
    
    Returns:
        list[dict]: List of raw flight dictionaries matching the criteria.
                    Returns all flights if no filters are specified.
    
    Example:
        >>> flights = search_raw_flights(origin="Delhi", destination="Mumbai", max_price=5000)
        >>> print(len(flights))
        12
    """
    flights = _load_flights_dataset()
    
    # Normalize filter inputs (with city alias/IATA support)
    origin_normalized = _normalize_city_name(origin) if origin else None
    destination_normalized = _normalize_city_name(destination) if destination else None
    
    logger.debug(
        f"Searching flights with filters: origin={origin_normalized}, "
        f"destination={destination_normalized}, max_price={max_price}"
    )
    
    # Apply filters
    results = []
    for flight in flights:
        # Filter by origin (with alias resolution)
        if origin_normalized:
            flight_origin = _normalize_city_name(flight.get("from", ""))
            if flight_origin != origin_normalized:
                continue
        
        # Filter by destination (with alias resolution)
        if destination_normalized:
            flight_destination = _normalize_city_name(flight.get("to", ""))
            if flight_destination != destination_normalized:
                continue
        
        # Filter by max_price
        if max_price is not None:
            flight_price = flight.get("price")
            if flight_price is None or flight_price > max_price:
                continue
        
        results.append(flight)
    
    logger.info(
        f"Found {len(results)} flights matching criteria "
        f"(out of {len(flights)} total flights)"
    )
    
    return results
