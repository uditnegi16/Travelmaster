"""
Flight Enrichment Layer - Intelligence + Reasoning + UX + Product Brain

This is NOT formatting. This is NOT API processing.
This is where TravelGuru becomes smart.

Architecture Flow:
API Tool → Normalize → Schema Objects → Enrichment → Composer → Final Output

Enrichment = Intelligence + Reasoning + UX + Product Brain

This layer transforms raw List[FlightOption] into decision-ready, insight-rich,
explainable recommendations that help users make informed travel decisions.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from pydantic import BaseModel, Field

from shared.schemas import FlightOption
from shared.constants import (
    # Insight types
    INSIGHT_TYPE_ADVANTAGE,
    INSIGHT_TYPE_CONSIDERATION,
    INSIGHT_TYPE_TIP,
    INSIGHT_TYPE_WARNING,
    # Sentiments
    SENTIMENT_POSITIVE,
    SENTIMENT_NEUTRAL,
    SENTIMENT_NEGATIVE,
    # Price categories
    PRICE_BUDGET,
    PRICE_MODERATE,
    PRICE_PREMIUM,
    # Time segments
    TIME_RED_EYE,
    TIME_EARLY_MORNING,
    TIME_MORNING,
    TIME_AFTERNOON,
    TIME_EVENING,
    TIME_NIGHT,
    # Recommendation categories
    REC_CATEGORY_TIMING,
    REC_CATEGORY_PRICE,
    REC_CATEGORY_CONVENIENCE,
    REC_CATEGORY_DURATION,
    REC_CATEGORY_AIRLINE,
    # Flight tags
    TAG_FLIGHT_CHEAPEST,
    TAG_FLIGHT_FASTEST,
    TAG_FLIGHT_BEST_VALUE,
    TAG_FLIGHT_MOST_CONVENIENT,
    TAG_FLIGHT_DIRECT,
    TAG_FLIGHT_MORNING_DEPARTURE,
    TAG_FLIGHT_EVENING_DEPARTURE,
    TAG_FLIGHT_RECOMMENDED,
    TAG_FLIGHT_BUDGET_FRIENDLY,
    TAG_FLIGHT_PREMIUM,
    # Scoring ranges
    SCORE_MIN,
    SCORE_MAX,
    MATCH_SCORE_MIN,
    MATCH_SCORE_MAX,
    # Enrichment weights
    WEIGHT_FLIGHT_PRICE,
    WEIGHT_FLIGHT_TIME,
    WEIGHT_FLIGHT_CONVENIENCE,
    WEIGHT_FLIGHT_COMFORT,
    # Preferences
    PREF_BUDGET_PREFERENCE,
    PREF_TIMING_PREFERENCE,
)


# ============================================================================
# ENRICHED OUTPUT SCHEMAS
# ============================================================================

class FlightInsight(BaseModel):
    """
    Represents an intelligent insight about a flight.
    These are AI-generated observations that help users make decisions.
    """
    type: str = Field(..., description=f"Type of insight: '{INSIGHT_TYPE_ADVANTAGE}', '{INSIGHT_TYPE_CONSIDERATION}', '{INSIGHT_TYPE_TIP}', '{INSIGHT_TYPE_WARNING}'")
    message: str = Field(..., description="Human-readable insight message")
    priority: int = Field(default=1, description="Priority level (1=low, 5=critical)")
    
    model_config = {"extra": "forbid"}


class FlightRecommendation(BaseModel):
    """
    Represents a smart recommendation or reason for/against a flight.
    """
    reason: str = Field(..., description="Explanation of why this is recommended or not")
    category: str = Field(
        ...,
        description=f"Category: '{REC_CATEGORY_TIMING}', '{REC_CATEGORY_PRICE}', '{REC_CATEGORY_CONVENIENCE}', '{REC_CATEGORY_DURATION}', '{REC_CATEGORY_AIRLINE}'"
    )
    sentiment: str = Field(..., description=f"{SENTIMENT_POSITIVE}, {SENTIMENT_NEUTRAL}, or {SENTIMENT_NEGATIVE}")
    
    model_config = {"extra": "forbid"}


class FlightSegmentAnalysis(BaseModel):
    """
    Analyzes flight timing in the context of a day.
    """
    segment: str = Field(..., description=f"Time segment: '{TIME_RED_EYE}', '{TIME_EARLY_MORNING}', '{TIME_MORNING}', '{TIME_AFTERNOON}', '{TIME_EVENING}', '{TIME_NIGHT}'")
    suitability: str = Field(..., description="Family/Business/Budget/Any traveler suitability")
    impact: str = Field(..., description="Impact on travel experience")
    
    model_config = {"extra": "forbid"}


class PriceIntelligence(BaseModel):
    """
    Smart pricing analysis and context.
    """
    price_category: str = Field(..., description=f"{PRICE_BUDGET}, {PRICE_MODERATE}, {PRICE_PREMIUM}")
    price_percentile: float = Field(..., description="Percentile rank (0-100) compared to other options")
    is_deal: bool = Field(default=False, description="Whether this is considered a good deal")
    savings_vs_average: int = Field(default=0, description="Savings compared to average price (can be negative)")
    value_score: float = Field(..., description=f"Composite value score ({SCORE_MIN}-{SCORE_MAX}) considering price, time, convenience")
    
    model_config = {"extra": "forbid"}


class ConvenienceScore(BaseModel):
    """
    Quantifies and explains flight convenience.
    """
    overall_score: float = Field(..., description=f"Overall convenience score ({SCORE_MIN}-{SCORE_MAX})")
    timing_score: float = Field(..., description=f"How convenient are departure/arrival times ({SCORE_MIN}-{SCORE_MAX})")
    duration_score: float = Field(..., description=f"How good is the flight duration ({SCORE_MIN}-{SCORE_MAX})")
    stops_score: float = Field(..., description=f"Score based on number of stops ({SCORE_MIN}-{SCORE_MAX})")
    explanation: str = Field(..., description="Human-readable explanation of the convenience score")
    
    model_config = {"extra": "forbid"}


class EnrichedFlight(BaseModel):
    """
    An enriched flight with intelligence, reasoning, and decision support.
    This is the output of the enrichment layer.
    """
    # Original flight data
    flight: FlightOption = Field(..., description="The original normalized flight data")
    
    # Intelligence layer
    insights: List[FlightInsight] = Field(
        default_factory=list,
        description="AI-generated insights about this flight"
    )
    recommendations: List[FlightRecommendation] = Field(
        default_factory=list,
        description="Smart recommendations explaining pros/cons"
    )
    
    # Reasoning layer
    timing_analysis: FlightSegmentAnalysis = Field(
        ...,
        description="Analysis of departure/arrival timing"
    )
    price_intelligence: PriceIntelligence = Field(
        ...,
        description="Smart pricing context and analysis"
    )
    convenience: ConvenienceScore = Field(
        ...,
        description="Quantified convenience score with explanation"
    )
    
    # Product brain
    rank: int = Field(..., description="Overall ranking among all options (1=best)")
    match_score: float = Field(..., description=f"How well this matches user needs ({MATCH_SCORE_MIN}-{MATCH_SCORE_MAX})")
    tags: List[str] = Field(
        default_factory=list,
        description="Smart tags: 'best-value', 'fastest', 'most-convenient', 'budget-friendly', etc."
    )
    
    # UX layer
    summary: str = Field(..., description="One-line summary for quick scanning")
    best_for: List[str] = Field(
        default_factory=list,
        description="Who this flight is best for: 'families', 'business', 'budget-conscious', etc."
    )
    
    model_config = {"extra": "forbid"}


class FlightEnrichmentResult(BaseModel):
    """
    Complete enrichment result with metadata and market intelligence.
    """
    enriched_flights: List[EnrichedFlight] = Field(
        ...,
        description="List of enriched flights with intelligence"
    )
    market_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Overall market analysis: price ranges, best time to book, etc."
    )
    travel_tips: List[str] = Field(
        default_factory=list,
        description="Smart travel tips based on the route and options"
    )
    best_choice: Optional[str] = Field(
        default=None,
        description="ID of the recommended best choice with explanation"
    )
    
    model_config = {"extra": "forbid"}


# ============================================================================
# INTELLIGENCE ENGINE
# ============================================================================

class FlightIntelligenceEngine:
    """
    The brain that adds intelligence to flight data.
    
    Responsibilities:
    1. Analyze timing patterns (red-eye, early morning, prime time, etc.)
    2. Compute price intelligence (percentiles, deals, value scores)
    3. Generate insights and recommendations
    4. Calculate convenience and match scores
    5. Add smart tags and categorization
    """
    
    def __init__(self, user_context: Optional[Dict[str, Any]] = None):
        """
        Initialize the intelligence engine with optional user context.
        
        Args:
            user_context: Optional context like trip purpose, traveler types, preferences
                         Supported fields:
                         - budget_preference: PRICE_BUDGET, PRICE_MODERATE, PRICE_PREMIUM
                         - timing_preference: TIME_MORNING, TIME_EVENING, "flexible", TIME_RED_EYE
                         - traveler_type: STYLE_FAMILY, STYLE_BUSINESS, STYLE_SOLO (future)
                         - baggage_sensitive: bool (future)
                         - avoid_layovers: bool (future)
        """
        self.user_context = user_context or {}
    
    def enrich_flights(self, flights: List[FlightOption]) -> FlightEnrichmentResult:
        """
        Main enrichment method - transforms raw flights into intelligent recommendations.
        
        Args:
            flights: List of normalized flight options
            
        Returns:
            FlightEnrichmentResult with enriched data and market analysis
        """
        if not flights:
            return FlightEnrichmentResult(
                enriched_flights=[],
                market_analysis={"error": "No flights to enrich"},
                travel_tips=[]
            )
        
        # Step 1: Compute market statistics
        market_stats = self._compute_market_statistics(flights)
        
        # Step 2: Enrich each flight
        enriched = []
        for flight in flights:
            enriched_flight = self._enrich_single_flight(flight, market_stats)
            enriched.append(enriched_flight)
        
        # Step 3: Rank flights based on match scores
        enriched = self._rank_flights(enriched)
        
        # Step 4: Generate market analysis and tips
        market_analysis = self._generate_market_analysis(flights, market_stats)
        travel_tips = self._generate_travel_tips(flights, market_stats)
        
        # Step 5: Identify best choice
        best_choice = self._identify_best_choice(enriched)
        
        return FlightEnrichmentResult(
            enriched_flights=enriched,
            market_analysis=market_analysis,
            travel_tips=travel_tips,
            best_choice=best_choice
        )
    
    def _compute_market_statistics(self, flights: List[FlightOption]) -> Dict[str, Any]:
        """
        Compute market-level statistics for pricing and timing intelligence.
        """
        prices = [f.price for f in flights]
        durations = [f.duration_minutes or self._parse_duration(f.duration) for f in flights]        
        stops = [f.stops for f in flights]
        
        return {
            "price_min": min(prices),
            "price_max": max(prices),
            "price_avg": statistics.mean(prices),
            "price_median": statistics.median(prices),
            "price_stddev": statistics.stdev(prices) if len(prices) > 1 else 0,
            "duration_avg": statistics.mean(durations) if durations else 0,
            "duration_min": min(durations) if durations else 0,
            "stops_avg": statistics.mean(stops),
            "total_options": len(flights),
            "airlines": list(set(f.airline for f in flights)),
            "price_quartiles": self._compute_quartiles(prices)
        }
    
    def _compute_quartiles(self, prices: List[int]) -> Dict[str, float]:
        """Compute price quartiles for categorization."""
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        
        return {
            "q1": sorted_prices[n // 4] if n >= 4 else sorted_prices[0],
            "q2": sorted_prices[n // 2] if n >= 2 else sorted_prices[0],
            "q3": sorted_prices[3 * n // 4] if n >= 4 else sorted_prices[-1]
        }
    
    def _enrich_single_flight(
        self,
        flight: FlightOption,
        market_stats: Dict[str, Any]
    ) -> EnrichedFlight:
        """
        Enrich a single flight with intelligence and reasoning.
        """
        # Timing analysis
        timing_analysis = self._analyze_timing(flight)
        
        # Price intelligence
        price_intelligence = self._analyze_price(flight, market_stats)
        
        # Convenience score
        convenience = self._calculate_convenience(flight, market_stats)
        
        # Generate insights
        insights = self._generate_insights(flight, timing_analysis, price_intelligence, convenience)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            flight, timing_analysis, price_intelligence, convenience
        )
        
        # Calculate match score
        match_score = self._calculate_match_score(
            flight, timing_analysis, price_intelligence, convenience
        )
        
        # Generate tags
        tags = self._generate_tags(flight, price_intelligence, convenience, market_stats)
        
        # Generate summary
        summary = self._generate_summary(flight, tags)
        
        # Determine best for
        best_for = self._determine_best_for(timing_analysis, price_intelligence, convenience)
        
        return EnrichedFlight(
            flight=flight,
            insights=insights,
            recommendations=recommendations,
            timing_analysis=timing_analysis,
            price_intelligence=price_intelligence,
            convenience=convenience,
            rank=0,  # Will be set during ranking
            match_score=match_score,
            tags=tags,
            summary=summary,
            best_for=best_for
        )
    
    def _analyze_timing(self, flight: FlightOption) -> FlightSegmentAnalysis:
        """
        Analyze flight timing to determine time segment and suitability.
        """
        try:
            # Parse departure time
            dep_time = datetime.fromisoformat(flight.departure_time.replace('Z', '+00:00'))
            arr_time = datetime.fromisoformat(flight.arrival_time.replace('Z', '+00:00'))
            
            dep_hour = dep_time.hour
            arr_hour = arr_time.hour
            
            # Determine segment
            if dep_hour >= 0 and dep_hour < 5:
                segment = TIME_RED_EYE
                suitability = "Budget-conscious travelers, those maximizing time at destination"
                impact = "Challenging departure time but may save on accommodation"
            elif dep_hour >= 5 and dep_hour < 8:
                segment = TIME_EARLY_MORNING
                suitability = "Business travelers, early risers"
                impact = "Requires early wake-up but maximizes day at destination"
            elif dep_hour >= 8 and dep_hour < 12:
                segment = TIME_MORNING
                suitability = "Most travelers, families, business"
                impact = "Convenient departure time, good for productivity"
            elif dep_hour >= 12 and dep_hour < 17:
                segment = TIME_AFTERNOON
                suitability = "Flexible travelers, leisure trips"
                impact = "Comfortable timing, no rush in the morning"
            elif dep_hour >= 17 and dep_hour < 21:
                segment = TIME_EVENING
                suitability = "Working professionals, those who prefer evening travel"
                impact = "Can work full day before departure"
            else:
                segment = TIME_NIGHT
                suitability = "Night travelers, red-eye seekers"
                impact = "Travel during sleep hours, arrive in morning"
            
            # Adjust based on arrival time
            if arr_hour >= 23 or arr_hour < 6:
                impact += ". Late/very early arrival may require airport accommodation or early hotel check-in."
            
            return FlightSegmentAnalysis(
                segment=segment,
                suitability=suitability,
                impact=impact
            )
        
        except Exception as e:
            # Fallback for parsing errors
            return FlightSegmentAnalysis(
                segment="unknown",
                suitability="Unable to determine timing suitability",
                impact=f"Timing analysis unavailable: {str(e)}"
            )
    
    def _analyze_price(
        self,
        flight: FlightOption,
        market_stats: Dict[str, Any]
    ) -> PriceIntelligence:
        """
        Analyze price in market context to determine value and deals.
        """
        price = flight.price
        avg_price = market_stats["price_avg"]
        min_price = market_stats["price_min"]
        max_price = market_stats["price_max"]
        quartiles = market_stats["price_quartiles"]
        
        # Calculate percentile
        price_percentile = ((price - min_price) / (max_price - min_price) * 100) if max_price > min_price else 50
        
        # Categorize price
        if price <= quartiles["q1"]:
            price_category = PRICE_BUDGET
        elif price <= quartiles["q2"]:
            price_category = PRICE_MODERATE
        else:
            price_category = PRICE_PREMIUM
        
        # Determine if it's a deal
        savings_vs_average = int(avg_price - price)
        is_deal = price < avg_price * 0.85  # 15% below average
        
        # Calculate value score using constants
        # Consider price, duration, and stops
        price_score = SCORE_MAX - (price_percentile / 10)  # Lower price = higher score
        duration_minutes = flight.duration_minutes or self._parse_duration(flight.duration)        
        duration_score = max(0, SCORE_MAX - (duration_minutes / 60))  # Shorter = better
        stops_score = SCORE_MAX - (flight.stops * 3)  # Direct = best
        
        value_score = (price_score * WEIGHT_FLIGHT_PRICE + duration_score * 0.3 + stops_score * 0.2)
        value_score = min(SCORE_MAX, max(SCORE_MIN, value_score))
        
        return PriceIntelligence(
            price_category=price_category,
            price_percentile=round(price_percentile, 1),
            is_deal=is_deal,
            savings_vs_average=savings_vs_average,
            value_score=round(value_score, 1)
        )
    
    def _calculate_convenience(
        self,
        flight: FlightOption,
        market_stats: Dict[str, Any]
    ) -> ConvenienceScore:
        """
        Calculate overall convenience score with breakdown.
        """
        # Timing score (based on departure/arrival hours)
        try:
            dep_time = datetime.fromisoformat(flight.departure_time.replace('Z', '+00:00'))
            arr_time = datetime.fromisoformat(flight.arrival_time.replace('Z', '+00:00'))
            dep_hour = dep_time.hour
            arr_hour = arr_time.hour
            
            # Ideal: 8am-6pm departures, 8am-10pm arrivals
            timing_score = SCORE_MAX
            if dep_hour < 6 or dep_hour > 21:
                timing_score -= 3
            elif dep_hour < 8 or dep_hour > 18:
                timing_score -= 1
            
            if arr_hour < 6 or arr_hour > 23:
                timing_score -= 3
            elif arr_hour > 22:
                timing_score -= 1
            
            timing_score = max(SCORE_MIN, timing_score)
        except:
            timing_score = 5.0
        
        # Duration score
        duration_minutes = flight.duration_minutes or self._parse_duration(flight.duration)        
        avg_duration = market_stats.get("duration_avg", duration_minutes)
        
        if duration_minutes == 0:
            duration_score = 5.0
        elif duration_minutes <= avg_duration * 0.9:
            duration_score = SCORE_MAX
        elif duration_minutes <= avg_duration:
            duration_score = 8.0
        elif duration_minutes <= avg_duration * 1.2:
            duration_score = 6.0
        else:
            duration_score = 4.0
        
        # Stops score
        stops = flight.stops
        if stops == 0:
            stops_score = SCORE_MAX
        elif stops == 1:
            stops_score = 6.0
        elif stops == 2:
            stops_score = 3.0
        else:
            stops_score = 1.0
        
        # Overall convenience (weighted average)
        overall_score = (timing_score * 0.4 + duration_score * 0.3 + stops_score * 0.3)
        overall_score = round(overall_score, 1)
        
        # Generate explanation
        explanation_parts = []
        if timing_score >= 8:
            explanation_parts.append("excellent departure and arrival times")
        elif timing_score >= 5:
            explanation_parts.append("acceptable timing")
        else:
            explanation_parts.append("challenging departure/arrival times")
        
        if stops == 0:
            explanation_parts.append("direct flight")
        elif stops == 1:
            explanation_parts.append("one stop")
        else:
            explanation_parts.append(f"{stops} stops")
        
        if duration_score >= 8:
            explanation_parts.append("optimal duration")
        elif duration_score >= 5:
            explanation_parts.append("reasonable duration")
        else:
            explanation_parts.append("longer than average")
        
        explanation = f"This flight offers {', '.join(explanation_parts)}."
        
        return ConvenienceScore(
            overall_score=overall_score,
            timing_score=round(timing_score, 1),
            duration_score=round(duration_score, 1),
            stops_score=round(stops_score, 1),
            explanation=explanation
        )
    
    def _generate_insights(
        self,
        flight: FlightOption,
        timing: FlightSegmentAnalysis,
        price: PriceIntelligence,
        convenience: ConvenienceScore
    ) -> List[FlightInsight]:
        """
        Generate AI-powered insights about the flight.
        """
        insights = []
        
        # Price insights
        currency = flight.currency
        if price.is_deal:
            insights.append(FlightInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message=f"Great deal! {self._format_price(abs(price.savings_vs_average), currency)} below average price",
                priority=4
            ))
        elif price.price_category == PRICE_BUDGET:
            insights.append(FlightInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message="Budget-friendly option in the lowest price tier",
                priority=3
            ))
        elif price.price_category == PRICE_PREMIUM:
            insights.append(FlightInsight(
                type=INSIGHT_TYPE_CONSIDERATION,
                message="Premium priced - ensure the extra cost aligns with your needs",
                priority=2
            ))
        
        # Timing insights
        if timing.segment == TIME_RED_EYE:
            insights.append(FlightInsight(
                type=INSIGHT_TYPE_WARNING,
                message="Red-eye flight - travel during sleep hours. Consider fatigue impact.",
                priority=3
            ))
        elif timing.segment == TIME_EARLY_MORNING:
            insights.append(FlightInsight(
                type=INSIGHT_TYPE_TIP,
                message="Early departure requires arrival at airport before sunrise. Plan transport ahead.",
                priority=2
            ))
        elif timing.segment == TIME_MORNING:
            insights.append(FlightInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message="Convenient morning departure - ideal for most travelers",
                priority=2
            ))
        
        # Convenience insights
        if convenience.overall_score >= 8:
            insights.append(FlightInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message="Highly convenient flight with excellent timing and minimal disruption",
                priority=3
            ))
        elif convenience.overall_score < 5:
            insights.append(FlightInsight(
                type=INSIGHT_TYPE_CONSIDERATION,
                message="Lower convenience score - review timing and stops carefully",
                priority=3
            ))
        
        # Stops insight
        if flight.stops == 0:
            insights.append(FlightInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message="Direct flight - no layovers, less stress, faster journey",
                priority=4
            ))
        elif flight.stops >= 2:
            insights.append(FlightInsight(
                type=INSIGHT_TYPE_CONSIDERATION,
                message=f"Multiple stops ({flight.stops}) - significantly longer travel time and connection risk",
                priority=4
            ))
        
        # Value insight
        if price.value_score >= 8:
            insights.append(FlightInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message="Excellent value for money considering price, time, and convenience",
                priority=5
            ))
        
        return insights
    
    def _generate_recommendations(
        self,
        flight: FlightOption,
        timing: FlightSegmentAnalysis,
        price: PriceIntelligence,
        convenience: ConvenienceScore
    ) -> List[FlightRecommendation]:
        """
        Generate smart recommendations explaining pros and cons.
        """
        recommendations = []
        currency = flight.currency
        
        # Price recommendation
        if price.is_deal:
            recommendations.append(FlightRecommendation(
                reason=f"Priced {self._format_price(abs(price.savings_vs_average), currency)} below market average - excellent value",
                category=REC_CATEGORY_PRICE,
                sentiment=SENTIMENT_POSITIVE
            ))
        elif price.savings_vs_average < -5000:
            recommendations.append(FlightRecommendation(
                reason=f"{self._format_price(abs(price.savings_vs_average), currency)} above average - consider if premium features justify cost",
                category=REC_CATEGORY_PRICE,
                sentiment=SENTIMENT_NEGATIVE
            ))
        
        # Timing recommendation
        if timing.segment in [TIME_MORNING, TIME_AFTERNOON]:
            recommendations.append(FlightRecommendation(
                reason=f"{timing.segment.title()} departure is convenient for most travelers - no early wake-up stress",
                category=REC_CATEGORY_TIMING,
                sentiment=SENTIMENT_POSITIVE
            ))
        elif timing.segment == TIME_RED_EYE:
            recommendations.append(FlightRecommendation(
                reason="Red-eye flight saves a day but may cause fatigue - ideal if you can sleep on planes",
                category=REC_CATEGORY_TIMING,
                sentiment=SENTIMENT_NEUTRAL
            ))
        
        # Duration recommendation
        duration_minutes = self._parse_duration(flight.duration)
        hours = duration_minutes // 60
        minutes = duration_minutes % 60
        if flight.stops == 0 and hours < 10:
            recommendations.append(FlightRecommendation(
                reason=f"Direct flight with reasonable {hours}h {minutes}m duration - efficient travel",
                category=REC_CATEGORY_DURATION,
                sentiment=SENTIMENT_POSITIVE
            ))
        elif flight.stops > 0:
            recommendations.append(FlightRecommendation(
                reason=f"{flight.stops} stop(s) adds connection time and complexity - direct flights reduce hassle",
                category=REC_CATEGORY_CONVENIENCE,
                sentiment=SENTIMENT_NEGATIVE
            ))
        
        # Airline recommendation
        recommendations.append(FlightRecommendation(
            reason=f"{flight.airline} operates this route - check airline reviews for service quality",
            category=REC_CATEGORY_AIRLINE,
            sentiment=SENTIMENT_NEUTRAL
        ))
        
        return recommendations
    
    def _calculate_match_score(
        self,
        flight: FlightOption,
        timing: FlightSegmentAnalysis,
        price: PriceIntelligence,
        convenience: ConvenienceScore
    ) -> float:
        """
        Calculate how well this flight matches user needs.
        Returns score from MATCH_SCORE_MIN to MATCH_SCORE_MAX.
        """
        # Base score from value and convenience
        match_score = (price.value_score * 5) + (convenience.overall_score * 5)
        
        # Adjust based on user context
        user_budget = self.user_context.get(PREF_BUDGET_PREFERENCE, PRICE_MODERATE)
        user_timing = self.user_context.get(PREF_TIMING_PREFERENCE, "flexible")
        
        # Budget alignment
        if user_budget == PRICE_BUDGET and price.price_category == PRICE_BUDGET:
            match_score += 10
        elif user_budget == PRICE_PREMIUM and price.price_category == PRICE_PREMIUM:
            match_score += 5
        
        # Timing alignment
        if user_timing == TIME_MORNING and timing.segment == TIME_MORNING:
            match_score += 10
        elif user_timing == "flexible":
            match_score += 2
        
        # Penalize red-eyes unless explicitly preferred
        if timing.segment == TIME_RED_EYE and user_timing != TIME_RED_EYE:
            match_score -= 15
        
        return min(MATCH_SCORE_MAX, max(MATCH_SCORE_MIN, round(match_score, 1)))
    
    def _format_price(self, amount: int, currency: str = "INR") -> str:
        """
        Format price with proper currency symbol.
        
        Args:
            amount: Price amount
            currency: Currency code (INR, USD, EUR, etc.)
            
        Returns:
            Formatted price string with currency symbol
        """
        # Currency symbol mapping
        currency_symbols = {
            "INR": "₹",
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "AUD": "A$",
            "CAD": "C$",
            "SGD": "S$",
            "AED": "AED",
            "JPY": "¥"
        }
        
        symbol = currency_symbols.get(currency.upper(), currency)
        return f"{symbol}{amount:,}"
    
    def _generate_tags(
        self,
        flight: FlightOption,
        price: PriceIntelligence,
        convenience: ConvenienceScore,
        market_stats: Dict[str, Any]
    ) -> List[str]:
        """
        Generate smart tags for quick identification.
        """
        tags = []
        
        # Price tags
        if price.is_deal:
            tags.append(TAG_FLIGHT_BEST_VALUE)
        if flight.price == market_stats["price_min"]:
            tags.append(TAG_FLIGHT_CHEAPEST)
        if price.price_category == PRICE_BUDGET:
            tags.append(TAG_FLIGHT_BUDGET_FRIENDLY)
        elif price.price_category == PRICE_PREMIUM:
            tags.append(TAG_FLIGHT_PREMIUM)
        
        # Convenience tags
        if convenience.overall_score >= 8:
            tags.append(TAG_FLIGHT_MOST_CONVENIENT)
        if flight.stops == 0:
            tags.append(TAG_FLIGHT_DIRECT)
        
        # Duration tags
        duration_minutes = self._parse_duration(flight.duration)
        if duration_minutes > 0 and duration_minutes == market_stats.get("duration_min", float('inf')):
            tags.append(TAG_FLIGHT_FASTEST)
        
        # Timing tags
        try:
            dep_time = datetime.fromisoformat(flight.departure_time.replace('Z', '+00:00'))
            dep_hour = dep_time.hour
            if 8 <= dep_hour <= 12:
                tags.append(TAG_FLIGHT_MORNING_DEPARTURE)
            elif 17 <= dep_hour <= 21:
                tags.append(TAG_FLIGHT_EVENING_DEPARTURE)
        except:
            pass
        
        # Special tags
        if price.value_score >= 8 and convenience.overall_score >= 8:
            tags.append(TAG_FLIGHT_RECOMMENDED)
        
        return tags
    
    def _generate_summary(self, flight: FlightOption, tags: List[str]) -> str:
        """
        Generate a one-line summary for quick scanning.
        """
        duration_minutes = flight.duration_minutes or self._parse_duration(flight.duration)        
        hours = duration_minutes // 60
        minutes = duration_minutes % 60
        
        # Build summary components
        stops_text = "Direct" if flight.stops == 0 else f"{flight.stops} stop(s)"
        duration_text = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        price_text = self._format_price(flight.price, flight.currency)
        
        # Add special highlight
        highlight = ""
        if "best-value" in tags:
            highlight = " • Best Value"
        elif "cheapest" in tags:
            highlight = " • Cheapest"
        elif "fastest" in tags:
            highlight = " • Fastest"
        elif "most-convenient" in tags:
            highlight = " • Most Convenient"
        
        return f"{flight.airline} • {stops_text} • {duration_text} • {price_text}{highlight}"
    
    def _determine_best_for(
        self,
        timing: FlightSegmentAnalysis,
        price: PriceIntelligence,
        convenience: ConvenienceScore
    ) -> List[str]:
        """
        Determine what type of travelers this flight is best suited for.
        """
        best_for = []
        
        # Based on price
        if price.price_category == PRICE_BUDGET:
            best_for.append("budget-conscious travelers")
        elif price.price_category == PRICE_PREMIUM:
            best_for.append("travelers seeking premium experience")
        
        # Based on timing
        if timing.segment in [TIME_MORNING, TIME_AFTERNOON]:
            best_for.append("families")
        if timing.segment == TIME_EVENING:
            best_for.append("working professionals")
        if timing.segment == TIME_RED_EYE:
            best_for.append("travelers who can sleep on planes")
        
        # Based on convenience
        if convenience.overall_score >= 8:
            best_for.append("all travelers seeking convenience")
        
        # Based on value
        if price.value_score >= 8:
            best_for.append("value-seekers")
        
        return best_for if best_for else ["flexible travelers"]
    
    def _rank_flights(self, enriched: List[EnrichedFlight]) -> List[EnrichedFlight]:
        sorted_flights = sorted(enriched, key=lambda f: f.match_score, reverse=True)
        ranked: List[EnrichedFlight] = []
        for i, ef in enumerate(sorted_flights, start=1):
            ranked.append(ef.model_copy(update={"rank": i}))
        return ranked
    
    def _generate_market_analysis(
        self,
        flights: List[FlightOption],
        market_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate overall market analysis and insights.
        """
        avg_price = market_stats["price_avg"]
        min_price = market_stats["price_min"]
        max_price = market_stats["price_max"]
        
        analysis = {
            "total_options": market_stats["total_options"],
            "price_range": {
                "min": min_price,
                "max": max_price,
                "average": round(avg_price, 2),
                "spread": max_price - min_price
            },
            "airlines": market_stats["airlines"],
            "direct_flights_available": any(f.stops == 0 for f in flights),
            "price_distribution": {
                "budget": sum(1 for f in flights if f.price <= market_stats["price_quartiles"]["q1"]),
                "moderate": sum(1 for f in flights if market_stats["price_quartiles"]["q1"] < f.price <= market_stats["price_quartiles"]["q3"]),
                "premium": sum(1 for f in flights if f.price > market_stats["price_quartiles"]["q3"])
            },
            "timing_distribution": self._analyze_timing_distribution(flights),
            "best_booking_advice": self._generate_booking_advice(market_stats)
        }
        
        return analysis
    
    def _analyze_timing_distribution(self, flights: List[FlightOption]) -> Dict[str, int]:
        """
        Analyze distribution of flight timings.
        """
        distribution = defaultdict(int)
        
        for flight in flights:
            try:
                dep_time = datetime.fromisoformat(flight.departure_time.replace('Z', '+00:00'))
                hour = dep_time.hour
                
                if 0 <= hour < 5:
                    distribution["red-eye"] += 1
                elif 5 <= hour < 8:
                    distribution["early-morning"] += 1
                elif 8 <= hour < 12:
                    distribution["morning"] += 1
                elif 12 <= hour < 17:
                    distribution["afternoon"] += 1
                elif 17 <= hour < 21:
                    distribution["evening"] += 1
                else:
                    distribution["night"] += 1
            except:
                distribution["unknown"] += 1
        
        return dict(distribution)
    
    def _generate_booking_advice(self, market_stats: Dict[str, Any]) -> str:
        """
        Generate smart booking advice based on market analysis.
        """
        avg_price = market_stats["price_avg"]
        price_spread = market_stats["price_max"] - market_stats["price_min"]
        
        advice_parts = []
        
        if price_spread > avg_price * 0.5:
            advice_parts.append("Significant price variation exists")
        
        # Note: Currency taken from first flight as all should be same route/currency
        advice_parts.append(f"Average price is {self._format_price(int(avg_price), 'INR')}")
        
        if market_stats.get("direct_flights_available"):
            advice_parts.append("Direct flights available for faster travel")
        
        return ". ".join(advice_parts) + "."
    
    def _generate_travel_tips(
        self,
        flights: List[FlightOption],
        market_stats: Dict[str, Any]
    ) -> List[str]:
        """
        Generate smart travel tips based on the route and options.
        """
        tips = []
        
        # Generic tips
        tips.append("Book flights 2-3 months in advance for best prices on domestic routes")
        tips.append("Check baggage allowance before booking - budget airlines may charge extra")
        
        # Route-specific tips
        if any(f.stops > 0 for f in flights):
            tips.append("For flights with layovers, ensure minimum 2-hour connection time")
        
        # Timing tips
        timing_dist = self._analyze_timing_distribution(flights)
        if timing_dist.get("red-eye", 0) > 0:
            tips.append("Red-eye flights can save time but may affect first-day productivity")
        
        # Price tips
        if market_stats["price_max"] > market_stats["price_min"] * 2:
            tips.append("Price varies significantly - flexibility with dates can lead to major savings")
        
        # Practical tips
        tips.append("Arrive at airport 2 hours before domestic flights, 3 hours for international")
        tips.append("Download airline app for mobile check-in and real-time updates")
        
        return tips
    
    def _identify_best_choice(self, enriched: List[EnrichedFlight]) -> Optional[str]:
        """
        Identify and explain the recommended best choice.
        """
        if not enriched:
            return None
        
        # The top-ranked flight is our best choice
        best = enriched[0]
        
        reasons = []
        if best.price_intelligence.is_deal:
            reasons.append("excellent value")
        if best.convenience.overall_score >= 8:
            reasons.append("high convenience")
        if best.flight.stops == 0:
            reasons.append("direct flight")
        
        if reasons:
            reason_text = " with " + ", ".join(reasons)
        else:
            reason_text = ""
        
        return f"{best.flight.id} (Rank #{best.rank}){reason_text}"
    
    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse duration string like '8h 30m' into total minutes.
        Returns 0 if parsing fails.
        """
        if not duration_str:
            return 0
        
        try:
            total_minutes = 0
            parts = duration_str.lower().replace(' ', '').split('h')
            
            if len(parts) == 2:
                hours = int(parts[0]) if parts[0] else 0
                minutes_str = parts[1].replace('m', '')
                minutes = int(minutes_str) if minutes_str else 0
                total_minutes = hours * 60 + minutes
            elif 'm' in duration_str:
                minutes = int(duration_str.replace('m', ''))
                total_minutes = minutes
            elif 'h' in duration_str:
                hours = int(duration_str.replace('h', ''))
                total_minutes = hours * 60
            
            return total_minutes
        except:
            return 0


# ============================================================================
# PUBLIC API
# ============================================================================

def enrich_flights(
    flights: List[FlightOption],
    user_context: Optional[Dict[str, Any]] = None
) -> FlightEnrichmentResult:
    """
    Main public API for flight enrichment.
    
    Transforms raw flight options into intelligent, decision-ready recommendations
    with insights, reasoning, and smart categorization.
    
    Args:
        flights: List of normalized flight options
        user_context: Optional user context (budget preference, timing preference, etc.)
        
    Returns:
        FlightEnrichmentResult with enriched flights and market analysis
        
    Example:
        ```python
        flights = [FlightOption(...), FlightOption(...)]
        result = enrich_flights(flights, {"budget_preference": "budget"})
        
        for enriched in result.enriched_flights:
            print(f"Rank #{enriched.rank}: {enriched.summary}")
            print(f"Match Score: {enriched.match_score}/100")
            print(f"Tags: {', '.join(enriched.tags)}")
            
            for insight in enriched.insights:
                print(f"  {insight.type}: {insight.message}")
        ```
    """
    engine = FlightIntelligenceEngine(user_context)
    return engine.enrich_flights(flights)


# ============================================================================
# EXAMPLE USAGE & TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Example usage demonstrating the enrichment layer.
    """
    # Sample flights for testing
    sample_flights = [
        FlightOption(
            id="FL001",
            airline="Air India",
            origin="DEL",
            destination="BOM",
            departure_time="2026-02-15T08:30:00Z",
            arrival_time="2026-02-15T10:45:00Z",
            duration="2h 15m",
            stops=0,
            price=4500,
            currency="INR"
        ),
        FlightOption(
            id="FL002",
            airline="IndiGo",
            origin="DEL",
            destination="BOM",
            departure_time="2026-02-15T06:00:00Z",
            arrival_time="2026-02-15T08:20:00Z",
            duration="2h 20m",
            stops=0,
            price=3800,
            currency="INR"
        ),
        FlightOption(
            id="FL003",
            airline="SpiceJet",
            origin="DEL",
            destination="BOM",
            departure_time="2026-02-15T14:30:00Z",
            arrival_time="2026-02-15T18:45:00Z",
            duration="4h 15m",
            stops=1,
            price=3200,
            currency="INR"
        )
    ]
    
    # Enrich flights
    result = enrich_flights(sample_flights, {"budget_preference": "moderate"})
    
    print("=" * 80)
    print("FLIGHT ENRICHMENT RESULTS")
    print("=" * 80)
    
    print(f"\nMarket Analysis:")
    print(f"  Total Options: {result.market_analysis['total_options']}")
    print(f"  Price Range: ₹{result.market_analysis['price_range']['min']:,} - ₹{result.market_analysis['price_range']['max']:,}")
    print(f"  Average Price: ₹{result.market_analysis['price_range']['average']:,.0f}")
    print(f"  Note: Using INR currency for test data")
    
    print(f"\nBest Choice: {result.best_choice}")
    
    print(f"\n{'-' * 80}")
    for enriched in result.enriched_flights:
        print(f"\nRank #{enriched.rank} - {enriched.summary}")
        print(f"Match Score: {enriched.match_score}/100")
        print(f"Tags: {', '.join(enriched.tags)}")
        print(f"Best For: {', '.join(enriched.best_for)}")
        
        print(f"\n  Timing: {enriched.timing_analysis.segment} - {enriched.timing_analysis.impact}")
        print(f"  Price: {enriched.price_intelligence.price_category} (Percentile: {enriched.price_intelligence.price_percentile})")
        print(f"  Convenience Score: {enriched.convenience.overall_score}/10")
        print(f"  {enriched.convenience.explanation}")
        
        if enriched.insights:
            print(f"\n  Key Insights:")
            for insight in enriched.insights[:3]:  # Top 3 insights
                print(f"    • [{insight.type.upper()}] {insight.message}")
        
        print(f"{'-' * 80}")
    
    print(f"\nTravel Tips:")
    for tip in result.travel_tips[:5]:  # Top 5 tips
        print(f"  • {tip}")


