"""Weather information service."""

import logging

from backend.app.core.config import DATA_SOURCE
from backend.app.shared.schemas import WeatherInfo
from .normalize import raw_to_weatherinfo

logger = logging.getLogger(__name__)


def get_weather(city: str, month: int) -> WeatherInfo | None:
    """
    Get weather information for a specific city and month.
    
    Args:
        city: City name (required)
        month: Month number 1-12 (required)
    
    Returns:
        WeatherInfo instance if found, None otherwise
    """
    # Validate inputs
    if not city or not city.strip():
        logger.error("City parameter is required")
        return None
    
    if not isinstance(month, int) or not (1 <= month <= 12):
        logger.error(f"Month must be an integer between 1 and 12, got {month}")
        return None
    
    # Load adapter based on config
    if DATA_SOURCE == "dataset":
        from .adapters import dataset as adapter
        logger.info("Using dataset adapter for weather lookup")
    elif DATA_SOURCE == "api":
        from .adapters import api as adapter
        logger.info("Using API adapter for weather lookup")
    else:
        logger.error(f"Unknown DATA_SOURCE: {DATA_SOURCE}")
        return None
    
    # Get raw weather data
    try:
        raw_weather = adapter.get_raw_weather(city=city, month=month)
    except Exception as e:
        logger.error(f"Adapter lookup failed: {e}")
        return None
    
    # Return None if no data found
    if raw_weather is None:
        logger.info(f"No weather data available for {city}, month {month}")
        return None
    
    # Normalize result
    try:
        weather = raw_to_weatherinfo(raw_weather)
        logger.info(f"Successfully retrieved weather for {city}, month {month}: {weather.condition}")
        return weather
    except Exception as e:
        logger.error(f"Failed to normalize weather data for {city}, month {month}: {e}")
        return None
