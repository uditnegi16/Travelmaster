# schemas.py

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


# ============================================================
# 🔍 EXPLORER AGENT SCHEMA
# ============================================================

class ExplorerAttraction(BaseModel):
    name: str
    city: Optional[str] = None
    category: Optional[str] = Field(
        default=None, description="beach | museum | adventure | cultural | shopping | nature"
    )
    short_description: Optional[str] = None


class ExplorerResponse(BaseModel):
    """
    Returned by Explorer Agent (CrewAI).
    Focus: where to go and what to see.
    """

    destinations: List[str] = Field(
        description="Cities or places suitable for the trip"
    )

    attractions: List[ExplorerAttraction] = Field(
        description="Major attractions and experiences"
    )

    experiences: List[str] = Field(
        description="Activities like hiking, food tours, nightlife, etc."
    )

    city_clusters: List[List[str]] = Field(
        description="Logical grouping of cities for routing"
    )

    route_notes: Optional[str] = Field(
        default=None, description="High-level travel routing tips"
    )


# ============================================================
# 💸 BUDGET AGENT SCHEMA
# ============================================================

class BudgetBreakdown(BaseModel):
    transport: float
    accommodation: float
    food: float
    activities: float


class BudgetResponse(BaseModel):
    """
    Returned by Budget Optimization Agent (ADK).
    Focus: cost estimation and savings.
    """

    total_estimate: float
    currency: str = "INR"

    breakdown: BudgetBreakdown

    saving_tips: List[str]


# ============================================================
# 🏨 BOOKING & LOGISTICS AGENT SCHEMA
# ============================================================

class TransportOption(BaseModel):
    mode: str = Field(description="flight | train | bus | cab")
    duration_hours: Optional[float] = None
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    """
    Returned by Booking & Logistics Agent (LangGraph).
    Focus: feasibility, weather, packing, logistics.
    """

    transport_options: List[TransportOption]

    hotel_zones: List[str] = Field(
        description="Recommended areas to stay"
    )

    booking_notes: Optional[str] = None

    weather_summary: Optional[str] = None

    packing_suggestions: List[str]


# ============================================================
# ❗ ERROR / FALLBACK SCHEMA
# ============================================================

class AgentErrorResponse(BaseModel):
    status: str = "error"
    message: str
