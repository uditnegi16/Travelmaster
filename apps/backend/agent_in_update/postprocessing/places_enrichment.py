"""
Places Enrichment Layer V2 - Comprehensive Intelligence

Answers all critical travel questions:
- Is this good for couples/family/kids/solo/elders?
- When should I visit? (morning/evening/sunset/avoid noon)
- How long should I spend here?
- How to reach? (walk/cab/metro)
- Where does it fit in the day plan?
- Weather sensitivity?
- Crowd analysis (crowded/peaceful/romantic/noisy)
- Is it skippable or must-visit?
- Who should avoid it?
- Contextual summary (why it exists, what makes it special)
- Open/Close timing
- Ticket/queue/dress code/restrictions
- Effort vs reward
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import statistics
import logging
import logging
from pydantic import BaseModel, Field
from openai import OpenAI

from shared.schemas import PlaceOption
from shared.constants import (
    INSIGHT_TYPE_ADVANTAGE,
    INSIGHT_TYPE_CONSIDERATION,
    INSIGHT_TYPE_TIP,
    INSIGHT_TYPE_WARNING,
    SENTIMENT_POSITIVE,
    SENTIMENT_NEUTRAL,
    SENTIMENT_NEGATIVE,
    PRICE_BUDGET,
    PRICE_MODERATE,
    PRICE_PREMIUM,
    SCORE_MIN,
    SCORE_MAX,
    MATCH_SCORE_MIN,
    MATCH_SCORE_MAX,
)

from place_knowledge.client_factory import get_openai_client

# ============================================================================
# COMPREHENSIVE ENRICHMENT SCHEMAS
# ============================================================================

class AudienceSuitability(BaseModel):
    """Who should visit this place?"""
    couples: Dict[str, Any] = Field(..., description="Suitability for couples with score and reason")
    families: Dict[str, Any] = Field(..., description="Suitability for families with score and reason")
    kids: Dict[str, Any] = Field(..., description="Suitability for kids with score and reason")
    solo_travelers: Dict[str, Any] = Field(..., description="Suitability for solo travelers")
    elderly: Dict[str, Any] = Field(..., description="Suitability for elderly visitors")
    
    model_config = {"extra": "forbid"}


class TimingIntelligence(BaseModel):
    """When and how long to visit"""
    best_time_of_day: str = Field(..., description="morning/afternoon/evening/sunset/night")
    time_to_avoid: Optional[str] = Field(None, description="When to avoid (e.g., 'noon - too hot')")
    recommended_duration: str = Field(..., description="How long to spend (e.g., '1-2 hours')")
    opening_time: Optional[str] = Field(None, description="Opening time (e.g., '9:00 AM')")
    closing_time: Optional[str] = Field(None, description="Closing time (e.g., '6:00 PM')")
    opening_hours: Optional[str] = Field(None, description="Full operating hours (e.g., '9:00 AM - 6:00 PM')")
    closed_on: Optional[str] = Field(None, description="Days when closed (e.g., 'Monday', 'Public holidays')")
    peak_hours: Optional[str] = Field(None, description="When it's most crowded")
    reasoning: str = Field(..., description="Why this timing is recommended")
    
    model_config = {"extra": "forbid"}


class AccessibilityInfo(BaseModel):
    """How to reach and navigate"""
    transport_modes: List[str] = Field(..., description="walk, metro, cab, bus, auto")
    recommended_transport: str = Field(..., description="Best way to reach")
    estimated_travel_time: Optional[str] = Field(None, description="From city center")
    parking_available: bool = Field(default=False, description="Parking availability")
    accessibility_notes: Optional[str] = Field(None, description="Wheelchair/mobility notes")
    
    model_config = {"extra": "forbid"}


class DayPlanFit(BaseModel):
    """Where this fits in the day's itinerary"""
    position_in_day: str = Field(..., description="morning-start/mid-day/evening-end/flexible")
    can_combine_with: List[str] = Field(default_factory=list, description="Nearby attractions")
    distance_category: str = Field(..., description="cluster/nearby/far/isolated")
    sequence_recommendation: str = Field(..., description="Visit before/after/standalone")
    
    model_config = {"extra": "forbid"}


class WeatherCrowdAnalysis(BaseModel):
    """Weather sensitivity and crowd dynamics"""
    weather_dependency: str = Field(..., description="indoor/outdoor/partial/weather-proof")
    weather_sensitivity: str = Field(..., description="low/medium/high")
    crowd_level: str = Field(..., description="peaceful/moderate/crowded/very-crowded")
    crowd_type: str = Field(..., description="tourists/locals/mixed/religious/family-oriented")
    ambiance: List[str] = Field(..., description="peaceful, romantic, noisy, spiritual, festive")
    best_for_crowd_avoiders: bool = Field(default=False)
    
    model_config = {"extra": "forbid"}


class PriorityAssessment(BaseModel):
    """Is it must-visit or skippable?"""
    priority_level: str = Field(..., description="must-visit/highly-recommended/recommended/optional/skippable")
    priority_score: float = Field(..., description="0-10 score")
    skip_if: List[str] = Field(default_factory=list, description="Conditions when you can skip")
    must_visit_because: Optional[str] = Field(None, description="Why it's unmissable")
    who_should_avoid: List[str] = Field(default_factory=list, description="Who shouldn't visit")
    
    model_config = {"extra": "forbid"}


