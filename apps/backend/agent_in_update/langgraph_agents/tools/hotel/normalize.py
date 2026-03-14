"""
Hotel Normalization Layer.

This module is a pure normalization/transformation layer that converts raw Amadeus
hotel search and ratings data into validated HotelOption schema objects.

Responsibilities:
- Transform raw API data into HotelOption schema
- Merge hotel search results with ratings data
- Handle missing/malformed data gracefully
- Enforce schema constraints and data types

Architecture Layer: Normalizer
- NO API calls
- NO business logic
- NO filtering or sorting
- NO pricing rules or complex calculations
- ONLY data shape transformation
"""

from typing import Any

from core.logging import get_logger
from agent_in_update.shared.schemas import HotelOption

logger = get_logger(__name__)

import urllib.parse

def _fallback_hotel_booking_url(name: str, city: str, check_in: str | None, check_out: str | None) -> str:
    try:
        q = f"{name} {city} hotel".strip()
        if check_in and check_out:
            q += f" {check_in} {check_out}"
        return "https://www.google.com/search?q=" + urllib.parse.quote(q)
    except Exception:
        return ""
    
def normalize_hotels(
    raw_hotels: list[dict],
    ratings_map: dict[str, dict],
    check_in: str | None = None,
    check_out: str | None = None,
) -> list[HotelOption]:
    """
    Normalize raw Amadeus hotel data into HotelOption schema objects.
    
    This function transforms raw hotel search results and ratings data from Amadeus
    into validated HotelOption objects. It handles missing data gracefully and
    logs warnings for items that cannot be normalized.
    
    Args:
        raw_hotels: List of raw hotel dictionaries from Amadeus search API.
                   Expected structure: [{"hotel": {...}, "offers": [...]}, ...]
        ratings_map: Dictionary mapping hotel IDs to raw rating objects.
                    Expected structure: {hotel_id: {"overallRating": "85", ...}, ...}
        check_in: Check-in date in YYYY-MM-DD format (optional)
        check_out: Check-out date in YYYY-MM-DD format (optional)
    
    Returns:
        List of validated HotelOption objects.
        Only successfully normalized hotels are included.
        Returns empty list if input is invalid or all hotels fail normalization.
    
    Notes:
        - This function is fault-tolerant and will not crash on bad data
        - Individual hotel failures are logged as warnings
        - Missing or malformed fields use sensible defaults where possible
        - Required fields (id, price) cause hotel to be skipped if missing
    
    Example:
        >>> raw = [{"hotel": {"hotelId": "H1", "name": "Grand Hotel"}, "offers": [...]}]
        >>> ratings = {"H1": {"overallRating": "85"}}
        >>> hotels = normalize_hotels(raw, ratings)
        >>> len(hotels)
        1
        >>> hotels[0].stars
        5
    """
    # Input validation - be defensive
    if not isinstance(raw_hotels, list):
        logger.warning("raw_hotels is not a list, returning empty list")
        return []
    
    if not isinstance(ratings_map, dict):
        logger.warning("ratings_map is not a dict, treating as empty")
        ratings_map = {}
    
    logger.info(f"Starting normalization of {len(raw_hotels)} raw hotel(s)")
    
    normalized_hotels = []
    failed_count = 0
    
    for idx, raw_item in enumerate(raw_hotels):
        try:
            # Extract hotel object and offers
            if not isinstance(raw_item, dict):
                logger.warning(f"Hotel item at index {idx} is not a dict, skipping")
                failed_count += 1
                continue
            
            hotel = raw_item.get("hotel", {})
            offers = raw_item.get("offers", [])
            
            if not isinstance(hotel, dict):
                logger.warning(f"Hotel object at index {idx} is not a dict, skipping")
                failed_count += 1
                continue
            
            # Extract required field: id
            hotel_id = hotel.get("hotelId") or hotel.get("dupeId")
            if not hotel_id:
                logger.warning(f"Hotel at index {idx} missing hotelId/dupeId, skipping")
                failed_count += 1
                continue
            
            hotel_id = str(hotel_id).strip()
            
            # Extract required field: price_per_night
            price_per_night = _extract_price(offers, idx)
            if price_per_night is None:
                failed_count += 1
                continue  # Already logged in _extract_price
            
            # Extract optional fields with fallbacks
            name = _extract_name(hotel)
            city = _extract_city(hotel)
            stars = _extract_stars(hotel, hotel_id, ratings_map)
            amenities = _extract_amenities(hotel)
            
            currency = _extract_currency(offers)
            rating = _extract_rating_0_to_5(hotel_id, ratings_map)
            stars = _extract_stars(hotel, hotel_id, ratings_map)

            booking_url = _fallback_hotel_booking_url(name, city, check_in, check_out)

            hotel_option = HotelOption(
                id=hotel_id,
                name=name,
                city=city or "",
                rating=float(rating or 0.0),
                star_category=int(stars or 0),
                price_per_night=float(price_per_night),
                currency=currency or "INR",
                booking_url=booking_url or "",
                amenities=amenities or [],
                check_in=check_in,
                check_out=check_out,
            )
            normalized_hotels.append(hotel_option)        
        except Exception as e:
            logger.warning(
                f"Failed to normalize hotel at index {idx}: {type(e).__name__}: {str(e)}"
            )
            failed_count += 1
            continue
    
    logger.info(
        f"Normalization complete: {len(normalized_hotels)} successful, "
        f"{failed_count} failed"
    )
    
    return normalized_hotels

