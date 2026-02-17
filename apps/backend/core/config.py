"""
Configuration module for TravelGuru v5
Handles environment loading, LLM settings, paths, and logging setup.
"""

from pathlib import Path
import os

try:
    from dotenv import load_dotenv

    # Force-load .env from backend/ directory
    env_path = Path(__file__).resolve().parents[3] / ".env"
    load_dotenv(dotenv_path=env_path, override=True)

except Exception as e:
    print("WARNING: Could not load .env file:", e)

import logging
from typing import Literal



# ============================================================================
# BASE PATHS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Points to backend/
DATA_DIR = BASE_DIR / "data"
FLIGHTS_DATASET_PATH = DATA_DIR / "flights.json"
HOTELS_DATASET_PATH = DATA_DIR / "hotels.json"
PLACES_DATASET_PATH = DATA_DIR / "places.json"

# ============================================================================
# ENVIRONMENT VARIABLES 
# ============================================================================

ENV: Literal["dev", "prod"] = os.getenv("ENV", "dev")  # type: ignore
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set")
DATA_SOURCE: Literal["dataset", "api"] = os.getenv("DATA_SOURCE", "dataset")  # type: ignore

# ============================================================================
# FLIGHT AND HOTEL API CONFIGURATION
# ============================================================================

AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
AMADEUS_ENV = os.getenv("AMADEUS_ENV", "test")  # 'production' or 'test'
AMADEUS_TIMEOUT = int(os.getenv("AMADEUS_TIMEOUT", "30"))
AMADEUS_MAX_RETRIES = int(os.getenv("AMADEUS_MAX_RETRIES", "3"))

# ============================================================================
# PLACES OF INTEREST API CONFIGURATION
# ============================================================================

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GOOGLE_MAPS_TIMEOUT = int(os.getenv("GOOGLE_MAPS_TIMEOUT", "30"))

# ============================================================================
# WEATHER DATA API CONFIGURATION
# ============================================================================

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_TIMEOUT = int(os.getenv("OPENWEATHER_TIMEOUT", "20"))

# ============================================================================
# LLM CONFIGURATION
# ============================================================================

# Planner LLM
PLANNER_LLM_PROVIDER = "openai"
PLANNER_MODEL = os.getenv("PLANNER_MODEL", "gpt-4.1")

# Composer LLM (multi-pass chunked generation with GPT-4.1)
COMPOSER_LLM_PROVIDER = "openai"
COMPOSER_MODEL = os.getenv("COMPOSER_MODEL", "gpt-4.1")


# gpt-4o-mini

# ============================================================================
# RUNTIME CONSTANTS
# ============================================================================

DEFAULT_CURRENCY = "INR"
TIMEZONE = "UTC"

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def setup_logging() -> None:
    """
    Configure application logging based on environment.
    
    - Dev: DEBUG level
    - Prod: INFO level
    - Format: [timestamp] [level] [logger_name] message
    """
    log_level = logging.DEBUG if ENV == "dev" else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

# ============================================================================
# VALIDATION
# ============================================================================

def _validate_config() -> None:
    """
    Validate critical configuration on module import.
    Raises RuntimeError or ValueError on misconfiguration.
    """
    # Validate OPENAI_API_KEY
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is required but not set. "
            "Please set it in your .env file or environment."
        )
    
    # Validate DATA_SOURCE
    if DATA_SOURCE not in {"dataset", "api"}:
        raise ValueError(
            f"Invalid DATA_SOURCE: '{DATA_SOURCE}'. "
            f"Must be either 'dataset' or 'api'."
        )
    
    # Validate ENV
    if ENV not in {"dev", "prod"}:
        raise ValueError(
            f"Invalid ENV: '{ENV}'. "
            f"Must be either 'dev' or 'prod'."
        )


# Execute validation on import
_validate_config()
