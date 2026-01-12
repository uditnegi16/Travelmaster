"""
API adapter for Amadeus Flight Offers Search.

This module provides a thin adapter layer between TravelGuru's flight service
and the Amadeus Flight Offers API. It handles parameter validation, conversion,
and error handling.
"""

import re
from datetime import datetime
from typing import Any

from backend.app.core.amadeus_client import call_amadeus, get_amadeus_client
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class FlightAPIError(RuntimeError):
    """Raised when the Amadeus Flight API call fails."""

    pass


def _validate_iata_code(code: str, field_name: str) -> None:
    """
    Validate IATA airport code format.

    Args:
        code: The IATA code to validate
        field_name: Name of the field for error messages

    Raises:
        ValueError: If the IATA code is invalid
    """
    if not code or not isinstance(code, str):
        raise ValueError(f"{field_name} must be a non-empty string")

    if len(code) != 3:
        raise ValueError(f"{field_name} must be exactly 3 characters, got: {code}")

    if not code.isalpha():
        raise ValueError(f"{field_name} must contain only letters, got: {code}")


def _validate_date_format(date_str: str, field_name: str) -> None:
    """
    Validate ISO date format (YYYY-MM-DD).

    Args:
        date_str: The date string to validate
        field_name: Name of the field for error messages

    Raises:
        ValueError: If the date format is invalid
    """
    if not date_str or not isinstance(date_str, str):
        raise ValueError(f"{field_name} must be a non-empty string")

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        raise ValueError(
            f"{field_name} must be in YYYY-MM-DD format, got: {date_str}"
        )

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"{field_name} is not a valid date: {date_str}") from e


def _validate_travel_class(travel_class: str) -> None:
    """
    Validate travel class against allowed values.

    Args:
        travel_class: The travel class to validate

    Raises:
        ValueError: If the travel class is invalid
    """
    valid_classes = {"ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"}
    if travel_class not in valid_classes:
        raise ValueError(
            f"travel_class must be one of {valid_classes}, got: {travel_class}"
        )


def _validate_currency(currency: str) -> None:
    """
    Validate currency code format (3 letters).

    Args:
        currency: The currency code to validate

    Raises:
        ValueError: If the currency code is invalid
    """
    if not currency or not isinstance(currency, str):
        raise ValueError("currency must be a non-empty string")

    if len(currency) != 3:
        raise ValueError(f"currency must be exactly 3 letters, got: {currency}")

    if not currency.isalpha():
        raise ValueError(f"currency must contain only letters, got: {currency}")


def search_flights_api(
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    adults: int = 1,
    children: int = 0,
    travel_class: str = "ECONOMY",
    max_results: int = 10,
    currency: str = "INR",
) -> list[dict]:
    """
    Search for flight offers using the Amadeus Flight Offers API.

    This function validates inputs, converts TravelGuru parameters to Amadeus API
    format, makes the API call, and returns raw flight offer data.

    Args:
        origin_iata: Origin airport IATA code (3 letters)
        destination_iata: Destination airport IATA code (3 letters)
        departure_date: Departure date in YYYY-MM-DD format
        adults: Number of adult passengers (>= 1)
        children: Number of child passengers (>= 0)
        travel_class: Travel class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
        max_results: Maximum number of results to return
        currency: Currency code for pricing (default: INR)

    Returns:
        List of flight offer dictionaries from Amadeus API

    Raises:
        ValueError: If any input validation fails
        FlightAPIError: If the Amadeus API call fails
    """
    # Validate IATA codes
    _validate_iata_code(origin_iata, "origin_iata")
    _validate_iata_code(destination_iata, "destination_iata")

    # Validate date format
    _validate_date_format(departure_date, "departure_date")

    # Validate passenger counts
    if not isinstance(adults, int) or adults < 1:
        raise ValueError(f"adults must be an integer >= 1, got: {adults}")

    if not isinstance(children, int) or children < 0:
        raise ValueError(f"children must be an integer >= 0, got: {children}")

    # Validate travel class
    _validate_travel_class(travel_class)

    # Validate currency
    _validate_currency(currency)

    # Cap max_results to Amadeus limit
    if max_results > 250:
        max_results = 250

    # Build API parameters
    params: dict[str, Any] = {
        "originLocationCode": origin_iata.upper(),
        "destinationLocationCode": destination_iata.upper(),
        "departureDate": departure_date,
        "adults": adults,
        "currencyCode": currency,
        "max": max_results,
    }

    # Add optional parameters only if non-zero/non-empty
    if children > 0:
        params["children"] = children

    if travel_class:
        params["travelClass"] = travel_class

    # Log request metadata (no credentials)
    logger.info(
        f"Searching flights: {origin_iata} → {destination_iata} on {departure_date}, "
        f"passengers: {adults} adults + {children} children, class: {travel_class}"
    )

    try:
        # Get Amadeus client
        client = get_amadeus_client()

        # Make API call using wrapper
        response = call_amadeus(
            lambda: client.shopping.flight_offers_search.get(**params)
        )

        # Extract flight offers from response
        offers = response.data if hasattr(response, "data") else []

        # Log result count
        logger.info(f"Received {len(offers)} flight offers from Amadeus API")

        return offers

    except Exception as e:
        # Convert any API error to FlightAPIError
        error_msg = f"Amadeus Flight API call failed: {str(e)}"
        logger.error(error_msg)
        raise FlightAPIError(error_msg) from e