def raw_hotel_item_to_contract(
    raw_item: dict,
    ratings_map: dict[str, dict],
    check_in: str | None = None,
    check_out: str | None = None,
) -> dict | None:
    """
    Convert a raw Amadeus hotel item ({"hotel":..., "offers":[...]}) to MLOps-ready hotel contract dict.
    """
    try:
        if not isinstance(raw_item, dict):
            return None

        hotel = raw_item.get("hotel", {})
        offers = raw_item.get("offers", [])
        if not isinstance(hotel, dict):
            return None

        hotel_id = hotel.get("hotelId") or hotel.get("dupeId")
        if not hotel_id:
            return None
        hotel_id = str(hotel_id).strip()

        price_per_night = _extract_price(offers, idx=-1)
        if price_per_night is None:
            return None

        name = _extract_name(hotel)
        city = _extract_city(hotel)
        stars = _extract_stars(hotel, hotel_id, ratings_map)
        currency = _extract_currency(offers)
        rating = _extract_rating_0_to_5(hotel_id, ratings_map)
        rating_val = float(rating) if rating is not None else 0.0        
        amenities = _extract_amenities(hotel)

        booking_url = _fallback_hotel_booking_url(name, city, check_in, check_out)

        return {
            "hotel_id": hotel_id,
            "name": name,
            "rating": rating_val,
            "star_category": int(stars),
            "price_per_night": float(price_per_night),
            "currency": currency,
            "amenities": amenities,
            "location": city,
            "booking_url": booking_url,
        }

    except Exception:
        return None


def normalize_hotels_to_contract(
    raw_hotels: list[dict],
    ratings_map: dict[str, dict],
    check_in: str | None = None,
    check_out: str | None = None,
) -> list[dict]:
    if not isinstance(raw_hotels, list) or not raw_hotels:
        return []

    items: list[dict] = []
    for raw_item in raw_hotels:
        contract = raw_hotel_item_to_contract(raw_item, ratings_map, check_in, check_out)
        if contract:
            items.append(contract)
    return items

def _extract_price(offers: Any, idx: int) -> float | None:
    """
    Extract price per night from offers array.
    
    Args:
        offers: Offers array from raw hotel data
        idx: Index of hotel (for logging)
    
    Returns:
        Price as integer, or None if extraction fails
    """
    try:
        if not isinstance(offers, list) or not offers:
            # Allow hotels to pass through even if Amadeus offers are missing.
            # Use 0.0 so UI can render; ranking layer should treat 0 as "unknown".
            return 0.0
                
        first_offer = offers[0]
        if not isinstance(first_offer, dict):
            logger.warning(f"Hotel at index {idx} has invalid offer structure, skipping")
            return None
        
        price_obj = first_offer.get("price", {})
        if not isinstance(price_obj, dict):
            logger.warning(f"Hotel at index {idx} has invalid price structure, skipping")
            return None
        
        total = price_obj.get("total")
        if total is None:
            logger.warning(f"Hotel at index {idx} missing price total, skipping")
            return None
        
        # Convert to int (handle both string and float)
        price = float(total)
        return price
    
    except (ValueError, TypeError) as e:
        logger.warning(
            f"Hotel at index {idx} has invalid price value: {e}, skipping"
        )
        return None
    
def _extract_currency(offers: Any) -> str:
    try:
        if not isinstance(offers, list) or not offers:
            return "INR"
        first_offer = offers[0]
        if not isinstance(first_offer, dict):
            return "INR"
        price_obj = first_offer.get("price", {})
        if not isinstance(price_obj, dict):
            return "INR"
        currency = price_obj.get("currency")
        if isinstance(currency, str) and currency.strip():
            return currency.strip().upper()
    except Exception:
        pass
    return "INR"

