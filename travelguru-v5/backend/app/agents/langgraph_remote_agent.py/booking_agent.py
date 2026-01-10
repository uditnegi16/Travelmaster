import os
import json
import logging
from typing import Dict, Any, List

from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, END

from app.agents.shared.mcp_client import get_mcp_client
from app.agents.shared.schemas import BookingResponse

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================
# CONFIG
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("⚠️ GROQ_API_KEY not set")

# ============================================================
# MCP CLIENT (SYNC)
# ============================================================

mcp = get_mcp_client()

# ============================================================
# LLM
# ============================================================

llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0.2,
)

# ============================================================
# STATE
# ============================================================

class BookingState(BaseModel):
    query: str
    travel_request: Dict[str, Any] = {}
    explorer: Dict[str, Any] = {}

    flights: Dict[str, Any] | None = None
    hotels: Dict[str, Any] | None = None
    weather: Dict[str, Any] | None = None

    final: BookingResponse | None = None

# ============================================================
# PARSERS (TEMP — LATER NLP)
# ============================================================

def extract_trip_info(state: BookingState) -> BookingState:
    """
    For MVP: assume Host already passed structured info in query JSON.
    """
    try:
        data = json.loads(state.query)
        state.travel_request = data.get("travel_request", {})
        state.explorer = data.get("explorer", {})
    except Exception:
        logger.warning("Query not JSON — using fallback parse")

    return state

# ============================================================
# MCP CALL NODES
# ============================================================

def call_flights(state: BookingState) -> BookingState:
    tr = state.travel_request
    from_city = tr.get("origin", "Bangalore")
    to_city = tr.get("destination", "Goa")
    people = tr.get("people", 1)

    state.flights = mcp.call_tool_sync(
        "flight_search",
        {"from_city": from_city, "to_city": to_city, "people": people},
    )
    return state


def call_hotels(state: BookingState) -> BookingState:
    tr = state.travel_request
    city = tr.get("destination", "Goa")
    nights = tr.get("days", 3)
    budget = tr.get("budget_level", "medium")

    state.hotels = mcp.call_tool_sync(
        "hotel_search",
        {"city": city, "nights": nights, "budget_level": budget},
    )
    return state


def call_weather(state: BookingState) -> BookingState:
    city = state.travel_request.get("destination", "Goa")

    state.weather = mcp.call_tool_sync("weather", {"city": city})
    return state

# ============================================================
# FINAL RESPONSE BUILDER
# ============================================================

def build_booking_response(state: BookingState) -> BookingState:
    prompt = f"""
You are a travel booking expert.

Based on:
Flights: {json.dumps(state.flights)}
Hotels: {json.dumps(state.hotels)}
Weather: {json.dumps(state.weather)}

Explain best options shortly and select best hotel and flight.
"""

    msg = llm.invoke([HumanMessage(content=prompt)])
    explanation = msg.content if isinstance(msg, AIMessage) else ""

    response = BookingResponse(
        flight_options=state.flights.get("flights", []) if state.flights else [],
        hotel_options=state.hotels.get("hotels", []) if state.hotels else [],
        weather_summary=state.weather,
        packing_tips=state.weather.get("packing_suggestions") if state.weather else [],
        booking_notes=explanation[:800],
    )

    state.final = response
    return state

# ============================================================
# LANGGRAPH
# ============================================================

def build_graph():
    g = StateGraph(BookingState)

    g.add_node("extract", extract_trip_info)
    g.add_node("flights", call_flights)
    g.add_node("hotels", call_hotels)
    g.add_node("weather", call_weather)
    g.add_node("finalize", build_booking_response)

    g.set_entry_point("extract")

    g.add_edge("extract", "flights")
    g.add_edge("flights", "hotels")
    g.add_edge("hotels", "weather")
    g.add_edge("weather", "finalize")
    g.add_edge("finalize", END)

    return g.compile()

GRAPH = build_graph()

# ============================================================
# A2A COMPATIBLE WRAPPER
# ============================================================

class BookingAgent:

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def invoke(self, query: str, context_id: str) -> Dict[str, Any]:
        state = GRAPH.invoke({"query": query})

        return {
            "is_task_complete": True,
            "require_user_input": False,
            "content": state.final.model_dump_json(),
        }

    async def stream(self, query: str, context_id: str):
        # simple non-streaming fallback
        result = self.invoke(query, context_id)
        yield result
