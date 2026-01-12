"""Budget computation service."""

import logging

from backend.app.core.config import DEFAULT_CURRENCY
from backend.app.shared.schemas import (
    FlightOption,
    HotelOption,
    PlaceOption,
    BudgetSummary
)
from .helpers import (
    compute_flights_cost,
    compute_hotel_cost,
    compute_activities_cost
)

logger = logging.getLogger(__name__)


def compute_budget(
    flight: FlightOption | None,
    hotel: HotelOption | None,
    nights: int,
    places: list[PlaceOption] | None = None
) -> BudgetSummary:
    """
    Compute budget summary for a trip.
    
    Args:
        flight: Selected flight option (optional)
        hotel: Selected hotel option (optional)
        nights: Number of nights for hotel stay (must be >= 0)
        places: List of places to visit (optional)
    
    Returns:
        BudgetSummary with breakdown of costs and total
    
    Raises:
        ValueError: If inputs are invalid (negative values, invalid nights)
    """
    logger.info(f"Computing budget: flight={flight is not None}, hotel={hotel is not None}, nights={nights}, places={len(places) if places else 0}")
    
    # Compute individual cost components
    flights_cost = compute_flights_cost(flight)
    hotel_cost = compute_hotel_cost(hotel, nights)
    activities_cost = compute_activities_cost(places)
    
    # Compute total
    total_cost = flights_cost + hotel_cost + activities_cost
    
    logger.info(
        f"Budget computed: flights={flights_cost}, hotel={hotel_cost}, "
        f"activities={activities_cost}, total={total_cost} {DEFAULT_CURRENCY}"
    )
    
    # Return budget summary
    return BudgetSummary(
        flights_cost=flights_cost,
        hotel_cost=hotel_cost,
        activities_cost=activities_cost,
        total_cost=total_cost,
        currency=DEFAULT_CURRENCY
    )
