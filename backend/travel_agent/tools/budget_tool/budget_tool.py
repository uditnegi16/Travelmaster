"""
Budget Tool - Pure Computation and Validation

This module provides budget calculation and validation functionality.
It does NOT call any external APIs or datasets - only performs calculations
on provided travel options.

Responsibilities:
- Calculate total flight costs
- Calculate total hotel costs (price_per_night × nights)
- Calculate/allocate activities/miscellaneous costs
- Validate against user budget
- Return detailed breakdown with BudgetSummary schema
"""

import logging
from dataclasses import dataclass
from typing import Optional, List
from decimal import Decimal

from travel_agent.schemas import FlightOption, HotelOption, BudgetSummary
from travel_agent.config import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)


@dataclass
class BudgetCalculationResult:
    """
    Result of budget calculation with detailed breakdown and validation.
    
    Attributes:
        budget_summary: BudgetSummary object with cost breakdown
        total_cost: Total trip cost in INR
        user_budget: User's specified budget (None if not provided)
        is_within_budget: Whether total is within budget (True if no budget specified)
        budget_remaining: Remaining budget (negative if over budget)
        budget_utilization_percent: Percentage of budget used
        warnings: List of warning messages
        recommendations: List of budget optimization recommendations
    """
    budget_summary: BudgetSummary
    total_cost: int
    user_budget: Optional[int]
    is_within_budget: bool
    budget_remaining: int
    budget_utilization_percent: float
    warnings: List[str]
    recommendations: List[str]


def calculate_flight_cost(
    outbound_flight: Optional[FlightOption] = None,
    return_flight: Optional[FlightOption] = None,
    additional_flights: Optional[List[FlightOption]] = None
) -> int:
    """
    Calculate total flight costs.
    
    Args:
        outbound_flight: Outbound flight option (optional)
        return_flight: Return flight option (optional)
        additional_flights: List of additional flights (optional)
    
    Returns:
        int: Total flight cost in INR
    
    Example:
        >>> outbound = FlightOption(price=5000, ...)
        >>> return_flight = FlightOption(price=4500, ...)
        >>> calculate_flight_cost(outbound, return_flight)
        9500
    """
    total = 0
    
    if outbound_flight:
        total += outbound_flight.price
        logger.debug(f"Outbound flight cost: ₹{outbound_flight.price:,}")
    
    if return_flight:
        total += return_flight.price
        logger.debug(f"Return flight cost: ₹{return_flight.price:,}")
    
    if additional_flights:
        for i, flight in enumerate(additional_flights, 1):
            total += flight.price
            logger.debug(f"Additional flight {i} cost: ₹{flight.price:,}")
    
    logger.info(f"Total flight cost: ₹{total:,}")
    return total


def calculate_hotel_cost(
    hotel: Optional[HotelOption] = None,
    nights: int = 1,
    additional_hotels: Optional[List[tuple[HotelOption, int]]] = None
) -> int:
    """
    Calculate total hotel accommodation costs.
    
    Args:
        hotel: Primary hotel option (optional)
        nights: Number of nights for primary hotel (default: 1)
        additional_hotels: List of (hotel, nights) tuples for multi-city trips
    
    Returns:
        int: Total hotel cost in INR
    
    Raises:
        ValueError: If nights < 0
    
    Example:
        >>> hotel = HotelOption(price_per_night=3000, ...)
        >>> calculate_hotel_cost(hotel, nights=3)
        9000
    """
    if nights < 0:
        raise ValueError(f"Nights cannot be negative, got {nights}")
    
    total = 0
    
    if hotel:
        hotel_total = hotel.price_per_night * nights
        total += hotel_total
        logger.debug(
            f"Primary hotel: ₹{hotel.price_per_night:,}/night × {nights} nights = ₹{hotel_total:,}"
        )
    
    if additional_hotels:
        for i, (hotel_option, hotel_nights) in enumerate(additional_hotels, 1):
            if hotel_nights < 0:
                raise ValueError(f"Nights cannot be negative for hotel {i}, got {hotel_nights}")
            
            hotel_total = hotel_option.price_per_night * hotel_nights
            total += hotel_total
            logger.debug(
                f"Additional hotel {i}: ₹{hotel_option.price_per_night:,}/night × "
                f"{hotel_nights} nights = ₹{hotel_total:,}"
            )
    
    logger.info(f"Total hotel cost: ₹{total:,}")
    return total


