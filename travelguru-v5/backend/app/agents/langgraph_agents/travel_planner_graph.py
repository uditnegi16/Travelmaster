"""
LangGraph Orchestrator for TravelGuru v5.
Main state machine coordinating planner, MCP tools, and composer agents.
"""

import logging
from typing import Any, Dict, TypedDict

from langgraph.graph import StateGraph, END

from backend.app.shared.schemas import PlannerOutput, ToolCallPlan
from backend.app.agents.langgraph_agents.planner_agent import plan_trip
from backend.app.agents.langgraph_agents.composer_agent import compose_itinerary
from backend.app.clients.mcp_client import call_tool

logger = logging.getLogger(__name__)


class PlannerState(TypedDict):
    """
    State object for the LangGraph travel planner workflow.
    """
    user_query: str
    plan: PlannerOutput | None
    tool_results: Dict[str, Any]
    final_output: str | None


def plan_node(state: PlannerState) -> PlannerState:
    """
    Call the planner agent to generate execution plan from user query.
    
    Args:
        state: Current state with user_query
        
    Returns:
        Updated state with plan populated
    """
    logger.info("=== PLAN NODE ===")
    logger.info(f"User query: {state['user_query']}")
    
    try:
        plan = plan_trip(state["user_query"])
        
        if not plan or not plan.tool_calls:
            raise RuntimeError("Planner returned empty plan")
        
        state["plan"] = plan
        logger.info(f"Generated plan with {len(plan.tool_calls)} tool calls")
        logger.info(f"Reasoning: {plan.reasoning}")
        
        return state
    
    except Exception as e:
        logger.error(f"Plan node failed: {e}", exc_info=True)
        raise RuntimeError(f"Planning failed: {e}") from e


def execute_tool_node(state: PlannerState) -> PlannerState:
    """
    Execute MCP tools based on plan steps sequentially.
    
    Args:
        state: Current state with plan
        
    Returns:
        Updated state with tool_results populated
    """
    logger.info("=== EXECUTE TOOL NODE ===")
    
    plan = state.get("plan")
    if not plan or not plan.tool_calls:
        raise RuntimeError("No plan or tool calls to execute")
    
    tool_results: Dict[str, Any] = {}
    
    for i, tool_call in enumerate(plan.tool_calls):
        logger.info(
            f"Executing tool {i+1}/{len(plan.tool_calls)}: "
            f"{tool_call.tool_name} with args {tool_call.arguments}"
        )
        
        try:
            result = call_tool(tool_call.tool_name, tool_call.arguments)
            
            tool_results[tool_call.tool_name] = result
            
            result_count = len(result) if isinstance(result, (list, tuple)) else 1
            logger.info(f"Tool {tool_call.tool_name} returned {result_count} results")
        
        except Exception as e:
            logger.error(f"Tool {tool_call.tool_name} failed: {e}", exc_info=True)
            raise RuntimeError(f"Tool execution failed for {tool_call.tool_name}: {e}") from e
    
    state["tool_results"] = tool_results
    logger.info(f"Executed {len(tool_results)} tools successfully")
    
    return state


def compose_node(state: PlannerState) -> PlannerState:
    """
    Compose final itinerary narrative from tool results.
    
    Args:
        state: Current state with tool_results
        
    Returns:
        Updated state with final_output populated
    """
    logger.info("=== COMPOSE NODE ===")
    
    try:
        narrative = compose_itinerary(
            user_query=state["user_query"],
            plan=state["plan"],
            tool_results=state["tool_results"]
        )
        
        state["final_output"] = narrative
        
        logger.info("Composition complete")
        logger.debug(f"Final output length: {len(narrative)} characters")
        
        return state
    
    except Exception as e:
        logger.error(f"Compose node failed: {e}", exc_info=True)
        raise RuntimeError(f"Composition failed: {e}") from e


# Build LangGraph
graph = StateGraph(PlannerState)

# Add nodes
graph.add_node("plan", plan_node)
graph.add_node("execute_tools", execute_tool_node)
graph.add_node("compose", compose_node)

# Define flow: START → plan → execute_tools → compose → END
graph.set_entry_point("plan")
graph.add_edge("plan", "execute_tools")
graph.add_edge("execute_tools", "compose")
graph.add_edge("compose", END)

# Compile graph
app = graph.compile()


def run_travel_planner(user_query: str) -> str:
    """
    Run the complete travel planning workflow.
    
    Args:
        user_query: User's travel request in natural language
        
    Returns:
        Final itinerary narrative as string
        
    Raises:
        ValueError: If user_query is empty
        RuntimeError: If any step in the workflow fails
    """
    if not user_query or not user_query.strip():
        raise ValueError("user_query cannot be empty")
    
    logger.info("=== STARTING TRAVEL PLANNER ===")
    logger.info(f"Query: {user_query}")
    
    # Create initial state
    initial_state: PlannerState = {
        "user_query": user_query.strip(),
        "plan": None,
        "tool_results": {},
        "final_output": None
    }
    
    try:
        # Run graph
        final_state = app.invoke(initial_state)
        
        # Extract final output
        final_output = final_state.get("final_output")
        if not final_output:
            raise RuntimeError("Workflow completed but missing final output")
        
        logger.info("=== TRAVEL PLANNER COMPLETE ===")
        return final_output
    
    except Exception as e:
        logger.error(f"Travel planner failed: {e}", exc_info=True)
        raise RuntimeError(f"Travel planning failed: {e}") from e
