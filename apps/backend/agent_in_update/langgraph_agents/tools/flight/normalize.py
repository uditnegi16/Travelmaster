from __future__ import annotations

"""
Normalization utilities for Amadeus Flight Offers.
Converts raw Amadeus API responses into FlightOption schema.
"""

import re
from typing import Any

from core.logging import get_logger
from shared.schemas import FlightOption

logger = get_logger(__name__)
import re
import urllib.parse


import hashlib
import urllib.parse
from typing import Any


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _stable_flight_id(offer: dict) -> str:
    """
    Creates stable id even if Amadeus 'id' missing.
    """
    raw = str(offer.get("id") or "") + "|" + str(offer.get("lastTicketingDate") or "") + "|" + str(offer.get("source") or "")
    if raw.strip("|") == "":
        raw = str(offer)[:500]
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _build_booking_url(offer_id: str, origin: str, destination: str, departure_time: str) -> str:
    """
    Placeholder booking link. Replace later with your actual booking/deeplink provider.
    Still satisfies contract: valid URL string.
    """
    q = urllib.parse.urlencode(
        {"offerId": offer_id, "from": origin, "to": destination, "depart": departure_time}
    )
    return f"https://www.amadeus.com/en/booking?{q}"



def _parse_iso8601_duration(duration: str) -> str:
    """
    Convert ISO-8601 duration to human-readable format.
    
    Args:
        duration: ISO-8601 duration string (e.g., "PT2H30M")
        
    Returns:
        Human-readable duration (e.g., "2h 30m")
    """
    if not duration:
        return ""
    
    try:
        # Match hours and minutes in ISO-8601 format
        hours_match = re.search(r'(\d+)H', duration)
        minutes_match = re.search(r'(\d+)M', duration)
        
        hours = int(hours_match.group(1)) if hours_match else 0
        minutes = int(minutes_match.group(1)) if minutes_match else 0
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return ""
    except Exception:
        return ""

def _iso8601_duration_to_minutes(duration: str) -> int:
    """
    Convert ISO-8601 duration to minutes (e.g., 'PT2H30M' -> 150).
    Returns 0 if parsing fails.
    """
    if not duration:
        return 0
    try:
        hours_match = re.search(r'(\d+)H', duration)
        minutes_match = re.search(r'(\d+)M', duration)
        hours = int(hours_match.group(1)) if hours_match else 0
        minutes = int(minutes_match.group(1)) if minutes_match else 0
        return hours * 60 + minutes
    except Exception:
        return 0
def _fallback_flight_booking_url(origin: str, destination: str, departure_date: str = "") -> str:
    """
    Fallback booking URL when provider deeplink isn't available.
    Uses a stable Google search URL.
    """
    try:
        import urllib.parse
        q = f"{origin} to {destination} flights {departure_date}".strip()
        return "https://www.google.com/search?q=" + urllib.parse.quote(q)
    except Exception:
        return ""
    