class ContextualInfo(BaseModel):
    """Why this place exists and what makes it special"""
    place_name: str = Field(..., description="Name of the place")
    category: str = Field(..., description="Category (museum, temple, park, etc.)")
    short_summary: str = Field(..., description="One-line what is this place")
    detailed_description: str = Field(..., description="Comprehensive description of the place")
    historical_significance: Optional[str] = Field(None, description="Historical background and importance")
    cultural_significance: Optional[str] = Field(None, description="Cultural or religious importance")
    architectural_significance: Optional[str] = Field(None, description="Architectural features")
    why_visit: List[str] = Field(..., description="Top reasons why tourists should visit")
    what_makes_special: str = Field(..., description="Unique selling points")
    famous_for: List[str] = Field(default_factory=list, description="What this place is famous for")
    experience_type: str = Field(..., description="cultural/spiritual/nature/adventure/educational/entertainment")
    must_see_features: List[str] = Field(default_factory=list, description="Key highlights to see")
    interesting_facts: List[str] = Field(default_factory=list, description="Fun or interesting facts")
    
    model_config = {"extra": "forbid"}


class PracticalDetails(BaseModel):
    """Tickets, queues, dress codes, restrictions"""
    entry_fee: int = Field(..., description="Entry fee in INR")
    ticket_booking: str = Field(..., description="online/onsite/both/free-entry")
    queue_situation: str = Field(..., description="no-queue/short/moderate/long/very-long")
    dress_code: Optional[str] = Field(None, description="Dress requirements")
    restrictions: List[str] = Field(default_factory=list, description="Photography/food/behavior rules")
    facilities: List[str] = Field(default_factory=list, description="Washroom/cafe/parking/guide")
    
    model_config = {"extra": "forbid"}


class EffortRewardBalance(BaseModel):
    """Is the effort worth it?"""
    effort_level: str = Field(..., description="minimal/low/moderate/high/strenuous")
    reward_level: str = Field(..., description="disappointing/average/good/excellent/exceptional")
    value_score: float = Field(..., description="Effort vs reward score (0-10)")
    worth_it: bool = Field(..., description="Overall verdict")
    reasoning: str = Field(..., description="Why effort is/isn't worth it")
    
    model_config = {"extra": "forbid"}


class PlaceInsight(BaseModel):
    """Intelligent insights"""
    type: str = Field(..., description="advantage/consideration/tip/warning")
    message: str = Field(..., description="Insight message")
    priority: int = Field(default=1, description="1-5 priority")
    model_config = {"extra": "forbid"}


class PlaceRecommendation(BaseModel):
    """Smart recommendations"""
    reason: str = Field(..., description="Recommendation text")
    category: str = Field(..., description="Category of recommendation")
    sentiment: str = Field(..., description="positive/neutral/negative")
    model_config = {"extra": "forbid"}


class EnrichedPlace(BaseModel):
    """Comprehensive enriched place with all intelligence layers"""
    # Original data
    place: PlaceOption = Field(..., description="Original place data")
    
    # Core intelligence
    rank: int = Field(..., description="Rank (1=best)")
    match_score: float = Field(..., description="Overall match score (0-100)")
    one_line_verdict: str = Field(..., description="Quick verdict")
    
    # Comprehensive analysis layers
    audience_suitability: AudienceSuitability
    timing_intelligence: TimingIntelligence
    accessibility_info: AccessibilityInfo
    day_plan_fit: DayPlanFit
    weather_crowd_analysis: WeatherCrowdAnalysis
    priority_assessment: PriorityAssessment
    contextual_info: ContextualInfo
    practical_details: PracticalDetails
    effort_reward_balance: EffortRewardBalance
    
    # Smart tags and classifications
    tags: List[str] = Field(default_factory=list)
    best_for: List[str] = Field(default_factory=list)
    
    # Decision support
    insights: List[PlaceInsight] = Field(default_factory=list)
    recommendations: List[PlaceRecommendation] = Field(default_factory=list)
    
    model_config = {"extra": "forbid"}


class EnrichmentResult(BaseModel):
    """Complete enrichment result"""
    enriched_places: List[EnrichedPlace] = Field(default_factory=list)
    market_analysis: Dict[str, Any] = Field(default_factory=dict)
    travel_tips: List[str] = Field(default_factory=list)
    best_choice: Optional[str] = Field(None)
    model_config = {"extra": "forbid"}


# ============================================================================
# COMPREHENSIVE INTELLIGENCE ENGINE
# ============================================================================

