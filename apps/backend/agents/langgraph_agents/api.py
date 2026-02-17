from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from agents.shared.schemas import TripRequest
from .travel_planner_graph import generate_trip_plan

app = FastAPI(title="LangGraph Agent API")


class AgentRequest(BaseModel):
    user_query: Optional[str] = None
    trip_request: Optional[TripRequest] = None


@app.post("/agent/plan-trip")
def plan_trip(request: AgentRequest):
    try:
        if not request.user_query and not request.trip_request:
            raise HTTPException(
                status_code=400,
                detail="Either user_query or trip_request must be provided"
            )

        # IMPORTANT:
        # Your orchestrator internally uses request.from_city etc,
        # so PASS TripRequest object (NOT dict).
        result = generate_trip_plan(
            user_query=request.user_query,
            trip_request=request.trip_request
        )

        trip = result.get("trip")
        debug = result.get("debug", {})
        timings = debug.get("timings", {})

        # Build places safely (don’t assume itinerary_enrichment exists)
        places = []
        if trip and hasattr(trip, "itinerary_enrichment") and trip.itinerary_enrichment:
            enrichment = trip.itinerary_enrichment
            if hasattr(enrichment, "places") and enrichment.places:
                places = [p.model_dump() for p in enrichment.places]

        return {
            "flights": (
                [trip.trip_plan.flight.model_dump()]
                if trip and trip.trip_plan and trip.trip_plan.flight
                else []
            ),
            "hotels": (
                [trip.trip_plan.hotel.model_dump()]
                if trip and trip.trip_plan and trip.trip_plan.hotel
                else []
            ),
            "places": places,
            "weather": (
                [w.model_dump() for w in trip.trip_plan.weather]
                if trip and trip.trip_plan and trip.trip_plan.weather
                else []
            ),
            "budget": (
                trip.budget_summary.model_dump()
                if trip and trip.budget_summary
                else {}
            ),
            "narrative": result.get("narrative", ""),
            "agent_status": "success",
            "execution_time": timings.get("total", None),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