def _extract_name(hotel: dict) -> str:
    """
    Extract hotel name with fallback.
    
    Args:
        hotel: Hotel object from raw data
    
    Returns:
        Hotel name or "Unknown Hotel" if missing
    """
    name = hotel.get("name")
    if not name or not isinstance(name, str):
        return "Unknown Hotel"
    return str(name).strip()


def _extract_city(hotel: dict) -> str:
    """
    Extract city code with fallback.
    
    Args:
        hotel: Hotel object from raw data
    
    Returns:
        City code or "UNKNOWN" if missing
    """
    city = hotel.get("cityCode")
    if not city or not isinstance(city, str):
        return "UNKNOWN"
    return str(city).strip().upper()


def _extract_stars(hotel: dict, hotel_id: str, ratings_map: dict[str, dict]) -> int:
    """
    Extract or compute star rating (1-5).
    
    Priority:
    1. hotel["rating"] if present
    2. ratings_map[hotel_id]["overallRating"] if present (map 0-100 to 1-5)
    3. Default to 3 stars
    
    Args:
        hotel: Hotel object from raw data
        hotel_id: Hotel ID for ratings lookup
        ratings_map: Ratings mapping
    
    Returns:
        Star rating clamped to 1-5
    """
    stars = None
    
    # Try hotel rating first
    if "rating" in hotel:
        try:
            stars = int(float(hotel["rating"]))
        except (ValueError, TypeError):
            pass
    
    # Try ratings map
    if stars is None and hotel_id in ratings_map:
        try:
            rating_obj = ratings_map[hotel_id]
            if isinstance(rating_obj, dict) and "overallRating" in rating_obj:
                overall_rating = int(float(rating_obj["overallRating"]))
                # Map 0-100 to 1-5 stars
                if overall_rating >= 80:
                    stars = 5
                elif overall_rating >= 65:
                    stars = 4
                elif overall_rating >= 50:
                    stars = 3
                elif overall_rating >= 35:
                    stars = 2
                else:
                    stars = 1
        except (ValueError, TypeError, KeyError):
            pass
    
    # Default to 3 stars if nothing worked
    if stars is None:
        stars = 3
    
    # Clamp to 1-5
    stars = max(1, min(5, stars))
    
    return stars

def _extract_rating_0_to_5(hotel_id: str, ratings_map: dict[str, dict]) -> float:
    """
    Try to compute a review rating (0.0 to 5.0).
    If only overallRating (0-100) exists, map it to 0-5.
    """
    try:
        rating_obj = ratings_map.get(hotel_id)
        if not isinstance(rating_obj, dict):
            return 0.0

        # If you later have direct 'rating' field (0-5), prioritize it
        direct = rating_obj.get("rating")
        if direct is not None:
            return float(direct)

        overall = rating_obj.get("overallRating")
        if overall is None:
            return 0.0

        overall_0_100 = float(overall)
        # Map 0-100 -> 0-5
        return max(0.0, min(5.0, overall_0_100 / 20.0))
    except Exception:
        return 0.0

def _extract_amenities(hotel: dict) -> list[str]:
    """
    Extract amenities list with validation.
    
    Args:
        hotel: Hotel object from raw data
    
    Returns:
        List of amenity strings, or empty list if missing/invalid
    """
    amenities = hotel.get("amenities", [])
    
    if not isinstance(amenities, list):
        return []
    
    # Convert all entries to strings and filter out empty ones
    result = []
    for amenity in amenities:
        try:
            amenity_str = str(amenity).strip()
            if amenity_str:
                result.append(amenity_str)
        except Exception:
            continue
    
    return result
def hotel_option_to_contract(h: HotelOption) -> dict:
    """
    Convert HotelOption to MLOps-ready contract dict.
    Preserves all fields including booking_url, check_in, check_out.
    """
    city = getattr(h, "city", "") or ""
    check_in = getattr(h, "check_in", None)
    check_out = getattr(h, "check_out", None)

    # Reuse booking_url already on the object; only rebuild if blank
    existing_url = getattr(h, "booking_url", "") or ""
    if not existing_url:
        existing_url = _fallback_hotel_booking_url(h.name, city, check_in, check_out)

    return {
        "hotel_id": h.id,
        "name": h.name,
        "city": city,
        "rating": float(getattr(h, "rating", 0.0)),
        "stars": int(getattr(h, "star_category", 0)),
        "star_category": int(getattr(h, "star_category", 0)),
        "price_per_night": float(h.price_per_night),
        "currency": (h.currency or "INR"),
        "amenities": getattr(h, "amenities", []) or [],
        "check_in": check_in,
        "check_out": check_out,
        "booking_url": existing_url,
    }