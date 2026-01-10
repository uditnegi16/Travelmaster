import os
import json
import logging
from typing import Dict, Any, List

from dotenv import load_dotenv
from pydantic import BaseModel

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage

from app.agents.shared.mcp_client import get_mcp_client
from app.agents.shared.schemas import BudgetResponse

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
# MCP CLIENT
# ============================================================

mcp = get_mcp_client()

# ============================================================
# LLM
# ============================================================

llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0.3,
)

# ============================================================
# INPUT PARSER
# ============================================================

def extract_trip_inputs(query: str) -> Dict[str, Any]:
    """
    Expect Host to send structured JSON:
    {
      "travel_request": {...},
      "explorer": {...},
      "booking": {...}
    }
    """
    try:
        return json.loads(query)
    except Exception:
        logger.warning("Budget agent received non-JSON query")
        return {}

# ============================================================
# CORE BUDGET LOGIC
# ============================================================

def compute_budget(travel_request: Dict[str, Any], booking: Dict[str, Any]) -> Dict[str, Any]:

    people = travel_request.get("people", 1)
    days = travel_request.get("days", 3)
    city = travel_request.get("destination", "Goa")

    try:
        estimate = mcp.call_tool_sync(
            "budget_estimate",
            {
                "city": city,
                "days": days,
                "people": people,
            },
        )
    except Exception as e:
        logger.error("Budget MCP failed: %s", e)
        estimate = None

    return estimate or {}

# ============================================================
# RESPONSE BUILDER
# ============================================================

def build_budget_response(
    travel_request: Dict[str, Any],
    explorer: Dict[str, Any],
    booking: Dict[str, Any],
    estimate: Dict[str, Any],
) -> BudgetResponse:

    prompt = f"""
You are a travel finance expert.

Trip:
{json.dumps(travel_request, indent=2)}

Booking:
{json.dumps(booking, indent=2)}

Budget Estimate:
{json.dumps(estimate, indent=2)}

Provide:
- category-wise budget breakdown
- total estimate
- saving tips
- upgrade suggestions if any
"""

    msg = llm.invoke([HumanMessage(content=prompt)])
    explanation = msg.content if isinstance(msg, AIMessage) else ""

    return BudgetResponse(
        total_estimate=estimate.get("total_estimate"),
        breakdown=estimate.get("breakdown", {}),
        savings_tips=estimate.get("savings_tips", []),
        upgrade_options=estimate.get("upgrade_options", []),
        notes=explanation[:800],
    )

# ============================================================
# A2A / ADK AGENT WRAPPER
# ============================================================

class BudgetOptimizationAgent:

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def invoke(self, query: str, context_id: str) -> Dict[str, Any]:
        payload = extract_trip_inputs(query)

        travel_request = payload.get("travel_request", {})
        explorer = payload.get("explorer", {})
        booking = payload.get("booking", {})

        estimate = compute_budget(travel_request, booking)

        response = build_budget_response(
            travel_request=travel_request,
            explorer=explorer,
            booking=booking,
            estimate=estimate,
        )

        return {
            "is_task_complete": True,
            "require_user_input": False,
            "content": response.model_dump_json(),
        }

    async def stream(self, query: str, context_id: str):
        yield self.invoke(query, context_id)
