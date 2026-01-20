"""
Google Places API Adapter.

This module is a pure API adapter for Google Places API (New) and Google Geocoding API.
It handles direct communication with Google APIs and returns raw JSON data.

Responsibilities:
- Convert city names to coordinates using Google Geocoding API
- Search for nearby places using Google Places API (New)
- Handle API errors gracefully
- Return raw JSON dictionaries (no normalization or schema validation)

Architecture Layer: Adapter
- NO business logic
- NO data normalization
- NO schema validation
- NO filtering or sorting
- NO caching
- ONLY raw API calls and error handling
"""

from urllib.parse import quote

import requests

from backend.app.core.config import GOOGLE_MAPS_API_KEY
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class PlacesGoogleAPIError(RuntimeError):
    """
    Custom exception raised when Google Places or Geocoding API calls fail.
    
    This exception wraps all API-related errors including network issues,
    authentication failures, rate limiting, and invalid responses.
    """
    pass


def search_places_google_api(
    city: str,
    radius_m: int = 5000,
    limit: int = 20,
) -> list[dict]:
    """
    Search for places near a city using Google Places API (New).
    
    This function implements a 2-step process:
    1. Geocode city name to latitude/longitude using Google Geocoding API
    2. Search for nearby places using Google Places API (New)
    
    This is a pure API adapter that returns raw JSON data without any
    transformation or validation.
    
    Args:
        city: City name to search places in (e.g., "Paris", "New Delhi").
              Must be a non-empty string.
        radius_m: Search radius in meters from city center.
                  Must be between 500 and 50000. Defaults to 5000.
        limit: Maximum number of places to return.
               Must be between 1 and 60. Defaults to 20.
    
    Returns:
        List of raw place dictionaries from Google Places API.
        Returns empty list if city not found or no places available.
    
    Raises:
        ValueError: If inputs are invalid (empty city, out-of-range radius/limit).
        RuntimeError: If GOOGLE_MAPS_API_KEY is not configured.
        PlacesGoogleAPIError: If any Google API call fails.
    
    Example:
        >>> places = search_places_google_api(city="Paris", radius_m=10000, limit=10)
        >>> len(places)
        10
        >>> places[0]["displayName"]["text"]
        "Eiffel Tower"
    """
    # Check API key
    if not GOOGLE_MAPS_API_KEY:
        raise RuntimeError("GOOGLE_MAPS_API_KEY is not configured")
    
    # Input validation
    if not isinstance(city, str) or not city.strip():
        raise ValueError("city must be a non-empty string")
    
    city = city.strip()
    
    if not isinstance(radius_m, int) or radius_m < 500 or radius_m > 50000:
        raise ValueError("radius_m must be between 500 and 50000")
    
    if not isinstance(limit, int) or limit < 1 or limit > 60:
        raise ValueError("limit must be between 1 and 60")
    
    logger.info(
        f"Starting Google Places search for city='{city}', "
        f"radius={radius_m}m, limit={limit}"
    )
    
    try:
        # ============================================================
        # STEP 1: Geocode city to lat/lng
        # ============================================================
        logger.debug(f"Step 1: Geocoding city '{city}'")
        
        geocode_url = (
            f"https://maps.googleapis.com/maps/api/geocode/json"
            f"?address={quote(city)}&key={GOOGLE_MAPS_API_KEY}"
        )
        
        geocode_response = requests.get(geocode_url, timeout=10)
        geocode_response.raise_for_status()
        geocode_data = geocode_response.json()
        
        # Check for API errors
        if geocode_data.get("status") != "OK":
            logger.warning(
                f"Step 1: Geocoding failed with status: {geocode_data.get('status')}"
            )
            return []
        
        # Extract results
        results = geocode_data.get("results", [])
        if not results:
            logger.info(f"Step 1: No geocoding results for city '{city}'")
            return []
        
        # Extract lat/lng
        location = results[0].get("geometry", {}).get("location", {})
        latitude = location.get("lat")
        longitude = location.get("lng")
        
        if latitude is None or longitude is None:
            logger.warning(f"Step 1: Could not extract lat/lng for city '{city}'")
            return []
        
        logger.info(
            f"Step 1: Geocoded '{city}' to lat={latitude}, lng={longitude}"
        )
        
        # ============================================================
        # STEP 2: Search nearby places
        # ============================================================
        logger.debug(f"Step 2: Searching nearby places")
        
        places_url = "https://places.googleapis.com/v1/places:searchNearby"
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.types,"
                "places.rating,places.priceLevel"
            ),
        }
        
        body = {
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "radius": radius_m
                }
            }
        }
        
        places_response = requests.post(
            places_url,
            headers=headers,
            json=body,
            timeout=10
        )
        places_response.raise_for_status()
        places_data = places_response.json()
        
        # Extract places
        places = places_data.get("places", [])
        
        if not places:
            logger.info(
                f"Step 2: No places found near '{city}' "
                f"(radius={radius_m}m)"
            )
            return []
        
        # Limit results
        places = places[:limit]
        
        logger.info(
            f"Step 2: Successfully retrieved {len(places)} place(s) "
            f"near '{city}'"
        )
        
        return places
    
    except ValueError as e:
        # Re-raise validation errors as-is
        raise
    
    except RuntimeError as e:
        # Re-raise RuntimeError (API key missing) as-is
        raise
    
    except requests.exceptions.RequestException as e:
        # Catch all HTTP/network errors
        error_msg = (
            f"Google API request failed for city='{city}': "
            f"{type(e).__name__}: {str(e)}"
        )
        logger.error(error_msg, exc_info=True)
        raise PlacesGoogleAPIError(error_msg) from e
    
    except (KeyError, TypeError) as e:
        # Catch JSON parsing errors
        error_msg = (
            f"Failed to parse Google API response for city='{city}': "
            f"{type(e).__name__}: {str(e)}"
        )
        logger.error(error_msg, exc_info=True)
        raise PlacesGoogleAPIError(error_msg) from e
    
    except Exception as e:
        # Catch all other errors
        error_msg = (
            f"Google Places search failed for city='{city}': "
            f"{type(e).__name__}: {str(e)}"
        )
        logger.error(error_msg, exc_info=True)
        raise PlacesGoogleAPIError(error_msg) from e
