"""
Hotel Tool Module

This module provides hotel search functionality for the Agentic AI Travel Planner.
It follows a clean adapter + normalizer + service architecture pattern.

Public API:
    - search_hotels: Main entry point for searching hotels
    - HotelSearchResult: Result object with pagination metadata (optional)

Architecture:
    - service.py: Public service layer
    - dataset_adapter.py: Dataset-based hotel search
    - api_adapter.py: API-based hotel search (stub)
    - normalize.py: Raw data to HotelOption normalization
"""

# Lazy import to avoid circular dependencies and schema loading issues
def __getattr__(name):
    if name == "search_hotels":
        from .hotel_tool import search_hotels
        return search_hotels
    elif name == "HotelSearchResult":
        from .hotel_tool import HotelSearchResult
        return HotelSearchResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["search_hotels", "HotelSearchResult"]
