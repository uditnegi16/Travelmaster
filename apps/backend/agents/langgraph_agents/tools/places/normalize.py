"""
Places Normalization Layer.

This module is a pure normalization layer that converts raw Google Places API (New)
data into validated PlaceOption schema objects.

Responsibilities:
- Transform raw Google Places data into PlaceOption schema
- Filter out non-sightseeing places (hotels, transit, banks, etc.)
- Map Google price levels to approximate INR values
- Handle missing/malformed data gracefully
- Enforce schema constraints and data types

Architecture Layer: Normalizer
- NO API calls
- NO logging
- NO orchestration
- NO caching
- ONLY data shape transformation and light filtering
"""

from shared.schemas import PlaceOption

# Google price level to approximate INR mapping
PRICE_MAP = {
    "PRICE_LEVEL_FREE": 0,
    "PRICE_LEVEL_INEXPENSIVE": 500,
    "PRICE_LEVEL_MODERATE": 1500,
    "PRICE_LEVEL_EXPENSIVE": 3000,
    "PRICE_LEVEL_VERY_EXPENSIVE": 6000,
}

# Place types to allow (sightseeing related)

ALLOWED_TYPES = {
    "tourist_attraction",
    "point_of_interest",
    "museum",
    "park",
    "zoo",
    "monument",
    "place_of_worship",
    "art_gallery",
    "aquarium",
    "amusement_park",
    "historical_landmark",
    "natural_feature",
    "landmark",
}


def normalize_places(
    raw_places: list[dict],
    city: str,
) -> list[PlaceOption]:
    """
    Normalize raw Google Places data into PlaceOption schema objects.
    
    This function transforms raw place data from Google Places API (New) into
    validated PlaceOption objects. It filters out non-sightseeing places and
    handles missing data gracefully.
    
    Args:
        raw_places: List of raw place dictionaries from Google Places API.
                   Expected structure: [{"id": "...", "displayName": {...}, ...}, ...]
        city: City name where these places are located.
    
    Returns:
        List of validated PlaceOption objects.
        Only successfully normalized places are included.
        Returns empty list if input is invalid or all places fail normalization.
    
    Notes:
        - Places without id or name are skipped
        - Places with excluded types (hotels, transit, banks, etc.) are filtered out
        - Missing ratings default to 4.0
        - Missing price levels default to 0 (free)
        - Category is derived from first type, defaulting to "attraction"
        - This function does NOT sort, deduplicate, or limit results
    
    Example:
        >>> raw = [{"id": "P1", "displayName": {"text": "India Gate"}, "types": ["tourist_attraction"]}]
        >>> places = normalize_places(raw, "Delhi")
        >>> len(places)
        1
        >>> places[0].name
        "India Gate"
    """
    # Input validation - be defensive
    if not isinstance(raw_places, list):
        return []
    
    if not isinstance(city, str) or not city.strip():
        city = "Unknown"
    else:
        city = city.strip()
    
    normalized_places = []
    
    for raw_place in raw_places:
        try:
            # Validate raw place is a dict
            if not isinstance(raw_place, dict):
                continue
            
            # Extract required field: id
            place_id = raw_place.get("id")
            if not place_id or not isinstance(place_id, str):
                continue  # Skip - id is required
            
            place_id = str(place_id).strip()
            if not place_id:
                continue
            
            # Extract required field: name
            display_name = raw_place.get("displayName", {})
            if not isinstance(display_name, dict):
                continue  # Skip - invalid displayName structure
            
            name = display_name.get("text")
            if not name or not isinstance(name, str):
                continue  # Skip - name is required
            
            name = str(name).strip()
            if not name:
                continue
            
            # Extract and check types for filtering
            types = raw_place.get("types", [])
            if not isinstance(types, list):
                types = []
            
            # Normalize types to lowercase strings
            types = [t.lower() for t in types if isinstance(t, str)]

            # Keyword-based sightseeing whitelist (Google-safe)
            ALLOWED_KEYWORDS = (
                "tourist",
                "attraction",
                "monument",
                "museum",
                "park",
                "garden",
                "zoo",
                "dam",
                "temple",
                "church",
                "mosque",
                "gurudwara",
                "historic",
                "landmark",
                "heritage",
                "nature",
            )
            
            # Keep only if ANY keyword matches ANY type
            if not any(
                keyword in place_type
                for place_type in types
                for keyword in ALLOWED_KEYWORDS
            ):
                continue  # Skip - not a sightseeing place

            
            # Extract and map category
            category = _extract_category(types)
            
            # Extract and map rating
            rating = _extract_rating(raw_place)
            
            # Extract and map entry fee from Google price level
            entry_fee = _extract_price(raw_place)
            
            # Create PlaceOption object
            place_option = PlaceOption(
                id=place_id,
                name=name,
                city=city,
                category=category,
                rating=rating,
                entry_fee=entry_fee,
            )
            
            normalized_places.append(place_option)
        
        except Exception:
            # Silently skip any place that fails normalization
            # No logging as per requirements
            continue
    
    return normalized_places


def _extract_category(types: list) -> str:
    """
    Extract category from place types.
    
    Args:
        types: List of type strings from Google Places API
    
    Returns:
        Category string with underscores replaced by spaces
    """
    if not types or not isinstance(types, list):
        return "attraction"
    
    # Get first type
    first_type = types[0]
    if not isinstance(first_type, str):
        return "attraction"
    
    # Replace underscores with spaces
    category = first_type.replace("_", " ")
    return category.strip() or "attraction"


def _extract_rating(raw_place: dict) -> float:
    """
    Extract rating from raw place data.
    
    Args:
        raw_place: Raw place dictionary
    
    Returns:
        Rating as float, defaults to 4.0 if missing or invalid
    """
    try:
        rating = raw_place.get("rating")
        if rating is None:
            return 4.0
        
        rating_float = float(rating)
        # Ensure rating is reasonable (Google uses 0-5 scale)
        if rating_float < 0:
            return 4.0
        if rating_float > 5:
            return 5.0
        
        return rating_float
    
    except (ValueError, TypeError):
        return 4.0


def _extract_price(raw_place: dict) -> int:
    """
    Extract and map price from raw place data.
    
    Maps Google's price level strings to approximate INR values.
    
    Args:
        raw_place: Raw place dictionary
    
    Returns:
        Price in INR, defaults to 0 if missing or unknown
    """
    price_level = raw_place.get("priceLevel")
    
    if not price_level or not isinstance(price_level, str):
        return 0
    
    # Map to INR using price map
    return PRICE_MAP.get(price_level, 0)



