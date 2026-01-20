"""
Hotel Intent Extractor - Natural Language Understanding for Hotel Queries

Extracts structured intent from free-form natural language hotel queries.
Supports queries like:
- "Find cheap hotels in Mumbai with pool and wifi"
- "I need a luxury 5-star hotel in Goa near the beach"
- "Book a family-friendly hotel in Delhi under 3000 per night"
- "Show me business hotels with meeting rooms in Bangalore"

SAFETY RULES:
- Never invent preferences if not mentioned
- Only include preferences that were explicitly stated or clearly implied
- Return empty preferences {} if none detected
- Default to no star filter if not specified
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field

from backend.app.shared.constants import (
    PREF_BUDGET_PREFERENCE,
    PREF_HOTEL_QUALITY,
    PRICE_BUDGET,
    PRICE_MODERATE,
    PRICE_PREMIUM,
    PRICE_LUXURY,
)


# ============================================================================
# INTENT SCHEMAS
# ============================================================================

class HotelIntent(BaseModel):
    """
    Structured representation of hotel search intent extracted from natural language.
    """
    city: str = Field(..., description="City to search hotels in")
    check_in: Optional[str] = Field(None, description="Check-in date in YYYY-MM-DD format")
    check_out: Optional[str] = Field(None, description="Check-out date in YYYY-MM-DD format")
    guests: int = Field(1, description="Number of guests")
    max_price: Optional[int] = Field(None, description="Maximum price per night in INR")
    min_stars: Optional[int | float] = Field(None, description="Minimum star rating (1-5, supports decimals like 3.5)")
    amenities: List[str] = Field(default_factory=list, description="Required amenities")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences extracted from query")
    
    model_config = {"extra": "forbid"}


class ExtractedPreferences(BaseModel):
    """
    User preferences extracted from natural language query.
    Only includes preferences that were explicitly mentioned or clearly implied.
    """
    budget_preference: Optional[str] = Field(None, description="Budget tier: budget, moderate, premium, luxury")
    hotel_quality: Optional[str] = Field(None, description="Quality expectation: basic, standard, high, luxury")
    location_preference: Optional[str] = Field(None, description="Location preference: central, beach, quiet, business-district")
    traveler_type: Optional[str] = Field(None, description="Type of traveler: family, business, couple, solo")
    
    model_config = {"extra": "forbid"}


# ============================================================================
# NLP KEYWORD PATTERNS
# ============================================================================

# Budget preference keywords
BUDGET_KEYWORDS = {
    PRICE_BUDGET: [
        "cheap", "cheapest", "budget", "affordable", "economical", "low cost",
        "inexpensive", "save money", "bargain", "under"
    ],
    PRICE_MODERATE: [
        "moderate", "reasonable", "fair price", "mid-range", "average", "decent"
    ],
    PRICE_PREMIUM: [
        "premium", "upscale", "high-end", "quality", "nice", "good"
    ],
    PRICE_LUXURY: [
        "luxury", "luxurious", "5-star", "five star", "finest", "best", "top",
        "deluxe", "exclusive", "elite"
    ]
}

# Quality keywords
QUALITY_KEYWORDS = {
    "basic": ["basic", "simple", "budget", "no-frills"],
    "standard": ["standard", "decent", "good", "comfortable"],
    "high": ["high quality", "excellent", "great", "superior", "premium"],
    "luxury": ["luxury", "luxurious", "5-star", "five star", "deluxe", "finest"]
}

# Location preference keywords
LOCATION_KEYWORDS = {
    "central": ["central", "downtown", "city center", "main area", "near airport"],
    "beach": ["beach", "beachfront", "seaside", "oceanfront", "near beach"],
    "quiet": ["quiet", "peaceful", "secluded", "away from noise", "serene"],
    "business-district": ["business district", "financial district", "commercial area"]
}

# Traveler type keywords
TRAVELER_KEYWORDS = {
    "family": ["family", "kids", "children", "family-friendly"],
    "business": ["business", "work", "conference", "meeting"],
    "couple": ["couple", "romantic", "honeymoon", "anniversary"],
    "solo": ["solo", "alone", "single"]
}

# Common amenity keywords and their variations
AMENITY_KEYWORDS = {
    "wifi": ["wifi", "wi-fi", "internet", "wireless"],
    "pool": ["pool", "swimming pool", "swimming"],
    "parking": ["parking", "car park", "valet"],
    "gym": ["gym", "fitness", "exercise", "workout"],
    "spa": ["spa", "massage", "wellness"],
    "restaurant": ["restaurant", "dining", "food"],
    "bar": ["bar", "lounge", "pub"],
    "room service": ["room service"],
    "breakfast": ["breakfast", "morning meal"],
    "air conditioning": ["ac", "air conditioning", "air conditioned", "a/c"],
    "business center": ["business center", "business facilities"],
    "meeting room": ["meeting room", "conference room", "meeting facilities"],
    "concierge": ["concierge"],
    "beach access": ["beach access", "private beach"],
    "free cancellation": ["free cancellation", "flexible booking"]
}

# Star rating patterns (ordered from most specific to least specific)
STAR_PATTERNS = [
    # Fractional ratings (e.g., "3.5 star", "4.5-star")
    (r'(\d\.\d)\s*-?star', lambda m: float(m.group(1))),
    # Word-based ratings (must come before single digit to avoid partial matches)
    (r'\b(five)\s*-?star', lambda m: 5),
    (r'\b(four)\s*-?star', lambda m: 4),
    (r'\b(three)\s*-?star', lambda m: 3),
    (r'\b(two)\s*-?star', lambda m: 2),
    (r'\b(one)\s*-?star', lambda m: 1),
    # Single digit ratings (e.g., "5 star", "4-star")
    (r'\b([1-5])\s*-?star', lambda m: int(m.group(1))),
]

# Price amount patterns
PRICE_PATTERNS = [
    r'under\s+(\d+)',
    r'below\s+(\d+)',
    r'less than\s+(\d+)',
    r'maximum\s+(\d+)',
    r'max\s+(\d+)',
    r'up to\s+(\d+)',
    r'(\d+)\s*rupees',
    r'(\d+)\s*rs',
    r'(\d+)\s*inr',
]

# Guest count patterns
GUEST_PATTERNS = [
    r'(\d+)\s+guests?',
    r'(\d+)\s+people',
    r'(\d+)\s+persons?',
    r'for\s+(\d+)',
]

# Common city name variations (Indian cities)
CITY_ALIASES = {
    "delhi": ["delhi", "new delhi", "del"],
    "mumbai": ["mumbai", "bombay", "bom"],
    "bangalore": ["bangalore", "bengaluru", "blr"],
    "chennai": ["chennai", "madras", "maa"],
    "kolkata": ["kolkata", "calcutta", "ccu"],
    "hyderabad": ["hyderabad", "hyd"],
    "goa": ["goa", "goi"],
    "pune": ["pune", "pnq"],
    "jaipur": ["jaipur", "jai"],
    "ahmedabad": ["ahmedabad", "amd"],
    "kochi": ["kochi", "cochin", "cok"],
    "trivandrum": ["trivandrum", "thiruvananthapuram", "trv"]
}

# Relative date keywords
DATE_KEYWORDS = {
    "today": 0,
    "tomorrow": 1,
    "day after tomorrow": 2,
    "next week": 7,
    "next month": 30,
}

# Month names mapping
MONTH_NAMES = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}


# ============================================================================
# EXTRACTION FUNCTIONS
# ============================================================================

def extract_city(query: str) -> Optional[str]:
    """
    Extract city name from query.
    
    Examples:
    - "hotels in Mumbai" → "Mumbai"
    - "find hotels near Delhi" → "Delhi"
    - "Goa hotels" → "Goa"
    """
    query_lower = query.lower()
    
    # First, try to find any known city name (most reliable)
    for canonical, aliases in CITY_ALIASES.items():
        for alias in aliases:
            # Use word boundaries to avoid matching parts of words
            if re.search(r'\b' + re.escape(alias) + r'\b', query_lower):
                return canonical.title()
    
    # Pattern 1: "in <city>"
    match = re.search(r'\bin\s+([a-z]+(?:\s+[a-z]+)?)', query_lower)
    if match:
        city_candidate = match.group(1).strip()
        # Skip common words that are not cities
        if city_candidate not in ["the", "a", "an", "that", "this"]:
            normalized = normalize_city_name(city_candidate)
            if normalized:
                return normalized.title()
    
    # Pattern 2: "near <city>"
    match = re.search(r'\bnear\s+([a-z]+(?:\s+[a-z]+)?)', query_lower)
    if match:
        city_candidate = match.group(1).strip()
        if city_candidate not in ["the", "a", "an", "that", "this"]:
            normalized = normalize_city_name(city_candidate)
            if normalized:
                return normalized.title()
    
    # Pattern 3: "<city> hotels"
    match = re.search(r'([a-z]+(?:\s+[a-z]+)?)\s+hotels?', query_lower)
    if match:
        city_candidate = match.group(1).strip()
        # Skip modifiers that commonly appear before "hotels"
        if city_candidate not in ["cheap", "luxury", "budget", "good", "nice", "best", "family", "friendly"]:
            normalized = normalize_city_name(city_candidate)
            if normalized:
                return normalized.title()
    
    return None


def normalize_city_name(city: str) -> Optional[str]:
    """Normalize city name using CITY_ALIASES."""
    city_lower = city.lower().strip()
    
    for canonical, aliases in CITY_ALIASES.items():
        if city_lower in aliases:
            return canonical
    
    # If not in aliases, return as-is if it looks like a valid city name
    if len(city_lower) >= 3 and city_lower.isalpha():
        return city_lower
    
    return None


def extract_dates(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract check-in and check-out dates from query.
    
    Returns:
        Tuple of (check_in, check_out) in YYYY-MM-DD format
    """
    query_lower = query.lower()
    today = datetime.now()
    
    check_in = None
    check_out = None
    
    # Check for relative dates
    for keyword, days_offset in DATE_KEYWORDS.items():
        if keyword in query_lower:
            check_in = (today + timedelta(days=days_offset)).strftime("%Y-%m-%d")
            # Default checkout is next day
            check_out = (today + timedelta(days=days_offset + 1)).strftime("%Y-%m-%d")
            break
    
    # Check for explicit dates (DD Month YYYY or DD-MM-YYYY)
    date_pattern = r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{4})'
    match = re.search(date_pattern, query_lower)
    if match:
        day = int(match.group(1))
        month = MONTH_NAMES[match.group(2)]
        year = int(match.group(3))
        check_in = f"{year:04d}-{month:02d}-{day:02d}"
        # Default checkout is next day
        checkout_date = datetime(year, month, day) + timedelta(days=1)
        check_out = checkout_date.strftime("%Y-%m-%d")
    
    # Check for ISO format dates
    iso_pattern = r'(\d{4}-\d{2}-\d{2})'
    matches = re.findall(iso_pattern, query)
    if len(matches) >= 1:
        check_in = matches[0]
    if len(matches) >= 2:
        check_out = matches[1]
    
    return check_in, check_out


