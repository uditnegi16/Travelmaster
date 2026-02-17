"""
Flight data adapters.
Provides different sources for flight data (dataset, API) using functional approach.
"""

from agents.langgraph_agents.tools.flight.adapters import dataset
from agents.langgraph_agents.tools.flight.adapters import api

__all__ = ["dataset", "api"]
