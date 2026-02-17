"""
Flight tool module for TravelGuru v5.
Provides flight search functionality using dataset or API sources.
"""

from agents.langgraph_agents.tools.flight.service import search_flights

__all__ = ["search_flights"]
