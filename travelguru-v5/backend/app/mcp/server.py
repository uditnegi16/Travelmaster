# backend/app/mcp/server.py
from fastmcp import FastMCP

mcp = FastMCP("TravelTools")

# Simple in-process tool implementations for local testing
@mcp.tool()
def flight_search(origin: str, dest: str, date: str) -> dict:
    """Return a tiny mock response for flight search."""
    return {
        "provider": "mock-air",
        "origin": origin,
        "dest": dest,
        "date": date,
        "results": [
            {"flight": "MA123", "price_usd": 199},
            {"flight": "MA456", "price_usd": 249},
        ],
    }

@mcp.tool()
def hotel_search(city: str, checkin: str, nights: int) -> dict:
    """Return a tiny mock response for hotel search."""
    return {
        "provider": "mock-hotels",
        "city": city,
        "checkin": checkin,
        "nights": nights,
        "options": [
            {"name": "Hotel A", "price_usd": 120},
            {"name": "Hotel B", "price_usd": 95},
        ],
    }

@mcp.tool()
def get_weather(city: str) -> dict:
    """Return a tiny mock weather response."""
    return {"city": city, "forecast": "sunny", "temp_c": 28}

if __name__ == "__main__":
    # For local dev run as HTTP server on port 8001
    # In production you can containerize and expose /mcp endpoint
    mcp.run(transport="http", host="0.0.0.0", port=8001)
