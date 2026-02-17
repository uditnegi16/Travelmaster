# ===== __init__.py =====
"""
Hotel tool module for TravelGuru v5.
Pure business logic for searching hotels.
"""

from agents.langgraph_agents.tools.hotel.service import search_hotels

__all__ = ["search_hotels"]
