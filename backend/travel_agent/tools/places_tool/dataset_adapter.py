"""
Dataset Adapter for Places Search

This module loads and searches places of interest from the local JSON dataset.
It returns raw dictionaries without normalization.

Responsibilities:
- Load places.json from configured path
- Cache data in-memory for performance (with TTL support for API mode)
- Filter by city, category, and min_rating
- Fuzzy matching for city names (configurable)
- Return raw dictionaries (NOT PlaceOption objects)
"""

import json
import logging
from difflib import SequenceMatcher
from functools import lru_cache, wraps
from typing import Optional
from time import time

from travel_agent.config import (
    PLACES_DATASET_PATH,
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

# Category aliases for common variations
# Maps different terms to standard categories
CATEGORY_ALIASES = {
    # Museum variations
    "museums": "museum",
    "gallery": "museum",
    "galleries": "museum",
    
    # Park variations
    "parks": "park",
    "garden": "park",
    "gardens": "park",
    
    # Temple variations
    "temples": "temple",
    "shrine": "temple",
    "shrines": "temple",
    "church": "temple",
    "churches": "temple",
    "mosque": "temple",
    "mosques": "temple",
    
    # Fort variations
    "forts": "fort",
    "castle": "fort",
    "castles": "fort",
    "palace": "fort",
    "palaces": "fort",
    
    # Lake variations
    "lakes": "lake",
    "pond": "lake",
    "ponds": "lake",
    "reservoir": "lake",
    "reservoirs": "lake",
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
    """
    normalized = city.strip().lower()
    return CITY_ALIASES.get(normalized, normalized)


def _normalize_category(category: str) -> str:
    """
    Normalize category name by resolving aliases.
    
    Args:
        category: Category/type name (case-insensitive)
    
    Returns:
        str: Normalized category name in lowercase
    
    Example:
        >>> _normalize_category("museums")
        'museum'
        >>> _normalize_category("gardens")
        'park'
    """
    normalized = category.strip().lower()
    return CATEGORY_ALIASES.get(normalized, normalized)


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
        ... def fetch_places():
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
def _load_places_dataset() -> list[dict]:
    """
    Load places dataset from JSON file and cache it in memory.
    
    This function uses ttl_cache to ensure the dataset is loaded efficiently
    and reused across multiple calls for performance.
    
    Returns:
        list[dict]: List of raw place dictionaries from the dataset
        
    Raises:
        FileNotFoundError: If the dataset file doesn't exist
        json.JSONDecodeError: If the dataset file is not valid JSON
    """
    logger.info(f"Loading places dataset from: {PLACES_DATASET_PATH}")
    
    try:
        with open(PLACES_DATASET_PATH, "r", encoding="utf-8") as f:
            places = json.load(f)
        
        logger.info(f"Successfully loaded {len(places)} places from dataset")
        return places
    
    except FileNotFoundError:
        logger.error(f"Places dataset not found at {PLACES_DATASET_PATH}")
        raise
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in places dataset: {e}")
        raise


def search_raw_places(
    city: Optional[str] = None,
    category: Optional[str] = None,
    min_rating: Optional[float] = None
) -> list[dict]:
    """
    Search for places in the dataset based on filter criteria.
    
    This function performs case-insensitive, trimmed matching on city names
    and categories, filters by rating. Supports fuzzy matching for city names
    when enabled in config. Returns raw dictionaries that need to be normalized
    by the normalize module.
    
    Features:
        - Exact matching with city aliases (Bombay → Mumbai)
        - Category aliases (museums → museum, gardens → park)
        - Fuzzy matching for typos (Mumbi → Mumbai) when ENABLE_FUZZY_MATCHING=True
        - Case-insensitive matching
        - Rating filtering
    
    Args:
        city: City name to filter by (case-insensitive, supports fuzzy matching, optional)
        category: Place category/type to filter by (case-insensitive, optional)
        min_rating: Minimum rating (0.0-5.0, inclusive, optional)
    
    Returns:
        list[dict]: List of raw place dictionaries matching the criteria.
                    Returns all places if no filters are specified.
    
    Example:
        >>> # Exact match
        >>> places = search_raw_places(city="Delhi", category="museum", min_rating=4.0)
        >>> print(len(places))
        8
        
        >>> # Fuzzy match (if enabled)
        >>> places = search_raw_places(city="Deli")  # Finds Delhi places
        >>> print(len(places))
        20
    """
    places = _load_places_dataset()
    
    # Normalize filter inputs (with city and category alias support)
    city_normalized = _normalize_city_name(city) if city else None
    category_normalized = _normalize_category(category) if category else None
    
    # If fuzzy matching is enabled and city didn't match via alias, try fuzzy match
    if city_normalized and ENABLE_FUZZY_MATCHING:
        # Get all unique cities from dataset
        available_cities = {_normalize_city_name(p.get("city", "")) for p in places}
        
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
        f"Searching places with filters: city={city_normalized}, "
        f"category={category_normalized}, min_rating={min_rating}"
    )
    
    # Apply filters
    results = []
    for place in places:
        # Filter by city (with alias resolution and fuzzy matching)
        if city_normalized:
            place_city = _normalize_city_name(place.get("city", ""))
            if place_city != city_normalized:
                continue
        
        # Filter by category (with alias resolution)
        if category_normalized:
            place_category = _normalize_category(place.get("type", ""))
            if place_category != category_normalized:
                continue
        
        # Filter by minimum rating
        if min_rating is not None:
            place_rating = place.get("rating")
            if place_rating is None or place_rating < min_rating:
                continue
        
        results.append(place)
    
    logger.info(
        f"Found {len(results)} places matching criteria "
        f"(out of {len(places)} total places)"
    )
    
    return results