def calculate_activities_cost(
    activities_budget: Optional[int] = None,
    percentage_of_budget: Optional[float] = None,
    base_amount: Optional[int] = None
) -> int:
    """
    Calculate or allocate activities/miscellaneous costs.
    
    Priority order:
    1. Explicit activities_budget (if provided)
    2. Percentage of base_amount (if both provided)
    3. Default to 0
    
    Args:
        activities_budget: Explicit activities budget in INR
        percentage_of_budget: Percentage of base_amount to allocate (0.0-1.0)
        base_amount: Base amount for percentage calculation
    
    Returns:
        int: Activities cost in INR
    
    Raises:
        ValueError: If percentage_of_budget is out of valid range
    
    Example:
        >>> calculate_activities_cost(activities_budget=5000)
        5000
        >>> calculate_activities_cost(percentage_of_budget=0.15, base_amount=20000)
        3000
    """
    # Priority 1: Explicit budget
    if activities_budget is not None:
        if activities_budget < 0:
            raise ValueError(f"Activities budget cannot be negative, got {activities_budget}")
        logger.debug(f"Using explicit activities budget: ₹{activities_budget:,}")
        return activities_budget
    
    # Priority 2: Percentage of base
    if percentage_of_budget is not None and base_amount is not None:
        if not (0.0 <= percentage_of_budget <= 1.0):
            raise ValueError(
                f"Percentage must be between 0.0 and 1.0, got {percentage_of_budget}"
            )
        
        activities_cost = int(base_amount * percentage_of_budget)
        logger.debug(
            f"Calculated activities budget: {percentage_of_budget*100:.1f}% of "
            f"₹{base_amount:,} = ₹{activities_cost:,}"
        )
        return activities_cost
    
    # Default: No activities budget
    logger.debug("No activities budget specified, defaulting to ₹0")
    return 0


def generate_recommendations(
    total_cost: int,
    user_budget: Optional[int],
    flights_cost: int,
    hotel_cost: int,
    activities_cost: int
) -> List[str]:
    """
    Generate budget optimization recommendations based on cost breakdown.
    
    Args:
        total_cost: Total trip cost
        user_budget: User's budget (None if not specified)
        flights_cost: Total flight costs
        hotel_cost: Total hotel costs
        activities_cost: Total activities costs
    
    Returns:
        List[str]: List of actionable recommendations
    """
    recommendations = []
    
    if user_budget is None:
        return recommendations
    
    if total_cost <= user_budget:
        # Within budget - suggest optimizations
        remaining = user_budget - total_cost
        if remaining > 0:
            recommendations.append(
                f"You have ₹{remaining:,} remaining in your budget for additional activities or upgrades"
            )
        return recommendations
    
    # Over budget - suggest cost reductions
    overage = total_cost - user_budget
    recommendations.append(f"Budget exceeded by ₹{overage:,}. Consider these options:")
    
    # Analyze cost components
    if total_cost > 0:
        flights_pct = (flights_cost / total_cost) * 100
        hotel_pct = (hotel_cost / total_cost) * 100
        activities_pct = (activities_cost / total_cost) * 100
        
        # Recommend reducing highest cost component
        if flights_pct > 50:
            recommendations.append(
                f"Flights are {flights_pct:.1f}% of total cost. "
                "Consider alternative airports or connecting flights"
            )
        
        if hotel_pct > 40:
            recommendations.append(
                f"Hotels are {hotel_pct:.1f}% of total cost. "
                "Consider lower-star options or shorter stays"
            )
        
        if activities_pct > 20:
            recommendations.append(
                f"Activities are {activities_pct:.1f}% of total cost. "
                "Consider reducing activity budget by ₹{activities_cost - int(activities_cost*0.5):,}"
            )
    
    return recommendations


def generate_warnings(
    total_cost: int,
    user_budget: Optional[int],
    flights_cost: int,
    hotel_cost: int,
    nights: int
) -> List[str]:
    """
    Generate budget warnings based on common issues.
    
    Args:
        total_cost: Total trip cost
        user_budget: User's budget
        flights_cost: Flight costs
        hotel_cost: Hotel costs
        nights: Number of nights
    
    Returns:
        List[str]: List of warning messages
    """
    warnings = []
    
    # Warning: No budget specified
    if user_budget is None:
        warnings.append("No budget specified - unable to validate costs")
    
    # Warning: Over budget
    elif total_cost > user_budget:
        overage_pct = ((total_cost - user_budget) / user_budget) * 100
        warnings.append(
            f"Total cost exceeds budget by ₹{total_cost - user_budget:,} ({overage_pct:.1f}%)"
        )
    
    # Warning: Very close to budget (>95%)
    elif user_budget > 0 and (total_cost / user_budget) > 0.95:
        warnings.append(
            "Budget utilization is very high (>95%). "
            "Consider keeping a buffer for unexpected expenses"
        )
    
    # Warning: No flights selected
    if flights_cost == 0:
        warnings.append("No flights selected - flight costs not included in budget")
    
    # Warning: No hotels selected
    if hotel_cost == 0 and nights > 0:
        warnings.append(
            f"No hotels selected for {nights} nights - accommodation costs not included"
        )
    
    return warnings


