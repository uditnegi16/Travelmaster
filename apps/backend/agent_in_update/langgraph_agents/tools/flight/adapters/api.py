"""
API adapter for Amadeus Flight Offers Search.

This module provides a thin adapter layer between TravelGuru's flight service
and the Amadeus Flight Offers API. It handles parameter validation, conversion,
and error handling.

Adapter responsibilities:
- Input validation
- Parameter mapping to Amadeus API
- Raw API calls
- Error handling (transient errors should not kill the whole agent run)
"""

import re
from datetime import datetime
from typing import Any

from core.amadeus_client import (
    AmadeusAPIError,
    call_amadeus,
    ensure_amadeus_healthy,
    get_amadeus_client,
)
from core.logging import get_logger

logger = get_logger(__name__)


class FlightAPIError(RuntimeError):
    """Raised when the Amadeus Flight API call fails (non-recoverable)."""

    pass


def _validate_iata_code(code: str, field_name: str) -> None:
    if not code or not isinstance(code, str):
        raise ValueError(f"{field_name} must be a non-empty string")

    code = code.strip()
    if len(code) != 3:
        raise ValueError(f"{field_name} must be exactly 3 characters, got: {code}")

    if not code.isalpha():
        raise ValueError(f"{field_name} must contain only letters, got: {code}")


def _validate_date_format(date_str: str, field_name: str) -> None:
    if not date_str or not isinstance(date_str, str):
        raise ValueError(f"{field_name} must be a non-empty string")

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        raise ValueError(f"{field_name} must be in YYYY-MM-DD format, got: {date_str}")

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"{field_name} is not a valid date: {date_str}") from e


def _validate_travel_class(travel_class: str) -> None:
    valid_classes = {"ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"}
    if travel_class not in valid_classes:
        raise ValueError(
            f"travel_class must be one of {valid_classes}, got: {travel_class}"
        )


def _validate_currency(currency: str) -> None:
    if not currency or not isinstance(currency, str):
        raise ValueError("currency must be a non-empty string")

    currency = currency.strip()
    if len(currency) != 3:
        raise ValueError(f"currency must be exactly 3 letters, got: {currency}")

    if not currency.isalpha():
        raise ValueError(f"currency must contain only letters, got: {currency}")


def search_flights_api(
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    return_date: str | None = None,
    adults: int = 1,
    children: int = 0,
    travel_class: str = "ECONOMY",
    non_stop: bool = False,
    max_results: int = 10,
    currency: str = "INR",
) -> list[dict]:
    """
    Search for flight offers using the Amadeus Flight Offers API.

    Returns:
        Raw list of offer dicts from Amadeus response.
        If Amadeus has transient errors (500), returns [] instead of failing the whole run.
    """
    ensure_amadeus_healthy()

    # Validate inputs
    _validate_iata_code(origin_iata, "origin_iata")
    _validate_iata_code(destination_iata, "destination_iata")
    _validate_date_format(departure_date, "departure_date")

    if return_date:
        _validate_date_format(return_date, "return_date")

    if not isinstance(adults, int) or adults < 1:
        raise ValueError(f"adults must be an integer >= 1, got: {adults}")

    if not isinstance(children, int) or children < 0:
        raise ValueError(f"children must be an integer >= 0, got: {children}")

    _validate_travel_class(travel_class)
    _validate_currency(currency)

    # Clamp max_results
    if not isinstance(max_results, int) or max_results < 1:
        max_results = 10
    max_results = min(max_results, 250)

    params: dict[str, Any] = {
        "originLocationCode": origin_iata.strip().upper(),
        "destinationLocationCode": destination_iata.strip().upper(),
        "departureDate": departure_date,
        "adults": adults,
        "currencyCode": currency.strip().upper(),
        "max": max_results,
    }

    if children > 0:
        params["children"] = children

    if travel_class:
        params["travelClass"] = travel_class

    if return_date:
        params["returnDate"] = return_date

    if non_stop:
        params["nonStop"] = True

    logger.info(
        f"Searching flights: {origin_iata} → {destination_iata} on {departure_date}, "
        f"passengers: {adults} adults + {children} children, class: {travel_class}, "
        f"non_stop={non_stop}"
    )

    try:
        client = get_amadeus_client()
        response = call_amadeus(
            client.shopping.flight_offers_search.get,
            **params,
        )

        offers = response.data if hasattr(response, "data") and response.data else []
        if not offers:
            logger.warning(f"Amadeus returned 0 flight offers for params={params}")
        else:
            logger.info(f"Received {len(offers)} flight offers from Amadeus API")
        return offers

    except AmadeusAPIError as e:
        msg = str(e).upper()

        # Transient provider/server errors should not kill pipeline
        if "[500]" in msg or "INTERNAL SERVER ERROR" in msg:
            logger.warning(f"Amadeus flights transient failure, returning []: {e}")
            return []

        # For 400/401/etc, treat as real bug or auth issue (surface it)
        raise FlightAPIError(f"Amadeus Flight API call failed: {str(e)}") from e

    except Exception as e:
        raise FlightAPIError(f"Amadeus Flight API call failed: {str(e)}") from e