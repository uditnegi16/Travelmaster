import os
import json
import logging
from typing import Dict, Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage

from google.adk.agents import Agent
from google.adk.tools import tool

from app.agents.shared.mcp_client import get_mcp_client
from app.agents.shared.schemas import BudgetResponse

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

mcp = get_mcp_client()

llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0.3,
)

# ---------------- TOOL ---------------- #

@tool
def budget_estimator(payload_json: str) -> str:
    """
    Estimate travel budget based on travel, booking and explorer info.
    Input must be JSON string.
    """
    try:
        payload = json.loads(payload_json)
    except Exception:
        return "Invalid JSON payload"

    travel_request = payload.get("travel_request", {})
    booking = payload.get("booking", {})

    people = travel_request.get("people", 1)
    days = travel_request.get("days", 3)
    city = travel_request.get("destination", "Goa")

    try:
        estimate = mcp.call_tool_sync(
            "budget_estimate",
            {"city": city, "days": days, "people": people},
        )
    except Exception as e:
        logger.error("Budget MCP failed: %s", e)
        estimate = {}

    prompt = f"""
    Trip:
    {json.dumps(travel_request, indent=2)}

    Booking:
    {json.dumps(booking, indent=2)}

    Estimate:
    {json.dumps(estimate, indent=2)}

    Provide:
    - category-wise breakdown
    - total estimate
    - saving tips
    - upgrade options
    """

        msg = llm.invoke([HumanMessage(content=prompt)])
        explanation = msg.content if isinstance(msg, AIMessage) else ""

        response = BudgetResponse(
            total_estimate=estimate.get("total_estimate"),
            breakdown=estimate.get("breakdown", {}),
            savings_tips=estimate.get("savings_tips", []),
            upgrade_options=estimate.get("upgrade_options", []),
            notes=explanation[:800],
        )

    return response.model_dump_json()


# ---------------- AGENT ---------------- #

def create_agent():
    return Agent(
        name="budget_agent",
        model="gemini-1.5-flash",
        tools=[budget_estimator],
        instructions="""
You are a travel budget optimization expert.
Always call budget_estimator tool with full JSON input.
""",
    )
