"""API adapter for weather data."""


def get_raw_weather(city: str, month: int) -> dict | None:
    """
    Get weather data via external API.
    
    Args:
        city: City name
        month: Month number (1-12)
    
    Returns:
        Raw weather dictionary if found, None otherwise
    
    Raises:
        NotImplementedError: This adapter is not yet implemented
    """
    raise NotImplementedError("Weather API adapter not implemented yet")