def extract_guests(query: str) -> int:
    """
    Extract number of guests from query.
    
    Default: 1 if not specified
    """
    query_lower = query.lower()
    
    for pattern in GUEST_PATTERNS:
        match = re.search(pattern, query_lower)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass
    
    return 1


def extract_max_price(query: str) -> Optional[int]:
    """
    Extract maximum price per night from query.
    
    Examples:
    - "under 3000" → 3000
    - "below 5000 rupees" → 5000
    - "max 2500" → 2500
    """
    query_lower = query.lower()
    
    for pattern in PRICE_PATTERNS:
        match = re.search(pattern, query_lower)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass
    
    return None


def extract_min_stars(query: str) -> Optional[int | float]:
    """
    Extract minimum star rating from query.
    
    Examples:
    - "5 star hotel" → 5
    - "4-star" → 4
    - "five star" → 5
    - "3.5 star" → 3.5
    - "4.5-star" → 4.5
    
    Returns:
        Integer or float star rating, or None if not found
    """
    query_lower = query.lower()
    
    for pattern, extractor in STAR_PATTERNS:
        match = re.search(pattern, query_lower)
        if match:
            rating = extractor(match)
            # Clamp to valid range 1-5
            if rating < 1:
                return 1
            elif rating > 5:
                return 5
            return rating
    
    return None


