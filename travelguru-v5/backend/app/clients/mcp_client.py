"""
MCP Client for TravelGuru v5.
In-process bridge between LangGraph orchestrator and MCP tool server.
"""

import asyncio
import logging
from typing import Any, Dict

from backend.app.mcp_server.server import mcp

logger = logging.getLogger(__name__)


async def _call_tool_async(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Call an MCP tool asynchronously.
    
    Args:
        tool_name: Name of the tool to call
        arguments: Arguments to pass to the tool
        
    Returns:
        Tool execution result
        
    Raises:
        RuntimeError: If tool call fails
    """
    logger.debug(f"Calling MCP tool async: {tool_name} with args: {arguments}")
    
    try:
        # Call the tool through FastMCP
        result = await mcp.call_tool(tool_name, arguments)
        
        logger.debug(f"Tool {tool_name} returned: {type(result)}")
        return result
    
    except Exception as e:
        logger.error(f"MCP tool call failed: {tool_name} - {e}", exc_info=True)
        raise RuntimeError(f"MCP tool call failed: {tool_name} - {e}") from e


def call_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Call an MCP tool synchronously.
    
    This is the main public API for calling MCP tools from the LangGraph orchestrator.
    Handles event loop management transparently.
    
    Args:
        tool_name: Name of the tool to call (e.g., 'search_flights', 'search_hotels')
        arguments: Dictionary of arguments to pass to the tool
        
    Returns:
        Tool execution result (already deserialized by MCP)
        
    Raises:
        ValueError: If tool_name is empty or arguments is not a dict
        RuntimeError: If tool call fails
    """
    # Validate inputs
    if not tool_name or not isinstance(tool_name, str):
        raise ValueError("tool_name must be a non-empty string")
    
    if not isinstance(arguments, dict):
        raise ValueError("arguments must be a dictionary")
    
    logger.info(f"MCP call_tool: {tool_name}")
    logger.debug(f"MCP call_tool arguments: {arguments}")
    
    try:
        # Check if we're already in an async context
        try:
            running_loop = asyncio.get_running_loop()
            # We're in an async context - this shouldn't happen from LangGraph
            # but handle it gracefully
            logger.warning(
                f"call_tool() called from async context (loop {running_loop}). "
                "This may indicate an architectural issue."
            )
            # Create a new thread to run the async call
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _call_tool_async(tool_name, arguments)
                )
                result = future.result()
        except RuntimeError:
            # No running loop - this is the expected case
            result = asyncio.run(_call_tool_async(tool_name, arguments))
        
        logger.info(f"MCP tool {tool_name} completed successfully")
        logger.debug(f"MCP tool {tool_name} result type: {type(result)}")
        
        return result
    
    except RuntimeError:
        # Re-raise RuntimeError from _call_tool_async
        raise
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error in call_tool: {e}", exc_info=True)
        raise RuntimeError(f"MCP tool call failed: {tool_name} - {e}") from e

