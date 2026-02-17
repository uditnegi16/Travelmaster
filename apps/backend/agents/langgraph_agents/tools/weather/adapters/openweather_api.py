"""
OpenWeather API adapter.

Fetches 5-day/3-hour forecast data from OpenWeather API.
Returns raw JSON response without normalization.
"""

import requests
from typing import Any

from core.amadeus_client import call_amadeus
from core.config import OPENWEATHER_API_KEY, OPENWEATHER_TIMEOUT
from core.logging import get_logger

logger = get_logger(__name__)

OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


class WeatherAPIError(Exception):
    """Raised when OpenWeather API call fails."""
    pass


def _build_params(
    *,
    city: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    units: str = "metric",
) -> dict[str, Any]:
    """
    Build query parameters for OpenWeather forecast API.
    
    Args:
        city: City name (e.g., "London", "New York")
        lat: Latitude coordinate
        lon: Longitude coordinate
        units: Temperature units (metric/imperial/standard)
    
    Returns:
        Dict of query parameters
    
    Raises:
        ValueError: If invalid parameter combination provided
    """
    if not OPENWEATHER_API_KEY:
        raise RuntimeError(
            "OPENWEATHER_API_KEY is not configured. "
            "Please set it in environment variables or config."
        )
    
    params = {
        "appid": OPENWEATHER_API_KEY,
        "units": units,
        "lang": "en",
    }
    
    # Validate exactly one query mode is provided
    has_city = city is not None
    has_coords = lat is not None and lon is not None
    
    if has_city and has_coords:
        raise ValueError("Cannot provide both 'city' and 'lat+lon'. Choose one query mode.")
    
    if not has_city and not has_coords:
        raise ValueError("Must provide either 'city' or both 'lat' and 'lon'.")
    
    if has_coords and (lat is None or lon is None):
        raise ValueError("Both 'lat' and 'lon' must be provided together.")
    
    # Add appropriate query parameters
    if has_city:
        params["q"] = city
        logger.debug(f"Query mode: city='{city}'")
    else:
        params["lat"] = lat
        params["lon"] = lon
        logger.debug(f"Query mode: lat={lat}, lon={lon}")
    
    return params


def fetch_weather_forecast_api(
    *,
    city: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    units: str = "metric",
) -> dict:
    """
    Fetch 5-day/3-hour weather forecast from OpenWeather API.
    
    Calls the OpenWeather forecast endpoint and returns the raw JSON response.
    Uses shared retry wrapper for resilient HTTP calls.
    
    Exactly one of the following must be provided:
        - city: Query by city name
        - lat + lon: Query by geographic coordinates
    
    Args:
        city: City name (e.g., "London", "Paris")
        lat: Latitude coordinate (range: -90 to 90)
        lon: Longitude coordinate (range: -180 to 180)
        units: Temperature units - "metric" (Celsius), "imperial" (Fahrenheit), 
               or "standard" (Kelvin). Default: "metric"
    
    Returns:
        Raw JSON response dict from OpenWeather API containing:
            - list: Array of forecast data points (3-hour intervals)
            - city: City information
            - cnt: Number of forecast entries
            - cod: API response code
            - message: API message
    
    Raises:
        RuntimeError: If OPENWEATHER_API_KEY is not configured
        ValueError: If invalid parameter combination provided
        WeatherAPIError: If API call fails or returns error response
    
    Example:
        >>> data = fetch_weather_forecast_api(city="London")
        >>> data = fetch_weather_forecast_api(lat=51.5074, lon=-0.1278)
    """
    logger.info("Starting OpenWeather forecast API call")
    
    # Build query parameters and validate inputs
    try:
        params = _build_params(city=city, lat=lat, lon=lon, units=units)
    except (ValueError, RuntimeError) as e:
        logger.error(f"Parameter validation failed: {e}")
        raise
    
    endpoint = OPENWEATHER_FORECAST_URL
    
    def do_request() -> dict:
        """
        Internal function that performs the actual HTTP request.
        Wrapped by call_amadeus for retry logic.
        """
        try:
            logger.debug(f"Calling OpenWeather API: {endpoint}")
            response = requests.get(
                endpoint,
                params=params,
                timeout=OPENWEATHER_TIMEOUT,
            )
            
            # Log response status
            logger.debug(f"OpenWeather API responded with status: {response.status_code}")
            
            # Raise for HTTP errors (4xx, 5xx)
            response.raise_for_status()
            
            # Parse JSON response
            try:
                data = response.json()
            except ValueError as json_err:
                logger.error(f"Failed to parse JSON response: {json_err}")
                raise WeatherAPIError(f"Invalid JSON response from OpenWeather API: {json_err}")
            
            # Check for API-level errors (OpenWeather returns 200 but with error payload)
            if isinstance(data, dict):
                # OpenWeather error responses have "cod" as string like "404" or "401"
                cod = data.get("cod")
                
                # Successful responses have cod="200" (string) or 200 (int)
                if cod not in [200, "200"]:
                    error_message = data.get("message", "Unknown error")
                    logger.error(f"OpenWeather API error (cod={cod}): {error_message}")
                    raise WeatherAPIError(f"OpenWeather API error: {error_message} (code: {cod})")
            
            # Validate response structure
            if not isinstance(data, dict):
                logger.error(f"Unexpected response type: {type(data)}")
                raise WeatherAPIError(f"Expected dict response, got {type(data)}")
            
            # Check for essential forecast data
            if "list" not in data:
                logger.warning("Response missing 'list' field with forecast data")
                # Don't raise error, let service/normalize handle it
            
            logger.info("OpenWeather API call successful")
            logger.debug(f"Received {len(data.get('list', []))} forecast entries")
            
            return data
            
        except requests.exceptions.Timeout as e:
            logger.error(f"OpenWeather API request timed out: {e}")
            raise WeatherAPIError(f"OpenWeather API timeout: {e}")
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error calling OpenWeather API: {e}")
            raise WeatherAPIError(f"Failed to connect to OpenWeather API: {e}")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error from OpenWeather API: {e}")
            raise WeatherAPIError(f"OpenWeather API HTTP error: {e}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error calling OpenWeather API: {e}")
            raise WeatherAPIError(f"OpenWeather API request failed: {e}")
    
    # Use shared retry wrapper
    try:
        response_data = call_amadeus(fn=do_request)
        return response_data
    except WeatherAPIError:
        # Re-raise our custom errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in OpenWeather API call: {e}")
        raise WeatherAPIError(f"Unexpected error: {e}")

