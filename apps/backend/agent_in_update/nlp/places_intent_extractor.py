"""
Places Intent Extractor - Natural Language Understanding for Places Queries

Extracts structured intent from free-form natural language places/attractions queries.
Supports queries like:
- "Find tourist places in Mumbai with high ratings"
- "Show me museums and parks in Delhi"
- "I want free attractions in Goa near the beach"
- "Best restaurants in Bangalore under 500 rupees"

SAFETY RULES:
- Never invent preferences if not mentioned
- Only include preferences that were explicitly stated or clearly implied
- Return empty preferences {} if none detected
- Default to no category filter if not specified
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from shared.constants import (
    PREF_BUDGET_PREFERENCE,
    PRICE_BUDGET,
    PRICE_MODERATE,
    PRICE_PREMIUM,
)


# ============================================================================
# INTENT SCHEMAS
# ============================================================================

class PlacesIntent(BaseModel):
    """
    Structured representation of places search intent extracted from natural language.
    """
    city: str = Field(..., description="City to search places in")
    categories: List[str] = Field(default_factory=list, description="Types of places to search for")
    max_entry_fee: Optional[int] = Field(None, description="Maximum entry fee in INR (0 for free only)")
    min_rating: Optional[float] = Field(None, description="Minimum rating (0.0-5.0)")
    radius_km: int = Field(10, description="Search radius in kilometers")
    limit: int = Field(10, description="Maximum number of results")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences extracted from query")
    
    model_config = {"extra": "forbid"}


class ExtractedPreferences(BaseModel):
    """
    User preferences extracted from natural language query.
    Only includes preferences that were explicitly mentioned or clearly implied.
    """
    budget_preference: Optional[str] = Field(None, description="Budget tier: budget, moderate, premium")
    location_preference: Optional[str] = Field(None, description="Location preference: central, beach, quiet, historic")
    activity_type: Optional[str] = Field(None, description="Activity type: cultural, outdoor, entertainment, educational")
    traveler_type: Optional[str] = Field(None, description="Type of traveler: family, solo, couple, group")
    
    model_config = {"extra": "forbid"}


# ============================================================================
# NLP KEYWORD PATTERNS
# ============================================================================

# Budget preference keywords
BUDGET_KEYWORDS = {
    PRICE_BUDGET: [
        "cheap", "cheapest", "budget", "affordable", "economical", "low cost",
        "inexpensive", "save money", "bargain", "free", "no entry fee"
    ],
    PRICE_MODERATE: [
        "moderate", "reasonable", "fair price", "mid-range", "average", "decent"
    ],
    PRICE_PREMIUM: [
        "premium", "upscale", "high-end", "quality", "best", "top-rated",
        "exclusive", "elite", "finest"
    ]
}

# Place category keywords
CATEGORY_KEYWORDS = {
    "museum": ["museum", "museums", "gallery", "galleries", "art", "exhibition"],
    "park": ["park", "parks", "garden", "gardens", "green space", "botanical"],
    "temple": ["temple", "temples", "shrine", "shrines", "religious", "spiritual"],
    "restaurant": ["restaurant", "restaurants", "dining", "food", "cafe", "cafes", "eatery", "eateries"],
    "shopping": ["shopping", "mall", "malls", "market", "markets", "bazaar", "store", "stores"],
    "beach": ["beach", "beaches", "seaside", "oceanfront", "coastal"],
    "monument": ["monument", "monuments", "memorial", "memorials", "landmark", "landmarks"],
    "entertainment": ["entertainment", "theater", "cinema", "amusement", "theme park", "arcade"],
    "sports": ["sports", "stadium", "arena", "gym", "fitness", "recreation"],
    "nightlife": ["nightlife", "bar", "bars", "pub", "pubs", "club", "clubs", "lounge"],
    "zoo": ["zoo", "zoos", "aquarium", "aquariums", "wildlife", "safari"],
    "viewpoint": ["viewpoint", "viewpoints", "scenic", "lookout", "observatory", "panoramic"],
}

# Activity type keywords
ACTIVITY_TYPE_KEYWORDS = {
    "cultural": ["cultural", "culture", "heritage", "traditional", "historical", "museum", "temple"],
    "outdoor": ["outdoor", "nature", "hiking", "park", "garden", "beach", "adventure"],
    "entertainment": ["entertainment", "fun", "amusement", "theme park", "cinema", "show"],
    "educational": ["educational", "learning", "museum", "library", "science", "planetarium"],
}

# Location preference keywords
LOCATION_KEYWORDS = {
    "central": ["central", "downtown", "city center", "main area", "heart of"],
    "beach": ["beach", "beachfront", "seaside", "oceanfront", "coastal", "near beach"],
    "quiet": ["quiet", "peaceful", "serene", "tranquil", "calm", "secluded"],
    "historic": ["historic", "historical", "old town", "heritage", "ancient"],
}

# Traveler type keywords
TRAVELER_KEYWORDS = {
    "family": ["family", "kids", "children", "family-friendly", "kid-friendly"],
    "solo": ["solo", "alone", "single", "individual"],
    "couple": ["couple", "romantic", "couples", "date"],
    "group": ["group", "friends", "team", "party"],
}

# Free/paid keywords
FREE_KEYWORDS = ["free", "no fee", "no charge", "free entry", "no cost", "complimentary", "gratis"]

# Rating keywords
RATING_KEYWORDS = {
    "high": ["high rating", "highly rated", "top rated", "best rated", "excellent", "5 star"],
    "good": ["good rating", "well rated", "quality", "recommended"],
}

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
    "trivandrum": ["trivandrum", "thiruvananthapuram", "trv"],
    "agra": ["agra"],
    "varanasi": ["varanasi", "benares", "banaras"],
    "udaipur": ["udaipur"],
}

# Price patterns for entry fees
PRICE_PATTERNS = [
    r'under\s+(\d+)',
    r'below\s+(\d+)',
    r'less than\s+(\d+)',
    r'maximum\s+(\d+)',
    r'max\s+(\d+)',
    r'up to\s+(\d+)',
]

# Rating patterns
RATING_PATTERNS = [
    r'(\d\.?\d?)\s*star',
    r'rating\s+(\d\.?\d?)',
    r'rated\s+(\d\.?\d?)',
    r'minimum\s+(\d\.?\d?)',
    r'min\s+(\d\.?\d?)',
    r'above\s+(\d\.?\d?)',
]

# Radius patterns
RADIUS_PATTERNS = [
    r'within\s+(\d+)\s*(?:km|kilometer|kilometers)',
    r'(\d+)\s*(?:km|kilometer|kilometers)\s+radius',
    r'radius\s+of\s+(\d+)',
]

# Limit patterns
LIMIT_PATTERNS = [
    r'top\s+(\d+)',
    r'best\s+(\d+)',
    r'(\d+)\s+places',
    r'(\d+)\s+attractions',
    r'(\d+)\s+options',
]


# ============================================================================
# PLACES INTENT EXTRACTOR
# ============================================================================

class PlacesIntentExtractor:
    """
    Extracts structured places search intent from natural language queries.
    
    Uses pattern matching and NLP heuristics to identify:
    - City name
    - Place categories (museums, parks, restaurants, etc.)
    - Entry fee constraints
    - Rating preferences
    - Search radius and result limits
    - User preferences (budget, location, activity type, etc.)
    """
    
    def extract(self, query: str) -> PlacesIntent:
        """
        Main extraction method - converts natural language to structured intent.
        
        Args:
            query: Natural language places search query
            
        Returns:
            PlacesIntent with extracted information and preferences
            
        Example:
            >>> extractor = PlacesIntentExtractor()
            >>> intent = extractor.extract("Find top 5 museums in Delhi with high ratings")
            >>> print(intent.city, intent.categories, intent.limit)
            Delhi ['museum'] 5
        """
        query_lower = query.lower()
        
        # Extract core entities
        city = self._extract_city(query_lower)
        categories = self._extract_categories(query_lower)
        max_entry_fee = self._extract_max_entry_fee(query_lower)
        min_rating = self._extract_min_rating(query_lower)
        radius_km = self._extract_radius(query_lower)
        limit = self._extract_limit(query_lower)
        
        # Extract preferences (only what's explicitly mentioned)
        preferences = self._extract_preferences(query_lower)
        
        return PlacesIntent(
            city=city,
            categories=categories,
            max_entry_fee=max_entry_fee,
            min_rating=min_rating,
            radius_km=radius_km,
            limit=limit,
            preferences=preferences
        )
    
    def _extract_city(self, query: str) -> str:
        """
        Extract city name from query.
        
        Looks for patterns like:
        - "in Mumbai"
        - "near Delhi"
        - "Mumbai tourist places"
        """
        # First, try to find any known city name
        for canonical, aliases in CITY_ALIASES.items():
            for alias in aliases:
                if re.search(r'\b' + re.escape(alias) + r'\b', query):
                    return canonical.title()
        
        # Pattern 1: "in <city>"
        in_pattern = r'\bin\s+([a-z\s]+?)(?:\s+with|\s+under|\s+near|\s+that|\s+for|$)'
        match = re.search(in_pattern, query)
        if match:
            city_candidate = match.group(1).strip()
            # Skip common false positives
            if city_candidate not in ["the", "a", "an", "area", "city"]:
                normalized = self._normalize_city(city_candidate)
                if normalized:
                    return normalized
        
        # Pattern 2: "near <city>"
        near_pattern = r'\bnear\s+([a-z\s]+?)(?:\s+with|\s+under|\s+in|\s+that|\s+for|$)'
        match = re.search(near_pattern, query)
        if match:
            city_candidate = match.group(1).strip()
            normalized = self._normalize_city(city_candidate)
            if normalized:
                return normalized
        
        # Pattern 3: "<city> places/attractions"
        city_pattern = r'([a-z\s]+?)\s+(?:places|attractions|tourist|sightseeing|spots)'
        match = re.search(city_pattern, query)
        if match:
            city_candidate = match.group(1).strip()
            # Skip common adjectives
            if city_candidate not in ["tourist", "best", "top", "good", "nice", "cheap", "free"]:
                normalized = self._normalize_city(city_candidate)
                if normalized:
                    return normalized
        
        raise ValueError("Could not extract city from query. Please specify a city.")
    
    def _normalize_city(self, city: str) -> Optional[str]:
        """Normalize city name to canonical form."""
        city_clean = city.strip().lower()
        
        # Check aliases
        for canonical, aliases in CITY_ALIASES.items():
            if city_clean in aliases:
                return canonical.title()
        
        # Return title case if it looks like a valid city name
        if len(city_clean) >= 3 and all(c.isalpha() or c.isspace() for c in city_clean):
            return city.strip().title()
        
        return None
    
    def _extract_categories(self, query: str) -> List[str]:
        """
        Extract place categories from query.
        
        Returns list of categories mentioned (museum, park, restaurant, etc.)
        """
        categories = []
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    if category not in categories:
                        categories.append(category)
                    break
        
        return categories
    
    def _extract_max_entry_fee(self, query: str) -> Optional[int]:
        """
        Extract maximum entry fee constraint.
        
        Looks for:
        - "free" keywords → 0
        - "under 500" → 500
        - "below 200 rupees" → 200
        """
        # Check for free keywords first
        for keyword in FREE_KEYWORDS:
            if keyword in query:
                return 0
        
        # Check for price patterns
        for pattern in PRICE_PATTERNS:
            match = re.search(pattern, query)
            if match:
                try:
                    fee = int(match.group(1))
                    # Sanity check: entry fees typically 0-5000
                    if 0 <= fee <= 5000:
                        return fee
                except (ValueError, IndexError):
                    pass
        
        return None
    
    def _extract_min_rating(self, query: str) -> Optional[float]:
        """
        Extract minimum rating preference.
        
        Looks for:
        - "high rating" → 4.0
        - "4.5 star" → 4.5
        - "minimum 4" → 4.0
        """
        # Check for rating keywords first
        if any(keyword in query for keyword in RATING_KEYWORDS.get("high", [])):
            return 4.0
        elif any(keyword in query for keyword in RATING_KEYWORDS.get("good", [])):
            return 3.5
        
        # Check for explicit rating patterns
        for pattern in RATING_PATTERNS:
            match = re.search(pattern, query)
            if match:
                try:
                    rating = float(match.group(1))
                    # Clamp to valid range
                    if rating < 0:
                        rating = 0.0
                    elif rating > 5:
                        rating = 5.0
                    return rating
                except (ValueError, IndexError):
                    pass
        
        return None
    
    def _extract_radius(self, query: str) -> int:
        """
        Extract search radius in kilometers.
        
        Defaults to 10 if not specified.
        """
        for pattern in RADIUS_PATTERNS:
            match = re.search(pattern, query)
            if match:
                try:
                    radius = int(match.group(1))
                    # Clamp to reasonable range
                    if radius < 1:
                        return 1
                    elif radius > 50:
                        return 50
                    return radius
                except (ValueError, IndexError):
                    pass
        
        return 10  # Default
    
    def _extract_limit(self, query: str) -> int:
        """
        Extract maximum number of results.
        
        Defaults to 10 if not specified.
        """
        for pattern in LIMIT_PATTERNS:
            match = re.search(pattern, query)
            if match:
                try:
                    limit = int(match.group(1))
                    # Clamp to reasonable range
                    if limit < 1:
                        return 1
                    elif limit > 50:
                        return 50
                    return limit
                except (ValueError, IndexError):
                    pass
        
        return 10  # Default
    
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
        
        # Location preference
        location_pref = self._detect_location_preference(query)
        if location_pref:
            prefs["location_preference"] = location_pref
        
        # Activity type
        activity_type = self._detect_activity_type(query)
        if activity_type:
            prefs["activity_type"] = activity_type
        
        # Traveler type
        traveler_type = self._detect_traveler_type(query)
        if traveler_type:
            prefs["traveler_type"] = traveler_type
        
        return prefs
    
    def _detect_budget_preference(self, query: str) -> Optional[str]:
        """Detect budget tier preference from keywords."""
        for tier, keywords in BUDGET_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return tier
        return None
    
    def _detect_location_preference(self, query: str) -> Optional[str]:
        """Detect location preference from keywords."""
        for location, keywords in LOCATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return location
        return None
    
    def _detect_activity_type(self, query: str) -> Optional[str]:
        """Detect activity type preference from keywords."""
        for activity, keywords in ACTIVITY_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return activity
        return None
    
    def _detect_traveler_type(self, query: str) -> Optional[str]:
        """Detect traveler type from keywords."""
        for traveler, keywords in TRAVELER_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return traveler
        return None


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def extract_places_intent(query: str) -> PlacesIntent:
    """
    Convenience function to extract places intent from natural language query.
    
    Args:
        query: Natural language places search query
        
    Returns:
        PlacesIntent with extracted information and preferences
        
    Example:
        >>> intent = extract_places_intent("Find free museums in Delhi with high ratings")
        >>> print(intent.city, intent.categories, intent.max_entry_fee)
        Delhi ['museum'] 0
    """
    extractor = PlacesIntentExtractor()
    return extractor.extract(query)


# ============================================================================
# TESTING & EXAMPLES
# ============================================================================

if __name__ == "__main__":
    """
    Test the intent extractor with sample queries.
    """
    test_queries = [
        "Find tourist places in Mumbai with high ratings",
        "Show me museums and parks in Delhi",
        "I want free attractions in Goa near the beach",
        "Best restaurants in Bangalore under 500 rupees",
        "Top 5 monuments in Agra",
        "Family-friendly places in Jaipur",
        "Cultural attractions in Varanasi with minimum 4 star rating",
        "Outdoor activities in Kochi within 5km",
    ]
    
    print("=" * 80)
    print("PLACES INTENT EXTRACTION TEST")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 80)
        
        try:
            intent = extract_places_intent(query)
            print(f"City: {intent.city}")
            print(f"Categories: {intent.categories or 'Any'}")
            print(f"Max Entry Fee: {intent.max_entry_fee if intent.max_entry_fee is not None else 'Not specified'}")
            print(f"Min Rating: {intent.min_rating or 'Not specified'}")
            print(f"Radius: {intent.radius_km} km")
            print(f"Limit: {intent.limit}")
            print(f"Preferences: {intent.preferences or 'None'}")
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("\n" + "=" * 80)


