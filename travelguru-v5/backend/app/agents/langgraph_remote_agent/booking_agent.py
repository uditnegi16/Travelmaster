import os
import json
import logging
from typing import Dict, Any, List

from dotenv import load_dotenv
from pydantic import BaseModel

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
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
# PARSER
# ============================================================

def extract_trip_info(state: BookingState) -> BookingState:
    try:
        data = json.loads(state.query)
        state.travel_request = data.get("travel_request", {})
        state.explorer = data.get("explorer", {})
    except Exception:
        logger.warning("Query not JSON — using fallback parse")

    return state

# ============================================================
# MCP TOOL CALLS
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
# FINAL RESPONSE
# ============================================================

def build_booking_response(state: BookingState) -> BookingState:

    flights_raw = state.flights.get("flights", []) if state.flights else []
    hotels_raw = state.hotels.get("hotels", []) if state.hotels else []
    weather = state.weather or {}

    # ---- normalize transport options to schema ----
    transport_options = []
    for f in flights_raw:
        transport_options.append({
            "mode": "flight",
            "provider": f.get("airline"),
            "price": f.get("price"),
            "duration": f.get("duration"),
        })

    hotel_zones = list({h.get("name", "Unknown Area") for h in hotels_raw})

    weather_text = (
        f"{weather.get('condition', 'unknown')} at {weather.get('temp_c', '?')}°C"
        if weather else "Weather unavailable"
    )

    packing = weather.get("packing_suggestions", []) if weather else []

    prompt = f"""
You are a travel booking expert.

Flights: {json.dumps(transport_options)}
Hotels: {json.dumps(hotels_raw)}
Weather: {json.dumps(weather)}

Give short booking advice and best choices.
"""

    msg = llm.invoke([HumanMessage(content=prompt)])
    explanation = msg.content if isinstance(msg, AIMessage) else ""

    response = BookingResponse(
        transport_options=transport_options,
        hotel_zones=hotel_zones,
        weather_summary=weather_text,
        packing_suggestions=packing,
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
# A2A WRAPPER
# ============================================================

class BookingAgent:

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def invoke(self, query: str, context_id: str) -> Dict[str, Any]:

        # LangGraph always returns dict, not BookingState
        result: Dict[str, Any] = GRAPH.invoke({"query": query})

        final: BookingResponse | None = result.get("final")

        return {
            "is_task_complete": True,
            "require_user_input": False,
            "content": final.model_dump_json() if final else "{}",
        }

    async def stream(self, query: str, context_id: str):
        yield self.invoke(query, context_id)
