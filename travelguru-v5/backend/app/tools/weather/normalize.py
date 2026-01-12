"""Normalization utilities for weather data."""

import logging

from backend.app.shared.schemas import WeatherInfo

logger = logging.getLogger(__name__)


def raw_to_weatherinfo(raw: dict) -> WeatherInfo:
    """
    Convert raw weather dictionary to WeatherInfo schema.
    
    Args:
        raw: Raw weather data dictionary
    
    Returns:
        WeatherInfo instance
    
    Raises:
        ValueError: If required fields are missing or invalid
        ValidationError: If Pydantic validation fails
    """
    # Extract and validate fields
    city = raw.get("city", "").strip()
    if not city:
        raise ValueError("Missing required field: city")
    
    # Validate month
    try:
        month = int(raw.get("month", 0))
        if not (1 <= month <= 12):
            raise ValueError(f"Month must be between 1 and 12, got {month}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid month: {e}")
    
    # Validate temperatures
    try:
        min_temp = int(raw.get("min_temp", 0))
        max_temp = int(raw.get("max_temp", 0))
        
        if min_temp > max_temp:
            raise ValueError(f"min_temp ({min_temp}) must be <= max_temp ({max_temp})")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid temperature: {e}")
    
    # Extract condition
    condition = raw.get("condition", "").strip()
    if not condition:
        raise ValueError("Missing required field: condition")
    
    # Let Pydantic handle the rest
    return WeatherInfo(
        city=city,
        month=month,
        min_temp=min_temp,
        max_temp=max_temp,
        condition=condition
    )