def extract_amenities(query: str) -> List[str]:
    """
    Extract required amenities from query.
    
    Examples:
    - "with pool and wifi" → ["pool", "wifi"]
    - "spa and gym" → ["spa", "gym"]
    """
    query_lower = query.lower()
    found_amenities = []
    
    for amenity, keywords in AMENITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                found_amenities.append(amenity)
                break
    
    return found_amenities


def extract_budget_preference(query: str) -> Optional[str]:
    """Extract budget preference from query."""
    query_lower = query.lower()
    
    # Check in order of specificity (luxury first, then budget)
    for category, keywords in sorted(BUDGET_KEYWORDS.items(), key=lambda x: len(x[1]), reverse=True):
        for keyword in keywords:
            if keyword in query_lower:
                return category
    
    return None


def extract_quality_preference(query: str) -> Optional[str]:
    """Extract hotel quality preference from query."""
    query_lower = query.lower()
    
    for quality, keywords in QUALITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                return quality
    
    return None


def extract_location_preference(query: str) -> Optional[str]:
    """Extract location preference from query."""
    query_lower = query.lower()
    
    for location, keywords in LOCATION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                return location
    
    return None


def extract_traveler_type(query: str) -> Optional[str]:
    """Extract traveler type from query."""
    query_lower = query.lower()
    
    for traveler_type, keywords in TRAVELER_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                return traveler_type
    
    return None