class PlacesIntelligenceEngine:
    """Advanced intelligence engine with comprehensive analysis"""
    
    def __init__(self, openai_client: Optional[OpenAI] = None, use_knowledge_system: bool = True):
        self.category_profiles = self._initialize_category_profiles()
        import logging
        # Auto-initialize OpenAI client from config if not provided
        if openai_client is None and use_knowledge_system:
            try:
                self.openai_client = get_openai_client()
            except Exception as e:
                self.logger.error(f"Failed to auto-initialize OpenAI client: {e}")
                self.openai_client = None
        else:
            self.openai_client = openai_client
            
        self.use_knowledge_system = use_knowledge_system
        self.logger = logging.getLogger(__name__)
    
    def _initialize_category_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Category-specific intelligence profiles"""
        return {
            "monument": {
                "experience": "cultural",
                "best_time": "morning",
                "avoid_time": "noon - too hot outdoors",
                "typical_duration": "1-2 hours",
                "weather_dependency": "outdoor",
                "crowd_type": "tourists",
                "ambiance": ["historical", "photo-worthy"],
                "audience_scores": {"couples": 8, "families": 7, "kids": 5, "solo": 8, "elderly": 6},
                "transport": ["metro", "cab"],
                "effort": "low",
                "cultural_value": "high"
            },
            "museum": {
                "experience": "educational",
                "best_time": "morning",
                "avoid_time": "weekends - too crowded",
                "typical_duration": "2-3 hours",
                "weather_dependency": "indoor",
                "crowd_type": "mixed",
                "ambiance": ["quiet", "educational", "air-conditioned"],
                "audience_scores": {"couples": 6, "families": 9, "kids": 7, "solo": 7, "elderly": 8},
                "transport": ["metro", "cab", "bus"],
                "effort": "low",
                "cultural_value": "high"
            },
            "temple": {
                "experience": "spiritual",
                "best_time": "early morning",
                "avoid_time": "festival days - very crowded",
                "typical_duration": "30-45 minutes",
                "weather_dependency": "partial",
                "crowd_type": "religious",
                "ambiance": ["peaceful", "spiritual", "traditional"],
                "audience_scores": {"couples": 7, "families": 9, "kids": 6, "solo": 8, "elderly": 9},
                "transport": ["walk", "auto", "metro"],
                "effort": "low",
                "cultural_value": "very-high"
            },
            "park": {
                "experience": "nature",
                "best_time": "evening",
                "avoid_time": "afternoon - too hot",
                "typical_duration": "1-2 hours",
                "weather_dependency": "outdoor",
                "crowd_type": "locals",
                "ambiance": ["peaceful", "green", "relaxing"],
                "audience_scores": {"couples": 9, "families": 9, "kids": 8, "solo": 6, "elderly": 7},
                "transport": ["walk", "cab"],
                "effort": "minimal",
                "cultural_value": "low"
            },
            "mosque": {
                "experience": "spiritual",
                "best_time": "morning",
                "avoid_time": "prayer times - restricted entry",
                "typical_duration": "20-30 minutes",
                "weather_dependency": "indoor",
                "crowd_type": "religious",
                "ambiance": ["peaceful", "spiritual", "architectural"],
                "audience_scores": {"couples": 7, "families": 8, "kids": 5, "solo": 8, "elderly": 8},
                "transport": ["walk", "metro"],
                "effort": "low",
                "cultural_value": "very-high"
            },
            "beach": {
                "experience": "nature",
                "best_time": "sunset",
                "avoid_time": "noon - too hot",
                "typical_duration": "2-4 hours",
                "weather_dependency": "outdoor",
                "crowd_type": "mixed",
                "ambiance": ["romantic", "relaxing", "scenic"],
                "audience_scores": {"couples": 10, "families": 9, "kids": 9, "solo": 6, "elderly": 5},
                "transport": ["cab", "bus"],
                "effort": "low",
                "cultural_value": "low"
            },
            "fort": {
                "experience": "cultural",
                "best_time": "morning",
                "avoid_time": "afternoon - too hot",
                "typical_duration": "2-3 hours",
                "weather_dependency": "outdoor",
                "crowd_type": "tourists",
                "ambiance": ["historical", "adventure", "photo-worthy"],
                "audience_scores": {"couples": 8, "families": 8, "kids": 7, "solo": 9, "elderly": 5},
                "transport": ["cab", "metro"],
                "effort": "moderate",
                "cultural_value": "very-high"
            },
            "market": {
                "experience": "shopping",
                "best_time": "evening",
                "avoid_time": "weekday mornings - many shops closed",
                "typical_duration": "2-3 hours",
                "weather_dependency": "partial",
                "crowd_type": "locals",
                "ambiance": ["bustling", "colorful", "chaotic"],
                "audience_scores": {"couples": 7, "families": 8, "kids": 6, "solo": 6, "elderly": 5},
                "transport": ["metro", "auto", "walk"],
                "effort": "moderate",
                "cultural_value": "medium"
            },
        }
    
    def enrich_places(self, places: List[PlaceOption], preferences: Optional[Dict[str, Any]] = None) -> EnrichmentResult:
        """Main enrichment orchestrator"""
        if not places:
            return EnrichmentResult()
        
        preferences = preferences or {}
        
        # Score and rank places
        scored_places = self._score_places(places, preferences)
        
        # Enrich each place comprehensively
        enriched = []
        for rank, (place, score) in enumerate(scored_places, start=1):
            enriched_place = self._enrich_single_place(place, rank, score, preferences, places)
            enriched.append(enriched_place)
        
        # Generate market analysis
        market_analysis = self._generate_market_analysis(places, enriched)
        
        # Generate travel tips
        travel_tips = self._generate_travel_tips(enriched, preferences)
        
        # Best choice summary
        best_choice = self._generate_best_choice(enriched) if enriched else None
        
        return EnrichmentResult(
            enriched_places=enriched,
            market_analysis=market_analysis,
            travel_tips=travel_tips,
            best_choice=best_choice
        )
    
    def _score_places(self, places: List[PlaceOption], preferences: Dict[str, Any]) -> List[tuple]:
        """Score and rank places"""
        scored = []
        for place in places:
            score = self._calculate_match_score(place, preferences)
            scored.append((place, score))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    def _calculate_match_score(self, place: PlaceOption, preferences: Dict[str, Any]) -> float:
        """Calculate match score"""
        score = 50.0  # Base score
        
        # Rating contribution (0-30 points)
        score += (place.rating / 5.0) * 30
        
        # Free entry bonus (0-10 points)
        if place.entry_fee == 0:
            score += 10
        
        # Budget preference (0-10 points)
        budget_pref = preferences.get("budget_preference", "moderate")
        if budget_pref == "budget" and place.entry_fee == 0:
            score += 10
        elif budget_pref == "moderate" and 0 < place.entry_fee < 500:
            score += 5
        
        return min(score, 100.0)
    
    def _enrich_single_place(
        self, 
        place: PlaceOption, 
        rank: int, 
        match_score: float,
        preferences: Dict[str, Any],
        all_places: List[PlaceOption]
    ) -> EnrichedPlace:
        """Create comprehensive enrichment for a single place"""
        
        # Get category profile
        profile = self.category_profiles.get(place.category.lower(), self.category_profiles.get("monument", {}))
        
        # Build all intelligence layers
        audience = self._analyze_audience_suitability(place, profile)
        timing = self._analyze_timing(place, profile)
        accessibility = self._analyze_accessibility(place, profile)
        day_plan = self._analyze_day_plan_fit(place, all_places, profile)
        weather_crowd = self._analyze_weather_crowd(place, profile)
        priority = self._assess_priority(place, match_score, profile)
        
        # Use knowledge-enhanced contextual info if enabled
        if self.use_knowledge_system and self.openai_client:
            try:
                from place_knowledge.integration import (
                    create_knowledge_enhanced_contextual_info
                )
                contextual = create_knowledge_enhanced_contextual_info(
                    place=place,
                    profile=profile,
                    openai_client=self.openai_client,
                    use_knowledge_system=True
                )
                self.logger.info(f"✅ Knowledge-enhanced info for {place.name}")
            except Exception as e:
                self.logger.warning(f"⚠️ Knowledge enrichment failed for {place.name}: {e}")
                contextual = self._generate_contextual_info(place, profile)
        else:
            contextual = self._generate_contextual_info(place, profile)
        
        practical = self._generate_practical_details(place, profile)
        effort_reward = self._analyze_effort_reward(place, profile)
        
        # Generate tags
        tags = self._generate_tags(place, profile, priority)
        
        # Generate insights
        insights = self._generate_insights(place, profile, priority, effort_reward)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(place, profile, audience, priority)
        
        # One-line verdict
        verdict = self._generate_verdict(place, priority, effort_reward)
        
        return EnrichedPlace(
            place=place,
            rank=rank,
            match_score=match_score,
            one_line_verdict=verdict,
            audience_suitability=audience,
            timing_intelligence=timing,
            accessibility_info=accessibility,
            day_plan_fit=day_plan,
            weather_crowd_analysis=weather_crowd,
            priority_assessment=priority,
            contextual_info=contextual,
            practical_details=practical,
            effort_reward_balance=effort_reward,
            tags=tags,
            best_for=self._extract_best_for(audience),
            insights=insights,
            recommendations=recommendations
        )
    
    def _analyze_audience_suitability(self, place: PlaceOption, profile: Dict) -> AudienceSuitability:
        """Analyze who should visit"""
        scores = profile.get("audience_scores", {"couples": 5, "families": 5, "kids": 5, "solo": 5, "elderly": 5})
        
        def build_audience_dict(score: int, category: str) -> Dict[str, Any]:
            if score >= 8:
                verdict = "excellent"
                reason = f"Perfect for {category}"
            elif score >= 6:
                verdict = "good"
                reason = f"Suitable for {category}"
            elif score >= 4:
                verdict = "okay"
                reason = f"Average for {category}"
            else:
                verdict = "not-recommended"
                reason = f"Not ideal for {category}"
            
            return {"score": score, "verdict": verdict, "reason": reason}
        
        return AudienceSuitability(
            couples=build_audience_dict(scores["couples"], "couples"),
            families=build_audience_dict(scores["families"], "families"),
            kids=build_audience_dict(scores["kids"], "kids"),
            solo_travelers=build_audience_dict(scores["solo"], "solo travelers"),
            elderly=build_audience_dict(scores["elderly"], "elderly visitors")
        )
    
    def _analyze_timing(self, place: PlaceOption, profile: Dict) -> TimingIntelligence:
        """When to visit"""
        # Parse opening hours if available
        opening_time = None
        closing_time = None
        opening_hours = place.opening_hours
        closed_on = None
        
        # Extract opening/closing times from opening_hours string
        if opening_hours:
            # Try to extract times like "9:00 AM - 6:00 PM"
            if " - " in opening_hours:
                parts = opening_hours.split(" - ")
                if len(parts) == 2:
                    opening_time = parts[0].strip()
                    closing_time = parts[1].strip()
        else:
            # Default hours based on category
            if place.category in ["monument", "museum", "fort"]:
                opening_time = "9:00 AM"
                closing_time = "6:00 PM"
                opening_hours = f"{opening_time} - {closing_time}"
                closed_on = "Monday" if place.category == "museum" else None
            elif place.category in ["temple", "mosque"]:
                opening_time = "6:00 AM"
                closing_time = "9:00 PM"
                opening_hours = f"{opening_time} - {closing_time}"
            elif place.category in ["park", "beach"]:
                opening_time = "5:00 AM"
                closing_time = "10:00 PM"
                opening_hours = f"{opening_time} - {closing_time}"
            elif place.category == "market":
                opening_time = "10:00 AM"
                closing_time = "10:00 PM"
                opening_hours = f"{opening_time} - {closing_time}"
                closed_on = "Sunday (some shops)"
        
        return TimingIntelligence(
            best_time_of_day=place.best_time_to_visit or profile.get("best_time", "morning"),
            time_to_avoid=profile.get("avoid_time"),
            recommended_duration=place.recommended_duration or profile.get("typical_duration", "1-2 hours"),
            opening_time=opening_time,
            closing_time=closing_time,
            opening_hours=opening_hours,
            closed_on=closed_on,
            peak_hours="weekends and holidays" if place.category in ["monument", "museum", "temple"] else "evenings",
            reasoning=f"Best visited {profile.get('best_time', 'morning')} to avoid crowds and heat"
        )
    
    def _analyze_accessibility(self, place: PlaceOption, profile: Dict) -> AccessibilityInfo:
        """How to reach"""
        transport = place.transport_modes or profile.get("transport", ["metro", "cab"])
        return AccessibilityInfo(
            transport_modes=transport,
            recommended_transport=transport[0] if transport else "cab",
            estimated_travel_time="15-30 mins from city center",
            parking_available=place.category not in ["temple", "market"],
            accessibility_notes="Wheelchair accessible" if place.category in ["museum", "mall"] else None
        )
    
    def _analyze_day_plan_fit(self, place: PlaceOption, all_places: List[PlaceOption], profile: Dict) -> DayPlanFit:
        """Where it fits in the day"""
        best_time = profile.get("best_time", "morning")
        
        if best_time == "morning":
            position = "morning-start"
        elif best_time == "evening":
            position = "evening-end"
        elif best_time == "sunset":
            position = "evening-end"
        else:
            position = "mid-day"
        
        # Find nearby places (same city, different category)
        nearby = [p.name for p in all_places if p.city == place.city and p.category != place.category][:3]
        
        return DayPlanFit(
            position_in_day=position,
            can_combine_with=nearby,
            distance_category="cluster" if nearby else "isolated",
            sequence_recommendation=f"Visit in {best_time}, combine with nearby attractions"
        )
    
    def _analyze_weather_crowd(self, place: PlaceOption, profile: Dict) -> WeatherCrowdAnalysis:
        """Weather and crowd dynamics"""
        weather_dep = place.weather_sensitivity or profile.get("weather_dependency", "outdoor")
        
        if weather_dep == "indoor":
            sensitivity = "low"
        elif weather_dep == "outdoor":
            sensitivity = "high"
        else:
            sensitivity = "medium"
        
        crowd = place.crowd_level or "moderate"
        ambiance = profile.get("ambiance", ["pleasant"])
        
        return WeatherCrowdAnalysis(
            weather_dependency=weather_dep,
            weather_sensitivity=sensitivity,
            crowd_level=crowd,
            crowd_type=profile.get("crowd_type", "mixed"),
            ambiance=ambiance,
            best_for_crowd_avoiders=(crowd in ["peaceful", "moderate"])
        )
    
    def _assess_priority(self, place: PlaceOption, match_score: float, profile: Dict) -> PriorityAssessment:
        """Must-visit or skippable?"""
        
        # Calculate priority score (0-10)
        priority_score = (place.rating / 5.0) * 4  # Rating: 0-4 points
        priority_score += (match_score / 100.0) * 3  # Match: 0-3 points
        
        if place.entry_fee == 0:
            priority_score += 1  # Free entry: +1 point
        
        if profile.get("cultural_value") == "very-high":
            priority_score += 2  # Cultural value: +2 points
        elif profile.get("cultural_value") == "high":
            priority_score += 1
        
        priority_score = min(priority_score, 10.0)
        
        # Determine level
        if priority_score >= 8.5:
            level = "must-visit"
            must_visit_because = f"Iconic {place.category} with {place.rating}★ rating - unmissable"
        elif priority_score >= 7.0:
            level = "highly-recommended"
            must_visit_because = f"Top-rated {place.category} worth visiting"
        elif priority_score >= 5.5:
            level = "recommended"
            must_visit_because = None
        elif priority_score >= 4.0:
            level = "optional"
            must_visit_because = None
        else:
            level = "skippable"
            must_visit_because = None
        
        # Who should skip/avoid
        skip_if = []
        who_should_avoid = []
        
        if place.entry_fee > 1000:
            skip_if.append("on tight budget")
        
        if profile.get("effort") in ["high", "strenuous"]:
            skip_if.append("limited mobility")
            who_should_avoid.append("elderly with mobility issues")
        
        if profile.get("weather_dependency") == "outdoor":
            skip_if.append("bad weather")
        
        if place.category in ["temple", "mosque"]:
            who_should_avoid.append("those not interested in religious sites")
        
        return PriorityAssessment(
            priority_level=level,
            priority_score=priority_score,
            skip_if=skip_if,
            must_visit_because=must_visit_because,
            who_should_avoid=who_should_avoid
        )
    
    def _generate_contextual_info(self, place: PlaceOption, profile: Dict) -> ContextualInfo:
        """Why this place exists and what makes it special"""
        
        experience = profile.get("experience", "cultural")
        category = place.category
        
        # Short summary
        short_summary = f"{place.rating}★ rated {category} in {place.city}"
        
        # Detailed description
        if place.description:
            detailed_description = place.description
        else:
            detailed_description = f"{place.name} is a renowned {category} located in {place.city}, attracting visitors with its {place.rating}★ rating and {experience} appeal."
        
        # Historical significance
        historical_significance = None
        if category in ["monument", "fort", "palace"]:
            historical_significance = f"Historical landmark with significant heritage value, representing {place.city}'s rich past and architectural legacy."
        elif category == "museum":
            historical_significance = f"Preserves and showcases important historical artifacts and cultural heritage of the region."
        
        # Cultural significance
        cultural_significance = None
        if category in ["temple", "mosque", "church", "gurudwara"]:
            cultural_significance = f"Sacred place of worship with deep religious and cultural importance for devotees and visitors."
        elif category in ["cultural center", "theater", "art gallery"]:
            cultural_significance = f"Hub of cultural activities and artistic expression in {place.city}."
        
        # Architectural significance
        architectural_significance = None
        if category in ["monument", "fort", "palace", "temple", "mosque"]:
            architectural_significance = f"Features distinctive {experience} architecture showcasing craftsmanship and design excellence."
        
        # Why visit - compelling reasons
        why_visit = []
        if place.rating >= 4.7:
            why_visit.append(f"Exceptional {place.rating}★ rating - one of the top-rated {category}s")
        elif place.rating >= 4.4:
            why_visit.append(f"Highly rated {category} with {place.rating}★ rating")
        
        if place.entry_fee == 0:
            why_visit.append("Free entry - excellent value for money")
        
        if category in ["monument", "fort", "palace"]:
            why_visit.append("Rich historical heritage and architectural beauty")
        elif category == "museum":
            why_visit.append("Educational experience with rare exhibits and artifacts")
        elif category in ["temple", "mosque"]:
            why_visit.append("Spiritual experience and peaceful atmosphere")
        elif category == "park":
            why_visit.append("Natural beauty and relaxing green space")
        elif category == "beach":
            why_visit.append("Scenic coastal views and refreshing sea breeze")
        
        if profile.get("cultural_value") in ["high", "very-high"]:
            why_visit.append(f"Important cultural landmark of {place.city}")
        
        if not why_visit:
            why_visit.append(f"Popular {category} worth visiting in {place.city}")
        
        # What makes special
        special_points = []
        if place.rating >= 4.5:
            special_points.append(f"exceptional {place.rating}★ rating")
        if place.entry_fee == 0:
            special_points.append("free entry")
        if profile.get("cultural_value") == "very-high":
            special_points.append("high cultural significance")
        
        what_makes_special = ", ".join(special_points) if special_points else f"well-rated {category}"
        
        # Famous for
        famous_for = []
        if category == "monument":
            famous_for = ["architecture", "history", "photo opportunities"]
        elif category == "museum":
            famous_for = ["exhibits", "artifacts", "collections"]
        elif category == "temple":
            famous_for = ["architecture", "spirituality", "rituals"]
        elif category == "park":
            famous_for = ["greenery", "recreation", "peaceful ambiance"]
        elif category == "beach":
            famous_for = ["sunset views", "water activities", "scenic beauty"]
        elif category == "market":
            famous_for = ["shopping", "local culture", "street food"]
        
        # Must-see features
        must_see = []
        if category == "monument":
            must_see = ["Main structure and architecture", "Historical plaques and inscriptions", "Photo points"]
        elif category == "museum":
            must_see = ["Key exhibits", "Rare artifacts", "Interactive sections"]
        elif category == "temple":
            must_see = ["Main deity/sanctum", "Architectural details", "Temple courtyard"]
        elif category == "park":
            must_see = ["Gardens", "Walking trails", "Viewpoints"]
        elif category == "beach":
            must_see = ["Sunset point", "Beach stretch", "Water activities area"]
        
        # Interesting facts
        interesting_facts = []
        if place.rating >= 4.7:
            interesting_facts.append(f"Consistently rated above 4.7★ by thousands of visitors")
        if place.entry_fee == 0:
            interesting_facts.append("One of the free attractions, making it accessible to all")
        
        return ContextualInfo(
            place_name=place.name,
            category=category,
            short_summary=short_summary,
            detailed_description=detailed_description,
            historical_significance=historical_significance,
            cultural_significance=cultural_significance,
            architectural_significance=architectural_significance,
            why_visit=why_visit,
            what_makes_special=what_makes_special.capitalize(),
            famous_for=famous_for,
            experience_type=experience,
            must_see_features=must_see,
            interesting_facts=interesting_facts
        )
    
    def _generate_practical_details(self, place: PlaceOption, profile: Dict) -> PracticalDetails:
        """Tickets, queues, dress codes"""
        
        # Queue situation
        if place.rating >= 4.5:
            queue = "long" if place.category in ["monument", "museum"] else "moderate"
        elif place.entry_fee == 0:
            queue = "short"
        else:
            queue = "moderate"
        
        # Ticket booking
        if place.entry_fee == 0:
            booking = "free-entry"
        elif place.entry_fee > 500:
            booking = "online"
        else:
            booking = "both"
        
        # Dress code
        dress = None
        if place.category in ["temple", "mosque"]:
            dress = "Modest clothing required - cover shoulders and knees"
        
        # Restrictions
        restrictions = []
        if place.category in ["temple", "mosque"]:
            restrictions.extend(["Remove footwear", "Maintain silence", "Photography may be restricted"])
        elif place.category == "museum":
            restrictions.extend(["No flash photography", "No food/drinks inside"])
        
        if place.special_notes:
            restrictions.append(place.special_notes)
        
        # Facilities
        facilities = []
        if place.category in ["museum", "monument", "park"]:
            facilities.extend(["Washroom", "Drinking water"])
        if place.entry_fee > 200:
            facilities.append("Paid guide available")
        if place.category in ["park", "monument"]:
            facilities.append("Cafe/snacks")
        
        return PracticalDetails(
            entry_fee=place.entry_fee,
            ticket_booking=booking,
            queue_situation=queue,
            dress_code=dress,
            restrictions=restrictions,
            facilities=facilities
        )
    
    def _analyze_effort_reward(self, place: PlaceOption, profile: Dict) -> EffortRewardBalance:
        """Is the effort worth it?"""
        
        effort = profile.get("effort", "low")
        
        # Calculate reward based on rating and experience
        if place.rating >= 4.7:
            reward = "exceptional"
            reward_score = 9
        elif place.rating >= 4.4:
            reward = "excellent"
            reward_score = 8
        elif place.rating >= 4.0:
            reward = "good"
            reward_score = 7
        elif place.rating >= 3.5:
            reward = "average"
            reward_score = 6
        else:
            reward = "disappointing"
            reward_score = 4
        
        # Value score calculation
        effort_map = {"minimal": 1, "low": 2, "moderate": 4, "high": 7, "strenuous": 9}
        effort_num = effort_map.get(effort, 2)
        
        value_score = (reward_score / effort_num) * 10
        value_score = min(value_score, 10.0)
        
        worth_it = value_score >= 6.0
        
        # Reasoning
        if worth_it:
            if place.entry_fee == 0:
                reasoning = f"{reward.capitalize()} experience with free entry - absolutely worth it"
            else:
                reasoning = f"{reward.capitalize()} experience justifies the {effort} effort required"
        else:
            reasoning = f"{effort.capitalize()} effort for {reward} experience - may not be worth it for everyone"
        
        return EffortRewardBalance(
            effort_level=effort,
            reward_level=reward,
            value_score=value_score,
            worth_it=worth_it,
            reasoning=reasoning
        )
    
    def _generate_tags(self, place: PlaceOption, profile: Dict, priority: PriorityAssessment) -> List[str]:
        """Generate smart tags"""
        tags = []
        
        if place.entry_fee == 0:
            tags.append("free")
        if place.rating >= 4.7:
            tags.append("top-rated")
        elif place.rating >= 4.3:
            tags.append("highly-rated")
        
        if priority.priority_level == "must-visit":
            tags.append("must-visit")
        
        if profile.get("experience"):
            tags.append(profile["experience"])
        
        if profile.get("weather_dependency") == "indoor":
            tags.append("weather-proof")
        
        if "peaceful" in profile.get("ambiance", []):
            tags.append("peaceful")
        
        if place.category in ["temple", "mosque"]:
            tags.append("spiritual")
        
        return tags
    
    def _extract_best_for(self, audience: AudienceSuitability) -> List[str]:
        """Extract best for list"""
        best_for = []
        
        if audience.couples["score"] >= 8:
            best_for.append("couples")
        if audience.families["score"] >= 8:
            best_for.append("families")
        if audience.kids["score"] >= 8:
            best_for.append("kids")
        if audience.solo_travelers["score"] >= 8:
            best_for.append("solo travelers")
        if audience.elderly["score"] >= 8:
            best_for.append("elderly")
        
        return best_for if best_for else ["all travelers"]
    
    def _generate_insights(
        self, 
        place: PlaceOption, 
        profile: Dict, 
        priority: PriorityAssessment,
        effort_reward: EffortRewardBalance
    ) -> List[PlaceInsight]:
        """Generate intelligent insights"""
        insights = []
        
        # Free entry advantage
        if place.entry_fee == 0:
            insights.append(PlaceInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message="Free entry - excellent value for budget travelers",
                priority=5
            ))
        
        # High rating
        if place.rating >= 4.5:
            insights.append(PlaceInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message=f"Exceptional {place.rating}★ rating - highly recommended by visitors",
                priority=4
            ))
        
        # Must visit
        if priority.priority_level == "must-visit":
            insights.append(PlaceInsight(
                type=INSIGHT_TYPE_TIP,
                message=priority.must_visit_because or "Top priority attraction",
                priority=5
            ))
        
        # Weather consideration
        if profile.get("weather_dependency") == "outdoor":
            insights.append(PlaceInsight(
                type=INSIGHT_TYPE_CONSIDERATION,
                message="Outdoor attraction - check weather before visiting",
                priority=3
            ))
        
        # Crowd warning
        if place.crowd_level == "very-crowded":
            insights.append(PlaceInsight(
                type=INSIGHT_TYPE_WARNING,
                message="Very crowded - visit early morning or book skip-the-line tickets",
                priority=4
            ))
        
        # Effort vs reward
        if effort_reward.worth_it and effort_reward.value_score >= 8:
            insights.append(PlaceInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message=effort_reward.reasoning,
                priority=4
            ))
        
        return sorted(insights, key=lambda x: x.priority, reverse=True)
    
    def _generate_recommendations(
        self,
        place: PlaceOption,
        profile: Dict,
        audience: AudienceSuitability,
        priority: PriorityAssessment
    ) -> List[PlaceRecommendation]:
        """Generate smart recommendations"""
        recommendations = []
        
        # Rating-based
        if place.rating >= 4.5:
            recommendations.append(PlaceRecommendation(
                reason=f"{place.rating}★ rating indicates high visitor satisfaction and quality experience",
                category="rating",
                sentiment=SENTIMENT_POSITIVE
            ))
        
        # Price-based
        if place.entry_fee == 0:
            recommendations.append(PlaceRecommendation(
                reason="No entry fee makes this accessible for all budgets",
                category="price",
                sentiment=SENTIMENT_POSITIVE
            ))
        elif place.entry_fee > 1000:
            recommendations.append(PlaceRecommendation(
                reason=f"High entry fee of Rs.{place.entry_fee} - consider if worth the cost",
                category="price",
                sentiment=SENTIMENT_NEUTRAL
            ))
        
        # Audience-based
        if audience.families["score"] >= 8:
            recommendations.append(PlaceRecommendation(
                reason="Perfect for families with children - educational and engaging",
                category="audience",
                sentiment=SENTIMENT_POSITIVE
            ))
        
        # Timing-based
        best_time = profile.get("best_time", "morning")
        recommendations.append(PlaceRecommendation(
            reason=f"{place.category.capitalize()} attraction - Best visited {best_time}",
            category="timing",
            sentiment=SENTIMENT_NEUTRAL
        ))
        
        return recommendations
    
    def _generate_verdict(self, place: PlaceOption, priority: PriorityAssessment, effort_reward: EffortRewardBalance) -> str:
        """Generate one-line verdict"""
        
        if priority.priority_level == "must-visit":
            return f"Must-visit {place.category} - {place.rating}★ rated, {effort_reward.reward_level} experience"
        elif priority.priority_level == "highly-recommended":
            return f"Highly recommended {place.category} - {place.rating}★ with {effort_reward.reward_level} experience"
        elif priority.priority_level == "recommended":
            return f"Recommended {place.category} - {place.rating}★, good for {', '.join(self._extract_best_for(self._analyze_audience_suitability(place, {})))}"
        elif priority.priority_level == "optional":
            return f"Optional {place.category} - visit if time permits"
        else:
            return f"Skippable - better options available"
    
    def _generate_market_analysis(self, places: List[PlaceOption], enriched: List[EnrichedPlace]) -> Dict[str, Any]:
        """Generate market-level analysis"""
        
        total = len(places)
        free_count = sum(1 for p in places if p.entry_fee == 0)
        avg_rating = statistics.mean([p.rating for p in places]) if places else 0
        avg_fee = statistics.mean([p.entry_fee for p in places]) if places else 0
        
        # Category distribution
        category_dist = defaultdict(int)
        for p in places:
            category_dist[p.category] += 1
        
        # Priority distribution
        priority_dist = defaultdict(int)
        for e in enriched:
            priority_dist[e.priority_assessment.priority_level] += 1
        
        return {
            "total_options": total,
            "free_places": free_count,
            "avg_rating": round(avg_rating, 1),
            "avg_entry_fee": round(avg_fee, 0),
            "category_distribution": dict(category_dist),
            "priority_distribution": dict(priority_dist),
            "must_visit_count": priority_dist.get("must-visit", 0),
            "weather_proof_count": sum(1 for e in enriched if e.weather_crowd_analysis.weather_dependency == "indoor")
        }
    
    def _generate_travel_tips(self, enriched: List[EnrichedPlace], preferences: Dict[str, Any]) -> List[str]:
        """Generate smart travel tips"""
        tips = []
        
        if not enriched:
            return tips
        
        # Free attractions tip
        free_count = sum(1 for e in enriched if e.place.entry_fee == 0)
        if free_count > 0:
            tips.append(f"{free_count} attractions with free entry - great for budget travelers")
        
        # Must-visit tip
        must_visit = [e for e in enriched if e.priority_assessment.priority_level == "must-visit"]
        if must_visit:
            tips.append(f"{len(must_visit)} must-visit attractions - prioritize these in your itinerary")
        
        # Weather tip
        outdoor_count = sum(1 for e in enriched if e.weather_crowd_analysis.weather_dependency == "outdoor")
        if outdoor_count >= len(enriched) * 0.6:
            tips.append("Most attractions are outdoors - check weather forecast before planning")
        
        # Timing tip
        morning_recs = sum(1 for e in enriched if "morning" in e.timing_intelligence.best_time_of_day)
        if morning_recs >= len(enriched) * 0.5:
            tips.append("Start your day early - many attractions are best visited in the morning")
        
        # Crowd tip
        crowded = sum(1 for e in enriched if e.weather_crowd_analysis.crowd_level in ["crowded", "very-crowded"])
        if crowded > 0:
            tips.append(f"{crowded} attractions tend to be crowded - visit during weekdays or early hours")
        
        return tips[:5]
    
    def _generate_best_choice(self, enriched: List[EnrichedPlace]) -> Optional[str]:
        """Generate best choice summary"""
        if not enriched:
            return None
        
        best = enriched[0]
        place = best.place
        
        return (f"{place.name} (Rank #{best.rank}) - {place.category} with {place.rating}★ rating, "
                f"{'free entry' if place.entry_fee == 0 else f'Rs.{place.entry_fee} entry'}, "
                f"{best.priority_assessment.priority_level}")


# ============================================================================
# PUBLIC API
# ============================================================================

def enrich_places(
    places: List[PlaceOption], 
    preferences: Optional[Dict[str, Any]] = None,
    openai_client: Optional[OpenAI] = None,
    use_knowledge_system: bool = True
) -> EnrichmentResult:
    """
    Enrich places with comprehensive intelligence.
    
    Args:
        places: List of PlaceOption objects to enrich
        preferences: User preferences (budget, traveler type, etc.)
        openai_client: OpenAI client for knowledge enrichment (auto-initializes from config if None)
        use_knowledge_system: Enable Wikipedia + GPT knowledge enrichment (default: True)
    
    Returns:
        EnrichmentResult with comprehensive intelligence layers including:
        - Historical summaries
        - Why visit reasons
        - What it's famous for
        - Best season/time of day
        - Suitability for couples/families/kids
        - Cultural importance
        - Interesting facts
        - Practical tips
        - Crowd information
        - Weather sensitivity
    """
    engine = PlacesIntelligenceEngine(
        openai_client=openai_client,
        use_knowledge_system=use_knowledge_system
    )
    return engine.enrich_places(places, preferences)