def calculate_budget(
    outbound_flight: Optional[FlightOption] = None,
    return_flight: Optional[FlightOption] = None,
    hotel: Optional[HotelOption] = None,
    nights: int = 1,
    user_budget: Optional[int] = None,
    activities_budget: Optional[int] = None,
    additional_flights: Optional[List[FlightOption]] = None,
    additional_hotels: Optional[List[tuple[HotelOption, int]]] = None,
    currency: str = DEFAULT_CURRENCY
) -> BudgetCalculationResult:
    """
    Calculate and validate trip budget based on selected options.
    
    This is the main entry point for budget calculations. It computes costs
    for all components (flights, hotels, activities) and validates against
    the user's budget.
    
    Args:
        outbound_flight: Selected outbound flight (optional)
        return_flight: Selected return flight (optional)
        hotel: Selected hotel (optional)
        nights: Number of nights stay (default: 1)
        user_budget: User's total budget in INR (optional)
        activities_budget: Budget for activities/misc expenses (optional)
        additional_flights: List of additional flights for multi-city trips
        additional_hotels: List of (hotel, nights) for multi-city trips
        currency: Currency code (default: INR from config)
    
    Returns:
        BudgetCalculationResult: Detailed budget breakdown with validation
    
    Raises:
        ValueError: If nights is negative or other validation errors
    
    Example:
        >>> result = calculate_budget(
        ...     outbound_flight=flight1,
        ...     return_flight=flight2,
        ...     hotel=hotel1,
        ...     nights=3,
        ...     user_budget=50000,
        ...     activities_budget=5000
        ... )
        >>> print(f"Total: ₹{result.total_cost:,}")
        >>> print(f"Within budget: {result.is_within_budget}")
    """
    logger.info("=" * 60)
    logger.info("BUDGET CALCULATION STARTED")
    logger.info("=" * 60)
    
    # Validate inputs
    if nights < 0:
        raise ValueError(f"Nights cannot be negative, got {nights}")
    
    if user_budget is not None and user_budget < 0:
        raise ValueError(f"User budget cannot be negative, got {user_budget}")
    
    # Calculate component costs
    flights_cost = calculate_flight_cost(
        outbound_flight=outbound_flight,
        return_flight=return_flight,
        additional_flights=additional_flights
    )
    
    hotel_cost = calculate_hotel_cost(
        hotel=hotel,
        nights=nights,
        additional_hotels=additional_hotels
    )
    
    activities_cost = calculate_activities_cost(
        activities_budget=activities_budget
    )
    
    # Calculate total
    total_cost = flights_cost + hotel_cost + activities_cost
    logger.info(f"Total trip cost: ₹{total_cost:,}")
    
    # Create BudgetSummary schema object
    budget_summary = BudgetSummary(
        flights_cost=flights_cost,
        hotels_cost=hotel_cost,
        activities_cost=activities_cost,
        total_cost=total_cost
    )
    
    # Validate against budget
    if user_budget is not None:
        is_within_budget = total_cost <= user_budget
        budget_remaining = user_budget - total_cost
        budget_utilization_percent = (total_cost / user_budget * 100) if user_budget > 0 else 0.0
        
        logger.info(f"User budget: ₹{user_budget:,}")
        logger.info(f"Budget remaining: ₹{budget_remaining:,}")
        logger.info(f"Budget utilization: {budget_utilization_percent:.1f}%")
        logger.info(f"Within budget: {is_within_budget}")
    else:
        is_within_budget = True  # No budget means no constraint
        budget_remaining = 0
        budget_utilization_percent = 0.0
        logger.info("No budget specified - skipping validation")
    
    # Generate warnings and recommendations
    warnings = generate_warnings(
        total_cost=total_cost,
        user_budget=user_budget,
        flights_cost=flights_cost,
        hotel_cost=hotel_cost,
        nights=nights
    )
    
    recommendations = generate_recommendations(
        total_cost=total_cost,
        user_budget=user_budget,
        flights_cost=flights_cost,
        hotel_cost=hotel_cost,
        activities_cost=activities_cost
    )
    
    # Log warnings
    for warning in warnings:
        logger.warning(warning)
    
    logger.info("=" * 60)
    logger.info("BUDGET CALCULATION COMPLETED")
    logger.info("=" * 60)
    
    return BudgetCalculationResult(
        budget_summary=budget_summary,
        total_cost=total_cost,
        user_budget=user_budget,
        is_within_budget=is_within_budget,
        budget_remaining=budget_remaining,
        budget_utilization_percent=budget_utilization_percent,
        warnings=warnings,
        recommendations=recommendations
    )
