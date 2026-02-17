"""
TravelGuru v5 - Global Constants
Single source of truth for all cross-system constants.

This file is pure configuration - NO imports, NO logic, NO functions.
Used by: Planner, Router, Tools, Enrichment, Composer, Orchestrator, API, UI.

Design Rules:
- Use ALL_CAPS for constant names
- Group related constants with clear section headers
- Add brief comments for clarity
- Keep it stable and extensible
- Zero runtime dependencies
"""

# ============================================================================
# 1. DOMAIN NAMES
# ============================================================================
# Domain identifiers used across the system for categorization and routing

DOMAIN_FLIGHT = "flight"
DOMAIN_HOTEL = "hotel"
DOMAIN_PLACES = "places"
DOMAIN_WEATHER = "weather"
DOMAIN_BUDGET = "budget"

# All valid domains as a tuple (immutable)
ALL_DOMAINS = (
    DOMAIN_FLIGHT,
    DOMAIN_HOTEL,
    DOMAIN_PLACES,
    DOMAIN_WEATHER,
    DOMAIN_BUDGET,
)


# ============================================================================
# 2. TOOL NAMES
# ============================================================================
# Exact tool name strings used by planner output, router dispatch, and tool implementations

TOOL_SEARCH_FLIGHTS = "search_flights"
TOOL_SEARCH_HOTELS = "search_hotels"
TOOL_SEARCH_PLACES = "search_places"
TOOL_GET_WEATHER = "get_weather"
TOOL_COMPUTE_BUDGET = "compute_budget"

# All valid tool names
ALL_TOOLS = (
    TOOL_SEARCH_FLIGHTS,
    TOOL_SEARCH_HOTELS,
    TOOL_SEARCH_PLACES,
    TOOL_GET_WEATHER,
    TOOL_COMPUTE_BUDGET,
)


# ============================================================================
# 3. AGENT NAMES
# ============================================================================
# Agent identifiers for orchestration and logging

AGENT_PLANNER = "planner"
AGENT_COMPOSER = "composer"
AGENT_ORCHESTRATOR = "orchestrator"
AGENT_ENRICHER = "enricher"
AGENT_ROUTER = "router"

# All agents
ALL_AGENTS = (
    AGENT_PLANNER,
    AGENT_COMPOSER,
    AGENT_ORCHESTRATOR,
    AGENT_ENRICHER,
    AGENT_ROUTER,
)


# ============================================================================
# 4. SHARED SCHEMA FIELD NAMES
# ============================================================================
# Common JSON field names used across planner, tools, enrichment, composer

# Tool call structure
FIELD_TOOL_NAME = "tool_name"
FIELD_ARGUMENTS = "arguments"
FIELD_TOOL_CALLS = "tool_calls"

# Agent output structure
FIELD_REASONING = "reasoning"
FIELD_OUTPUT = "output"
FIELD_METADATA = "metadata"

# User context
FIELD_PREFERENCES = "preferences"
FIELD_CONTEXT = "context"

# Enrichment fields
FIELD_RANKING = "ranking"
FIELD_RANK = "rank"
FIELD_SCORE = "score"
FIELD_INSIGHTS = "insights"
FIELD_RECOMMENDATIONS = "recommendations"
FIELD_TAGS = "tags"
FIELD_SUMMARY = "summary"
FIELD_BEST_FOR = "best_for"

# Analysis fields
FIELD_PRICE_INTELLIGENCE = "price_intelligence"
FIELD_CONVENIENCE = "convenience"
FIELD_TIMING_ANALYSIS = "timing_analysis"
FIELD_MATCH_SCORE = "match_score"

# Market analysis
FIELD_MARKET_ANALYSIS = "market_analysis"
FIELD_TRAVEL_TIPS = "travel_tips"
FIELD_BEST_CHOICE = "best_choice"


# ============================================================================
# 5. USER PREFERENCE KEYS (NLP NORMALIZED)
# ============================================================================
# Normalized preference keys extracted from user queries

PREF_BUDGET = "budget"
PREF_TIME = "time"
PREF_COMFORT = "comfort"
PREF_CONVENIENCE = "convenience"
PREF_SPEED = "speed"
PREF_LAYOVER_TOLERANCE = "layover_tolerance"
PREF_TRAVEL_STYLE = "travel_style"
PREF_HOTEL_QUALITY = "hotel_quality"
PREF_ACTIVITY_DENSITY = "activity_density"
PREF_BUDGET_PREFERENCE = "budget_preference"
PREF_TIMING_PREFERENCE = "timing_preference"
PREF_TRAVELER_TYPE = "traveler_type"
PREF_BAGGAGE_SENSITIVE = "baggage_sensitive"
PREF_AVOID_LAYOVERS = "avoid_layovers"

