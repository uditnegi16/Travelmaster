# adk_tools.py

from datetime import datetime
from typing import Dict, Any, List
import uuid

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# -----------------------------
# MCP TOOLSET (Travel Services)
# -----------------------------

# Placeholder MCP server — later we’ll replace with:
# - travel search
# - maps
# - visa rules
# - booking services

travel_mcp_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "@modelcontextprotocol/server-everything"  # dev/demo MCP server
            ],
        ),
    ),
)

# -----------------------------
# IN-MEMORY MASTERPLAN STORE
# -----------------------------

MASTERPLANS: Dict[str, Dict[str, Any]] = {}

# -----------------------------
# CORE HOST TOOLS
# -----------------------------

def classify_trip(travel_request: Dict[str, Any]) -> Dict[str, str]:
    """
    Determines trip_type and travel_scope.
    """

    destination = travel_request.get("destination", "").lower()
    country = travel_request.get("country", "").lower()

    if country and country != "india":
        scope = "international"
    elif destination:
        scope = "state"
    else:
        scope = "city"

    trip_type = travel_request.get("trip_type", "budget")

    return {
        "trip_type": trip_type,
        "travel_scope": scope,
    }


def create_masterplan(travel_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a task DAG for travel planning.
    """

    trip_type = travel_request.get("trip_type", "budget")
    scope = travel_request.get("travel_scope", "city")

    tasks = ["intent_validation", "exploration"]

    if trip_type in ["budget", "family"]:
        tasks.append("budget_optimization")

    tasks.append("itinerary_generation")

    if scope in ["state", "international"]:
        tasks.append("booking_validation")

    if scope == "international":
        tasks.append("visa_check")

    tasks.append("final_plan")

    plan_id = str(uuid.uuid4())

    plan = {
        "plan_id": plan_id,
        "created_at": datetime.utcnow().isoformat(),
        "travel_request": travel_request,
        "tasks": tasks,
        "results": {},
        "status": "in_progress",
    }

    MASTERPLANS[plan_id] = plan
    return plan


def update_masterplan(plan_id: str, task: str, result: Any) -> Dict[str, Any]:
    if plan_id not in MASTERPLANS:
        return {"status": "error", "message": "Invalid plan_id"}

    MASTERPLANS[plan_id]["results"][task] = result
    return {"status": "success"}


def finalize_masterplan(plan_id: str) -> Dict[str, Any]:
    if plan_id not in MASTERPLANS:
        return {"status": "error", "message": "Invalid plan_id"}

    MASTERPLANS[plan_id]["status"] = "completed"
    return MASTERPLANS[plan_id]


def get_masterplan(plan_id: str) -> Dict[str, Any]:
    return MASTERPLANS.get(plan_id, {"status": "not_found"})
