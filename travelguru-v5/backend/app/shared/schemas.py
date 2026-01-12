"""
Domain schemas for TravelGuru v5
Defines all data models used across the multi-agent AI system.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


# ============================================================================
# DOMAIN MODELS (Core Travel Objects)
# ============================================================================

class FlightOption(BaseModel):
    """
    Represents a flight option returned from search.
    Immutable value object.
    """
    id: str = Field(..., description="Unique flight identifier")
    airline: str = Field(..., description="Airline carrier code")
    origin: str = Field(..., description="Origin airport IATA code")
    destination: str = Field(..., description="Destination airport IATA code")
    departure_time: str = Field(..., description="Departure time in ISO 8601 UTC format")
    arrival_time: str = Field(..., description="Arrival time in ISO 8601 UTC format")
    duration: str = Field(default="", description="Flight duration (e.g., '8h 30m')")
    stops: int = Field(default=0, description="Number of stops")
    price: int = Field(..., description="Price in specified currency")
    currency: str = Field(default="INR", description="Currency code")
    
    model_config = {"extra": "forbid", "frozen": True}


class HotelOption(BaseModel):
    """
    Represents a hotel option returned from search.
    Immutable value object.
    """
    id: str = Field(..., description="Unique hotel identifier")
    name: str = Field(..., description="Hotel name")
    city: str = Field(..., description="City where hotel is located")
    stars: int = Field(..., description="Star rating (1-5)")
    price_per_night: int = Field(..., description="Price per night in INR")
    amenities: List[str] = Field(default_factory=list, description="List of available amenities")
    
    model_config = {"extra": "forbid", "frozen": True}


class PlaceOption(BaseModel):
    """
    Represents a place/activity option returned from search.
    Immutable value object.
    """
    id: str = Field(..., description="Unique place identifier")
    name: str = Field(..., description="Place or activity name")
    city: str = Field(..., description="City where place is located")
    category: str = Field(..., description="Category of the place (e.g., museum, park, restaurant)")
    rating: float = Field(..., description="User rating (0.0-5.0)")
    entry_fee: int = Field(default=0, description="Entry fee in INR (0 for free entry)")
    
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

class BudgetSummary(BaseModel):
    """
    Represents the budget breakdown for a trip.
    """
    flights_cost: int = Field(..., description="Total cost of flights in INR")
    hotel_cost: int = Field(..., description="Total cost of hotel in INR")
    activities_cost: int = Field(..., description="Total cost of activities in INR")
    total_cost: int = Field(..., description="Total cost of the entire trip in INR")
    currency: str = Field(..., description="Currency code (e.g., INR)")
    
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
    Contains the complete trip plan, budget, and a natural language narrative.
    """
    trip_plan: TripPlan = Field(..., description="Complete trip itinerary")
    budget_summary: BudgetSummary = Field(..., description="Budget breakdown")
    total_cost: int = Field(..., description="Total trip cost in INR")
    currency: str = Field(..., description="Currency code (e.g., INR)")
    narrative: str = Field(..., description="Natural language summary of the trip plan")
    
    model_config = {"extra": "forbid"}
