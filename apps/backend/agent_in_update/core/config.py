# core/config.py
"""
Central configuration: loads all env vars for the agent service.
Every downstream module imports from here — never from os.getenv directly.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (two levels up from core/)
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=False)

# ── Amadeus ───────────────────────────────────────────────────────
AMADEUS_CLIENT_ID: str = os.getenv("AMADEUS_CLIENT_ID", "")
AMADEUS_CLIENT_SECRET: str = os.getenv("AMADEUS_CLIENT_SECRET", "")

# FIX: Determines sandbox vs production automatically based on key prefix.
# Amadeus test keys start with the same prefix but the hostname differs.
# Set AMADEUS_HOSTNAME=production in .env to switch; defaults to test.
AMADEUS_HOSTNAME: str = os.getenv("AMADEUS_HOSTNAME", "test").lower()

DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "INR")

# ── OpenAI ────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")
PLANNER_MODEL: str = os.getenv("PLANNER_MODEL", "gpt-4o-mini")
COMPOSER_MODEL: str = os.getenv("COMPOSER_MODEL", "gpt-4o-mini")

# ── OpenWeather ───────────────────────────────────────────────────
OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_TIMEOUT: int = int(os.getenv("OPENWEATHER_TIMEOUT", "15"))

# ── Google Places ─────────────────────────────────────────────────
GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")

# ── Dataset paths (fallback when APIs are unavailable) ────────────
_BASE = Path(__file__).parent.parent
FLIGHTS_DATASET_PATH: str = os.getenv(
    "FLIGHTS_DATASET_PATH",
    str(_BASE / "langgraph_agents" / "tools" / "flight" / "adapters" / "dataset.py"),
)
PLACES_DATASET_PATH: str = os.getenv(
    "PLACES_DATASET_PATH",
    str(_BASE / "langgraph_agents" / "tools" / "places" / "adapters" / "dataset.py"),
)
WEATHER_DATASET_PATH: str = os.getenv(
    "WEATHER_DATASET_PATH",
    str(_BASE / "langgraph_agents" / "tools" / "weather" / "adapters" / "dataset.py"),
)

# ── Feature flags ─────────────────────────────────────────────────
USE_AMADEUS_API: bool = os.getenv("USE_AMADEUS_API", "true").lower() in {"1", "true", "yes"}
USE_GOOGLE_PLACES: bool = os.getenv("USE_GOOGLE_PLACES", "true").lower() in {"1", "true", "yes"}
USE_OPENWEATHER: bool = os.getenv("USE_OPENWEATHER", "true").lower() in {"1", "true", "yes"}
