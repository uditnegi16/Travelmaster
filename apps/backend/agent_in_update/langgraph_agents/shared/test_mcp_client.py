from shared.mcp_client import get_mcp_client

def main():
    mcp = get_mcp_client()

    print("\n--- WEATHER ---")
    print(mcp.call_tool_sync("weather", {"city": "Goa"}))

    print("\n--- FLIGHTS ---")
    print(mcp.call_tool_sync("flight_search", {
        "from_city": "Bangalore",
        "to_city": "Goa",
        "people": 2
    }))

    print("\n--- HOTELS ---")
    print(mcp.call_tool_sync("hotel_search", {
        "city": "Goa",
        "nights": 3,
        "budget_level": "medium"
    }))

    print("\n--- BUDGET ---")
    print(mcp.call_tool_sync("budget_estimate", {
        "city": "Goa",
        "days": 3,
        "people": 2
    }))

if __name__ == "__main__":
    main()