# All preference keys
ALL_PREFERENCE_KEYS = (
    PREF_BUDGET,
    PREF_TIME,
    PREF_COMFORT,
    PREF_CONVENIENCE,
    PREF_SPEED,
    PREF_LAYOVER_TOLERANCE,
    PREF_TRAVEL_STYLE,
    PREF_HOTEL_QUALITY,
    PREF_ACTIVITY_DENSITY,
    PREF_BUDGET_PREFERENCE,
    PREF_TIMING_PREFERENCE,
    PREF_TRAVELER_TYPE,
    PREF_BAGGAGE_SENSITIVE,
    PREF_AVOID_LAYOVERS,
)


# ============================================================================
# 6. TRAVEL STYLES
# ============================================================================
# User travel style categories for personalization

STYLE_BACKPACKER = "backpacker"
STYLE_FAMILY = "family"
STYLE_LUXURY = "luxury"
STYLE_BUSINESS = "business"
STYLE_HONEYMOON = "honeymoon"
STYLE_SOLO = "solo"
STYLE_ADVENTURE = "adventure"
STYLE_RELAXATION = "relaxation"

# All travel styles
ALL_TRAVEL_STYLES = (
    STYLE_BACKPACKER,
    STYLE_FAMILY,
    STYLE_LUXURY,
    STYLE_BUSINESS,
    STYLE_HONEYMOON,
    STYLE_SOLO,
    STYLE_ADVENTURE,
    STYLE_RELAXATION,
)


# ============================================================================
# 7. PRICE CATEGORIES
# ============================================================================
# Price tier classifications for products and user preferences

PRICE_BUDGET = "budget"
PRICE_MODERATE = "moderate"
PRICE_PREMIUM = "premium"
PRICE_LUXURY = "luxury"

# All price categories
ALL_PRICE_CATEGORIES = (
    PRICE_BUDGET,
    PRICE_MODERATE,
    PRICE_PREMIUM,
    PRICE_LUXURY,
)


# ============================================================================
# 8. TIME BUCKETS
# ============================================================================
# Time-of-day segments for timing analysis

TIME_RED_EYE = "red-eye"
TIME_EARLY_MORNING = "early-morning"
TIME_MORNING = "morning"
TIME_AFTERNOON = "afternoon"
TIME_EVENING = "evening"
TIME_NIGHT = "night"

# All time buckets
ALL_TIME_BUCKETS = (
    TIME_RED_EYE,
    TIME_EARLY_MORNING,
    TIME_MORNING,
    TIME_AFTERNOON,
    TIME_EVENING,
    TIME_NIGHT,
)

# Time bucket hour ranges (for reference)
TIME_BUCKET_RANGES = {
    TIME_RED_EYE: (0, 5),          # 00:00 - 04:59
    TIME_EARLY_MORNING: (5, 8),     # 05:00 - 07:59
    TIME_MORNING: (8, 12),          # 08:00 - 11:59
    TIME_AFTERNOON: (12, 17),       # 12:00 - 16:59
    TIME_EVENING: (17, 21),         # 17:00 - 20:59
    TIME_NIGHT: (21, 24),           # 21:00 - 23:59
}


# ============================================================================
# 9. FLIGHT TAGS
# ============================================================================
# Smart tags for flight categorization and filtering

TAG_FLIGHT_CHEAPEST = "cheapest"
TAG_FLIGHT_FASTEST = "fastest"
TAG_FLIGHT_BEST_VALUE = "best-value"
TAG_FLIGHT_MOST_CONVENIENT = "most-convenient"
TAG_FLIGHT_DIRECT = "direct-flight"
TAG_FLIGHT_SHORT_LAYOVER = "short-layover"
TAG_FLIGHT_LONG_LAYOVER = "long-layover"
TAG_FLIGHT_MORNING_DEPARTURE = "morning-departure"
TAG_FLIGHT_EVENING_DEPARTURE = "evening-departure"
TAG_FLIGHT_RECOMMENDED = "recommended"
TAG_FLIGHT_BUDGET_FRIENDLY = "budget-friendly"
TAG_FLIGHT_PREMIUM = "premium"

