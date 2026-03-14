from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from agent_in_update.shared.schemas import TripRequest
from .travel_planner_graph import generate_trip_plan


from .tools.flight.normalize import flight_option_to_contract
from .tools.hotel.normalize import hotel_option_to_contract
  
app = FastAPI(title="LangGraph Agent API")


class AgentRequest(BaseModel):
    user_query: Optional[str] = None
    trip_request: Optional[TripRequest] = None
import re


import urllib.parse

@app.get("/health")
def health():
    return {"status": "ok", "service": "agent", "port": 8001}

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
        trip_req_dict = request.trip_request.model_dump() if request.trip_request else None

        result = generate_trip_plan(
            user_query=request.user_query,
            trip_request=trip_req_dict
        )
        debug = result.get("debug", {})
        timings = debug.get("timings", {})

        # multi options from orchestrator
        flights_list = result.get("flights", []) or []
        hotels_list = result.get("hotels", []) or []

        trip_req = trip_req_dict or {}
        departure_date = trip_req.get("start_date", "") or ""
        flights = [flight_option_to_contract(f, departure_date=departure_date) for f in flights_list]

        hotels = [hotel_option_to_contract(h) for h in hotels_list]

        has_any = bool(flights) or bool(hotels) or bool(result.get("places")) or bool(result.get("weather"))
        agent_status = "SUCCESS" if (flights and hotels) else ("PARTIAL" if has_any else "FAILED")

        budget_summary = result.get("budget_summary")
        budget = budget_summary.model_dump() if budget_summary is not None else {}

        return {
            "flights": flights,
            "hotels": hotels,
            "places": result.get("places", []) or [],
            "weather": result.get("weather", []) or [],
            "budget": budget,
            "narrative": result.get("narrative", ""),
            "agent_status": agent_status,
            "execution_time": timings.get("total", None),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
