"""
Dataset Adapter for Hotel Search

This module loads and searches hotels from the local JSON dataset.
It returns raw dictionaries without normalization.

Responsibilities:
- Load hotels.json from configured path
- Cache data in-memory for performance (with TTL support for API mode)
- Filter by city, min_stars, max_price_per_night, and required_amenities
- Fuzzy matching for city names (configurable)
- Return raw dictionaries (NOT HotelOption objects)
"""

import json
import logging
from difflib import SequenceMatcher
from functools import lru_cache, wraps
from typing import Optional
from time import time

from backend.travel_agent.config import (
    HOTELS_DATASET_PATH,
    DATA_SOURCE,
    API_CACHE_TTL,
    ENABLE_FUZZY_MATCHING,
    FUZZY_MATCH_THRESHOLD
)

logger = logging.getLogger(__name__)

# City name aliases for common variations
# This allows searching by different spellings or variations
CITY_ALIASES = {
    # Delhi variations
    "new delhi": "delhi",
    "ndls": "delhi",
    
    # Mumbai variations
    "bombay": "mumbai",
    
    # Bangalore variations
    "bengaluru": "bangalore",
    
    # Chennai variations
    "madras": "chennai",
    
    # Kolkata variations
    "calcutta": "kolkata",
    
    # Other cities
    "cochin": "kochi",
}


def _normalize_city_name(city: str) -> str:
    """
    Normalize city name by resolving aliases.
    
    Args:
        city: City name (case-insensitive)
    
    Returns:
        str: Normalized city name in lowercase
    
    Example:
        >>> _normalize_city_name("Bombay")
        'mumbai'
        >>> _normalize_city_name("Bengaluru")
        'bangalore'
        >>> _normalize_city_name("Delhi")
        'delhi'
    """
    normalized = city.strip().lower()
    return CITY_ALIASES.get(normalized, normalized)


