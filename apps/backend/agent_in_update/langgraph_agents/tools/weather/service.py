"""
Weather information service.
Orchestrates weather forecast retrieval using OpenWeather API.
"""

from core.logging import get_logger
from shared.schemas import WeatherSummary
from .adapters.openweather_api import (
    fetch_weather_forecast_api,
    WeatherAPIError,
)
from .normalize import normalize_weather_forecast
from postprocessing.weather_enrichment import enrich_weather_forecast

logger = get_logger(__name__)


class WeatherServiceError(Exception):
    """Raised when weather service operations fail."""
    pass


def get_weather_forecast(
    *,
    city: str,
    days: int = 5,
) -> list[WeatherSummary]:
    """
    High-level weather forecast API used by the TravelGuru brain.
    
    Retrieves multi-day weather forecast for a specified city.
    Orchestrates adapter call (OpenWeather API) and normalization
    into WeatherSummary schema objects.
    
    Args:
        city: City name (required, non-empty string)
        days: Number of forecast days to return (default: 5, max: 16)
        
    Returns:
        List of WeatherSummary objects, one per day, up to `days` limit.
        Returns empty list if no data available.
        
    Raises:
        WeatherServiceError: If validation fails, API call fails, or normalization fails
        
    Example:
        >>> forecast = get_weather_forecast(city="London", days=5)
        >>> len(forecast)
        5
    """
    logger.info(f"Starting weather forecast service for city='{city}', days={days}")
    
    # Validate inputs
    if not city or not isinstance(city, str) or not city.strip():
        logger.error("City parameter is required and must be a non-empty string")
        raise WeatherServiceError("City parameter is required and must be a non-empty string")
    
    city = city.strip()
    
    if not isinstance(days, int) or days < 1:
        logger.error(f"Days parameter must be a positive integer, got: {days}")
        raise WeatherServiceError(f"Days parameter must be a positive integer, got: {days}")
    
    if days > 16:
        logger.warning(f"Requested {days} days, but OpenWeather forecast supports max 16 days. Capping to 16.")
        days = 16
    
    # Call adapter to fetch raw forecast data
    try:
        logger.debug(f"Calling OpenWeather adapter for city='{city}'")
        raw_data = fetch_weather_forecast_api(city=city)
        logger.info(f"Successfully fetched raw weather data for city='{city}'")
    except WeatherAPIError as e:
        logger.error(f"OpenWeather API call failed: {e}")
        raise WeatherServiceError(f"Failed to fetch weather data: {e}")
    except Exception as e:
        logger.error(f"Unexpected error calling weather adapter: {e}")
        raise WeatherServiceError(f"Unexpected weather adapter error: {e}")
    
    # Call normalizer to convert raw data to WeatherSummary objects
    try:
        logger.debug(f"Normalizing weather forecast data for city='{city}'")
        summaries = normalize_weather_forecast(raw_data, city=city, max_days=days)
        logger.info(f"Normalization complete: {len(summaries)} daily summaries created")
    except Exception as e:
        logger.error(f"Weather normalization failed: {e}")
        raise WeatherServiceError(f"Failed to normalize weather data: {e}")
    
    # Limit results to requested days (defensive, normalizer should already do this)
    summaries = summaries[:days]
    
    # Apply enrichment layer (intelligence engine)
    try:
        logger.debug(f"Applying weather intelligence enrichment for city='{city}'")
        enrichment_result = enrich_weather_forecast(summaries)
        logger.info(
            f"Weather enrichment complete: {len(enrichment_result.enriched_days)} days enriched, "
            f"{len(enrichment_result.trip_insights)} trip-level insights generated"
        )
        
        # Extract enriched WeatherSummary objects for return
        # TODO: Consider returning full EnrichedWeatherDay objects once consumer supports richer schema
        enriched_summaries = [day.weather for day in enrichment_result.enriched_days]
        
    except Exception as e:
        logger.warning(f"Weather enrichment failed, returning un-enriched summaries: {e}")
        enriched_summaries = summaries  # Fallback to un-enriched if enrichment fails
    
    # Log result
    if not enriched_summaries:
        logger.warning(f"No weather forecast data available for city='{city}'")
        return []
    
    logger.info(f"Returning {len(enriched_summaries)} weather forecast summaries for '{city}'")
    return enriched_summaries


