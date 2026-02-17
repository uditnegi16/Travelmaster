"""
Normalization utilities for OpenWeather forecast data.
Converts raw OpenWeather API 3-hour interval forecasts into daily WeatherSummary objects.
"""

from collections import defaultdict, Counter
from datetime import datetime
from typing import Any

from core.logging import get_logger
from shared.schemas import WeatherSummary

logger = get_logger(__name__)


def _safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _most_common(items: list[str]) -> str:
    """
    Find the most common item in a list.
    
    Args:
        items: List of strings
        
    Returns:
        Most common string, or empty string if list is empty
    """
    if not items:
        return ""
    
    try:
        counter = Counter(items)
        return counter.most_common(1)[0][0]
    except (IndexError, Exception):
        return items[0] if items else ""


def normalize_weather_forecast(
    raw: dict,
    *,
    city: str,
    max_days: int = 5,
) -> list[WeatherSummary]:
    """
    Convert OpenWeather 3-hour forecast JSON into daily WeatherSummary list.
    
    Takes raw OpenWeather forecast data with 3-hour intervals and aggregates
    it into daily summaries. For each day:
    - Temperature: Average of all 3-hour readings
    - Condition: Most frequently occurring weather condition
    - Rain chance: Maximum precipitation probability
    
    Args:
        raw: Raw JSON response from OpenWeather forecast API
        city: City name to use in summaries
        max_days: Maximum number of days to include (default: 5)
        
    Returns:
        List of WeatherSummary objects, one per day, sorted by date.
        Returns empty list if data is malformed or missing.
        
    Example:
        >>> raw_data = fetch_weather_forecast_api(city="London")
        >>> summaries = normalize_weather_forecast(raw_data, city="London")
        >>> len(summaries)
        5
    """
    logger.info(f"Normalizing weather forecast for city: {city}")
    
    # Defensive: Validate input
    if not isinstance(raw, dict):
        logger.warning(f"Invalid raw data type: {type(raw)}. Expected dict.")
        return []
    
    # Extract forecast list
    forecast_list = raw.get("list", [])
    if not isinstance(forecast_list, list):
        logger.warning("'list' field is not a list or is missing")
        return []
    
    if not forecast_list:
        logger.warning("Forecast list is empty")
        return []
    
    logger.debug(f"Received {len(forecast_list)} 3-hour forecast entries")
    
    # Group entries by date
    # Key: YYYY-MM-DD, Value: list of 3-hour entries for that day
    daily_data: dict[str, list[dict]] = defaultdict(list)
    
    for entry in forecast_list:
        if not isinstance(entry, dict):
            logger.debug("Skipping non-dict entry")
            continue
        
        # Extract date from dt_txt field (e.g., "2024-01-15 12:00:00")
        dt_txt = entry.get("dt_txt", "")
        if not dt_txt:
            logger.debug("Skipping entry without dt_txt")
            continue
        
        try:
            # Parse date and extract YYYY-MM-DD
            # dt_txt format: "2024-01-15 12:00:00"
            date_str = dt_txt.split(" ")[0]  # "2024-01-15"
            
            # Validate date format
            datetime.strptime(date_str, "%Y-%m-%d")
            
            daily_data[date_str].append(entry)
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to parse date from dt_txt='{dt_txt}': {e}")
            continue
    
    if not daily_data:
        logger.warning("No valid daily data after grouping")
        return []
    
    logger.debug(f"Grouped into {len(daily_data)} days")
    
    # Convert daily data into WeatherSummary objects
    summaries: list[WeatherSummary] = []
    
    for date_str in sorted(daily_data.keys())[:max_days]:
        entries = daily_data[date_str]
        
        if not entries:
            continue
        
        # Aggregate temperatures (min, max, average)
        temps: list[float] = []
        for entry in entries:
            main = entry.get("main", {})
            if isinstance(main, dict):
                temp = main.get("temp")
                if temp is not None:
                    temps.append(_safe_float(temp))
        
        min_temp = min(temps) if temps else 0.0
        max_temp = max(temps) if temps else 0.0
        avg_temp = sum(temps) / len(temps) if temps else 0.0
        
        # Aggregate condition (most common)
        conditions: list[str] = []
        for entry in entries:
            weather = entry.get("weather", [])
            if isinstance(weather, list) and len(weather) > 0:
                weather_main = weather[0].get("main", "")
                if weather_main:
                    conditions.append(weather_main)
        
        most_common_condition = _most_common(conditions)
        
        # Aggregate rain chance (maximum)
        rain_chances: list[float] = []
        for entry in entries:
            pop = entry.get("pop")  # Probability of precipitation
            if pop is not None:
                rain_chances.append(_safe_float(pop))
        
        max_rain_chance = max(rain_chances) if rain_chances else 0.0
        # Clamp to [0.0, 1.0] to handle any weird API values
        max_rain_chance = max(0.0, min(1.0, max_rain_chance))
        
        # Create WeatherSummary
        try:
            summary = WeatherSummary(
                city=city,
                date=date_str,
                temp_min_c=round(min_temp, 1),
                temp_max_c=round(max_temp, 1),
                temp_avg_c=round(avg_temp, 1),
                condition=most_common_condition if most_common_condition else "Unknown",
                rain_chance=round(max_rain_chance, 2),
            )
            summaries.append(summary)
            logger.debug(
                f"Created summary for {date_str}: "
                f"temp={summary.temp_min_c}/{summary.temp_avg_c}/{summary.temp_max_c}°C (min/avg/max), "
                f"condition={summary.condition}, rain_chance={summary.rain_chance}"
            )
        except Exception as e:
            logger.error(f"Failed to create WeatherSummary for {date_str}: {e}")
            continue
    
    logger.info(f"Normalized {len(summaries)} daily weather summaries")
    
    return summaries

