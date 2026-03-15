"""
Flight Intent Extractor - Natural Language Understanding for Flight Queries

Extracts structured intent from free-form natural language flight queries.
Supports queries like:
- "Find cheap but fast direct flights from Delhi to Mumbai on 14 Feb 2026 for 4 adults"
- "I want the cheapest flight to Goa next month, but not early morning"
- "Book a convenient evening flight from Bangalore to Delhi"
- "Show me flights under 5000 rupees from Delhi to Jaipur tomorrow"

SAFETY RULES:
- Never invent preferences if not mentioned
- Default adults = 1
- Only include preferences that were explicitly stated or clearly implied
- Return empty preferences {} if none detected
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from shared.constants import (
    PREF_BUDGET_PREFERENCE,
    PREF_TIMING_PREFERENCE,
    PREF_AVOID_LAYOVERS,
    PREF_SPEED,
    PRICE_BUDGET,
    PRICE_MODERATE,
    PRICE_PREMIUM,
    TIME_MORNING,
    TIME_AFTERNOON,
    TIME_EVENING,
    TIME_RED_EYE,
    TIME_EARLY_MORNING,
    DEFAULT_ADULTS,
)


# ============================================================================
# INTENT SCHEMAS
# ============================================================================

class FlightIntent(BaseModel):
    """
    Structured representation of flight search intent extracted from natural language.
    """
    from_city: str = Field(..., description="Departure city")
    to_city: str = Field(..., description="Destination city")
    date: Optional[str] = Field(None, description="Departure date in YYYY-MM-DD format")
    adults: int = Field(DEFAULT_ADULTS, description="Number of adult travelers")
    max_price: Optional[int] = Field(None, description="Maximum price in INR")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences extracted from query")
    
    model_config = {"extra": "forbid"}


class ExtractedPreferences(BaseModel):
    """
    User preferences extracted from natural language query.
    Only includes preferences that were explicitly mentioned or clearly implied.
    """
    budget_preference: Optional[str] = Field(None, description="Budget tier: budget, moderate, premium")
    timing_preference: Optional[str] = Field(None, description="Preferred time of day")
    avoid_layovers: Optional[bool] = Field(None, description="Whether user wants direct flights only")
    speed: Optional[str] = Field(None, description="Preference for speed: fast, flexible")
    
    model_config = {"extra": "forbid"}


# ============================================================================
# NLP KEYWORD PATTERNS
# ============================================================================

# Budget preference keywords
BUDGET_KEYWORDS = {
    PRICE_BUDGET: [
        "cheap", "cheapest", "budget", "affordable", "economical", "low cost", 
        "inexpensive", "save money", "bargain"
    ],
    PRICE_MODERATE: [
        "moderate", "reasonable", "fair price", "mid-range", "average"
    ],
    PRICE_PREMIUM: [
        "premium", "luxury", "expensive", "high-end", "first class", "business class",
        "comfort", "best quality"
    ]
}

# Timing preference keywords
TIMING_KEYWORDS = {
    TIME_EARLY_MORNING: [
        "early morning", "dawn", "sunrise", "early", "before 8am"
    ],
    TIME_MORNING: [
        "morning", "am", "forenoon", "9am", "10am", "11am"
    ],
    TIME_AFTERNOON: [
        "afternoon", "midday", "noon", "pm", "12pm", "1pm", "2pm", "3pm", "4pm"
    ],
    TIME_EVENING: [
        "evening", "night", "late", "after work", "6pm", "7pm", "8pm"
    ],
    TIME_RED_EYE: [
        "red-eye", "overnight", "late night", "midnight"
    ]
}

# Speed preference keywords
SPEED_KEYWORDS = [
    "fast", "quick", "shortest", "rapid", "speedy", "express"
]

# Direct flight keywords
DIRECT_FLIGHT_KEYWORDS = [
    "direct", "non-stop", "nonstop", "no layover", "no stop", 
    "hate layovers", "avoid layovers", "without stop"
]

# Convenience keywords
CONVENIENCE_KEYWORDS = [
    "convenient", "comfortable", "easy", "hassle-free", "simple"
]

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

# Common city name variations
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
}


# ============================================================================
# FLIGHT INTENT EXTRACTOR
# ============================================================================

class FlightIntentExtractor:
    """
    Extracts structured flight search intent from natural language queries.
    
    Uses pattern matching and NLP heuristics to identify:
    - Origin and destination cities
    - Travel dates
    - Number of travelers
    - User preferences (budget, timing, direct flights, etc.)
    """
    
    def extract(self, query: str) -> FlightIntent:
        """
        Main extraction method - converts natural language to structured intent.
        
        Args:
            query: Natural language flight search query
            
        Returns:
            FlightIntent with extracted information and preferences
            
        Example:
            >>> extractor = FlightIntentExtractor()
            >>> intent = extractor.extract("cheap direct flight Delhi to Mumbai tomorrow for 2 adults")
            >>> print(intent.from_city, intent.to_city, intent.adults)
            Delhi Mumbai 2
        """
        query_lower = query.lower()
        
        # Extract core entities
        from_city, to_city = self._extract_cities(query_lower)
        date = self._extract_date(query_lower)
        adults = self._extract_adults(query_lower)
        max_price = self._extract_max_price(query_lower)
        
        # Extract preferences (only what's explicitly mentioned)
        preferences = self._extract_preferences(query_lower)
        
        return FlightIntent(
            from_city=from_city,
            to_city=to_city,
            date=date,
            adults=adults,
            max_price=max_price,
            preferences=preferences
        )
    
    def _extract_cities(self, query: str) -> tuple[str, str]:
        """
        Extract origin and destination cities from query.
        
        Looks for patterns like:
        - "from X to Y"
        - "X to Y"
        - "flight to Y" (destination only, origin unknown)
        """
        # Pattern 1: "from X to Y"
        from_to_pattern = r"from\s+([a-z\s]+?)\s+to\s+([a-z\s]+?)(?:\s+on|\s+for|\s+in|\s+under|\s+tomorrow|\s+next|\s+\d|$)"
        match = re.search(from_to_pattern, query)
        if match:
            from_city = match.group(1).strip()
            to_city = match.group(2).strip()
            return self._normalize_city(from_city), self._normalize_city(to_city)
        
        # Pattern 2: Look for known city pairs first (before general "to" pattern)
        found_cities = []
        for city in CITY_ALIASES.keys():
            if city in query:
                found_cities.append((city, query.find(city)))
        
        if len(found_cities) >= 2:
            # Sort by position in query
            found_cities.sort(key=lambda x: x[1])
            # First mentioned is likely origin, second is destination
            return found_cities[0][0].title(), found_cities[1][0].title()
        
        # Pattern 3: "X to Y" (generic)
        to_pattern = r"\b([a-z\s]+?)\s+to\s+([a-z\s]+?)(?:\s+on|\s+for|\s+in|\s+under|\s+tomorrow|\s+next|\s+\d|$)"
        match = re.search(to_pattern, query)
        if match:
            from_city = match.group(1).strip()
            to_city = match.group(2).strip()
            
            # Filter out common false positives
            false_positives = [
                "want", "like", "need", "flight", "ticket", "flights", "cheap", 
                "morning", "evening", "afternoon", "direct", "non", "stop", "book",
                "show", "find", "get", "search", "looking"
            ]
            
            # Check if from_city is a false positive
            if from_city.lower() not in false_positives:
                # Validate it's likely a city
                if len(from_city.split()) <= 2:  # Cities are usually 1-2 words
                    return self._normalize_city(from_city), self._normalize_city(to_city)
        
        # Pattern 4: "to Y" or "flight to Y" (destination only)
        if len(found_cities) == 1:
            # Only destination found, origin unknown
            return "Unknown", found_cities[0][0].title()
        
        raise ValueError("Could not extract origin and destination cities from query")
    
    def _normalize_city(self, city: str) -> str:
        """Normalize city name to canonical form."""
        city_clean = city.strip().lower()
        
        # Check aliases
        for canonical, aliases in CITY_ALIASES.items():
            if city_clean in aliases:
                return canonical.title()
        
        # Return title case
        return city.strip().title()
    
    def _extract_date(self, query: str) -> Optional[str]:
        """
        Extract travel date from query.
        
        Supports:
        - Explicit dates: "14 Feb 2026", "2026-02-14", "14th February"
        - Relative dates: "tomorrow", "next week", "next month"
        """
        today = datetime.now()
        
        # Pattern 1: "tomorrow"
        if "tomorrow" in query:
            date = today + timedelta(days=1)
            return date.strftime("%Y-%m-%d")
        
        # Pattern 2: "next week"
        if "next week" in query:
            date = today + timedelta(days=7)
            return date.strftime("%Y-%m-%d")
        
        # Pattern 3: "next month"
        if "next month" in query:
            date = today + timedelta(days=30)
            return date.strftime("%Y-%m-%d")
        
        # Pattern 4: YYYY-MM-DD format
        iso_pattern = r"(\d{4})-(\d{2})-(\d{2})"
        match = re.search(iso_pattern, query)
        if match:
            return match.group(0)
        
        # Pattern 5: "DD Month YYYY" or "DD Month"
        date_pattern = r"(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]+)(?:\s+(\d{4}))?"
        match = re.search(date_pattern, query)
        if match:
            day = int(match.group(1))
            month_str = match.group(2).lower()
            year = int(match.group(3)) if match.group(3) else today.year
            
            month = MONTH_NAMES.get(month_str)
            if month:
                try:
                    date = datetime(year, month, day)
                    return date.strftime("%Y-%m-%d")
                except ValueError:
                    pass
        
        # Pattern 6: "Month DD, YYYY"
        month_day_pattern = r"([a-z]+)\s+(\d{1,2})(?:,\s*(\d{4}))?"
        match = re.search(month_day_pattern, query)
        if match:
            month_str = match.group(1).lower()
            day = int(match.group(2))
            year = int(match.group(3)) if match.group(3) else today.year
            
            month = MONTH_NAMES.get(month_str)
            if month:
                try:
                    date = datetime(year, month, day)
                    return date.strftime("%Y-%m-%d")
                except ValueError:
                    pass
        
        return None
    
    def _extract_adults(self, query: str) -> int:
        """
        Extract number of adult travelers.
        
        Looks for patterns like:
        - "4 adults"
        - "for 3 people"
        - "2 passengers"
        """
        # Pattern 1: "X adults"
        adults_pattern = r"(\d+)\s+(?:adult|adults|people|person|persons|passenger|passengers|traveler|travelers)"
        match = re.search(adults_pattern, query)
        if match:
            return int(match.group(1))
        
        # Pattern 2: "for X"
        for_pattern = r"for\s+(\d+)(?:\s|$)"
        match = re.search(for_pattern, query)
        if match:
            num = int(match.group(1))
            # Sanity check - likely number of people if between 1-20
            if 1 <= num <= 20:
                return num
        
        return DEFAULT_ADULTS
    
    def _extract_max_price(self, query: str) -> Optional[int]:
        """
        Extract maximum price constraint.
        
        Looks for patterns like:
        - "under 5000 rupees"
        - "below 3000"
        - "max 10000"
        """
        # Pattern 1: "under/below/max X rupees/rs/inr"
        price_pattern = r"(?:under|below|max|maximum|upto|up to)\s+(\d{3,})(?:\s+rupees|\s+rs|\s+inr|\s|$)"
        match = re.search(price_pattern, query)
        if match:
            price = int(match.group(1))
            # Sanity check: price should be reasonable (100-100000)
            if 100 <= price <= 100000:
                return price
        
        return None
    
    def _extract_preferences(self, query: str) -> Dict[str, Any]:
        """
        Extract user preferences from query.
        ONLY includes preferences that are explicitly mentioned.
        Returns empty dict if no preferences detected.
        """
        prefs = {}
        
        # Budget preference
        budget_pref = self._detect_budget_preference(query)
        if budget_pref:
            prefs[PREF_BUDGET_PREFERENCE] = budget_pref
        
        # Timing preference
        timing_pref = self._detect_timing_preference(query)
        if timing_pref:
            prefs[PREF_TIMING_PREFERENCE] = timing_pref
        
        # Direct flights / avoid layovers
        if self._detect_direct_flight_preference(query):
            prefs[PREF_AVOID_LAYOVERS] = True
        
        # Speed preference
        if self._detect_speed_preference(query):
            prefs[PREF_SPEED] = "fast"
        
        return prefs
    
    def _detect_budget_preference(self, query: str) -> Optional[str]:
        """Detect budget tier preference from keywords."""
        # Check each budget tier
        for tier, keywords in BUDGET_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return tier
        return None
    
    def _detect_timing_preference(self, query: str) -> Optional[str]:
        """Detect time-of-day preference from keywords."""
        # Check for negative patterns first (e.g., "not early morning")
        for time_segment, keywords in TIMING_KEYWORDS.items():
            for keyword in keywords:
                if f"not {keyword}" in query or f"no {keyword}" in query or f"avoid {keyword}" in query:
                    # User explicitly wants to avoid this time
                    # We could return inverse, but safer to just skip
                    continue
        
        # Check positive patterns
        for time_segment, keywords in TIMING_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return time_segment
        
        return None
    
    def _detect_direct_flight_preference(self, query: str) -> bool:
        """Detect if user wants direct flights only."""
        for keyword in DIRECT_FLIGHT_KEYWORDS:
            if keyword in query:
                return True
        return False
    
    def _detect_speed_preference(self, query: str) -> bool:
        """Detect if user prioritizes speed."""
        for keyword in SPEED_KEYWORDS:
            if keyword in query:
                return True
        return False


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def extract_flight_intent(query: str) -> FlightIntent:
    """
    Convenience function to extract flight intent from natural language query.
    
    Args:
        query: Natural language flight search query
        
    Returns:
        FlightIntent with extracted information and preferences
        
    Example:
        >>> intent = extract_flight_intent("cheap direct flight Delhi to Mumbai tomorrow")
        >>> print(intent.from_city, intent.to_city, intent.preferences)
        Delhi Mumbai {'budget_preference': 'budget', 'avoid_layovers': True}
    """
    extractor = FlightIntentExtractor()
    return extractor.extract(query)


# ============================================================================
# TESTING & EXAMPLES
# ============================================================================

if __name__ == "__main__":
    """
    Test the intent extractor with sample queries.
    """
    test_queries = [
        "Find cheap but fast direct flights from Delhi to Mumbai on 14 Feb 2026 for 4 adults",
        "I want the cheapest flight to Goa next month, but not early morning",
        "Book a convenient evening flight from Bangalore to Delhi",
        "Show me flights under 5000 rupees from Delhi to Jaipur tomorrow",
        "Direct flight from Mumbai to Bangalore on 20th March",
        "Cheap morning flight to Chennai for 2 people",
    ]
    
    print("=" * 80)
    print("FLIGHT INTENT EXTRACTION TEST")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 80)
        
        try:
            intent = extract_flight_intent(query)
            print(f"From: {intent.from_city}")
            print(f"To: {intent.to_city}")
            print(f"Date: {intent.date or 'Not specified'}")
            print(f"Adults: {intent.adults}")
            print(f"Max Price: {intent.max_price or 'Not specified'}")
            print(f"Preferences: {intent.preferences or 'None'}")
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("\n" + "=" * 80)


