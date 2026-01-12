"""
Flight data adapters.
Provides different sources for flight data (dataset, API) using functional approach.
"""

from backend.app.tools.flight.adapters import dataset
from backend.app.tools.flight.adapters import api

__all__ = ["dataset", "api"]
