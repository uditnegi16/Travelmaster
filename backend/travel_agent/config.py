"""
Configuration settings for the Travel Agent system.

This module defines global configuration constants and ensures consistency
across all components of the travel planning system.
"""

# ============================================================================
# PRICE UNIT STANDARDIZATION
# ============================================================================
# CRITICAL: All adapters (dataset and API) MUST produce integer prices in INR.
# 
# Dataset adapters: Parse price fields directly as integers (already in INR).
# API adapters: Convert API responses to integer INR before creating schemas.
# 
# The normalized schemas (FlightOption, HotelOption, etc.) expect:
# - price: int (INR rupees, not paise)
# - Example: ₹2,907 → 2907 (integer)
# 
# DO NOT use paise or smallest currency units. Use whole rupees.
# ============================================================================

CURRENCY_CODE = "INR"
CURRENCY_SYMBOL = "₹"

# ============================================================================
# TIMEZONE STANDARDIZATION
# ============================================================================
# All datetime objects MUST be timezone-aware UTC.
# Adapters must convert local times to UTC before creating FlightOption schemas.
# ============================================================================

DEFAULT_TIMEZONE = "UTC"

# ============================================================================
# VALIDATION SETTINGS
# ============================================================================

# Enable strict itinerary validation by default
STRICT_ITINERARY_VALIDATION = True

# Hotel star rating bounds
MIN_HOTEL_STARS = 1
MAX_HOTEL_STARS = 5

# Rating bounds for places
MIN_PLACE_RATING = 0.0
MAX_PLACE_RATING = 5.0

# ============================================================================
# DATA SOURCES
# ============================================================================

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data source configuration
DATA_SOURCE = os.getenv("DATA_SOURCE", "dataset")  # "dataset" or "api"
VALID_DATA_SOURCES = {"dataset", "api"}

# LLM provider configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" or "openai"
VALID_LLM_PROVIDERS = {"gemini", "openai"}

# Dataset paths (relative to project root)
DATASETS_DIR = PROJECT_ROOT / "backend" / "data"
FLIGHTS_DATASET_PATH = DATASETS_DIR / "flights.json"
HOTELS_DATASET_PATH = DATASETS_DIR / "hotels.json"
PLACES_DATASET_PATH = DATASETS_DIR / "places.json"

# API keys (loaded from environment variables)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Price and datetime configuration
DEFAULT_CURRENCY = "INR"
TIMEZONE = "UTC"

# ============================================================================
# CACHING CONFIGURATION
# ============================================================================

# Cache TTL (Time To Live) for API responses in seconds
# Used when DATA_SOURCE="api" to cache API responses and reduce API calls
# Dataset mode uses permanent caching (no TTL) since data is static
API_CACHE_TTL = int(os.getenv("API_CACHE_TTL", "3600"))  # Default: 1 hour

# Maximum number of cached entries
CACHE_MAXSIZE = int(os.getenv("CACHE_MAXSIZE", "128"))  # Default: 128 entries

# ============================================================================
# FUZZY MATCHING CONFIGURATION
# ============================================================================

# Enable fuzzy matching for city names
# When True, searches will find approximate matches (e.g., "Mumbi" → "Mumbai")
ENABLE_FUZZY_MATCHING = os.getenv("ENABLE_FUZZY_MATCHING", "true").lower() == "true"

# Minimum similarity score for fuzzy matching (0.0 to 1.0)
# Higher values require closer matches (0.8 = 80% similarity)
FUZZY_MATCH_THRESHOLD = float(os.getenv("FUZZY_MATCH_THRESHOLD", "0.75"))

# Maximum number of fuzzy match suggestions to return
FUZZY_MATCH_MAX_SUGGESTIONS = int(os.getenv("FUZZY_MATCH_MAX_SUGGESTIONS", "3"))


def validate_config():
    """Validate configuration settings and raise clear errors if invalid."""
    
    # Validate DATA_SOURCE
    if DATA_SOURCE not in VALID_DATA_SOURCES:
        raise ValueError(
            f"Invalid DATA_SOURCE '{DATA_SOURCE}'. "
            f"Must be one of: {', '.join(VALID_DATA_SOURCES)}"
        )
    
    # Validate LLM_PROVIDER
    if LLM_PROVIDER not in VALID_LLM_PROVIDERS:
        raise ValueError(
            f"Invalid LLM_PROVIDER '{LLM_PROVIDER}'. "
            f"Must be one of: {', '.join(VALID_LLM_PROVIDERS)}"
        )
    
    # Validate API keys when using API data source
    if DATA_SOURCE == "api":
        if LLM_PROVIDER == "gemini" and not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required when "
                "DATA_SOURCE='api' and LLM_PROVIDER='gemini'"
            )
        if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required when "
                "DATA_SOURCE='api' and LLM_PROVIDER='openai'"
            )
    
    # Validate dataset paths when using dataset source
    if DATA_SOURCE == "dataset":
        if not FLIGHTS_DATASET_PATH.exists():
            raise FileNotFoundError(f"Flights dataset not found at {FLIGHTS_DATASET_PATH}")
        if not HOTELS_DATASET_PATH.exists():
            raise FileNotFoundError(f"Hotels dataset not found at {HOTELS_DATASET_PATH}")
        if not PLACES_DATASET_PATH.exists():
            raise FileNotFoundError(f"Places dataset not found at {PLACES_DATASET_PATH}")


def get_llm_api_key():
    """Return the appropriate API key based on LLM_PROVIDER."""
    if LLM_PROVIDER == "gemini":
        return GEMINI_API_KEY
    elif LLM_PROVIDER == "openai":
        return OPENAI_API_KEY
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")


# Validate configuration on module import
validate_config()
