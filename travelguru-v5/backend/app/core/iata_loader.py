"""
Amadeus-backed airport loader.

Provides utilities to fetch airport information from Amadeus and to
load/save a local `airports.json` used to augment the static CITY_DB.

This module is optional — the code that imports it handles absence of
the Amadeus SDK or missing credentials gracefully.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    from amadeus import Client
    AMADEUS_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    Client = None  # type: ignore
    AMADEUS_AVAILABLE = False


def _normalize_key(name: str) -> str:
    return name.strip().lower()


def _get_client() -> "Client":
    if not AMADEUS_AVAILABLE:
        raise RuntimeError("Amadeus SDK not installed. Install with `pip install amadeus`.")

    client_id = os.getenv("AMADEUS_CLIENT_ID") or os.getenv("AMADEUS_API_KEY")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET") or os.getenv("AMADEUS_API_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError("Missing Amadeus credentials. Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET.")

    return Client(client_id=client_id, client_secret=client_secret)


def fetch_airports_for_city(city: str, max_results: int = 5) -> List[Dict]:
    """Query Amadeus for airports matching a city name.

    Returns list of airport dicts with keys: iata, city, country, airport
    """
    if not AMADEUS_AVAILABLE:
        raise RuntimeError("Amadeus SDK not available")

    client = _get_client()

    try:
        resp = client.reference_data.locations.get(subType="AIRPORT", keyword=city)
    except Exception:
        logger.exception("Amadeus request failed")
        raise

    results: List[Dict] = []

    for item in getattr(resp, "data", [])[:max_results]:
        iata = item.get("iataCode") or item.get("id") or ""
        address = item.get("address") or {}

        airport_entry = {
            "iata": iata,
            "city": address.get("cityName") or item.get("name") or city,
            "country": address.get("countryName") or address.get("countryCode") or "",
            "airport": item.get("name") or item.get("detailedName") or "",
        }

        results.append(airport_entry)

    return results


def build_city_db_from_amadeus(cities: List[str], output_path: str | Path, max_results_per_city: int = 3) -> Dict[str, Dict]:
    """Build a CITY_DB-like dict for given cities and write to `output_path`.

    The returned dict maps normalized city keys to airport info.
    """
    db: Dict[str, Dict] = {}

    for city in cities:
        try:
            airports = fetch_airports_for_city(city, max_results=max_results_per_city)
        except Exception:
            logger.warning(f"Skipping city '{city}' due to Amadeus error")
            continue

        if not airports:
            continue

        chosen = airports[0]
        key = _normalize_key(city)

        if not chosen.get("iata"):
            logger.debug(f"No IATA for city {city}, skipping")
            continue

        db[key] = {
            "iata": chosen["iata"],
            "city": chosen["city"] or city,
            "country": chosen.get("country") or "",
            "airport": chosen.get("airport") or "",
        }

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(db, fh, ensure_ascii=False, indent=2)

    logger.info(f"Wrote {len(db)} entries to {out_path}")

    return db


def load_local_db(path: str | Path) -> Dict[str, Dict]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"DB file not found: {p}")

    with p.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    normalized = {k.strip().lower(): v for k, v in data.items()}
    logger.info(f"Loaded {len(normalized)} entries from {p}")
    return normalized
