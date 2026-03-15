# core/amadeus_iata.py
"""
City name → IATA airport code resolver.

BUG FIX: This module was entirely missing — caused UnknownCityError on every
flight/hotel search. Amadeus sandbox only accepts IATA codes (e.g. 'DEL'),
never plain city names ('Delhi').
"""

from __future__ import annotations

import unicodedata
from typing import Optional
from core.logging import get_logger

logger = get_logger(__name__)


class UnknownCityError(ValueError):
    """Raised when a city cannot be resolved to an IATA code."""
    pass


def _normalise(text: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join(text.lower().split())


# Static lookup table — city name/alias → IATA code
_CITY_TO_IATA: dict[str, str] = {
    # India
    "delhi": "DEL", "new delhi": "DEL", "igi": "DEL", "indira gandhi": "DEL",
    "mumbai": "BOM", "bombay": "BOM",
    "bengaluru": "BLR", "bangalore": "BLR",
    "hyderabad": "HYD", "rajiv gandhi": "HYD",
    "chennai": "MAA", "madras": "MAA",
    "kolkata": "CCU", "calcutta": "CCU",
    "goa": "GOI", "dabolim": "GOI", "north goa": "GOI", "south goa": "GOI", "panaji": "GOI",
    "pune": "PNQ",
    "ahmedabad": "AMD",
    "jaipur": "JAI",
    "kochi": "COK", "cochin": "COK",
    "lucknow": "LKO",
    "varanasi": "VNS", "benaras": "VNS",
    "bhopal": "BHO",
    "indore": "IDR",
    "nagpur": "NAG",
    "coimbatore": "CJB",
    "thiruvananthapuram": "TRV", "trivandrum": "TRV",
    "calicut": "CCJ", "kozhikode": "CCJ",
    "mangalore": "IXE", "mangaluru": "IXE",
    "vizag": "VTZ", "visakhapatnam": "VTZ",
    "bhubaneswar": "BBI",
    "patna": "PAT",
    "ranchi": "IXR",
    "raipur": "RPR",
    "amritsar": "ATQ",
    "chandigarh": "IXC",
    "jammu": "IXJ",
    "srinagar": "SXR",
    "leh": "IXL",
    "dehradun": "DED",
    "agra": "AGR",
    "jodhpur": "JDH",
    "udaipur": "UDR",
    "guwahati": "GAU",
    "port blair": "IXZ", "andaman": "IXZ",
    "tirupati": "TIR",
    "madurai": "IXM",
    "tiruchirappalli": "TRZ", "trichy": "TRZ",
    "bagdogra": "IXB",
    "mysore": "MYQ", "mysuru": "MYQ",
    "aurangabad": "IXU",
    "imphal": "IMF",
    "dibrugarh": "DIB",
    "hubli": "HBX",
    "belagavi": "IXG", "belgaum": "IXG",
    "surat": "STV",
    # International
    "london": "LHR", "heathrow": "LHR",
    "paris": "CDG", "charles de gaulle": "CDG",
    "dubai": "DXB",
    "abu dhabi": "AUH",
    "doha": "DOH",
    "singapore": "SIN",
    "bangkok": "BKK", "suvarnabhumi": "BKK",
    "kuala lumpur": "KUL",
    "hong kong": "HKG",
    "tokyo": "NRT", "narita": "NRT",
    "osaka": "KIX",
    "new york": "JFK", "jfk": "JFK",
    "los angeles": "LAX",
    "chicago": "ORD",
    "san francisco": "SFO",
    "toronto": "YYZ",
    "sydney": "SYD",
    "melbourne": "MEL",
    "frankfurt": "FRA",
    "amsterdam": "AMS",
    "madrid": "MAD",
    "barcelona": "BCN",
    "rome": "FCO",
    "milan": "MXP",
    "zurich": "ZRH",
    "vienna": "VIE",
    "istanbul": "IST",
    "cairo": "CAI",
    "johannesburg": "JNB",
    "beijing": "PEK",
    "shanghai": "PVG",
    "seoul": "ICN", "incheon": "ICN",
    "kathmandu": "KTM",
    "colombo": "CMB",
    "dhaka": "DAC",
    "karachi": "KHI",
    "lahore": "LHE",
    "islamabad": "ISB",
    "male": "MLE", "maldives": "MLE",
    "bali": "DPS", "denpasar": "DPS",
    "jakarta": "CGK",
    "manila": "MNL",
    "ho chi minh": "SGN", "saigon": "SGN",
    "hanoi": "HAN",
}

# Normalised lookup built once at import time
_LOOKUP: dict[str, str] = {_normalise(k): v for k, v in _CITY_TO_IATA.items()}


def resolve_city_to_iata(city: str) -> str:
    """
    Convert a city name to an IATA airport code.

    Resolution order:
    1. Exact match in static table
    2. Already a valid IATA code → return as-is
    3. Partial / contains match
    4. Live Amadeus Airport & City Search API
    5. Raise UnknownCityError
    """
    if not city or not isinstance(city, str):
        raise UnknownCityError(f"Invalid city: {city!r}")

    norm = _normalise(city.strip())

    # 1. Exact match
    if norm in _LOOKUP:
        code = _LOOKUP[norm]
        logger.debug("IATA resolved (exact): %s → %s", city, code)
        return code

    # 2. Already an IATA code
    stripped = city.strip().upper()
    if len(stripped) == 3 and stripped.isalpha():
        logger.debug("IATA resolved (passthrough): %s", stripped)
        return stripped

    # 3. Partial / contains match
    for key, code in _LOOKUP.items():
        if key in norm or norm in key:
            logger.debug("IATA resolved (partial): %s → %s (via %s)", city, code, key)
            return code

    # 4. Live Amadeus lookup
    try:
        code = _resolve_via_amadeus(city)
        if code:
            logger.info("IATA resolved (amadeus API): %s → %s", city, code)
            _LOOKUP[norm] = code
            return code
    except Exception as e:
        logger.warning("Amadeus IATA lookup failed for %r: %s", city, e)

    raise UnknownCityError(
        f"Cannot resolve '{city}' to an IATA code. "
        "Add it to core/amadeus_iata.py or check spelling."
    )


def _resolve_via_amadeus(city: str) -> Optional[str]:
    """Use Amadeus Airport & City Search API. Returns None if not found."""
    try:
        from core.amadeus_client import get_amadeus_client, call_amadeus
        client = get_amadeus_client()
        response = call_amadeus(
            client.reference_data.locations.get,
            keyword=city,
            subType="AIRPORT,CITY",
            max=5,
        )
        data = getattr(response, "data", None) or []
        for item in data:
            iata = item.get("iataCode") if isinstance(item, dict) else getattr(item, "iataCode", None)
            if iata and len(iata) == 3:
                return iata.upper()
    except Exception:
        pass
    return None


