"""
Domain schemas for TravelGuru v5
Defines all data models used across the multi-agent AI system.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


# ============================================================================
# DOMAIN MODELS (Core Travel Objects)
# ============================================================================

from pydantic import BaseModel, Field, AliasChoices

class FlightOption(BaseModel):
    id: str = Field(..., description="Unique flight identifier", validation_alias=AliasChoices("id", "flight_id"))
    airline: str = Field(..., description="Airline carrier code")
    origin: str = Field(..., description="Origin airport IATA code")
    destination: str = Field(..., description="Destination airport IATA code")
    departure_time: str = Field(..., description="Departure time in ISO 8601 UTC format")
    arrival_time: str = Field(..., description="Arrival time in ISO 8601 UTC format")

    # keep duration string, but accept duration_minutes too
    duration: str = Field(default="", description="Flight duration (e.g., '8h 30m')")
    duration_minutes: int = Field(default=0, description="Flight duration in minutes")

    stops: int = Field(default=0, description="Number of stops")

    # accept int or float safely
    price: float = Field(..., description="Price in specified currency")
    currency: str = Field(default="INR", description="Currency code")

    booking_url: str = Field(default="", description="Booking URL")

    model_config = {"extra": "forbid", "frozen": True}


from pydantic import BaseModel, Field, AliasChoices
from typing import List, Optional

class HotelOption(BaseModel):
    """
    Represents a hotel option returned from search.
    Immutable value object.
    """

    # Accept both "id" and "hotel_id"
    id: str = Field(..., description="Unique hotel identifier",
                    validation_alias=AliasChoices("id", "hotel_id"))

    name: str = Field(..., description="Hotel name")

    # Optional because some APIs don't always provide it
    city: str = Field(default="", description="City where hotel is located")

    # Scoring fields (align with MLOps)
    rating: float = Field(default=0.0, description="Rating 0-5")
    star_category: int = Field(default=0, description="Star category (1-5)",
                               validation_alias=AliasChoices("star_category", "stars"))

    price_per_night: float = Field(..., description="Price per night in specified currency")
    currency: str = Field(default="INR", description="Currency code")

    # Must-show field for UI + DB merge
    booking_url: str = Field(default="", description="Booking URL")

    # Nice-to-have details (often present and useful in UI)
    amenities: List[str] = Field(default_factory=list, description="List of available amenities")
    check_in: Optional[str] = Field(None, description="Check-in date in YYYY-MM-DD format")
    check_out: Optional[str] = Field(None, description="Check-out date in YYYY-MM-DD format")

    model_config = {"extra": "forbid", "frozen": True}


class PlaceOption(BaseModel):
    """
    Represents a place/activity option returned from search.
    Immutable value object with extended metadata.
    """
    # Core identification
    id: str = Field(..., description="Unique place identifier")
    name: str = Field(..., description="Place or activity name")
    city: str = Field(..., description="City where place is located")
    category: str = Field(..., description="Category of the place (e.g., museum, park, restaurant)")
    rating: float = Field(..., description="User rating (0.0-5.0)")
    entry_fee: int = Field(default=0, description="Entry fee in INR (0 for free entry)")
    
    # Timing and operational info
    opening_hours: Optional[str] = Field(None, description="Operating hours (e.g., '9:00 AM - 6:00 PM')")
    best_time_to_visit: Optional[str] = Field(None, description="Recommended visit time (morning/afternoon/evening/sunset)")
    recommended_duration: Optional[str] = Field(None, description="How long to spend (e.g., '1-2 hours', '2-3 hours')")
    
    # Location and accessibility
    address: Optional[str] = Field(None, description="Full address of the place")
    coordinates: Optional[Dict[str, float]] = Field(None, description="Lat/lng coordinates")
    transport_modes: Optional[List[str]] = Field(None, description="How to reach: walk, metro, cab, bus")
    
    # Context and special info
    description: Optional[str] = Field(None, description="Brief description of the place")
    special_notes: Optional[str] = Field(None, description="Ticket/queue/dress code/restrictions")
    weather_sensitivity: Optional[str] = Field(None, description="Indoor/outdoor/weather-dependent")
    crowd_level: Optional[str] = Field(None, description="Typical crowd: peaceful, moderate, crowded, very-crowded")
    
    model_config = {"extra": "forbid", "frozen": True}


class WeatherInfo(BaseModel):
    """
    Represents weather information for a city on a specific date.
    """
    city: str = Field(..., description="City name")
    date: str = Field(..., description="Date in ISO 8601 format")
    condition: str = Field(..., description="Weather condition (e.g., sunny, rainy, cloudy)")
    temperature_c: float = Field(..., description="Temperature in Celsius")
    
    model_config = {"extra": "forbid"}


class WeatherSummary(BaseModel):
    """
    Represents daily weather summary from OpenWeather forecast.
    Normalized from 3-hour interval data into daily aggregates.
    """
    city: str = Field(..., description="City name")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    temp_min_c: float = Field(..., description="Minimum temperature in Celsius")
    temp_max_c: float = Field(..., description="Maximum temperature in Celsius")
    temp_avg_c: float = Field(..., description="Average temperature in Celsius")
    condition: str = Field(..., description="Most common weather condition for the day")
    rain_chance: float = Field(..., description="Probability of precipitation (0.0 to 1.0)")
    
    model_config = {"extra": "forbid"}


# ============================================================================
# USER INPUT MODELS
# ============================================================================

class TripRequest(BaseModel):
    """
    Represents the user's trip request.
    Contains all the input parameters for planning a trip.
    """
    from_city: str = Field(..., description="Departure city")
    to_city: str = Field(..., description="Destination city")
    start_date: str = Field(..., description="Trip start date in ISO 8601 format")
    end_date: str = Field(..., description="Trip end date in ISO 8601 format")
    budget: int = Field(..., description="Total budget in INR")
    travelers: int = Field(default=1, description="Number of travelers")
    preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional preferences (e.g., hotel amenities, activity types)"
    )
    
    model_config = {"extra": "forbid"}


# ============================================================================
# PLAN STRUCTURE MODELS
# ============================================================================

class DayPlan(BaseModel):
    """
    Represents the plan for a single day of the trip.
    """
    date: str = Field(..., description="Date in ISO 8601 format")
    activities: List[PlaceOption] = Field(
        default_factory=list,
        description="List of activities/places to visit on this day"
    )
    
    model_config = {"extra": "forbid"}


class TripPlan(BaseModel):
    """
    Represents the complete trip plan.
    Contains flight, hotel, daily activities, and weather information.
    """
    flight: Optional[FlightOption] = Field(default=None, description="Selected flight")
    hotel: Optional[HotelOption] = Field(default=None, description="Selected hotel")
    days: List[DayPlan] = Field(default_factory=list, description="Day-by-day itinerary")
    weather: Optional[List[WeatherInfo]] = Field(
        default=None,
        description="Weather forecast for the trip dates"
    )
    notes: Optional[str] = Field(default=None, description="Additional notes or recommendations")
    
    model_config = {"extra": "forbid"}


# ============================================================================
# BUDGET MODELS
# ============================================================================

class CostBreakdown(BaseModel):
    """
    Detailed cost breakdown with additional estimates.
    """
    flights: int = Field(..., description="Total flight cost")
    hotel: int = Field(..., description="Total hotel cost")
    activities: int = Field(..., description="Entry fees for places/activities")
    local_transport: int = Field(default=0, description="Estimated local transport cost")
    food: int = Field(default=0, description="Estimated food cost")
    buffer: int = Field(default=0, description="Buffer/miscellaneous expenses")
    
    model_config = {"extra": "forbid"}


class IntelligenceMetrics(BaseModel):
    """
    Intelligence metrics derived from budget analysis.
    """
    cost_per_day: float = Field(..., description="Average cost per day")
    cost_per_person: float = Field(..., description="Average cost per person")
    category_percentages: Dict[str, float] = Field(..., description="Percentage spent on each category")
    dominant_cost_driver: str = Field(..., description="Category with highest cost (e.g., 'hotel')")
    dominant_cost_percentage: float = Field(..., description="Percentage of dominant cost")
    
    model_config = {"extra": "forbid"}


class TripClassification(BaseModel):
    """
    Classification of trip based on cost.
    """
    classification: Literal["Budget", "Moderate", "Premium", "Luxury"] = Field(
        ..., 
        description="Trip cost classification"
    )
    threshold_info: Optional[str] = Field(
        None, 
        description="Information about classification thresholds"
    )
    
    model_config = {"extra": "forbid"}


class BudgetIssue(BaseModel):
    """
    Represents a detected budget issue or problem.
    """
    severity: Literal["warning", "critical"] = Field(..., description="Issue severity level")
    category: str = Field(..., description="Issue category (e.g., 'over_budget', 'flight_heavy')")
    description: str = Field(..., description="Human-readable description of the issue")
    impact_amount: Optional[int] = Field(None, description="Financial impact in INR")
    
    model_config = {"extra": "forbid"}


class BudgetRecommendation(BaseModel):
    """
    Represents a budget optimization recommendation.
    """
    action: str = Field(..., description="Recommended action")
    savings: int = Field(..., description="Potential savings in INR")
    category: str = Field(..., description="Category affected (e.g., 'hotel', 'flight')")
    priority: Literal["high", "medium", "low"] = Field(..., description="Recommendation priority")
    
    model_config = {"extra": "forbid"}


class BudgetHealthScore(BaseModel):
    """
    Overall health score of the budget (0-10 scale).
    """
    score: float = Field(..., description="Health score from 0 to 10")
    severity: Literal["Critical", "Poor", "Fair", "Good", "Excellent"] = Field(
        ..., 
        description="Severity level based on score"
    )
    factors: List[str] = Field(
        default_factory=list, 
        description="Factors affecting the score"
    )
    
    model_config = {"extra": "forbid"}


class BudgetVerdict(BaseModel):
    """
    Overall verdict on the budget plan.
    """
    status: Literal["approved", "needs_optimization"] = Field(
        ..., 
        description="Approval status"
    )
    message: str = Field(..., description="Human-readable verdict message")
    
    model_config = {"extra": "forbid"}


class BudgetSimulation(BaseModel):
    """
    Simulation of budget if top recommendations are applied.
    """
    applied_recommendations: List[str] = Field(
        ..., 
        description="List of recommendations being simulated"
    )
    original_total: int = Field(..., description="Original estimated total")
    new_total: int = Field(..., description="New estimated total after applying recommendations")
    total_savings: int = Field(..., description="Total savings amount")
    within_budget: bool = Field(..., description="Whether new total is within user budget")
    verdict_message: str = Field(..., description="Verdict message for simulation")
    
    model_config = {"extra": "forbid"}


class BudgetEnrichment(BaseModel):
    """
    Enriched budget information with intelligence and recommendations.
    """
    cost_breakdown: CostBreakdown = Field(..., description="Detailed cost breakdown")
    intelligence_metrics: IntelligenceMetrics = Field(..., description="Computed intelligence metrics")
    classification: TripClassification = Field(..., description="Trip cost classification")
    health_score: BudgetHealthScore = Field(..., description="Budget health score")
    verdict: BudgetVerdict = Field(..., description="Overall budget verdict")
    issues: List[BudgetIssue] = Field(default_factory=list, description="Detected budget issues")
    recommendations: List[BudgetRecommendation] = Field(
        default_factory=list, 
        description="Budget optimization recommendations"
    )
    simulation: Optional[BudgetSimulation] = Field(
        None, 
        description="Simulation of applying top recommendations"
    )
    
    model_config = {"extra": "forbid"}


class BudgetSummary(BaseModel):
    """
    Represents the budget breakdown for a trip.
    """
    flights_cost: int = Field(..., description="Total cost of flights in INR")
    hotel_cost: int = Field(..., description="Total cost of hotel in INR")
    activities_cost: int = Field(..., description="Total cost of activities in INR")
    total_cost: int = Field(..., description="Total cost of the entire trip in INR")
    currency: str = Field(..., description="Currency code (e.g., INR)")
    enrichment: Optional[BudgetEnrichment] = Field(None, description="Enriched budget information")
    
    model_config = {"extra": "forbid"}


# ============================================================================
# AGENT / ORCHESTRATION MODELS
# ============================================================================

class ToolCallPlan(BaseModel):
    """
    Represents a single tool call in the planner's execution plan.
    Used by the Planner LLM to specify which tool to call and with what arguments.
    """
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(..., description="Arguments to pass to the tool")
    
    model_config = {"extra": "forbid"}


class PlannerOutput(BaseModel):
    """
    Represents the complete output from the Planner Agent.
    Contains the execution plan and reasoning.
    """
    tool_calls: List[ToolCallPlan] = Field(..., description="List of tool calls to execute in order")
    reasoning: str = Field(..., description="Explanation of the planning decisions")
    
    model_config = {"extra": "forbid"}


class PlannerStep(BaseModel):
    """
    Represents a single step in the planner's execution plan.
    Used by the Planner LLM to specify which tool to call and with what arguments.
    """
    tool: Literal[
        "search_flights",
        "search_hotels",
        "search_places",
        "get_weather",
        "compute_budget"
    ] = Field(..., description="Name of the tool to execute")
    args: Dict[str, Any] = Field(..., description="Arguments to pass to the tool")
    
    model_config = {"extra": "forbid"}


class ToolResult(BaseModel):
    """
    Represents the result of a tool execution.
    """
    tool: str = Field(..., description="Name of the tool that was executed")
    data: Any = Field(..., description="Result data returned by the tool")
    
    model_config = {"extra": "forbid"}


class ExecutionState(BaseModel):
    """
    Represents the complete state of the agent execution.
    Used by LangGraph to track progress through the multi-agent workflow.
    """
    user_query: str = Field(..., description="Original user query")
    trip_request: Optional[TripRequest] = Field(
        default=None,
        description="Parsed trip request from user query"
    )
    plan_steps: List[PlannerStep] = Field(
        default_factory=list,
        description="List of planned tool execution steps"
    )
    tool_results: Dict[str, ToolResult] = Field(
        default_factory=dict,
        description="Results from executed tools, keyed by tool name"
    )
    trip_plan: Optional[TripPlan] = Field(
        default=None,
        description="Assembled trip plan from tool results"
    )
    budget_summary: Optional[BudgetSummary] = Field(
        default=None,
        description="Budget breakdown for the trip"
    )
    final_output: Optional[str] = Field(
        default=None,
        description="Final natural language response to the user"
    )
    
    model_config = {"extra": "forbid"}


# ============================================================================
# FINAL RESPONSE MODEL
# ============================================================================

class TripResponse(BaseModel):
    """
    Represents the final response sent to the user.
    Contains complete multi-agent analysis + trip plan + narrative.
    
    ARCHITECTURE: This response preserves ALL agent intelligence so the composer
    can explain reasoning, tradeoffs, and decision-making process.
    """
    # Core trip plan (schema-compatible format)
    trip_plan: TripPlan = Field(..., description="Complete trip itinerary")
    budget_summary: BudgetSummary = Field(..., description="Budget breakdown")
    total_cost: int = Field(..., description="Total trip cost in INR")
    currency: str = Field(..., description="Currency code (e.g., INR)")
    narrative: str = Field(..., description="Natural language summary of the trip plan")
    
    # Multi-agent enrichment analyses (preserved for composer)
    flight_analysis: Optional[Any] = Field(None, description="Flight market analysis & enrichment")
    hotel_analysis: Optional[Any] = Field(None, description="Hotel scoring & enrichment")
    places_analysis: Optional[Any] = Field(None, description="Places curation & enrichment")
    weather_analysis: Optional[Any] = Field(None, description="Weather impact analysis")
    budget_analysis: Optional[Any] = Field(None, description="Budget breakdown, health score, and recommendations")
    itinerary_enrichment: Optional[Any] = Field(None, description="Itinerary intelligence & scheduling")
    
    model_config = {"extra": "forbid"}
