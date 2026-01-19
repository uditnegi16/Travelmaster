"""
Flight Tool Module

This module provides flight search functionality for the Agentic AI Travel Planner.
It follows a clean adapter + normalizer + service architecture pattern.

Public API:
    - search_flights: Main entry point for searching flights
    - FlightSearchResult: Result object with pagination metadata (optional)

Architecture:
    - flight_tool.py: Public service layer
    - dataset_adapter.py: Dataset-based flight search
    - api_adapter.py: API-based flight search (stub)
    - normalize.py: Raw data to FlightOption normalization
"""

# Lazy import to avoid circular dependencies and schema loading issues
def __getattr__(name):
    if name == "search_flights":
        from .flight_tool import search_flights
        return search_flights
    elif name == "FlightSearchResult":
        from .flight_tool import FlightSearchResult
        return FlightSearchResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["search_flights", "FlightSearchResult"]
