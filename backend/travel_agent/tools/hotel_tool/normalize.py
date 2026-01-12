"""
Hotel Data Normalizer

This module converts raw hotel dictionaries from adapters into normalized
HotelOption schema objects.

Responsibilities:
- Map dataset field names to schema field names
- Validate data integrity (e.g., star rating bounds, price validation)
- Ensure amenities list is properly formatted
- Return valid HotelOption objects
"""

import logging

from backend.travel_agent.schemas import HotelOption

logger = logging.getLogger(__name__)


def raw_to_hoteloption(raw: dict) -> HotelOption:
    """
    Convert a raw hotel dictionary to a normalized HotelOption object.
    
    This function maps dataset field names to schema field names, validates
    data integrity, and ensures all fields are properly typed.
    
    Args:
        raw: Raw hotel dictionary with keys like 'hotel_id', 'name', 'city', etc.
    
    Returns:
        HotelOption: Normalized hotel option schema object
    
    Raises:
        ValueError: If required fields are missing or data is invalid
        KeyError: If required fields are missing from raw dictionary
    
    Example:
        >>> raw = {
        ...     "hotel_id": "HOT0001",
        ...     "name": "Grand Palace Hotel",
        ...     "city": "Delhi",
        ...     "stars": 4,
        ...     "price_per_night": 3897,
        ...     "amenities": ["wifi", "pool"]
        ... }
        >>> hotel = raw_to_hoteloption(raw)
        >>> hotel.name
        'Grand Palace Hotel'
    """
    try:
        # Extract and validate required fields
        hotel_id = raw["hotel_id"]
        name = raw["name"]
        city = raw["city"]
        stars = raw["stars"]
        price_per_night = raw["price_per_night"]
        amenities = raw.get("amenities", [])  # Optional field with default
        
        # Validate name is not empty
        if not name or not name.strip():
            raise ValueError(
                f"Hotel name cannot be empty for hotel {hotel_id}"
            )
        
        # Validate city is not empty
        if not city or not city.strip():
            raise ValueError(
                f"City cannot be empty for hotel {hotel_id}"
            )
        
        # Validate star rating is within bounds (1-5)
        if not isinstance(stars, int) or not (1 <= stars <= 5):
            raise ValueError(
                f"Star rating must be an integer between 1 and 5, got {stars} "
                f"for hotel {hotel_id}"
            )
        
        # Ensure price is an integer
        if not isinstance(price_per_night, int):
            try:
                price_per_night = int(price_per_night)
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Price per night must be an integer, got {price_per_night} "
                    f"for hotel {hotel_id}"
                ) from e
        
        # Validate price is non-negative
        if price_per_night < 0:
            raise ValueError(
                f"Price per night cannot be negative, got {price_per_night} "
                f"for hotel {hotel_id}"
            )
        
        # Ensure amenities is a list
        if not isinstance(amenities, list):
            logger.warning(
                f"Amenities field is not a list for hotel {hotel_id}, converting to list"
            )
            amenities = []
        
        # Validate amenities are strings and non-empty
        validated_amenities = []
        for amenity in amenities:
            if isinstance(amenity, str) and amenity.strip():
                validated_amenities.append(amenity.strip())
            else:
                logger.warning(
                    f"Skipping invalid amenity '{amenity}' for hotel {hotel_id}"
                )
        
        # Create and return normalized HotelOption
        hotel_option = HotelOption(
            id=hotel_id,
            name=name.strip(),
            city=city.strip(),
            stars=stars,
            price_per_night=price_per_night,
            amenities=validated_amenities
        )
        
        logger.debug(
            f"Normalized hotel {hotel_id}: {name} in {city} "
            f"({stars}★, ₹{price_per_night}/night)"
        )
        return hotel_option
    
    except KeyError as e:
        missing_field = str(e).strip("'")
        logger.error(f"Missing required field in raw hotel data: {missing_field}")
        raise ValueError(f"Missing required field: {missing_field}") from e
    
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to normalize hotel data: {e}")
        raise
