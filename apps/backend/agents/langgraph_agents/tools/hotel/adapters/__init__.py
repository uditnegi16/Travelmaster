# ===== __init__.py =====
"""
Hotel data adapters.
Provides different sources for hotel data (dataset, API) using functional approach.
"""

from agents.langgraph_agents.tools.hotel.adapters import dataset
from agents.langgraph_agents.tools.hotel.adapters.search_api import search_hotels_api
from agents.langgraph_agents.tools.hotel.adapters.ratings_api import get_hotel_ratings_api
from agents.langgraph_agents.tools.hotel.adapters.booking_api import book_hotel_api

__all__ = [
    "search_hotels_api",
    "get_hotel_ratings_api",
    "book_hotel_api",
]

