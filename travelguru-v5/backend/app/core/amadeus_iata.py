"""
IATA resolver using Amadeus Airport & City Search API.

This module provides comprehensive airport and city resolution using the Amadeus
Reference Data API. It includes caching, search capabilities, and detailed
airport information retrieval.

Features:
- City-to-IATA code resolution
- Airport search by keyword
- Detailed airport information
- In-memory caching to reduce API calls
- Support for fuzzy matching
- Pagination support for large result sets

Usage:
    >>> resolve_city_to_iata("Delhi")
    'DEL'
    
    >>> airport_info = resolve_city_to_airport("New York")
    >>> airport_info['iata']
    'JFK'
    
    >>> results = search_airports("London", max_results=5)
    >>> len(results) > 0
    True
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.amadeus_client import call_amadeus, get_amadeus_client
from app.core.logging import get_logger

logger = get_logger(__name__)


class UnknownCityError(ValueError):
    """Raised when a city cannot be resolved to an IATA code."""

    pass


class AmadeusAPIError(Exception):
    """Raised when Amadeus API call fails."""

    pass


# In-memory cache for resolved cities/airports
_CITY_CACHE: Dict[str, Dict[str, Any]] = {}


def _normalize_query(query: str) -> str:
    """Normalize city/airport query for consistent lookups."""
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")
    return query.strip().lower()


def _extract_airport_data(location_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract standardized airport data from Amadeus location response.

    Args:
        location_data: Raw location data from Amadeus API

    Returns:
        Standardized airport dictionary with keys:
        - iata: IATA airport code
        - city: City name
        - country: Country name
        - country_code: ISO country code
        - airport: Full airport name
        - subType: Location type (CITY or AIRPORT)
        - latitude: Geographic latitude
        - longitude: Geographic longitude
        - timezone: Airport timezone
    """
    address = location_data.get("address", {})
    geo_code = location_data.get("geoCode", {})

    return {
        "iata": location_data.get("iataCode", ""),
        "city": address.get("cityName", ""),
        "country": address.get("countryName", ""),
        "country_code": address.get("countryCode", ""),
        "airport": location_data.get("name", ""),
        "subType": location_data.get("subType", ""),
        "latitude": geo_code.get("latitude"),
        "longitude": geo_code.get("longitude"),
        "timezone": location_data.get("timeZoneOffset"),
        "relevance": location_data.get("relevance", 0),
    }


