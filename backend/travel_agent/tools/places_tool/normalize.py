"""
Place Data Normalizer

This module converts raw place dictionaries from adapters into normalized
PlaceOption schema objects.

Responsibilities:
- Map dataset field names to schema field names (type → category)
- Validate data integrity (e.g., rating bounds 0.0-5.0)
- Ensure all fields are properly typed
- Return valid PlaceOption objects
"""

import logging

from travel_agent.schemas import PlaceOption

logger = logging.getLogger(__name__)


def raw_to_placeoption(raw: dict) -> PlaceOption:
    """
    Convert a raw place dictionary to a normalized PlaceOption object.
    
    This function maps dataset field names to schema field names, validates
    data integrity, and ensures all fields are properly typed.
    
    Dataset field mapping:
        - place_id → id
        - name → name
        - city → city
        - type → category
        - rating → rating
    
    Args:
        raw: Raw place dictionary with keys like 'place_id', 'name', 'city', 'type', 'rating'
    
    Returns:
        PlaceOption: Normalized place option schema object
    
    Raises:
        ValueError: If required fields are missing or data is invalid
        KeyError: If required fields are missing from raw dictionary
    
    Example:
        >>> raw = {
        ...     "place_id": "PLC0001",
        ...     "name": "Famous Fort",
        ...     "city": "Delhi",
        ...     "type": "museum",
        ...     "rating": 4.5
        ... }
        >>> place = raw_to_placeoption(raw)
        >>> place.name
        'Famous Fort'
        >>> place.category
        'museum'
    """
    try:
        # Extract and validate required fields
        place_id = raw["place_id"]
        name = raw["name"]
        city = raw["city"]
        place_type = raw["type"]  # Maps to 'category' in schema
        rating = raw["rating"]
        
        # Validate name is not empty
        if not name or not name.strip():
            raise ValueError(
                f"Place name cannot be empty for place {place_id}"
            )
        
        # Validate city is not empty
        if not city or not city.strip():
            raise ValueError(
                f"City cannot be empty for place {place_id}"
            )
        
        # Validate category/type is not empty
        if not place_type or not place_type.strip():
            raise ValueError(
                f"Type/category cannot be empty for place {place_id}"
            )
        
        # Ensure rating is a float
        if not isinstance(rating, (int, float)):
            try:
                rating = float(rating)
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Rating must be a number, got {rating} for place {place_id}"
                ) from e
        else:
            rating = float(rating)
        
        # Validate rating is within bounds (0.0 to 5.0)
        if not (0.0 <= rating <= 5.0):
            raise ValueError(
                f"Rating must be between 0.0 and 5.0, got {rating} "
                f"for place {place_id}"
            )
        
        # Create and return normalized PlaceOption
        place_option = PlaceOption(
            id=place_id,
            name=name.strip(),
            city=city.strip(),
            category=place_type.strip(),
            rating=rating
        )
        
        logger.debug(
            f"Normalized place {place_id}: {name} in {city} "
            f"({place_type}, {rating}★)"
        )
        return place_option
    
    except KeyError as e:
        missing_field = str(e).strip("'")
        logger.error(f"Missing required field in raw place data: {missing_field}")
        raise ValueError(f"Missing required field: {missing_field}") from e
    
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to normalize place data: {e}")
        raise
