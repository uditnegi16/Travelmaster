# backend/app/clients/multi_client.py
import os
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

# Local defaults for testing
DEFAULT_MCP_URL = os.getenv("MCP_TRAVEL_URL", "http://localhost:8001/mcp")
DEFAULT_MCP_TOKEN = os.getenv("MCP_TOKEN", "")

def create_mcp_client():
    """
    Create a MultiServerMCPClient configured to talk to the local TravelTools server.
    This function returns the client instance; callers should await client.get_tools()
    or use client.session(...) for stateful usage.
    """
    config = {
        "travel": {
            "transport": "http",
            "url": DEFAULT_MCP_URL,
            "headers": {"Authorization": f"Bearer {DEFAULT_MCP_TOKEN}"},
        }
    }
    return MultiServerMCPClient(config)

async def test_discover_tools():
    """
    Quick async test that fetches tools from the MCP server and prints their names.
    Run with: python -m backend.app.clients.multi_client
    """
    client = create_mcp_client()
    tools = await client.get_tools()
    print("Discovered tools:")
    for t in tools:
        # LangChain Tool objects have a .name attribute
        print(" -", getattr(t, "name", repr(t)))

if __name__ == "__main__":
    asyncio.run(test_discover_tools())