def search_airports(
    keyword: str,
    max_results: int = 10,
    subtype: str = "CITY,AIRPORT",
    country_code: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search for airports and cities using Amadeus Locations API.

    Args:
        keyword: Search keyword (city name, airport name, or IATA code)
        max_results: Maximum number of results to return (default: 10)
        subtype: Filter by location type - "CITY", "AIRPORT", or "CITY,AIRPORT"
        country_code: Optional ISO country code filter (e.g., "US", "IN")

    Returns:
        List of airport dictionaries sorted by relevance

    Raises:
        AmadeusAPIError: If the API call fails
        ValueError: If keyword is invalid

    Examples:
        >>> results = search_airports("Delhi")
        >>> results[0]['iata']
        'DEL'
        
        >>> us_airports = search_airports("New York", country_code="US")
    """
    normalized = _normalize_query(keyword)

    logger.info(f"Searching airports via Amadeus: {keyword}")

    client = get_amadeus_client()

    try:
        params = {
            "keyword": keyword.strip(),
            "subType": subtype,
            "page": {"limit": min(max_results, 20)},  # Amadeus max is typically 20
        }

        if country_code:
            params["countryCode"] = country_code.upper()

        response = call_amadeus(client.reference_data.locations.get, **params)

        data = response.data if hasattr(response, "data") else []

        results = [_extract_airport_data(loc) for loc in data]

        # Sort by relevance (descending) and filter out entries without IATA codes
        results = [r for r in results if r.get("iata")]
        results.sort(key=lambda x: x.get("relevance", 0), reverse=True)

        logger.info(f"Found {len(results)} airports for keyword '{keyword}'")

        return results[:max_results]

    except Exception as e:
        logger.error(f"Amadeus airport search failed for '{keyword}': {e}")
        raise AmadeusAPIError(f"Failed to search airports: {keyword}") from e


def resolve_city_to_iata(
    city_name: str, prefer_city: bool = True, use_cache: bool = True
) -> str:
    """
    Resolve a city name to an IATA code using Amadeus Locations API.

    Args:
        city_name: Human readable city name (e.g., "Delhi", "New York")
        prefer_city: If True, prefer CITY-type results over AIRPORT-type
        use_cache: If True, use cached results to reduce API calls

    Returns:
        IATA code (e.g., "DEL", "JFK")

    Raises:
        UnknownCityError: If city cannot be resolved
        ValueError: If city_name is invalid

    Examples:
        >>> resolve_city_to_iata("Delhi")
        'DEL'
        
        >>> resolve_city_to_iata("Mumbai")
        'BOM'
    """
    normalized = _normalize_query(city_name)

    # Check cache first
    if use_cache and normalized in _CITY_CACHE:
        cached_iata = _CITY_CACHE[normalized].get("iata")
        if cached_iata:
            logger.debug(f"Cache hit for city '{city_name}' → '{cached_iata}'")
            return cached_iata

    logger.info(f"Resolving city to IATA via Amadeus: {city_name}")

    try:
        results = search_airports(city_name, max_results=10)

        if not results:
            raise UnknownCityError(f"No IATA code found for city: {city_name}")

        # Prefer CITY results if requested
        if prefer_city:
            city_results = [r for r in results if r.get("subType") == "CITY"]
            chosen = city_results[0] if city_results else results[0]
        else:
            chosen = results[0]

        iata = chosen.get("iata", "").upper()

        if not iata:
            raise UnknownCityError(f"No IATA code found for city: {city_name}")

        # Cache the result
        if use_cache:
            _CITY_CACHE[normalized] = chosen

        logger.info(f"Resolved city '{city_name}' → IATA '{iata}'")
        return iata

    except AmadeusAPIError as e:
        raise UnknownCityError(f"Failed to resolve city: {city_name}") from e


def resolve_city_to_airport(city_name: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    Resolve a city name to full airport information.

    Args:
        city_name: City name (e.g., "Delhi", "New York")
        use_cache: If True, use cached results to reduce API calls

    Returns:
        Dictionary containing complete airport information

    Raises:
        UnknownCityError: If city cannot be resolved
        ValueError: If city_name is invalid

    Examples:
        >>> info = resolve_city_to_airport("Delhi")
        >>> info['iata']
        'DEL'
        >>> info['airport']
        'Indira Gandhi International Airport'
    """
    normalized = _normalize_query(city_name)

    # Check cache first
    if use_cache and normalized in _CITY_CACHE:
        logger.debug(f"Cache hit for city '{city_name}'")
        return _CITY_CACHE[normalized].copy()

    logger.info(f"Resolving city to airport info via Amadeus: {city_name}")

    try:
        results = search_airports(city_name, max_results=10)

        if not results:
            raise UnknownCityError(f"No airport found for city: {city_name}")

        # Prefer CITY results, fallback to AIRPORT
        city_results = [r for r in results if r.get("subType") == "CITY"]
        chosen = city_results[0] if city_results else results[0]

        # Cache the result
        if use_cache:
            _CITY_CACHE[normalized] = chosen

        logger.info(
            f"Resolved city '{city_name}' to airport '{chosen.get('airport')}'"
        )

        return chosen.copy()

    except AmadeusAPIError as e:
        raise UnknownCityError(f"Failed to resolve city: {city_name}") from e


def get_airport_by_iata(iata_code: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    Get detailed airport information by IATA code.

    Args:
        iata_code: 3-letter IATA airport code (e.g., "DEL", "JFK")
        use_cache: If True, use cached results

    Returns:
        Dictionary containing airport information

    Raises:
        UnknownCityError: If airport not found
        ValueError: If IATA code is invalid

    Examples:
        >>> airport = get_airport_by_iata("DEL")
        >>> airport['city']
        'Delhi'
    """
    if not iata_code or not isinstance(iata_code, str):
        raise ValueError("IATA code must be a non-empty string")

    iata_upper = iata_code.strip().upper()

    if len(iata_upper) != 3:
        raise ValueError(f"IATA code must be 3 characters: {iata_code}")

    cache_key = f"iata:{iata_upper}"

    # Check cache
    if use_cache and cache_key in _CITY_CACHE:
        logger.debug(f"Cache hit for IATA '{iata_upper}'")
        return _CITY_CACHE[cache_key].copy()

    logger.info(f"Looking up IATA code via Amadeus: {iata_upper}")

    try:
        results = search_airports(iata_upper, max_results=5, subtype="AIRPORT")

        # Find exact match
        exact_match = next((r for r in results if r.get("iata") == iata_upper), None)

        if not exact_match:
            raise UnknownCityError(f"No airport found for IATA code: {iata_code}")

        # Cache the result
        if use_cache:
            _CITY_CACHE[cache_key] = exact_match

        logger.info(
            f"Found airport '{exact_match.get('airport')}' for IATA '{iata_upper}'"
        )

        return exact_match.copy()

    except AmadeusAPIError as e:
        raise UnknownCityError(f"Failed to lookup IATA code: {iata_code}") from e


def is_supported_city(city_name: str) -> bool:
    """
    Check if a city is supported (can be resolved to an IATA code).

    Args:
        city_name: City name to check

    Returns:
        True if the city can be resolved, False otherwise

    Examples:
        >>> is_supported_city("Delhi")
        True
        >>> is_supported_city("NonexistentCity12345")
        False
    """
    try:
        resolve_city_to_iata(city_name)
        return True
    except (UnknownCityError, ValueError, AmadeusAPIError):
        return False


def clear_cache() -> None:
    """Clear the in-memory cache of resolved cities and airports."""
    global _CITY_CACHE
    cache_size = len(_CITY_CACHE)
    _CITY_CACHE.clear()
    logger.info(f"Cleared {cache_size} entries from IATA cache")


def save_cache_to_file(file_path: str | Path) -> None:
    """
    Save the current cache to a JSON file for persistence.

    Args:
        file_path: Path where the cache should be saved

    Examples:
        >>> save_cache_to_file("airports_cache.json")
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(_CITY_CACHE, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(_CITY_CACHE)} cache entries to {path}")


def load_cache_from_file(file_path: str | Path) -> None:
    """
    Load cache from a JSON file.

    Args:
        file_path: Path to the cache file

    Raises:
        FileNotFoundError: If the cache file doesn't exist

    Examples:
        >>> load_cache_from_file("airports_cache.json")
    """
    global _CITY_CACHE

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Cache file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        _CITY_CACHE = json.load(f)

    logger.info(f"Loaded {len(_CITY_CACHE)} cache entries from {path}")


__all__ = [
    "UnknownCityError",
    "AmadeusAPIError",
    "search_airports",
    "resolve_city_to_iata",
    "resolve_city_to_airport",
    "get_airport_by_iata",
    "is_supported_city",
    "clear_cache",
    "save_cache_to_file",
    "load_cache_from_file",
]