# All flight tags
ALL_FLIGHT_TAGS = (
    TAG_FLIGHT_CHEAPEST,
    TAG_FLIGHT_FASTEST,
    TAG_FLIGHT_BEST_VALUE,
    TAG_FLIGHT_MOST_CONVENIENT,
    TAG_FLIGHT_DIRECT,
    TAG_FLIGHT_SHORT_LAYOVER,
    TAG_FLIGHT_LONG_LAYOVER,
    TAG_FLIGHT_MORNING_DEPARTURE,
    TAG_FLIGHT_EVENING_DEPARTURE,
    TAG_FLIGHT_RECOMMENDED,
    TAG_FLIGHT_BUDGET_FRIENDLY,
    TAG_FLIGHT_PREMIUM,
)


# ============================================================================
# 10. HOTEL TAGS
# ============================================================================
# Smart tags for hotel categorization and filtering

TAG_HOTEL_BEST_LOCATION = "best-location"
TAG_HOTEL_BEST_RATING = "best-rating"
TAG_HOTEL_BEST_VALUE = "best-value"
TAG_HOTEL_CHEAPEST = "cheapest"
TAG_HOTEL_LUXURY = "luxury"
TAG_HOTEL_FAMILY_FRIENDLY = "family-friendly"
TAG_HOTEL_BUSINESS = "business"
TAG_HOTEL_BOUTIQUE = "boutique"
TAG_HOTEL_CENTRAL = "central"
TAG_HOTEL_BEACH = "beach"
TAG_HOTEL_POOL = "pool"
TAG_HOTEL_SPA = "spa"

# All hotel tags
ALL_HOTEL_TAGS = (
    TAG_HOTEL_BEST_LOCATION,
    TAG_HOTEL_BEST_RATING,
    TAG_HOTEL_BEST_VALUE,
    TAG_HOTEL_CHEAPEST,
    TAG_HOTEL_LUXURY,
    TAG_HOTEL_FAMILY_FRIENDLY,
    TAG_HOTEL_BUSINESS,
    TAG_HOTEL_BOUTIQUE,
    TAG_HOTEL_CENTRAL,
    TAG_HOTEL_BEACH,
    TAG_HOTEL_POOL,
    TAG_HOTEL_SPA,
)


# ============================================================================
# 11. PLACES TAGS
# ============================================================================
# Smart tags for places categorization and filtering

TAG_PLACES_MUST_SEE = "must-see"
TAG_PLACES_HIDDEN_GEM = "hidden-gem"
TAG_PLACES_NATURE = "nature"
TAG_PLACES_CULTURE = "culture"
TAG_PLACES_ADVENTURE = "adventure"
TAG_PLACES_RELAXATION = "relaxation"
TAG_PLACES_SHOPPING = "shopping"
TAG_PLACES_FAMILY = "family"
TAG_PLACES_ROMANTIC = "romantic"
TAG_PLACES_HISTORICAL = "historical"
TAG_PLACES_MODERN = "modern"
TAG_PLACES_FREE = "free"
TAG_PLACES_PAID = "paid"
TAG_PLACES_INDOOR = "indoor"
TAG_PLACES_OUTDOOR = "outdoor"

# All places tags
ALL_PLACES_TAGS = (
    TAG_PLACES_MUST_SEE,
    TAG_PLACES_HIDDEN_GEM,
    TAG_PLACES_NATURE,
    TAG_PLACES_CULTURE,
    TAG_PLACES_ADVENTURE,
    TAG_PLACES_RELAXATION,
    TAG_PLACES_SHOPPING,
    TAG_PLACES_FAMILY,
    TAG_PLACES_ROMANTIC,
    TAG_PLACES_HISTORICAL,
    TAG_PLACES_MODERN,
    TAG_PLACES_FREE,
    TAG_PLACES_PAID,
    TAG_PLACES_INDOOR,
    TAG_PLACES_OUTDOOR,
)


# ============================================================================
# 12. WEATHER TAGS
# ============================================================================
# Weather condition tags for trip planning

TAG_WEATHER_SUNNY = "sunny"
TAG_WEATHER_RAINY = "rainy"
TAG_WEATHER_CLOUDY = "cloudy"
TAG_WEATHER_EXTREME = "extreme"
TAG_WEATHER_PLEASANT = "pleasant"
TAG_WEATHER_HOT = "hot"
TAG_WEATHER_COLD = "cold"
TAG_WEATHER_WINDY = "windy"
TAG_WEATHER_SNOWY = "snowy"

