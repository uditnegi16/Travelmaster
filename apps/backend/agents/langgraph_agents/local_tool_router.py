"""
Local tool router for LangGraph agents.
Dispatches tool calls to local Python functions.

This is a temporary implementation that will be replaced with MCP (Model Context Protocol)
in the future. The interface is designed to be swappable.
"""

from typing import Any, Callable

from core.logging import get_logger
from agents.langgraph_agents.tools.flight.service import search_flights
from agents.langgraph_agents.tools.hotel.service import search_hotels
from agents.langgraph_agents.tools.places.service import search_places
from agents.langgraph_agents.tools.weather.service import get_weather_forecast
from agents.langgraph_agents.tools.budget.service import compute_budget

logger = get_logger(__name__)


class ToolRouterError(Exception):
    """Raised when tool routing or execution fails."""
    pass


# Tool registry mapping tool names to their implementation functions
TOOL_REGISTRY: dict[str, Callable] = {
    "search_flights": search_flights,
    "search_hotels": search_hotels,
    "search_places": search_places,
    "get_weather_forecast": get_weather_forecast,
    "compute_budget": compute_budget,
}


def call_local_tool(tool_name: str, arguments: dict) -> Any:
    """
    Dispatch tool calls from LangGraph planner to local Python functions.
    
    Routes tool invocations by name to the appropriate service function,
    unpacks arguments, and returns the result. Provides unified error
    handling and logging for all tool executions.
    
    This function serves as the interface between LangGraph's tool calling
    mechanism and the local Python service layer. It is designed to be
    replaced with MCP (Model Context Protocol) in the future while maintaining
    the same interface.
    
    Args:
        tool_name: Name of the tool to execute (e.g., "search_flights")
        arguments: Dictionary of arguments to pass to the tool function
        
    Returns:
        Result from the tool execution (type varies by tool)
        
    Raises:
        ToolRouterError: If tool name is unknown or tool execution fails
        
    Example:
        >>> result = call_local_tool(
        ...     "search_flights",
        ...     {"origin": "DEL", "destination": "BOM", "date": "2026-02-15"}
        ... )
        >>> len(result)
        10
    """
    logger.info(f"Routing tool call: {tool_name}")
    logger.debug(f"Tool arguments: {arguments}")
    
    # Validate tool name
    if not tool_name:
        logger.error("Tool name is required but was empty or None")
        raise ToolRouterError("Tool name is required")
    
    if tool_name not in TOOL_REGISTRY:
        logger.error(f"Unknown tool requested: '{tool_name}'")
        logger.debug(f"Available tools: {list(TOOL_REGISTRY.keys())}")
        raise ToolRouterError(
            f"Unknown tool: '{tool_name}'. "
            f"Available tools: {', '.join(TOOL_REGISTRY.keys())}"
        )
    
    # Get tool function
    tool_fn = TOOL_REGISTRY[tool_name]
    logger.debug(f"Resolved tool '{tool_name}' to function: {tool_fn.__name__}")
    
    # Validate arguments
    if not isinstance(arguments, dict):
        logger.error(f"Arguments must be a dict, got {type(arguments)}")
        raise ToolRouterError(f"Arguments must be a dict, got {type(arguments)}")
    
    # Execute tool with argument unpacking
    try:
        logger.info(f"Executing tool: {tool_name}")
        result = tool_fn(**arguments)
        logger.info(f"Tool '{tool_name}' executed successfully")
        
        # Log result summary (not full data to avoid log spam)
        if isinstance(result, list):
            logger.debug(f"Tool returned list with {len(result)} items")
        elif isinstance(result, dict):
            logger.debug(f"Tool returned dict with keys: {list(result.keys())}")
        elif result is None:
            logger.debug("Tool returned None")
        else:
            logger.debug(f"Tool returned {type(result).__name__}")
        
        return result
        
    except TypeError as e:
        # Likely wrong arguments passed to function
        logger.error(f"Tool '{tool_name}' received invalid arguments: {e}", exc_info=True)
        raise ToolRouterError(
            f"Invalid arguments for tool '{tool_name}': {e}. "
            f"Check that all required parameters are provided."
        )
    
    except Exception as e:
        # Tool execution failed
        logger.error(
            f"Tool '{tool_name}' execution failed: {e}",
            exc_info=True,
            extra={
                "tool_name": tool_name,
                "arguments": arguments,
            }
        )
        raise ToolRouterError(f"Tool '{tool_name}' execution failed: {e}")


def get_available_tools() -> list[str]:
    """
    Get list of all available tool names.
    
    Useful for debugging, validation, and displaying capabilities
    to the LangGraph planner or external systems.
    
    Returns:
        List of registered tool names
        
    Example:
        >>> tools = get_available_tools()
        >>> "search_flights" in tools
        True
    """
    return list(TOOL_REGISTRY.keys())