def extract_preferences(query: str) -> Dict[str, Any]:
    """
    Extract all user preferences from query.
    
    Returns only preferences that are explicitly mentioned or clearly implied.
    """
    preferences = {}
    
    budget_pref = extract_budget_preference(query)
    if budget_pref:
        preferences[PREF_BUDGET_PREFERENCE] = budget_pref
    
    quality_pref = extract_quality_preference(query)
    if quality_pref:
        preferences[PREF_HOTEL_QUALITY] = quality_pref
    
    location_pref = extract_location_preference(query)
    if location_pref:
        preferences["location_preference"] = location_pref
    
    traveler_type = extract_traveler_type(query)
    if traveler_type:
        preferences["traveler_type"] = traveler_type
    
    return preferences


# ============================================================================
# MAIN EXTRACTION FUNCTION
# ============================================================================

def extract_hotel_intent(query: str) -> HotelIntent:
    """
    Extract structured hotel search intent from natural language query.
    
    This is the main entry point for hotel NLP processing.
    
    Args:
        query: Natural language hotel search query
    
    Returns:
        HotelIntent with extracted structured parameters
    
    Raises:
        ValueError: If city cannot be extracted from query
    
    Examples:
        >>> intent = extract_hotel_intent("Find cheap hotels in Mumbai with pool")
        >>> intent.city
        "Mumbai"
        >>> intent.amenities
        ["pool"]
        >>> intent.preferences["budget_preference"]
        "budget"
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")
    
    query = query.strip()
    
    # Extract city (required)
    city = extract_city(query)
    if not city:
        raise ValueError("Could not extract city from query. Please specify a city.")
    
    # Extract dates
    check_in, check_out = extract_dates(query)
    
    # Extract guests
    guests = extract_guests(query)
    
    # Extract price
    max_price = extract_max_price(query)
    
    # Extract stars
    min_stars = extract_min_stars(query)
    
    # Extract amenities
    amenities = extract_amenities(query)
    
    # Extract preferences
    preferences = extract_preferences(query)
    
    return HotelIntent(
        city=city,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        max_price=max_price,
        min_stars=min_stars,
        amenities=amenities,
        preferences=preferences
    )


# ============================================================================
# EXTRACTOR CLASS (for OOP usage)
# ============================================================================

class HotelIntentExtractor:
    """
    Object-oriented interface for hotel intent extraction.
    Use this when you need stateful extraction or custom configuration.
    """
    
    def __init__(self):
        """Initialize the extractor."""
        pass
    
    def extract(self, query: str) -> HotelIntent:
        """
        Extract intent from query.
        
        Args:
            query: Natural language hotel search query
        
        Returns:
            HotelIntent with extracted parameters
        """
        return extract_hotel_intent(query)
    
    def extract_preferences(self, query: str) -> ExtractedPreferences:
        """
        Extract only preferences from query.
        
        Args:
            query: Natural language query
        
        Returns:
            ExtractedPreferences object
        """
        prefs = extract_preferences(query)
        
        return ExtractedPreferences(
            budget_preference=prefs.get(PREF_BUDGET_PREFERENCE),
            hotel_quality=prefs.get(PREF_HOTEL_QUALITY),
            location_preference=prefs.get("location_preference"),
            traveler_type=prefs.get("traveler_type")
        )
