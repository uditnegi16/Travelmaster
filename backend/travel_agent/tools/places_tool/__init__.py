"""
Places Tool Module

This module provides places of interest search functionality for the Agentic AI Travel Planner.
It follows a clean adapter + normalizer + service architecture pattern.

Public API:
    - search_places: Main entry point for searching places of interest
    - PlaceSearchResult: Result object with pagination metadata (optional)

Architecture:
    - places_tool.py: Public service layer
    - dataset_adapter.py: Dataset-based places search
    - api_adapter.py: API-based places search (stub)
    - normalize.py: Raw data to PlaceOption normalization
"""

# Lazy import to avoid circular dependencies and schema loading issues
def __getattr__(name):
    if name == "search_places":
        from .places_tool import search_places
        return search_places
    elif name == "PlaceSearchResult":
        from .places_tool import PlaceSearchResult
        return PlaceSearchResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["search_places", "PlaceSearchResult"]