def _calculate_layover_durations(segments: list[dict]) -> list[str]:
    """
    Calculate layover durations between flight segments.
    
    Args:
        segments: List of flight segments
        
    Returns:
        List of layover durations in human-readable format
    """
    layovers = []
    try:
        for i in range(len(segments) - 1):
            arrival_time = segments[i].get("arrival", {}).get("at", "")
            next_departure = segments[i + 1].get("departure", {}).get("at", "")
            
            if arrival_time and next_departure:
                from datetime import datetime
                arr = datetime.fromisoformat(arrival_time.replace("Z", "+00:00"))
                dep = datetime.fromisoformat(next_departure.replace("Z", "+00:00"))
                diff = dep - arr
                
                hours = int(diff.total_seconds() // 3600)
                minutes = int((diff.total_seconds() % 3600) // 60)
                
                if hours > 0 and minutes > 0:
                    layovers.append(f"{hours}h {minutes}m")
                elif hours > 0:
                    layovers.append(f"{hours}h")
                elif minutes > 0:
                    layovers.append(f"{minutes}m")
    except Exception:
        pass
    return layovers


def _extract_airline_code(segments: list[dict]) -> str:
    """
    Extract airline code from flight segments.
    
    Args:
        segments: List of flight segments
        
    Returns:
        Airline carrier code (or empty string if not found)
    """
    try:
        if segments and len(segments) > 0:
            return segments[0].get("carrierCode", "")
    except Exception:
        pass
    return ""


def _extract_all_carriers(segments: list[dict]) -> str:
    """
    Extract all unique carrier codes from flight segments.
    
    Args:
        segments: List of flight segments
        
    Returns:
        Comma-separated carrier codes (e.g., "AA,BA")
    """
    try:
        carriers = []
        for segment in segments:
            carrier = segment.get("carrierCode", "")
            if carrier and carrier not in carriers:
                carriers.append(carrier)
        return ",".join(carriers) if carriers else ""
    except Exception:
        pass
    return ""


def _map_cabin_class(segments: list[dict]) -> str:
    """
    Map cabin class from flight segments.
    
    Args:
        segments: List of flight segments
        
    Returns:
        Cabin class (e.g., "ECONOMY", "BUSINESS")
    """
    try:
        if segments and len(segments) > 0:
            return segments[0].get("cabin", "")
    except Exception:
        pass
    return ""


def _extract_fare_family(offer: dict) -> str:
    """
    Extract fare family/brand from offer.
    
    Args:
        offer: Raw Amadeus flight offer
        
    Returns:
        Fare family name (or empty string)
    """
    try:
        traveler_pricings = offer.get("travelerPricings", [])
        if traveler_pricings and len(traveler_pricings) > 0:
            fare_details = traveler_pricings[0].get("fareDetailsBySegment", [])
            if fare_details and len(fare_details) > 0:
                return fare_details[0].get("fareBasis", "")
    except Exception:
        pass
    return ""


def _map_refundability(offer: dict) -> bool:
    """
    Determine if the fare is refundable.
    
    Args:
        offer: Raw Amadeus flight offer
        
    Returns:
        True if refundable, False otherwise
    """
    try:
        price_data = offer.get("price", {})
        refundable = price_data.get("refundableTaxes", False)
        return bool(refundable)
    except Exception:
        pass
    return False


def _normalize_single_offer(offer: dict) -> FlightOption | None:
    """
    Normalize a single Amadeus flight offer to FlightOption.
    
    Args:
        offer: Raw Amadeus flight offer dictionary
        
    Returns:
        FlightOption if successful, None if offer is invalid
    """
    try:
        # Extract price information
        price_data = offer.get("price", {})
        grand_total = price_data.get("grandTotal", "0")
        currency = price_data.get("currency", "USD")
        
        # Normalize price to integer
        price = int(round(float(grand_total)))
        
        # Extract itinerary information
        itineraries = offer.get("itineraries", [])
        if not itineraries or len(itineraries) == 0:
            return None
        
        first_itinerary = itineraries[0]
        segments = first_itinerary.get("segments", [])
        
        if not segments or len(segments) == 0:
            return None
        
        # Extract segments data
        first_segment = segments[0]
        last_segment = segments[-1]
        
        # Extract origin and destination
        origin = first_segment.get("departure", {}).get("iataCode", "")
        destination = last_segment.get("arrival", {}).get("iataCode", "")
        
        # Extract departure and arrival times
        departure_time = first_segment.get("departure", {}).get("at", "")
        arrival_time = last_segment.get("arrival", {}).get("at", "")
        
        # Extract airline code
        airline = _extract_airline_code(segments)
        
        # Calculate stops
        stops = len(segments) - 1
        
        # Extract and convert duration
        duration_iso = first_itinerary.get("duration", "")
        duration = _parse_iso8601_duration(duration_iso)
        
        cabin_class = _map_cabin_class(segments) or "ECONOMY"
        duration_minutes = _iso8601_duration_to_minutes(duration_iso)
        
        # Generate unique ID
        flight_id = f"{airline}_{origin}_{destination}_{departure_time}"
        
        # Validate required fields
        if not all([airline, origin, destination, departure_time, arrival_time]):
            return None
        
        booking_url = _fallback_flight_booking_url(
            origin, destination, departure_time[:10] if departure_time else ""
        )

        return FlightOption(
            id=flight_id,
            airline=airline,
            origin=origin,
            destination=destination,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration=duration,
            duration_minutes=duration_minutes,
            stops=stops,
            price=price,
            currency=currency,
            booking_url=booking_url,
        )
        
    except Exception as e:
        # Skip invalid offers gracefully
        logger.debug(f"Skipping invalid offer: {str(e)}")
        return None

def offer_to_flight_contract(offer: dict, departure_date: str = "") -> dict | None:
    """
    Convert a raw Amadeus flight offer into MLOps-ready flight contract dict.
    This is used by the agent API to return flights[] with scoring keys.
    """
    try:
        price_data = offer.get("price", {})
        grand_total = price_data.get("grandTotal", "0")
        currency = price_data.get("currency", "USD")
        price = float(grand_total)

        itineraries = offer.get("itineraries", [])
        if not itineraries:
            return None

        first_itinerary = itineraries[0]
        segments = first_itinerary.get("segments", [])
        if not segments:
            return None

        first_segment = segments[0]
        last_segment = segments[-1]

        origin = first_segment.get("departure", {}).get("iataCode", "")
        destination = last_segment.get("arrival", {}).get("iataCode", "")
        departure_time = first_segment.get("departure", {}).get("at", "")
        arrival_time = last_segment.get("arrival", {}).get("at", "")

        airline = _extract_airline_code(segments)
        stops = len(segments) - 1

        duration_iso = first_itinerary.get("duration", "")
        duration_minutes = _iso8601_duration_to_minutes(duration_iso)

        cabin_class = _map_cabin_class(segments) or "ECONOMY"

        flight_id = f"{airline}_{origin}_{destination}_{departure_time}"

        if not all([airline, origin, destination, departure_time, arrival_time]):
            return None

        return {
            "flight_id": flight_id,
            "airline": airline,
            "price": float(price),
            "currency": currency,
            "duration_minutes": int(duration_minutes),
            "cabin_class": cabin_class,
            "stops": int(stops),
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "booking_url": _fallback_flight_booking_url(origin, destination, departure_date),
        }

    except Exception as e:
        logger.debug(f"Skipping invalid offer for contract: {str(e)}")
        return None
    
def normalize_flight_offers(raw_offers: list[dict]) -> list[FlightOption]:
    """
    Convert raw Amadeus Flight Offers JSON into FlightOption schema objects.
    
    This function handles empty input safely, never crashes on missing fields,
    and skips invalid offers gracefully.
    
    Args:
        raw_offers: List of raw Amadeus flight offer dictionaries
        
    Returns:
        List of normalized FlightOption objects
    """
    # Handle empty input
    if not raw_offers:
        logger.info("No raw offers to normalize")
        return []
    
    logger.info(f"Normalizing {len(raw_offers)} raw flight offers")
    
    normalized_offers: list[FlightOption] = []
    
    for offer in raw_offers:
        normalized = _normalize_single_offer(offer)
        if normalized:
            normalized_offers.append(normalized)
    
    logger.info(
        f"Successfully normalized {len(normalized_offers)} out of {len(raw_offers)} offers"
    )
    
    return normalized_offers

def normalize_flight_offers_to_contract(
    raw_offers: list[dict],
    departure_date: str = "",
) -> list[dict]:
    """
    Convert raw Amadeus flight offers directly to MLOps-ready contract dicts.
    """
    if not raw_offers:
        return []

    flights: list[dict] = []
    for offer in raw_offers:
        item = offer_to_flight_contract(offer, departure_date=departure_date)
        if item:
            flights.append(item)
    return flights

def normalize_dataset_flights(raw_flights: list[dict]) -> list[FlightOption]:
    """
    Convert raw dataset flight records into FlightOption schema objects.
    
    Args:
        raw_flights: List of raw dataset flight dictionaries
        
    Returns:
        List of normalized FlightOption objects
    """
    if not raw_flights:
        logger.info("No raw dataset flights to normalize")
        return []
    
    logger.info(f"Normalizing {len(raw_flights)} dataset flights")
    
    normalized_flights: list[FlightOption] = []
    
    for flight in raw_flights:
        try:
            flight_id = flight.get("flight_id") or flight.get("id", "")
            airline = flight.get("airline", "")
            origin = flight.get("from") or flight.get("from_city", "")
            destination = flight.get("to") or flight.get("to_city", "")
            departure_time = flight.get("departure_time", "")
            arrival_time = flight.get("arrival_time", "")
            price = flight.get("price", 0)
            
            if not all([flight_id, airline, origin, destination, departure_time, arrival_time]):
                continue
            
            duration = ""
            try:
                from datetime import datetime
                dep = datetime.fromisoformat(departure_time.replace("Z", "+00:00"))
                arr = datetime.fromisoformat(arrival_time.replace("Z", "+00:00"))
                diff = arr - dep
                hours = int(diff.total_seconds() // 3600)
                minutes = int((diff.total_seconds() % 3600) // 60)
                if hours > 0 and minutes > 0:
                    duration = f"{hours}h {minutes}m"
                elif hours > 0:
                    duration = f"{hours}h"
                elif minutes > 0:
                    duration = f"{minutes}m"
            except Exception:
                pass
            
            flight_option = FlightOption(
                id=flight_id,
                airline=airline,
                origin=origin,
                destination=destination,
                departure_time=departure_time,
                arrival_time=arrival_time,
                duration=duration,
                stops=0,
                price=int(price),
                currency="INR",
            )
            
            normalized_flights.append(flight_option)
            
        except Exception as e:
            logger.debug(f"Skipping invalid dataset flight: {str(e)}")
            continue
    
    logger.info(
        f"Successfully normalized {len(normalized_flights)} out of {len(raw_flights)} dataset flights"
    )
    
    return normalized_flights
import re

def _duration_text_to_minutes(duration_text: str) -> int:
    """
    Convert '2h 30m' / '45m' / '3h' to minutes.
    Returns 0 if parsing fails.
    """
    if not duration_text:
        return 0
    try:
        h = re.search(r"(\d+)\s*h", duration_text)
        m = re.search(r"(\d+)\s*m", duration_text)
        hours = int(h.group(1)) if h else 0
        mins = int(m.group(1)) if m else 0
        return hours * 60 + mins
    except Exception:
        return 0


def flight_option_to_contract(
    f,
    departure_date: str = "",
    cabin_class: str = "ECONOMY",
    duration_minutes: int | None = None,
) -> dict:
    """
    Convert internal FlightOption to MLOps-ready contract dict.
    Preserves all fields including booking_url, origin, destination.
    """
    dm = duration_minutes if duration_minutes is not None else (
        getattr(f, "duration_minutes", 0) or _duration_text_to_minutes(getattr(f, "duration", ""))
    )
    origin = getattr(f, "origin", "") or ""
    destination = getattr(f, "destination", "") or ""

    # Reuse booking_url already on the object; only rebuild if blank
    existing_url = getattr(f, "booking_url", "") or ""
    if not existing_url:
        dep_date = departure_date or (getattr(f, "departure_time", "") or "")[:10]
        existing_url = _fallback_flight_booking_url(origin, destination, dep_date)

    return {
        "flight_id": f.id,
        "airline": f.airline,
        "origin": origin,
        "destination": destination,
        "price": float(f.price),
        "currency": getattr(f, "currency", None) or "INR",
        "duration": getattr(f, "duration", "") or "",
        "duration_minutes": int(dm),
        "cabin_class": cabin_class or getattr(f, "cabin_class", "ECONOMY") or "ECONOMY",
        "stops": int(getattr(f, "stops", 0)),
        "departure_time": getattr(f, "departure_time", ""),
        "arrival_time": getattr(f, "arrival_time", ""),
        "booking_url": existing_url,
    }

