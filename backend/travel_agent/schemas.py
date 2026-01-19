"""
Normalized internal schemas for the Agentic AI Travel Planner.

These schemas define the standardized data structures used by the LLM orchestrator
and all tools. They are independent of external APIs or dataset formats.

Notes:
- All datetime fields (departure_time, arrival_time) are timezone-aware UTC datetimes.
- All price fields are in INR (Indian Rupees) as integers.
"""

from datetime import date as Date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class BudgetSummary(BaseModel):
    """
    Represents a detailed cost breakdown for trip planning.
    
    This schema provides transparency in cost calculation, showing
    how the total budget is distributed across different categories.
    """
    
    flights_cost: int = Field(..., ge=0, description="Total cost for flights in INR")
    hotels_cost: int = Field(..., ge=0, description="Total cost for hotel accommodation in INR")
    activities_cost: int = Field(default=0, ge=0, description="Estimated cost for activities and attractions in INR")
    total_cost: int = Field(..., ge=0, description="Total combined cost in INR")


class FlightOption(BaseModel):
    """
    Represents a flight option with normalized fields.
    
    This schema is used internally by the agent and tools to represent
    flight information in a consistent format regardless of the data source.
    
    Note: departure_time and arrival_time are timezone-aware UTC datetimes.
    """
    
    id: str = Field(..., description="Unique identifier for the flight")
    airline: str = Field(..., min_length=1, description="Name of the airline")
    origin: str = Field(..., min_length=1, description="Origin city or airport")
    destination: str = Field(..., min_length=1, description="Destination city or airport")
    departure_time: datetime = Field(..., description="Departure date and time (timezone-aware UTC)")
    arrival_time: datetime = Field(..., description="Arrival date and time (timezone-aware UTC)")
    price: int = Field(..., ge=0, description="Flight price in INR")
    
    @field_validator("arrival_time")
    @classmethod
    def validate_arrival_after_departure(cls, v: datetime, info) -> datetime:
        """Ensure arrival time is after departure time."""
        if "departure_time" in info.data and v <= info.data["departure_time"]:
            raise ValueError("Arrival time must be after departure time")
        return v


class HotelOption(BaseModel):
    """
    Represents a hotel option with normalized fields.
    
    This schema is used internally by the agent and tools to represent
    hotel information in a consistent format regardless of the data source.
    """
    
    id: str = Field(..., description="Unique identifier for the hotel")
    name: str = Field(..., min_length=1, description="Name of the hotel")
    city: str = Field(..., min_length=1, description="City where the hotel is located")
    stars: int = Field(..., ge=1, le=5, description="Hotel star rating (1-5)")
    price_per_night: int = Field(..., ge=0, description="Price per night in INR")
    amenities: List[str] = Field(default_factory=list, description="List of hotel amenities")


class PlaceOption(BaseModel):
    """
    Represents a place of interest with normalized fields.
    
    This schema is used internally by the agent and tools to represent
    tourist attractions and places in a consistent format regardless of the data source.
    """
    
    id: str = Field(..., description="Unique identifier for the place")
    name: str = Field(..., min_length=1, description="Name of the place")
    city: str = Field(..., min_length=1, description="City where the place is located")
    category: str = Field(..., min_length=1, description="Type or category of the place (e.g., museum, park)")
    rating: float = Field(..., ge=0.0, le=5.0, description="User rating on a scale of 0-5")
    lat: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude coordinate for maps or external APIs")
    lon: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude coordinate for maps or external APIs")


class TripRequest(BaseModel):
    """
    Represents a user's trip planning request.
    
    This schema captures all the necessary information from the user
    to plan a complete trip including flights, hotels, and itinerary.
    """
    
    origin_city: str = Field(..., min_length=1, description="City where the trip starts")
    destination_city: str = Field(..., min_length=1, description="City of the destination")
    start_date: Date = Field(..., description="Start date of the trip")
    end_date: Date = Field(..., description="End date of the trip")
    budget: int = Field(..., gt=0, description="Total budget in INR")
    travelers: int = Field(..., ge=1, description="Number of travelers")
    preferences: Optional[List[str]] = Field(None, description="User preferences for activities, hotels, etc.")
    
    @field_validator("end_date")
    @classmethod
    def validate_end_after_start(cls, v: Date, info) -> Date:
        """Ensure end date is after or equal to start date."""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("End date must be on or after start date")
        return v


