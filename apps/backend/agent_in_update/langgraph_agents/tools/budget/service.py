"""Budget computation service."""

import logging
from typing import Optional

from core.config import DEFAULT_CURRENCY
from shared.schemas import (
    FlightOption,
    HotelOption,
    PlaceOption,
    BudgetSummary
)
from postprocessing.budget_enrichment import enrich_budget
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
    places: list[PlaceOption] | None = None,
    num_travelers: int = 1,
    user_budget: Optional[int] = None,
    enable_enrichment: bool = True
) -> BudgetSummary:
    """
    Compute budget summary for a trip with optional enrichment.
    
    Args:
        flight: Selected flight option (optional)
        hotel: Selected hotel option (optional)
        nights: Number of nights for hotel stay (must be >= 0)
        places: List of places to visit (optional)
        num_travelers: Number of travelers (default: 1)
        user_budget: User's stated budget in INR (optional)
        enable_enrichment: Whether to enrich with intelligence and recommendations (default: True)
    
    Returns:
        BudgetSummary with breakdown of costs, total, and optional enrichment
    
    Raises:
        ValueError: If inputs are invalid (negative values, invalid nights)
    """
    logger.info(
        f"Computing budget: flight={flight is not None}, hotel={hotel is not None}, "
        f"nights={nights}, places={len(places) if places else 0}, travelers={num_travelers}, "
        f"user_budget={user_budget}, enrichment={enable_enrichment}"
    )
    
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
    
    # Create base budget summary
    def _to_int_money(x) -> int:
        try:
            return int(round(float(x)))
        except Exception:
            return 0

    budget_summary = BudgetSummary(
            flights_cost=_to_int_money(flights_cost),
            hotel_cost=_to_int_money(hotel_cost),
            activities_cost=_to_int_money(activities_cost),
            total_cost=_to_int_money(total_cost),
            currency=DEFAULT_CURRENCY,
        )
    
    # Add enrichment if enabled
    if enable_enrichment and nights > 0:
        num_days = nights + 1  # nights + 1 = total days
        
        try:
            enrichment = enrich_budget(
                flights_cost=flights_cost,
                hotel_cost=hotel_cost,
                activities_cost=activities_cost,
                total_cost=total_cost,
                num_days=num_days,
                num_travelers=num_travelers,
                user_budget=user_budget,
                flight=flight,
                hotel=hotel,
                places=places,
            )
            
            # Create enriched budget summary (need to use model_copy to set enrichment)
            budget_summary = BudgetSummary(
                flights_cost=flights_cost,
                hotel_cost=hotel_cost,
                activities_cost=activities_cost,
                total_cost=total_cost,
                currency=DEFAULT_CURRENCY,
                enrichment=enrichment
            )
            
            logger.info(
                f"Budget enrichment added: classification={enrichment.classification.classification}, "
                f"issues={len(enrichment.issues)}, recommendations={len(enrichment.recommendations)}"
            )
        except Exception as e:
            logger.warning(f"Budget enrichment failed: {e}. Returning basic budget summary.")
    
    return budget_summary


