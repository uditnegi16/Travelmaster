"""
Budget Enrichment Module

Provides comprehensive budget analysis and enrichment capabilities:
- Full cost breakdown with estimates for transport, food, buffer
- Intelligence metrics (cost per day, per person, category distribution)
- Trip cost classification (Budget/Moderate/Premium/Luxury)
- Problem detection (over budget, poor distribution, etc.)
- Actionable recommendations for cost optimization
"""

import logging
from typing import Optional

from backend.app.shared.schemas import (
    FlightOption,
    HotelOption,
    PlaceOption,
    BudgetEnrichment,
    CostBreakdown,
    IntelligenceMetrics,
    TripClassification,
    BudgetIssue,
    BudgetRecommendation,
    BudgetHealthScore,
    BudgetVerdict,
    BudgetSimulation,
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Cost estimation factors
FOOD_COST_PER_DAY_PER_PERSON = 800  # INR - conservative estimate
LOCAL_TRANSPORT_PER_DAY = 500  # INR - metro/cab/auto
BUFFER_PERCENTAGE = 0.10  # 10% buffer on total known costs

# Classification thresholds (per person per day)
BUDGET_THRESHOLD = 3000  # Below this = Budget
MODERATE_THRESHOLD = 6000  # Below this = Moderate
PREMIUM_THRESHOLD = 12000  # Below this = Premium
# Above PREMIUM_THRESHOLD = Luxury

# Issue detection thresholds
OVER_BUDGET_THRESHOLD = 1.05  # 5% over budget is a warning
CRITICAL_OVER_BUDGET = 1.20  # 20% over budget is critical
FLIGHT_HEAVY_THRESHOLD = 0.40  # Flights > 40% of total
HOTEL_HEAVY_THRESHOLD = 0.50  # Hotel > 50% of total
POOR_VALUE_ACTIVITIES_THRESHOLD = 0.05  # Activities < 5% is poor value


# ============================================================================
# CORE ENRICHMENT FUNCTION
# ============================================================================

def enrich_budget(
    flights_cost: int,
    hotel_cost: int,
    activities_cost: int,
    total_cost: int,
    num_days: int,
    num_travelers: int = 1,
    user_budget: Optional[int] = None,
    flight: Optional[FlightOption] = None,
    hotel: Optional[HotelOption] = None,
    places: Optional[list[PlaceOption]] = None,
) -> BudgetEnrichment:
    """
    Enrich budget with intelligence, classification, and recommendations.
    
    Args:
        flights_cost: Total flight cost
        hotel_cost: Total hotel cost
        activities_cost: Total activities cost
        total_cost: Total known cost
        num_days: Number of days in trip
        num_travelers: Number of travelers
        user_budget: User's stated budget (optional)
        flight: Flight option (for context)
        hotel: Hotel option (for context)
        places: Places to visit (for context)
    
    Returns:
        BudgetEnrichment with full analysis
    """
    logger.info(
        f"Enriching budget: flights={flights_cost}, hotel={hotel_cost}, "
        f"activities={activities_cost}, days={num_days}, travelers={num_travelers}"
    )
    
    # 1️⃣ Build Full Cost Breakdown
    cost_breakdown = _build_cost_breakdown(
        flights_cost=flights_cost,
        hotel_cost=hotel_cost,
        activities_cost=activities_cost,
        num_days=num_days,
        num_travelers=num_travelers,
    )
    
    # Compute total with estimates
    total_estimated_cost = (
        cost_breakdown.flights
        + cost_breakdown.hotel
        + cost_breakdown.activities
        + cost_breakdown.local_transport
        + cost_breakdown.food
        + cost_breakdown.buffer
    )
    
    # 2️⃣ Compute Intelligence Metrics
    intelligence_metrics = _compute_intelligence_metrics(
        cost_breakdown=cost_breakdown,
        total_cost=total_estimated_cost,
        num_days=num_days,
        num_travelers=num_travelers,
    )
    
    # 3️⃣ Classify Trip Cost
    classification = _classify_trip(
        cost_per_person_per_day=intelligence_metrics.cost_per_person / num_days
    )
    
    # 4️⃣ Detect Problems
    issues = _detect_issues(
        cost_breakdown=cost_breakdown,
        total_estimated_cost=total_estimated_cost,
        intelligence_metrics=intelligence_metrics,
        user_budget=user_budget,
        num_travelers=num_travelers,
    )
    
    # 5️⃣ Generate Recommendations
    recommendations = _generate_recommendations(
        cost_breakdown=cost_breakdown,
        total_estimated_cost=total_estimated_cost,
        intelligence_metrics=intelligence_metrics,
        issues=issues,
        user_budget=user_budget,
        hotel=hotel,
        flight=flight,
        num_days=num_days,
    )
    
    # 6️⃣ Calculate Budget Health Score
    health_score = _calculate_health_score(
        total_estimated_cost=total_estimated_cost,
        user_budget=user_budget,
        intelligence_metrics=intelligence_metrics,
        issues=issues,
    )
    
    # 7️⃣ Generate Verdict
    verdict = _generate_verdict(
        total_estimated_cost=total_estimated_cost,
        user_budget=user_budget,
        health_score=health_score,
        issues=issues,
    )
    
    # 8️⃣ Simulate Recommendations
    simulation = _simulate_recommendations(
        recommendations=recommendations,
        total_estimated_cost=total_estimated_cost,
        user_budget=user_budget,
    )
    
    logger.info(
        f"Budget enrichment complete: classification={classification.classification}, "
        f"health_score={health_score.score:.1f}, issues={len(issues)}, "
        f"recommendations={len(recommendations)}"
    )
    
    return BudgetEnrichment(
        cost_breakdown=cost_breakdown,
        intelligence_metrics=intelligence_metrics,
        classification=classification,
        health_score=health_score,
        verdict=verdict,
        issues=issues,
        recommendations=recommendations,
        simulation=simulation,
    )


# ============================================================================
# 1️⃣ COST BREAKDOWN BUILDER
# ============================================================================

def _build_cost_breakdown(
    flights_cost: int,
    hotel_cost: int,
    activities_cost: int,
    num_days: int,
    num_travelers: int,
) -> CostBreakdown:
    """Build full cost breakdown with estimates."""
    
    # Estimate local transport
    local_transport = LOCAL_TRANSPORT_PER_DAY * num_days
    
    # Estimate food costs
    food = FOOD_COST_PER_DAY_PER_PERSON * num_days * num_travelers
    
    # Calculate buffer (10% of known costs)
    known_costs = flights_cost + hotel_cost + activities_cost + local_transport + food
    buffer = int(known_costs * BUFFER_PERCENTAGE)
    
    return CostBreakdown(
        flights=flights_cost,
        hotel=hotel_cost,
        activities=activities_cost,
        local_transport=local_transport,
        food=food,
        buffer=buffer,
    )


# ============================================================================
# 2️⃣ INTELLIGENCE METRICS COMPUTER
# ============================================================================

def _compute_intelligence_metrics(
    cost_breakdown: CostBreakdown,
    total_cost: int,
    num_days: int,
    num_travelers: int,
) -> IntelligenceMetrics:
    """Compute intelligence metrics from cost breakdown."""
    
    # Cost per day
    cost_per_day = total_cost / num_days if num_days > 0 else 0
    
    # Cost per person (total divided by travelers)
    cost_per_person = total_cost / num_travelers if num_travelers > 0 else total_cost
    
    # Category percentages
    category_percentages = {}
    if total_cost > 0:
        category_percentages = {
            "flights": round((cost_breakdown.flights / total_cost) * 100, 1),
            "hotel": round((cost_breakdown.hotel / total_cost) * 100, 1),
            "activities": round((cost_breakdown.activities / total_cost) * 100, 1),
            "local_transport": round((cost_breakdown.local_transport / total_cost) * 100, 1),
            "food": round((cost_breakdown.food / total_cost) * 100, 1),
            "buffer": round((cost_breakdown.buffer / total_cost) * 100, 1),
        }
    
    # Find dominant cost driver
    dominant_cost_driver = "unknown"
    dominant_cost_percentage = 0.0
    
    if category_percentages:
        dominant_cost_driver = max(category_percentages, key=category_percentages.get)
        dominant_cost_percentage = category_percentages[dominant_cost_driver]
    
    return IntelligenceMetrics(
        cost_per_day=round(cost_per_day, 2),
        cost_per_person=round(cost_per_person, 2),
        category_percentages=category_percentages,
        dominant_cost_driver=dominant_cost_driver,
        dominant_cost_percentage=dominant_cost_percentage,
    )


# ============================================================================
# 3️⃣ TRIP CLASSIFIER
# ============================================================================

def _classify_trip(cost_per_person_per_day: float) -> TripClassification:
    """Classify trip based on cost per person per day."""
    
    if cost_per_person_per_day < BUDGET_THRESHOLD:
        classification = "Budget"
        threshold_info = f"< ₹{BUDGET_THRESHOLD}/person/day"
    elif cost_per_person_per_day < MODERATE_THRESHOLD:
        classification = "Moderate"
        threshold_info = f"₹{BUDGET_THRESHOLD}-{MODERATE_THRESHOLD}/person/day"
    elif cost_per_person_per_day < PREMIUM_THRESHOLD:
        classification = "Premium"
        threshold_info = f"₹{MODERATE_THRESHOLD}-{PREMIUM_THRESHOLD}/person/day"
    else:
        classification = "Luxury"
        threshold_info = f"> ₹{PREMIUM_THRESHOLD}/person/day"
    
    return TripClassification(
        classification=classification,
        threshold_info=threshold_info,
    )


# ============================================================================
# 4️⃣ ISSUE DETECTOR
# ============================================================================

def _detect_issues(
    cost_breakdown: CostBreakdown,
    total_estimated_cost: int,
    intelligence_metrics: IntelligenceMetrics,
    user_budget: Optional[int],
    num_travelers: int,
) -> list[BudgetIssue]:
    """Detect budget issues and problems."""
    
    issues = []
    
    # Check if over budget
    if user_budget and total_estimated_cost > user_budget:
        overage = total_estimated_cost - user_budget
        overage_pct = (total_estimated_cost / user_budget - 1) * 100
        
        if total_estimated_cost >= user_budget * CRITICAL_OVER_BUDGET:
            issues.append(
                BudgetIssue(
                    severity="critical",
                    category="over_budget",
                    description=f"Current plan is {overage_pct:.0f}% over budget (₹{overage:,} excess)",
                    impact_amount=overage,
                )
            )
        elif total_estimated_cost >= user_budget * OVER_BUDGET_THRESHOLD:
            issues.append(
                BudgetIssue(
                    severity="warning",
                    category="over_budget",
                    description=f"Current plan is {overage_pct:.0f}% over budget (₹{overage:,} excess)",
                    impact_amount=overage,
                )
            )
    
    # Check if flight heavy
    flight_pct = intelligence_metrics.category_percentages.get("flights", 0) / 100
    if flight_pct > FLIGHT_HEAVY_THRESHOLD:
        issues.append(
            BudgetIssue(
                severity="warning",
                category="flight_heavy",
                description=f"Flights consume {flight_pct*100:.0f}% of budget - consider alternative transport",
                impact_amount=cost_breakdown.flights,
            )
        )
    
    # Check if hotel too expensive
    hotel_pct = intelligence_metrics.category_percentages.get("hotel", 0) / 100
    if hotel_pct > HOTEL_HEAVY_THRESHOLD:
        issues.append(
            BudgetIssue(
                severity="warning",
                category="hotel_expensive",
                description=f"Hotel costs {hotel_pct*100:.0f}% of budget - consider lower star rating",
                impact_amount=cost_breakdown.hotel,
            )
        )
    
    # Check for poor value distribution (activities too low)
    activities_pct = intelligence_metrics.category_percentages.get("activities", 0) / 100
    if activities_pct < POOR_VALUE_ACTIVITIES_THRESHOLD and cost_breakdown.activities < 1000:
        issues.append(
            BudgetIssue(
                severity="warning",
                category="poor_value_distribution",
                description=f"Only {activities_pct*100:.1f}% allocated to activities - consider adding more experiences",
                impact_amount=cost_breakdown.activities,
            )
        )
    
    return issues


# ============================================================================
# 5️⃣ RECOMMENDATION GENERATOR
# ============================================================================

def _generate_recommendations(
    cost_breakdown: CostBreakdown,
    total_estimated_cost: int,
    intelligence_metrics: IntelligenceMetrics,
    issues: list[BudgetIssue],
    user_budget: Optional[int],
    hotel: Optional[HotelOption],
    flight: Optional[FlightOption],
    num_days: int,
) -> list[BudgetRecommendation]:
    """Generate actionable budget recommendations."""
    
    recommendations = []
    
    # If over budget, provide specific recommendations
    if user_budget and total_estimated_cost > user_budget:
        overage = total_estimated_cost - user_budget
        
        # Recommend hotel downgrade if hotel is expensive
        if hotel and hotel.stars > 3:
            potential_savings = int(cost_breakdown.hotel * 0.30)  # 30% savings estimate
            if potential_savings > overage * 0.5:  # Can save at least half the overage
                recommendations.append(
                    BudgetRecommendation(
                        action=f"Switch to {hotel.stars - 1}★ hotel to save approximately ₹{potential_savings:,}",
                        savings=potential_savings,
                        category="hotel",
                        priority="high",
                    )
                )
        
        # Recommend reducing nights if trip is long
        if num_days > 3:
            nights_saved = 1
            if hotel:
                savings_per_night = hotel.price_per_night
            else:
                savings_per_night = int(cost_breakdown.hotel / num_days) if num_days > 0 else 0
            
            savings = savings_per_night + FOOD_COST_PER_DAY_PER_PERSON + LOCAL_TRANSPORT_PER_DAY
            
            recommendations.append(
                BudgetRecommendation(
                    action=f"Reduce trip by {nights_saved} night to save ₹{savings:,}",
                    savings=savings,
                    category="duration",
                    priority="medium",
                )
            )
        
        # Recommend train over flight if flight is expensive
        if flight and cost_breakdown.flights > overage * 0.8:
            potential_savings = int(cost_breakdown.flights * 0.60)  # Assume train is 60% cheaper
            recommendations.append(
                BudgetRecommendation(
                    action=f"Take train instead of flight to save approximately ₹{potential_savings:,}",
                    savings=potential_savings,
                    category="flight",
                    priority="high",
                )
            )
    
    # If hotel is dominant cost driver
    if intelligence_metrics.dominant_cost_driver == "hotel" and hotel:
        if hotel.stars >= 4:
            savings = int(cost_breakdown.hotel * 0.25)
            recommendations.append(
                BudgetRecommendation(
                    action=f"Hotel consumes {intelligence_metrics.dominant_cost_percentage:.0f}% of budget - consider 3★ option",
                    savings=savings,
                    category="hotel",
                    priority="medium",
                )
            )
    
    # If flight is dominant cost driver
    if intelligence_metrics.dominant_cost_driver == "flights":
        savings = int(cost_breakdown.flights * 0.40)
        recommendations.append(
            BudgetRecommendation(
                action=f"Flights consume {intelligence_metrics.dominant_cost_percentage:.0f}% of budget - look for cheaper airlines or dates",
                savings=savings,
                category="flight",
                priority="medium",
            )
        )
    
    # General optimization if under budget
    if user_budget and total_estimated_cost < user_budget * 0.85:  # More than 15% under
        remaining = user_budget - total_estimated_cost
        recommendations.append(
            BudgetRecommendation(
                action=f"You have ₹{remaining:,} remaining - consider upgrading hotel or adding activities",
                savings=-remaining,  # Negative savings = additional spending opportunity
                category="optimization",
                priority="low",
            )
        )
    
    # Sort by priority (high > medium > low) and savings (descending)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda r: (priority_order[r.priority], -r.savings))
    
    return recommendations


# ============================================================================
# 6️⃣ BUDGET HEALTH SCORE CALCULATOR
# ============================================================================

def _calculate_health_score(
    total_estimated_cost: int,
    user_budget: Optional[int],
    intelligence_metrics: IntelligenceMetrics,
    issues: list[BudgetIssue],
) -> BudgetHealthScore:
    """
    Calculate overall budget health score (0-10 scale).
    
    Factors:
    - Overrun %: -4 points per 10% over budget
    - Buffer left: +points based on remaining budget
    - Hotel dominance: -2 points if > 50%
    - Critical issues: -2 points each
    - Warning issues: -1 point each
    """
    score = 10.0  # Start with perfect score
    factors = []
    
    # Factor 1: Budget overrun
    if user_budget:
        overrun_pct = ((total_estimated_cost / user_budget) - 1) * 100
        if overrun_pct > 0:
            # Lose 4 points per 10% over budget
            penalty = min((overrun_pct / 10) * 4, 8)  # Cap at 8 points loss
            score -= penalty
            factors.append(f"Over budget by {overrun_pct:.1f}%")
        else:
            # Gain points for being under budget
            under_pct = abs(overrun_pct)
            bonus = min(under_pct / 10, 2)  # Up to 2 bonus points
            score = min(score + bonus, 10)
            factors.append(f"Under budget by {under_pct:.1f}%")
    
    # Factor 2: Hotel dominance
    hotel_pct = intelligence_metrics.category_percentages.get("hotel", 0)
    if hotel_pct > 50:
        score -= 2
        factors.append(f"Hotel dominates at {hotel_pct:.0f}%")
    
    # Factor 3: Issues severity
    for issue in issues:
        if issue.severity == "critical":
            score -= 2
            factors.append(f"Critical: {issue.category}")
        elif issue.severity == "warning":
            score -= 1
            factors.append(f"Warning: {issue.category}")
    
    # Ensure score is within bounds
    score = max(0, min(10, score))
    
    # Determine severity
    if score >= 8:
        severity = "Excellent"
    elif score >= 6:
        severity = "Good"
    elif score >= 4:
        severity = "Fair"
    elif score >= 2:
        severity = "Poor"
    else:
        severity = "Critical"
    
    return BudgetHealthScore(
        score=round(score, 1),
        severity=severity,
        factors=factors,
    )


# ============================================================================
# 7️⃣ VERDICT GENERATOR
# ============================================================================

def _generate_verdict(
    total_estimated_cost: int,
    user_budget: Optional[int],
    health_score: BudgetHealthScore,
    issues: list[BudgetIssue],
) -> BudgetVerdict:
    """Generate overall budget verdict."""
    
    # Check if over budget
    is_over_budget = False
    if user_budget and total_estimated_cost > user_budget:
        is_over_budget = True
    
    # Check for critical issues
    has_critical_issues = any(issue.severity == "critical" for issue in issues)
    
    # Determine verdict
    if is_over_budget or has_critical_issues or health_score.score < 5:
        status = "needs_optimization"
        message = "Over Budget - Plan needs optimization before booking"
    else:
        status = "approved"
        message = "Within Budget - Well balanced plan"
    
    return BudgetVerdict(
        status=status,
        message=message,
    )


# ============================================================================
# 8️⃣ RECOMMENDATION SIMULATOR
# ============================================================================

def _simulate_recommendations(
    recommendations: list[BudgetRecommendation],
    total_estimated_cost: int,
    user_budget: Optional[int],
) -> Optional[BudgetSimulation]:
    """
    Simulate applying top recommendations.
    Only generates simulation if there are recommendations with savings > 0.
    """
    
    # Filter recommendations with actual savings (exclude negative ones)
    saveable_recs = [r for r in recommendations if r.savings > 0]
    
    if not saveable_recs:
        return None
    
    # Take top 2-3 high-priority recommendations
    top_recommendations = []
    total_savings = 0
    
    for rec in saveable_recs[:3]:  # Max 3 recommendations
        if rec.priority in ["high", "medium"]:
            top_recommendations.append(rec.action)
            total_savings += rec.savings
    
    if not top_recommendations:
        return None
    
    # Calculate new total
    new_total = total_estimated_cost - total_savings
    
    # Check if within budget
    within_budget = False
    if user_budget:
        within_budget = new_total <= user_budget
    
    # Generate verdict message
    if within_budget:
        verdict_message = "Within Budget"
    else:
        verdict_message = "Still Over Budget"
    
    return BudgetSimulation(
        applied_recommendations=top_recommendations,
        original_total=total_estimated_cost,
        new_total=new_total,
        total_savings=total_savings,
        within_budget=within_budget,
        verdict_message=verdict_message,
    )

