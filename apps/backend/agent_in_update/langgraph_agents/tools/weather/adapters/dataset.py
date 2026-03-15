"""Dataset adapter for weather data."""

import json
import logging
from functools import lru_cache
from pathlib import Path

from core.config import WEATHER_DATASET_PATH

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_weather_dataset() -> list[dict]:
    """Load and cache the weather dataset from JSON file."""
    try:
        path = Path(WEATHER_DATASET_PATH)
        if not path.exists():
            logger.error(f"Weather dataset not found at {WEATHER_DATASET_PATH}")
            return []
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            logger.error("Weather dataset must be a JSON array")
            return []
        
        logger.info(f"Loaded {len(data)} weather records from dataset")
        return data
    except Exception as e:
        logger.error(f"Failed to load weather dataset: {e}")
        return []


def get_raw_weather(city: str, month: int) -> dict | None:
    """
    Get weather data for a specific city and month.
    
    Args:
        city: City name (case-insensitive)
        month: Month number (1-12)
    
    Returns:
        Raw weather dictionary if found, None otherwise
    """
    dataset = _load_weather_dataset()
    
    city_normalized = city.strip().lower()
    
    for weather in dataset:
        if not isinstance(weather, dict):
            continue
        
        # City matching (case-insensitive)
        weather_city = weather.get("city", "").strip().lower()
        if weather_city != city_normalized:
            continue
        
        # Month matching (exact)
        try:
            weather_month = int(weather.get("month", 0))
            if weather_month != month:
                continue
        except (ValueError, TypeError):
            logger.warning(f"Invalid month in weather data for city {weather.get('city')}")
            continue
        
        # Return first match
        logger.info(f"Found weather data for {city}, month {month}")
        return weather
    
    logger.info(f"No weather data found for {city}, month {month}")
    return None