# All weather tags
ALL_WEATHER_TAGS = (
    TAG_WEATHER_SUNNY,
    TAG_WEATHER_RAINY,
    TAG_WEATHER_CLOUDY,
    TAG_WEATHER_EXTREME,
    TAG_WEATHER_PLEASANT,
    TAG_WEATHER_HOT,
    TAG_WEATHER_COLD,
    TAG_WEATHER_WINDY,
    TAG_WEATHER_SNOWY,
)


# ============================================================================
# 13. ENRICHMENT RANKING WEIGHTS
# ============================================================================
# Central tuning knobs for AI ranking algorithms
# These weights determine how different factors contribute to overall ranking scores
# Sum should typically equal 1.0 for normalized scoring

# Flight ranking weights
WEIGHT_FLIGHT_PRICE = 0.35
WEIGHT_FLIGHT_TIME = 0.25
WEIGHT_FLIGHT_CONVENIENCE = 0.25
WEIGHT_FLIGHT_COMFORT = 0.15

# Hotel ranking weights
WEIGHT_HOTEL_PRICE = 0.30
WEIGHT_HOTEL_RATING = 0.30
WEIGHT_HOTEL_LOCATION = 0.25
WEIGHT_HOTEL_AMENITIES = 0.15
WEIGHT_HOTEL_STARS = 0.30

# Places ranking weights
WEIGHT_PLACES_RATING = 0.40
WEIGHT_PLACES_POPULARITY = 0.25
WEIGHT_PLACES_RELEVANCE = 0.20
WEIGHT_PLACES_PROXIMITY = 0.15

# General weights (fallback)
WEIGHT_PRICE = 0.35
WEIGHT_TIME = 0.25
WEIGHT_CONVENIENCE = 0.20
WEIGHT_COMFORT = 0.10
WEIGHT_RATING = 0.10
WEIGHT_LOCATION = 0.10


# ============================================================================
# 14. SYSTEM LIMITS
# ============================================================================
# Hard limits for system operations to prevent abuse and control costs

# Search result limits
MAX_FLIGHT_RESULTS = 50
MAX_HOTEL_RESULTS = 50
MAX_PLACES_RESULTS = 100
MAX_WEATHER_DAYS = 14

# Itinerary limits
MAX_ITINERARY_DAYS = 30
MIN_ITINERARY_DAYS = 1

# Enrichment limits
MAX_ENRICHED_OPTIONS = 20
MAX_INSIGHTS_PER_OPTION = 10
MAX_RECOMMENDATIONS_PER_OPTION = 10

# Budget limits
MAX_BUDGET_INR = 10000000  # 1 crore INR
MIN_BUDGET_INR = 1000

# Traveler limits
MAX_TRAVELERS = 20
MIN_TRAVELERS = 1

# Query limits
MAX_QUERY_LENGTH = 2000
MAX_TOOL_CALLS = 10

# Timeout limits (seconds)
TIMEOUT_API_CALL = 30
TIMEOUT_ENRICHMENT = 60
TIMEOUT_TOTAL_REQUEST = 180


# ============================================================================
# 15. DEFAULTS
# ============================================================================
# Default values used throughout the system

# Currency and localization
DEFAULT_CURRENCY = "INR"
DEFAULT_LANGUAGE = "en"
DEFAULT_COUNTRY = "IN"

# Travelers
DEFAULT_ADULTS = 1
DEFAULT_CHILDREN = 0
DEFAULT_INFANTS = 0

# Search defaults
DEFAULT_FLIGHT_LIMIT = 5
DEFAULT_HOTEL_LIMIT = 5
DEFAULT_PLACES_LIMIT = 10

# Sorting defaults
DEFAULT_SORT_BY_PRICE = True
DEFAULT_SORT_BY_RATING = True

# Enrichment defaults
DEFAULT_ENRICHMENT_ENABLED = True
DEFAULT_USER_CONTEXT = {}

# Time defaults
DEFAULT_CHECKIN_TIME = "14:00"
DEFAULT_CHECKOUT_TIME = "11:00"


# ============================================================================
# 16. SCORING RANGES
# ============================================================================
# Score boundaries for normalization and comparison

# General score range
SCORE_MIN = 0.0
SCORE_MAX = 10.0