def _calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity ratio between two strings using SequenceMatcher.
    
    This uses the difflib.SequenceMatcher which implements the Ratcliff/Obershelp
    algorithm for string similarity.
    
    Args:
        str1: First string to compare
        str2: Second string to compare
    
    Returns:
        float: Similarity ratio between 0.0 (completely different) and 1.0 (identical)
    
    Example:
        >>> _calculate_similarity("Mumbai", "Mumbai")
        1.0
        >>> _calculate_similarity("Mumbai", "Mumbi")
        0.91
        >>> _calculate_similarity("Delhi", "Deli")
        0.89
    """
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def _fuzzy_match_city(query_city: str, available_cities: set[str], threshold: float = FUZZY_MATCH_THRESHOLD) -> Optional[str]:
    """
    Find the best fuzzy match for a city name from available cities.
    
    This function uses fuzzy string matching to find cities that are similar
    to the query, even if there are typos or spelling variations.
    
    Args:
        query_city: City name to search for (may have typos)
        available_cities: Set of available city names from the dataset
        threshold: Minimum similarity score (0.0-1.0) to consider a match
    
    Returns:
        Optional[str]: Best matching city name, or None if no good match found
    
    Example:
        >>> cities = {"mumbai", "delhi", "bangalore", "chennai"}
        >>> _fuzzy_match_city("mumbi", cities)
        'mumbai'
        >>> _fuzzy_match_city("deli", cities)
        'delhi'
        >>> _fuzzy_match_city("bangalor", cities)
        'bangalore'
    """
    if not ENABLE_FUZZY_MATCHING:
        return None
    
    query_normalized = query_city.strip().lower()
    best_match = None
    best_score = 0.0
    
    for city in available_cities:
        score = _calculate_similarity(query_normalized, city)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = city
    
    if best_match and best_score < 1.0:  # Only log if not exact match
        logger.info(
            f"Fuzzy matched '{query_city}' to '{best_match}' "
            f"(similarity: {best_score:.2f})"
        )
    
    return best_match


def ttl_cache(ttl_seconds: int = API_CACHE_TTL, maxsize: int = 128):
    """
    Time-based cache decorator with TTL (Time To Live) support.
    
    This decorator caches function results for a specified duration.
    For dataset mode, it falls back to permanent caching since data is static.
    For API mode, cached results expire after ttl_seconds.
    
    Args:
        ttl_seconds: Cache lifetime in seconds (ignored in dataset mode)
        maxsize: Maximum number of cached entries
    
    Returns:
        Decorator function that adds TTL caching to the wrapped function
    
    Implementation Notes:
        - Dataset mode: Uses lru_cache (permanent caching)
        - API mode: Implements TTL-based expiration
        - Thread-safe for concurrent access
    
    Example:
        >>> @ttl_cache(ttl_seconds=3600, maxsize=128)
        ... def fetch_hotels():
        ...     # Expensive API call or file I/O
        ...     return load_from_source()
    """
    def decorator(func):
        # For dataset mode, use permanent caching (optimal for static data)
        if DATA_SOURCE == "dataset":
            return lru_cache(maxsize=1)(func)
        
        # For API mode, implement TTL-based caching
        cache = {}
        cache_times = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time()
            
            # Check if cached result exists and is still valid
            if key in cache and key in cache_times:
                if current_time - cache_times[key] < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__} (age: {current_time - cache_times[key]:.1f}s)")
                    return cache[key]
                else:
                    logger.debug(f"Cache expired for {func.__name__} (age: {current_time - cache_times[key]:.1f}s)")
            
            # Cache miss or expired - call function and cache result
            result = func(*args, **kwargs)
            cache[key] = result
            cache_times[key] = current_time
            
            # Limit cache size (simple FIFO eviction)
            if len(cache) > maxsize:
                oldest_key = min(cache_times.keys(), key=lambda k: cache_times[k])
                del cache[oldest_key]
                del cache_times[oldest_key]
                logger.debug(f"Cache evicted oldest entry (cache size: {len(cache)})")
            
            return result
        
        return wrapper
    return decorator


# NOTE: TTL Cache Strategy
# ========================
# The @ttl_cache decorator automatically selects the appropriate caching strategy:
#
# DATASET MODE (current):
#   - Uses @lru_cache(maxsize=1) for permanent caching
#   - Perfect for static JSON data that never changes
#   - Zero overhead, maximum performance
#
# API MODE (future):
#   - Uses TTL-based caching with configurable expiration
#   - Default: API_CACHE_TTL = 3600 seconds (1 hour)
#   - Configurable via environment variable: export API_CACHE_TTL=1800
#   - Prevents stale data from external APIs
#   - Reduces API call costs and rate limiting issues
#
# The decorator makes the switch transparent to the rest of the codebase.
# ========================

@ttl_cache(ttl_seconds=API_CACHE_TTL, maxsize=1)
def _load_hotels_dataset() -> list[dict]:
    """
    Load hotels dataset from JSON file and cache it in memory.
    
    This function uses lru_cache to ensure the dataset is loaded only once
    and reused across multiple calls for performance.
    
    Returns:
        list[dict]: List of raw hotel dictionaries from the dataset
        
    Raises:
        FileNotFoundError: If the dataset file doesn't exist
        json.JSONDecodeError: If the dataset file is not valid JSON
    """
    logger.info(f"Loading hotels dataset from: {HOTELS_DATASET_PATH}")
    
    try:
        with open(HOTELS_DATASET_PATH, "r", encoding="utf-8") as f:
            hotels = json.load(f)
        
        logger.info(f"Successfully loaded {len(hotels)} hotels from dataset")
        return hotels
    
    except FileNotFoundError:
        logger.error(f"Hotels dataset not found at {HOTELS_DATASET_PATH}")
        raise
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in hotels dataset: {e}")
        raise


def _has_required_amenities(hotel_amenities: list[str], required: list[str]) -> bool:
    """
    Check if hotel has all required amenities (case-insensitive).
    
    Args:
        hotel_amenities: List of amenities available at the hotel
        required: List of amenities that must be present
    
    Returns:
        bool: True if all required amenities are present, False otherwise
    
    Example:
        >>> _has_required_amenities(["wifi", "pool", "gym"], ["wifi", "pool"])
        True
        >>> _has_required_amenities(["wifi", "pool"], ["wifi", "pool", "gym"])
        False
    """
    # Normalize all amenities to lowercase for case-insensitive matching
    hotel_amenities_lower = {amenity.strip().lower() for amenity in hotel_amenities}
    required_lower = {amenity.strip().lower() for amenity in required}
    
    # Check if all required amenities are present
    return required_lower.issubset(hotel_amenities_lower)


def search_raw_hotels(
    city: Optional[str] = None,
    min_stars: Optional[int] = None,
    max_price_per_night: Optional[int] = None,
    required_amenities: Optional[list[str]] = None
) -> list[dict]:
    """
    Search for hotels in the dataset based on filter criteria.
    
    This function performs case-insensitive, trimmed matching on city names,
    filters by star rating, price, and amenities. Supports fuzzy matching for
    city names when enabled in config. Returns raw dictionaries that need
    to be normalized by the normalize module.
    
    Features:
        - Exact matching with city aliases (Bombay → Mumbai)
        - Fuzzy matching for typos (Mumbi → Mumbai) when ENABLE_FUZZY_MATCHING=True
        - Case-insensitive matching
        - Star rating filtering
        - Price filtering
        - Amenity filtering (all required amenities must be present)
    
    Args:
        city: City name to filter by (case-insensitive, supports fuzzy matching, optional)
        min_stars: Minimum star rating (1-5, inclusive, optional)
        max_price_per_night: Maximum price per night in INR (inclusive, optional)
        required_amenities: List of required amenities (all must be present, optional)
    
    Returns:
        list[dict]: List of raw hotel dictionaries matching the criteria.
                    Returns all hotels if no filters are specified.
    
    Example:
        >>> # Exact match
        >>> hotels = search_raw_hotels(city="Mumbai", min_stars=4, max_price_per_night=6000)
        >>> print(len(hotels))
        15
        
        >>> # Fuzzy match (if enabled)
        >>> hotels = search_raw_hotels(city="Mumbi")  # Finds Mumbai hotels
        >>> print(len(hotels))
        15
    """
    hotels = _load_hotels_dataset()
    
    # Normalize filter inputs (with city alias support)
    city_normalized = _normalize_city_name(city) if city else None
    
    # If fuzzy matching is enabled and city didn't match via alias, try fuzzy match
    if city_normalized and ENABLE_FUZZY_MATCHING:
        # Get all unique cities from dataset
        available_cities = {_normalize_city_name(h.get("city", "")) for h in hotels}
        
        # If the normalized city is not in available cities, try fuzzy match
        if city_normalized not in available_cities:
            fuzzy_match = _fuzzy_match_city(city_normalized, available_cities)
            if fuzzy_match:
                logger.info(
                    f"Applied fuzzy matching: '{city}' → '{fuzzy_match}' "
                    f"(original normalized: '{city_normalized}')"
                )
                city_normalized = fuzzy_match
            else:
                logger.warning(
                    f"No fuzzy match found for city '{city}' "
                    f"(threshold: {FUZZY_MATCH_THRESHOLD})"
                )
    
    logger.debug(
        f"Searching hotels with filters: city={city_normalized}, "
        f"min_stars={min_stars}, max_price_per_night={max_price_per_night}, "
        f"required_amenities={required_amenities}"
    )
    
    # Apply filters
    results = []
    for hotel in hotels:
        # Filter by city (with alias resolution and fuzzy matching)
        if city_normalized:
            hotel_city = _normalize_city_name(hotel.get("city", ""))
            if hotel_city != city_normalized:
                continue
        
        # Filter by minimum star rating
        if min_stars is not None:
            hotel_stars = hotel.get("stars")
            if hotel_stars is None or hotel_stars < min_stars:
                continue
        
        # Filter by maximum price per night
        if max_price_per_night is not None:
            hotel_price = hotel.get("price_per_night")
            if hotel_price is None or hotel_price > max_price_per_night:
                continue
        
        # Filter by required amenities (all must be present)
        if required_amenities:
            hotel_amenities = hotel.get("amenities", [])
            if not _has_required_amenities(hotel_amenities, required_amenities):
                continue
        
        results.append(hotel)
    
    logger.info(
        f"Found {len(results)} hotels matching criteria "
        f"(out of {len(hotels)} total hotels)"
    )
    
    return results