class DayPlan(BaseModel):
    """
    Represents the itinerary plan for a single day.
    
    This schema organizes the places to visit and activities
    for a specific day during the trip.
    """
    
    day_number: int = Field(..., ge=1, description="Day number in the trip sequence (1-based)")
    date: Date = Field(..., description="Date of this day plan")
    places: List[PlaceOption] = Field(default_factory=list, description="List of places to visit on this day")
    notes: Optional[str] = Field(None, description="Additional notes or recommendations for the day")


class TripResponse(BaseModel):
    """
    Represents the complete trip plan generated by the agent.
    
    This schema contains all the components of a planned trip including
    flights, accommodation, daily itinerary, and cost breakdown.
    """
    
    selected_flight: FlightOption = Field(..., description="Selected flight for the trip")
    selected_hotel: HotelOption = Field(..., description="Selected hotel for accommodation")
    start_date: Optional[Date] = Field(None, description="Trip start date (from original TripRequest)")
    end_date: Optional[Date] = Field(None, description="Trip end date (from original TripRequest)")
    itinerary: List[DayPlan] = Field(default_factory=list, description="Day-by-day itinerary for the trip")
    nights: Optional[int] = Field(None, ge=1, description="Number of nights for the hotel stay")
    strict_itinerary_validation: bool = Field(default=True, description="Whether to enforce strict consecutive date validation")
    budget_summary: Optional[BudgetSummary] = Field(None, description="Detailed cost breakdown by category")
    total_cost: int = Field(..., ge=0, description="Total estimated cost in INR")
    currency: str = Field(default="INR", min_length=3, max_length=3, description="ISO 4217 currency code")
    warnings: List[str] = Field(default_factory=list, description="Any warnings or important notes about the trip plan")
    candidate_flights: Optional[List[FlightOption]] = Field(None, description="Alternative flight options considered")
    candidate_hotels: Optional[List[HotelOption]] = Field(None, description="Alternative hotel options considered")
    
    @field_validator("currency")
    @classmethod
    def validate_currency_uppercase(cls, v: str) -> str:
        """Ensure currency code is uppercase."""
        return v.upper()
    
    @field_validator("itinerary")
    @classmethod
    def validate_itinerary_coverage(cls, v: List[DayPlan], info) -> List[DayPlan]:
        """
        Validate that itinerary has one DayPlan per calendar day.
        
        This ensures complete coverage of the trip period without gaps.
        Set strict_itinerary_validation=False for flexible partial itineraries.
        """
        if not v:
            return v
        
        # Skip strict validation if flag is disabled
        strict_mode = info.data.get("strict_itinerary_validation", True)
        if not strict_mode:
            return v
        
        # Check that day_numbers are sequential starting from 1
        day_numbers = [day.day_number for day in v]
        expected_days = list(range(1, len(v) + 1))
        
        if day_numbers != expected_days:
            raise ValueError(
                f"Itinerary must have sequential day numbers starting from 1. "
                f"Expected {expected_days}, got {day_numbers}"
            )
        
        # Check that dates are sequential (one per day)
        dates = [day.date for day in v]
        for i in range(1, len(dates)):
            delta = (dates[i] - dates[i-1]).days
            if delta != 1:
                raise ValueError(
                    f"Itinerary must have consecutive dates. "
                    f"Gap found between {dates[i-1]} and {dates[i]}"
                )
        
        return v


__all__ = [
    "BudgetSummary",
    "FlightOption",
    "HotelOption",
    "PlaceOption",
    "TripRequest",
    "DayPlan",
    "TripResponse",
]