"""
Flight Data Normalizer

This module converts raw flight dictionaries from adapters into normalized
FlightOption schema objects.

Responsibilities:
- Parse ISO datetime strings to timezone-aware UTC datetimes
- Map dataset field names to schema field names
- Validate data integrity (e.g., arrival after departure)
- Handle timezone conversions
- Return valid FlightOption objects
"""

import logging
from datetime import datetime, timezone

from backend.travel_agent.schemas import FlightOption

logger = logging.getLogger(__name__)


def _parse_datetime_to_utc(dt_string: str) -> datetime:
    """
    Parse an ISO datetime string and ensure it's timezone-aware UTC.
    
    If the input datetime has no timezone information, it's assumed to be UTC.
    If it has timezone information, it's converted to UTC.
    
    Args:
        dt_string: ISO format datetime string (e.g., "2025-01-04T11:32:00")
    
    Returns:
        datetime: Timezone-aware UTC datetime object
    
    Raises:
        ValueError: If the datetime string cannot be parsed
    
    Example:
        >>> dt = _parse_datetime_to_utc("2025-01-04T11:32:00")
        >>> dt.tzinfo
        datetime.timezone.utc
    """
    try:
        # Try parsing with fromisoformat (handles most ISO formats)
        dt = datetime.fromisoformat(dt_string)
        
        # If naive (no timezone), assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            logger.debug(f"Assumed UTC for naive datetime: {dt_string}")
        else:
            # Convert to UTC if it has a different timezone
            dt = dt.astimezone(timezone.utc)
        
        return dt
    
    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse datetime '{dt_string}': {e}")
        raise ValueError(f"Invalid datetime format: {dt_string}") from e


def raw_to_flightoption(raw: dict) -> FlightOption:
    """
    Convert a raw flight dictionary to a normalized FlightOption object.
    
    This function maps dataset field names to schema field names, parses
    datetime strings, ensures timezone awareness, and validates data integrity.
    
    Args:
        raw: Raw flight dictionary with keys like 'flight_id', 'from', 'to', etc.
    
    Returns:
        FlightOption: Normalized flight option schema object
    
    Raises:
        ValueError: If required fields are missing or data is invalid
        KeyError: If required fields are missing from raw dictionary
    
    Example:
        >>> raw = {
        ...     "flight_id": "FL0001",
        ...     "airline": "IndiGo",
        ...     "from": "Delhi",
        ...     "to": "Mumbai",
        ...     "departure_time": "2025-01-04T11:32:00",
        ...     "arrival_time": "2025-01-04T13:32:00",
        ...     "price": 2907
        ... }
        >>> flight = raw_to_flightoption(raw)
        >>> flight.airline
        'IndiGo'
    """
    try:
        # Extract and validate required fields
        flight_id = raw["flight_id"]
        airline = raw["airline"]
        origin = raw["from"]
        destination = raw["to"]
        departure_time_str = raw["departure_time"]
        arrival_time_str = raw["arrival_time"]
        price = raw["price"]
        
        # Parse datetimes to timezone-aware UTC
        departure_time = _parse_datetime_to_utc(departure_time_str)
        arrival_time = _parse_datetime_to_utc(arrival_time_str)
        
        # Additional validation: arrival must be after departure
        if arrival_time <= departure_time:
            raise ValueError(
                f"Arrival time ({arrival_time}) must be after departure time ({departure_time}) "
                f"for flight {flight_id}"
            )
        
        # Ensure price is an integer
        if not isinstance(price, int):
            price = int(price)
        
        # Create and return normalized FlightOption
        flight_option = FlightOption(
            id=flight_id,
            airline=airline,
            origin=origin,
            destination=destination,
            departure_time=departure_time,
            arrival_time=arrival_time,
            price=price
        )
        
        logger.debug(f"Normalized flight {flight_id}: {origin} → {destination}")
        return flight_option
    
    except KeyError as e:
        missing_field = str(e).strip("'")
        logger.error(f"Missing required field in raw flight data: {missing_field}")
        raise ValueError(f"Missing required field: {missing_field}") from e
    
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to normalize flight data: {e}")
        raise