# Match score range (percentile-based)
MATCH_SCORE_MIN = 0.0
MATCH_SCORE_MAX = 100.0

# Rating ranges
RATING_MIN = 0.0
RATING_MAX = 5.0

# Convenience score ranges
CONVENIENCE_MIN = 0.0
CONVENIENCE_MAX = 10.0

# Value score ranges
VALUE_SCORE_MIN = 0.0
VALUE_SCORE_MAX = 10.0

# Quality thresholds
SCORE_EXCELLENT = 8.0
SCORE_GOOD = 6.0
SCORE_FAIR = 4.0
SCORE_POOR = 2.0


# ============================================================================
# 17. INTERNAL PIPELINE KEYS
# ============================================================================
# Keys for tracking data through the processing pipeline

PIPELINE_RAW = "raw"
PIPELINE_NORMALIZED = "normalized"
PIPELINE_ENRICHED = "enriched"
PIPELINE_COMPOSED = "composed"
PIPELINE_FINAL = "final"

# Pipeline stages (ordered)
ALL_PIPELINE_STAGES = (
    PIPELINE_RAW,
    PIPELINE_NORMALIZED,
    PIPELINE_ENRICHED,
    PIPELINE_COMPOSED,
    PIPELINE_FINAL,
)

# Pipeline metadata keys
PIPELINE_KEY_STAGE = "pipeline_stage"
PIPELINE_KEY_TIMESTAMP = "pipeline_timestamp"
PIPELINE_KEY_VERSION = "pipeline_version"
PIPELINE_KEY_SOURCE = "pipeline_source"


# ============================================================================
# 18. LOGGING / DEBUG TAGS
# ============================================================================
# Structured logging tags for observability and debugging

LOG_PLANNER = "planner"
LOG_TOOLS = "tools"
LOG_ENRICHMENT = "enrichment"
LOG_COMPOSER = "composer"
LOG_ORCHESTRATOR = "orchestrator"
LOG_ROUTER = "router"
LOG_API = "api"
LOG_DATABASE = "database"

# Log levels (matching Python logging)
LOG_DEBUG = "DEBUG"
LOG_INFO = "INFO"
LOG_WARNING = "WARNING"
LOG_ERROR = "ERROR"
LOG_CRITICAL = "CRITICAL"

# All log tags
ALL_LOG_TAGS = (
    LOG_PLANNER,
    LOG_TOOLS,
    LOG_ENRICHMENT,
    LOG_COMPOSER,
    LOG_ORCHESTRATOR,
    LOG_ROUTER,
    LOG_API,
    LOG_DATABASE,
)


# ============================================================================
# 19. ERROR CATEGORIES
# ============================================================================
# Error classification for handling and logging

ERROR_VALIDATION = "validation_error"
ERROR_TOOL = "tool_error"
ERROR_API = "api_error"
ERROR_TIMEOUT = "timeout_error"
ERROR_INTERNAL = "internal_error"
ERROR_NOT_FOUND = "not_found_error"
ERROR_RATE_LIMIT = "rate_limit_error"
ERROR_AUTH = "auth_error"
ERROR_NETWORK = "network_error"
ERROR_PARSING = "parsing_error"

# All error categories
ALL_ERROR_CATEGORIES = (
    ERROR_VALIDATION,
    ERROR_TOOL,
    ERROR_API,
    ERROR_TIMEOUT,
    ERROR_INTERNAL,
    ERROR_NOT_FOUND,
    ERROR_RATE_LIMIT,
    ERROR_AUTH,
    ERROR_NETWORK,
    ERROR_PARSING,
)


# ============================================================================
# 20. INSIGHT AND RECOMMENDATION TYPES
# ============================================================================
# Types for categorizing insights and recommendations

# Insight types
INSIGHT_TYPE_ADVANTAGE = "advantage"
INSIGHT_TYPE_CONSIDERATION = "consideration"
INSIGHT_TYPE_TIP = "tip"
INSIGHT_TYPE_WARNING = "warning"
INSIGHT_TYPE_INFO = "info"

# All insight types
ALL_INSIGHT_TYPES = (
    INSIGHT_TYPE_ADVANTAGE,
    INSIGHT_TYPE_CONSIDERATION,
    INSIGHT_TYPE_TIP,
    INSIGHT_TYPE_WARNING,
    INSIGHT_TYPE_INFO,
)

