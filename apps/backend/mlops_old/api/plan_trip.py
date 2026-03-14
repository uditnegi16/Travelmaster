# app/mlops/api/plan_trip.py

from fastapi import APIRouter, HTTPException
import os

from api.schemas import PlanTripRequest
from adapters.agent_adapter import AgentAdapter

router = APIRouter()

AGENT_URL = os.getenv("LANGGRAPH_AGENT_URL", "http://localhost:8001")
agent_adapter = AgentAdapter(agent_url=AGENT_URL, timeout_sec=900)  # 15 min


@router.post("/plan-trip")
def plan_trip(request: PlanTripRequest):
    try:
        user_input = request.user_input or {}

        # Build payload EXACTLY as agent expects (TripRequest-like)
        trip_request = {
            "from_city": user_input.get("origin"),
            "to_city": user_input.get("destination"),
            "start_date": user_input.get("start_date"),
            "end_date": user_input.get("end_date"),
            "budget": user_input.get("budget"),
            # Streamlit uses "people" → agent expects "travelers"
            "travelers": user_input.get("travelers") or user_input.get("people") or 1,
            # optional
            "preferences": user_input.get("preferences", {}),
        }

        agent_payload = {
            # optional natural language query (if you want)
            "user_query": user_input.get("query"),
            "trip_request": trip_request,
        }

        agent_output = agent_adapter.call_agent(agent_payload)

        if agent_output.get("agent_status") == "failed":
            raise HTTPException(status_code=502, detail=agent_output.get("error", "Agent failed"))

        flights = agent_output.get("flights", []) or []
        hotels = agent_output.get("hotels", []) or []

        return {
            "flights": flights[: request.top_k_flights],
            "hotels": hotels[: request.top_k_hotels],
            "places": agent_output.get("places", []) or [],
            "weather": agent_output.get("weather", []) or [],
            "budget": agent_output.get("budget", {}) or {},
            "narrative": agent_output.get("narrative", "") or "",
            "agent_status": agent_output.get("agent_status", "success"),
            "execution_time": agent_output.get("execution_time"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
