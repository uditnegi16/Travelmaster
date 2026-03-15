"""
Flight search service.
Business orchestrator for flight search operations.
"""

from __future__ import annotations

import os
from datetime import date as dt_date
from typing import Any

from core.config import DEFAULT_CURRENCY
from core.logging import get_logger
from core.amadeus_iata import resolve_city_to_iata, UnknownCityError

from shared.schemas import FlightOption
from .adapters.api import search_flights_api
from .normalize import normalize_flight_offers

# Keep import, but we will gate it behind a flag to avoid current EnrichedFlight crash
from postprocessing.flight_enrichment import FlightIntelligenceEngine  # noqa: F401


logger = get_logger(__name__)


class FlightSearchError(RuntimeError):
    """Raised when flight search operation fails."""
    pass


def _bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def search_flights(
    from_city: str,
    to_city: str,
    date: str | None = None,
    adults: int = 1,
    max_price: int | None = None,
    preferences: dict[str, Any] | None = None,
    limit: int = 5,
    sort_by_price: bool = True,
) -> list[FlightOption]:
    """
    Search for flights using Amadeus API.
    """
    logger.info(
        "Flight search requested: %s → %s, date=%s, adults=%s, max_price=%s, preferences=%s, limit=%s",
        from_city, to_city, date, adults, max_price, preferences, limit
    )

    try:
        origin_iata = resolve_city_to_iata(from_city)
        destination_iata = resolve_city_to_iata(to_city)

        departure_date = date or dt_date.today().isoformat()

        avoid_layovers = bool((preferences or {}).get("avoid_layovers", False))
        non_stop = avoid_layovers
        travel_class = ((preferences or {}).get("cabin_class") or "ECONOMY").upper()

        max_results = max(limit * 3, 10)

        # ✅ CRITICAL: log exactly what will be sent to Amadeus
        logger.info(
            "FLIGHT AMADEUS PARAMS -> origin=%s dest=%s date=%s adults=%s class=%s non_stop=%s max=%s currency=%s",
            origin_iata, destination_iata, departure_date, adults, travel_class, non_stop, max_results, DEFAULT_CURRENCY
        )

        raw_offers = search_flights_api(
            origin_iata=origin_iata,
            destination_iata=destination_iata,
            departure_date=departure_date,
            adults=adults,
            travel_class=travel_class,
            non_stop=non_stop,
            max_results=max_results,
            currency=DEFAULT_CURRENCY,
        )

        logger.info("FLIGHT RAW OFFERS COUNT: %s", len(raw_offers) if raw_offers else 0)

        flights = normalize_flight_offers(raw_offers) or []
        logger.info("FLIGHT NORMALIZED COUNT: %s", len(flights))

        if max_price is not None:
            flights = [f for f in flights if getattr(f, "price", 0) <= max_price]

        if sort_by_price:
            flights.sort(key=lambda f: getattr(f, "price", 0))

        flights = flights[: max(1, limit)]
        logger.info("FLIGHT FINAL COUNT (after filters/limit): %s", len(flights))

        # ✅ keep enrichment OFF (your previous env check was broken anyway)
        return flights

    except UnknownCityError as e:
        logger.warning("Flight search failed (UnknownCityError): %s", e)
        return []
    except Exception as e:
        logger.exception("Flight search failed: %s", e)
        return []