# Recommendation sentiments
SENTIMENT_POSITIVE = "positive"
SENTIMENT_NEUTRAL = "neutral"
SENTIMENT_NEGATIVE = "negative"

# All sentiments
ALL_SENTIMENTS = (
    SENTIMENT_POSITIVE,
    SENTIMENT_NEUTRAL,
    SENTIMENT_NEGATIVE,
)

# Recommendation categories
REC_CATEGORY_TIMING = "timing"
REC_CATEGORY_PRICE = "price"
REC_CATEGORY_CONVENIENCE = "convenience"
REC_CATEGORY_DURATION = "duration"
REC_CATEGORY_AIRLINE = "airline"
REC_CATEGORY_LOCATION = "location"
REC_CATEGORY_AMENITIES = "amenities"
REC_CATEGORY_RATING = "rating"
REC_CATEGORY_COMFORT = "comfort"

# All recommendation categories
ALL_REC_CATEGORIES = (
    REC_CATEGORY_TIMING,
    REC_CATEGORY_PRICE,
    REC_CATEGORY_CONVENIENCE,
    REC_CATEGORY_DURATION,
    REC_CATEGORY_AIRLINE,
    REC_CATEGORY_LOCATION,
    REC_CATEGORY_AMENITIES,
    REC_CATEGORY_RATING,
    REC_CATEGORY_COMFORT,
)


# ============================================================================
# 21. ADDITIONAL DOMAIN-SPECIFIC CONSTANTS
# ============================================================================

# Flight-specific
FLIGHT_CLASS_ECONOMY = "economy"
FLIGHT_CLASS_PREMIUM_ECONOMY = "premium_economy"
FLIGHT_CLASS_BUSINESS = "business"
FLIGHT_CLASS_FIRST = "first"

ALL_FLIGHT_CLASSES = (
    FLIGHT_CLASS_ECONOMY,
    FLIGHT_CLASS_PREMIUM_ECONOMY,
    FLIGHT_CLASS_BUSINESS,
    FLIGHT_CLASS_FIRST,
)

# Stop categories
STOPS_DIRECT = 0
STOPS_ONE = 1
STOPS_TWO_PLUS = 2

# Hotel star ratings
HOTEL_STARS_MIN = 1
HOTEL_STARS_MAX = 5

# Place categories
PLACE_CATEGORY_ATTRACTION = "attraction"
PLACE_CATEGORY_RESTAURANT = "restaurant"
PLACE_CATEGORY_SHOPPING = "shopping"
PLACE_CATEGORY_PARK = "park"
PLACE_CATEGORY_MUSEUM = "museum"
PLACE_CATEGORY_BEACH = "beach"

# Weather conditions
WEATHER_SUNNY = "sunny"
WEATHER_CLOUDY = "cloudy"
WEATHER_RAINY = "rainy"
WEATHER_SNOWY = "snowy"
WEATHER_STORMY = "stormy"
WEATHER_CLEAR = "clear"


# ============================================================================
# 22. SYSTEM METADATA
# ============================================================================
# System version and build information

SYSTEM_NAME = "TravelGuru"
SYSTEM_VERSION = "v5"
SYSTEM_FULL_NAME = f"{SYSTEM_NAME} {SYSTEM_VERSION}"

# API versioning
API_VERSION_V1 = "v1"
API_CURRENT_VERSION = API_VERSION_V1

# Data schema versions
SCHEMA_VERSION_FLIGHT = "1.0"
SCHEMA_VERSION_HOTEL = "1.0"
SCHEMA_VERSION_PLACE = "1.0"
SCHEMA_VERSION_WEATHER = "1.0"


# ============================================================================
# 23. CONFIGURATION FLAGS
# ============================================================================
# Feature flags and configuration switches

# Feature flags
FEATURE_ENRICHMENT_ENABLED = True
FEATURE_CACHING_ENABLED = True
FEATURE_PARALLEL_TOOLS = True
FEATURE_AUTO_RETRY = True

# Debug flags
DEBUG_LOG_RAW_RESPONSES = False
DEBUG_LOG_ENRICHMENT_DETAILS = False
DEBUG_SIMULATE_ERRORS = False

# Performance flags
ENABLE_RESULT_CACHING = True
ENABLE_COMPRESSION = False
ENABLE_METRICS = True


# ============================================================================
# END OF CONSTANTS
# ============================================================================
# This file should remain pure constants with no runtime logic.
# Any computed values should be derived in dedicated utility modules.
