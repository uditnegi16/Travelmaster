"""Helper functions for budget computation."""

import logging

from shared.schemas import FlightOption, HotelOption, PlaceOption

logger = logging.getLogger(__name__)


def compute_flights_cost(flight: FlightOption | None) -> int:
    """
    Compute total cost for flights.
    
    Args:
        flight: Flight option with pricing, or None
    
    Returns:
        Total flight cost (0 if flight is None)
    
    Raises:
        ValueError: If flight price is negative
    """
    if flight is None:
        logger.debug("No flight provided, flights_cost = 0")
        return 0
    
    if flight.price < 0:
        raise ValueError(f"Flight price must be >= 0, got {flight.price}")
    
    logger.debug(f"Flights cost: {flight.price}")
    return flight.price


def compute_hotel_cost(hotel: HotelOption | None, nights: int) -> int:
    """
    Compute total cost for hotel accommodation.
    
    Args:
        hotel: Hotel option with price per night, or None
        nights: Number of nights to stay
    
    Returns:
        Total hotel cost (0 if hotel is None)
    
    Raises:
        ValueError: If nights is negative or hotel price_per_night is negative
    """
    if nights < 0:
        raise ValueError(f"Nights must be >= 0, got {nights}")
    
    if hotel is None:
        logger.debug("No hotel provided, hotel_cost = 0")
        return 0
    
    if hotel.price_per_night < 0:
        raise ValueError(f"Hotel price_per_night must be >= 0, got {hotel.price_per_night}")
    
    total = hotel.price_per_night * nights
    logger.debug(f"Hotel cost: {hotel.price_per_night} * {nights} = {total}")
    return total


def compute_activities_cost(places: list[PlaceOption] | None) -> int:
    """
    Compute total cost for visiting places/activities.
    
    Args:
        places: List of places to visit, or None
    
    Returns:
        Total activities cost (0 if places is None or empty)
    
    Raises:
        ValueError: If any place has negative entry_fee
    """
    if places is None or len(places) == 0:
        logger.debug("No places provided, activities_cost = 0")
        return 0
    
    total = 0
    for place in places:
        if place.entry_fee < 0:
            raise ValueError(f"Place entry_fee must be >= 0, got {place.entry_fee} for {place.name}")
        total += place.entry_fee
    
    logger.debug(f"Activities cost: {total} (from {len(places)} places)")
    return total


