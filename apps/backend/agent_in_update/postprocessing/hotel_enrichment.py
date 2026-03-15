"""
Hotel Enrichment Layer - Intelligence + Reasoning + UX + Product Brain

This is NOT formatting. This is NOT API processing.
This is where TravelGuru becomes smart for hotel recommendations.

Architecture Flow:
API Tool → Normalize → Schema Objects → Enrichment → Composer → Final Output

Enrichment = Intelligence + Reasoning + UX + Product Brain

This layer transforms raw List[HotelOption] into decision-ready, insight-rich,
explainable recommendations that help users make informed accommodation decisions.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import statistics

from pydantic import BaseModel, Field

from shared.schemas import HotelOption
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
    PRICE_LUXURY,
    # Recommendation categories
    REC_CATEGORY_LOCATION,
    REC_CATEGORY_PRICE,
    REC_CATEGORY_COMFORT,
    REC_CATEGORY_AMENITIES,
    REC_CATEGORY_RATING,
    # Hotel tags
    TAG_HOTEL_CHEAPEST,
    TAG_HOTEL_BEST_VALUE,
    TAG_HOTEL_BEST_RATING,
    TAG_HOTEL_BEST_LOCATION,
    TAG_HOTEL_LUXURY,
    TAG_HOTEL_FAMILY_FRIENDLY,
    TAG_HOTEL_BUSINESS,
    TAG_HOTEL_BOUTIQUE,
    TAG_HOTEL_CENTRAL,
    TAG_HOTEL_POOL,
    TAG_HOTEL_SPA,
    # Scoring ranges
    SCORE_MIN,
    SCORE_MAX,
    MATCH_SCORE_MIN,
    MATCH_SCORE_MAX,
    # Enrichment weights
    WEIGHT_HOTEL_PRICE,
    WEIGHT_HOTEL_RATING,
    WEIGHT_HOTEL_AMENITIES,
    WEIGHT_HOTEL_STARS,
    # Preferences
    PREF_BUDGET_PREFERENCE,
    PREF_HOTEL_QUALITY,
)


# ============================================================================
# ENRICHED OUTPUT SCHEMAS
# ============================================================================

class HotelInsight(BaseModel):
    """
    Represents an intelligent insight about a hotel.
    These are AI-generated observations that help users make decisions.
    """
    type: str = Field(..., description=f"Type of insight: '{INSIGHT_TYPE_ADVANTAGE}', '{INSIGHT_TYPE_CONSIDERATION}', '{INSIGHT_TYPE_TIP}', '{INSIGHT_TYPE_WARNING}'")
    message: str = Field(..., description="Human-readable insight message")
    priority: int = Field(default=1, description="Priority level (1=low, 5=critical)")
    
    model_config = {"extra": "forbid"}


class HotelRecommendation(BaseModel):
    """
    Represents a smart recommendation or reason for/against a hotel.
    """
    reason: str = Field(..., description="Explanation of why this is recommended or not")
    category: str = Field(
        ...,
        description=f"Category: '{REC_CATEGORY_LOCATION}', '{REC_CATEGORY_PRICE}', '{REC_CATEGORY_COMFORT}', '{REC_CATEGORY_AMENITIES}', '{REC_CATEGORY_RATING}'"
    )
    sentiment: str = Field(..., description=f"{SENTIMENT_POSITIVE}, {SENTIMENT_NEUTRAL}, or {SENTIMENT_NEGATIVE}")
    
    model_config = {"extra": "forbid"}


class PriceIntelligence(BaseModel):
    """
    Smart pricing analysis and context for hotels.
    """
    price_category: str = Field(..., description=f"{PRICE_BUDGET}, {PRICE_MODERATE}, {PRICE_PREMIUM}, {PRICE_LUXURY}")
    price_percentile: float = Field(..., description="Percentile rank (0-100) compared to other options")
    is_deal: bool = Field(default=False, description="Whether this is considered a good deal")
    savings_vs_average: int = Field(default=0, description="Savings compared to average price (can be negative)")
    value_score: float = Field(..., description=f"Composite value score ({SCORE_MIN}-{SCORE_MAX}) considering price, rating, amenities")
    
    model_config = {"extra": "forbid"}


class AmenitiesAnalysis(BaseModel):
    """
    Analysis of hotel amenities and facilities.
    """
    total_amenities: int = Field(..., description="Total number of amenities")
    key_amenities: List[str] = Field(default_factory=list, description="Most important amenities")
    amenity_score: float = Field(..., description=f"Amenity richness score ({SCORE_MIN}-{SCORE_MAX})")
    missing_essentials: List[str] = Field(default_factory=list, description="Essential amenities that are missing")
    unique_features: List[str] = Field(default_factory=list, description="Unique or standout features")
    
    model_config = {"extra": "forbid"}


class QualityScore(BaseModel):
    """
    Quantifies and explains hotel quality.
    """
    overall_score: float = Field(..., description=f"Overall quality score ({SCORE_MIN}-{SCORE_MAX})")
    rating_score: float = Field(..., description=f"Score based on star rating ({SCORE_MIN}-{SCORE_MAX})")
    amenity_score: float = Field(..., description=f"Score based on amenities ({SCORE_MIN}-{SCORE_MAX})")
    value_score: float = Field(..., description=f"Score based on value for money ({SCORE_MIN}-{SCORE_MAX})")
    explanation: str = Field(..., description="Human-readable explanation of the quality score")
    
    model_config = {"extra": "forbid"}


class EnrichedHotel(BaseModel):
    """
    An enriched hotel with intelligence, reasoning, and decision support.
    This is the output of the enrichment layer.
    """
    # Original hotel data
    hotel: HotelOption = Field(..., description="Original hotel data")
    
    # Intelligence layers
    rank: int = Field(..., description="Rank in the enriched results (1=best)")
    match_score: float = Field(..., description=f"Overall match score ({MATCH_SCORE_MIN}-{MATCH_SCORE_MAX})")
    summary: str = Field(..., description="One-line human-readable summary")
    
    # Categorization
    tags: List[str] = Field(default_factory=list, description="Smart tags for quick filtering")
    best_for: List[str] = Field(default_factory=list, description="Who this hotel is best suited for")
    
    # Analysis layers
    price_intelligence: PriceIntelligence = Field(..., description="Smart pricing analysis")
    amenities_analysis: AmenitiesAnalysis = Field(..., description="Amenity analysis")
    quality_score: QualityScore = Field(..., description="Quality and comfort assessment")
    
    # Decision support
    insights: List[HotelInsight] = Field(default_factory=list, description="Intelligent insights")
    recommendations: List[HotelRecommendation] = Field(default_factory=list, description="Recommendations for/against")
    
    model_config = {"extra": "forbid"}


class EnrichmentResult(BaseModel):
    """
    Complete enrichment result with market analysis and ranked hotels.
    """
    enriched_hotels: List[EnrichedHotel] = Field(default_factory=list, description="Ranked and enriched hotels")
    market_analysis: Dict[str, Any] = Field(default_factory=dict, description="Market-level insights")
    best_choice: Optional[str] = Field(None, description="Summary of the best overall choice")
    
    model_config = {"extra": "forbid"}


# ============================================================================
# HOTEL INTELLIGENCE ENGINE
# ============================================================================

class HotelIntelligenceEngine:
    """
    Core intelligence engine for hotel enrichment.
    Transforms List[HotelOption] into EnrichmentResult with smart insights.
    """
    
    def __init__(self):
        """Initialize the intelligence engine."""
        self.essential_amenities = ["wifi", "parking", "air conditioning"]
        self.family_amenities = ["pool", "restaurant", "room service"]
        self.business_amenities = ["wifi", "business center", "meeting room"]
        self.luxury_amenities = ["spa", "gym", "concierge", "bar"]
    
    def enrich_hotels(
        self,
        hotels: List[HotelOption],
        preferences: Optional[Dict[str, Any]] = None
    ) -> EnrichmentResult:
        """
        Enrich a list of hotels with intelligence and insights.
        
        Args:
            hotels: List of hotel options to enrich
            preferences: Optional user preferences for personalization
        
        Returns:
            EnrichmentResult with enriched hotels and market analysis
        """
        if not hotels:
            return EnrichmentResult(
                enriched_hotels=[],
                market_analysis=self._empty_market_analysis(),
                best_choice=None
            )
        
        # Market analysis
        market = self._analyze_market(hotels)
        
        # Enrich each hotel
        enriched_list = []
        for hotel in hotels:
            enriched = self._enrich_single_hotel(hotel, hotels, market, preferences)
            enriched_list.append(enriched)
        
        # Rank hotels by overall match score
        enriched_list.sort(key=lambda h: h.match_score, reverse=True)
        for idx, enriched in enumerate(enriched_list, 1):
            enriched.rank = idx
        
        # Determine best choice
        best_choice = self._determine_best_choice(enriched_list) if enriched_list else None
        
        return EnrichmentResult(
            enriched_hotels=enriched_list,
            market_analysis=market,
            best_choice=best_choice
        )
    
    def _analyze_market(self, hotels: List[HotelOption]) -> Dict[str, Any]:
        """Analyze the hotel market to provide context."""
        if not hotels:
            return self._empty_market_analysis()
        
        prices = [h.price_per_night for h in hotels]
        stars = [h.star_category for h in hotels]
        
        avg_price = statistics.mean(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        # Price distribution
        budget_count = sum(1 for p in prices if p < avg_price * 0.7)
        moderate_count = sum(1 for p in prices if avg_price * 0.7 <= p <= avg_price * 1.3)
        premium_count = sum(1 for p in prices if p > avg_price * 1.3)
        
        # Star distribution
        star_distribution = {}
        for s in range(1, 6):
            star_distribution[f"{s}_star"] = sum(1 for hotel in hotels if hotel.star_category == s)
        
        # Amenity analysis
        all_amenities = set()
        for hotel in hotels:
            all_amenities.update(hotel.amenities)
        
        return {
            "total_options": len(hotels),
            "price_range": {
                "min": min_price,
                "max": max_price,
                "average": int(avg_price)
            },
            "price_distribution": {
                PRICE_BUDGET: budget_count,
                PRICE_MODERATE: moderate_count,
                PRICE_PREMIUM: premium_count
            },
            "star_distribution": star_distribution,
            "average_stars": statistics.mean(stars),
            "available_amenities": sorted(list(all_amenities)),
            "best_booking_advice": self._generate_booking_advice(avg_price, min_price, max_price)
        }
    
    def _empty_market_analysis(self) -> Dict[str, Any]:
        """Return empty market analysis structure."""
        return {
            "total_options": 0,
            "price_range": {"min": 0, "max": 0, "average": 0},
            "price_distribution": {PRICE_BUDGET: 0, PRICE_MODERATE: 0, PRICE_PREMIUM: 0},
            "star_distribution": {},
            "average_stars": 0,
            "available_amenities": [],
            "best_booking_advice": "N/A"
        }
    
    def _generate_booking_advice(self, avg_price: float, min_price: int, max_price: int) -> str:
        """Generate smart booking advice based on market conditions."""
        if max_price - min_price < avg_price * 0.3:
            return f"Prices are fairly consistent around ₹{int(avg_price)} per night."
        elif min_price < avg_price * 0.6:
            return f"Great budget options available! Cheapest at ₹{min_price}, average ₹{int(avg_price)}."
        else:
            return f"Average price is ₹{int(avg_price)} per night."
    
    def _enrich_single_hotel(
        self,
        hotel: HotelOption,
        all_hotels: List[HotelOption],
        market: Dict[str, Any],
        preferences: Optional[Dict[str, Any]]
    ) -> EnrichedHotel:
        """Enrich a single hotel with intelligence."""
        
        # Price intelligence
        price_intel = self._analyze_price(hotel, all_hotels, market)
        
        # Amenities analysis
        amenities_analysis = self._analyze_amenities(hotel)
        
        # Quality score
        quality = self._compute_quality_score(hotel, price_intel, amenities_analysis)
        
        # Match score (personalized if preferences provided)
        match_score = self._compute_match_score(hotel, quality, price_intel, amenities_analysis, preferences)
        
        # Tags
        tags = self._generate_tags(hotel, all_hotels, price_intel, quality, amenities_analysis)
        
        # Best for
        best_for = self._determine_best_for(hotel, amenities_analysis)
        
        # Summary
        summary = self._generate_summary(hotel, tags)
        
        # Insights
        insights = self._generate_insights(hotel, price_intel, amenities_analysis, quality)
        
        # Recommendations
        recommendations = self._generate_recommendations(hotel, price_intel, amenities_analysis, quality)
        
        return EnrichedHotel(
            hotel=HotelOption.model_validate(hotel.model_dump() if hasattr(hotel, "model_dump") else hotel),            rank=0,  # Will be set after sorting
            match_score=match_score,
            summary=summary,
            tags=tags,
            best_for=best_for,
            price_intelligence=price_intel,
            amenities_analysis=amenities_analysis,
            quality_score=quality,
            insights=insights,
            recommendations=recommendations
        )
    
    def _analyze_price(
        self,
        hotel: HotelOption,
        all_hotels: List[HotelOption],
        market: Dict[str, Any]
    ) -> PriceIntelligence:
        """Analyze hotel pricing with intelligence."""
        prices = [h.price_per_night for h in all_hotels]
        avg_price = statistics.mean(prices)
        
        # Percentile
        sorted_prices = sorted(prices)
        percentile = (sorted_prices.index(hotel.price_per_night) / len(sorted_prices)) * 100
        
        # Category
        if hotel.price_per_night < avg_price * 0.7:
            category = PRICE_BUDGET
        elif hotel.price_per_night <= avg_price * 1.3:
            category = PRICE_MODERATE
        elif hotel.price_per_night <= avg_price * 2.0:
            category = PRICE_PREMIUM
        else:
            category = PRICE_LUXURY
        
        # Savings vs average
        savings = int(avg_price - hotel.price_per_night)
        
        # Is it a deal?
        is_deal = savings > avg_price * 0.2 and hotel.star_category >= 3
        
        # Value score (0-10)
        # Higher stars and amenities with lower price = better value
        star_value = hotel.star_category / 5.0 * 3  # 0-3 points
        price_value = (1 - (hotel.price_per_night / max(prices))) * 4  # 0-4 points
        amenity_value = min(len(hotel.amenities) / 10.0, 1.0) * 3  # 0-3 points
        value_score = round(star_value + price_value + amenity_value, 1)
        
        return PriceIntelligence(
            price_category=category,
            price_percentile=round(percentile, 1),
            is_deal=is_deal,
            savings_vs_average=savings,
            value_score=value_score
        )
    
    def _analyze_amenities(self, hotel: HotelOption) -> AmenitiesAnalysis:
        """Analyze hotel amenities."""
        amenities_lower = [a.lower() for a in hotel.amenities]
        
        # Key amenities (most important ones present)
        key_amenities = []
        for amenity in hotel.amenities[:5]:  # Top 5
            key_amenities.append(amenity)
        
        # Missing essentials
        missing = []
        for essential in self.essential_amenities:
            if not any(essential in a for a in amenities_lower):
                missing.append(essential)
        
        # Unique features (luxury items)
        unique = []
        for luxury in self.luxury_amenities:
            if any(luxury in a for a in amenities_lower):
                unique.append(luxury)
        
        # Amenity score (0-10)
        amenity_score = min(len(hotel.amenities) / 2.0, 10.0)
        
        return AmenitiesAnalysis(
            total_amenities=len(hotel.amenities),
            key_amenities=key_amenities,
            amenity_score=round(amenity_score, 1),
            missing_essentials=missing,
            unique_features=unique
        )
    
    def _compute_quality_score(
        self,
        hotel: HotelOption,
        price_intel: PriceIntelligence,
        amenities: AmenitiesAnalysis
    ) -> QualityScore:
        """Compute overall quality score."""
        # Rating score (0-10)
        rating_score = (hotel.star_category / 5.0) * 10
        
        # Amenity score (already 0-10)
        amenity_score = amenities.amenity_score
        
        # Value score (already 0-10)
        value_score = price_intel.value_score
        
        # Overall weighted score
        overall = (rating_score * 0.4 + amenity_score * 0.3 + value_score * 0.3)
        
        # Explanation
        if overall >= 8:
            explanation = f"Excellent {hotel.star_category}-star hotel with great amenities and value"
        elif overall >= 6:
            explanation = f"Good {hotel.star_category}-star hotel with solid amenities"
        else:
            explanation = f"Basic {hotel.star_category}-star accommodation"
        
        return QualityScore(
            overall_score=round(overall, 1),
            rating_score=round(rating_score, 1),
            amenity_score=round(amenity_score, 1),
            value_score=round(value_score, 1),
            explanation=explanation
        )
    
    def _compute_match_score(
        self,
        hotel: HotelOption,
        quality: QualityScore,
        price_intel: PriceIntelligence,
        amenities: AmenitiesAnalysis,
        preferences: Optional[Dict[str, Any]]
    ) -> float:
        """Compute personalized match score (0-100)."""
        base_score = quality.overall_score * 10  # Convert 0-10 to 0-100
        
        # Adjust based on preferences
        if preferences:
            budget_pref = preferences.get(PREF_BUDGET_PREFERENCE)
            if budget_pref:
                if budget_pref == PRICE_BUDGET and price_intel.price_category == PRICE_BUDGET:
                    base_score += 10
                elif budget_pref == PRICE_PREMIUM and price_intel.price_category in [PRICE_PREMIUM, PRICE_LUXURY]:
                    base_score += 10
            
            quality_pref = preferences.get(PREF_HOTEL_QUALITY)
            if quality_pref == "high" and hotel.star_category >= 4:
                base_score += 5
        
        return round(min(base_score, 100), 1)
    
    def _generate_tags(
        self,
        hotel: HotelOption,
        all_hotels: List[HotelOption],
        price_intel: PriceIntelligence,
        quality: QualityScore,
        amenities: AmenitiesAnalysis
    ) -> List[str]:
        """Generate smart tags for the hotel."""
        tags = []
        
        # Price-based tags
        min_price = min(h.price_per_night for h in all_hotels)
        if hotel.price_per_night == min_price:
            tags.append(TAG_HOTEL_CHEAPEST)
        
        if price_intel.is_deal:
            tags.append(TAG_HOTEL_BEST_VALUE)
        
        if price_intel.price_category == PRICE_LUXURY:
            tags.append(TAG_HOTEL_LUXURY)
        
        # Quality-based tags
        max_stars = max(h.star_category for h in all_hotels)
        if hotel.star_category == max_stars and hotel.star_category >= 4:
            tags.append(TAG_HOTEL_BEST_RATING)
        
        # Amenity-based tags
        amenities_lower = [a.lower() for a in hotel.amenities]
        if any("pool" in a for a in amenities_lower):
            tags.append(TAG_HOTEL_POOL)
        if any("spa" in a for a in amenities_lower):
            tags.append(TAG_HOTEL_SPA)
        if any("business" in a for a in amenities_lower):
            tags.append(TAG_HOTEL_BUSINESS)
        
        # Family-friendly
        has_family_amenities = sum(1 for fam in self.family_amenities 
                                   if any(fam in a for a in amenities_lower))
        if has_family_amenities >= 2:
            tags.append(TAG_HOTEL_FAMILY_FRIENDLY)
        
        return tags
    
    def _determine_best_for(self, hotel: HotelOption, amenities: AmenitiesAnalysis) -> List[str]:
        """Determine who this hotel is best suited for."""
        best_for = []
        
        amenities_lower = [a.lower() for a in hotel.amenities]
        
        # Budget travelers
        if hotel.price_per_night < 3000:
            best_for.append("budget travelers")
        
        # Families
        has_family = any(fam in a for fam in self.family_amenities for a in amenities_lower)
        if has_family:
            best_for.append("families")
        
        # Business travelers
        has_business = any(biz in a for biz in self.business_amenities for a in amenities_lower)
        if has_business:
            best_for.append("business travelers")
        
        # Luxury seekers
        if hotel.star_category >= 4 and amenities.unique_features:
            best_for.append("luxury seekers")
        
        # Default
        if not best_for:
            best_for.append("all travelers")
        
        return best_for
    
    def _generate_summary(self, hotel: HotelOption, tags: List[str]) -> str:
        """Generate a one-line summary of the hotel."""
        tag_str = tags[0] if tags else ""
        summary = f"{hotel.name} • {hotel.star_category}★ • ₹{hotel.price_per_night:,}/night"
        
        if tag_str:
            summary += f" • {tag_str.replace('-', ' ').title()}"
        
        return summary
    
    def _generate_insights(
        self,
        hotel: HotelOption,
        price_intel: PriceIntelligence,
        amenities: AmenitiesAnalysis,
        quality: QualityScore
    ) -> List[HotelInsight]:
        """Generate intelligent insights about the hotel."""
        insights = []
        
        # Price insights
        if price_intel.is_deal:
            insights.append(HotelInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message=f"Excellent value - {hotel.star_category}★ hotel at {price_intel.price_category} prices",
                priority=4
            ))
        
        if price_intel.savings_vs_average > 500:
            insights.append(HotelInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message=f"Saves ₹{price_intel.savings_vs_average:,} per night compared to average",
                priority=3
            ))
        
        # Amenity insights
        if amenities.unique_features:
            insights.append(HotelInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message=f"Premium amenities: {', '.join(amenities.unique_features)}",
                priority=3
            ))
        
        if amenities.missing_essentials:
            insights.append(HotelInsight(
                type=INSIGHT_TYPE_CONSIDERATION,
                message=f"Note: Missing {', '.join(amenities.missing_essentials)}",
                priority=2
            ))
        
        # Quality insights
        if quality.overall_score >= 8:
            insights.append(HotelInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message="High-quality accommodation with excellent ratings and amenities",
                priority=4
            ))
        
        return insights
    
    def _generate_recommendations(
        self,
        hotel: HotelOption,
        price_intel: PriceIntelligence,
        amenities: AmenitiesAnalysis,
        quality: QualityScore
    ) -> List[HotelRecommendation]:
        """Generate smart recommendations."""
        recommendations = []
        
        # Rating recommendation
        if hotel.star_category >= 4:
            recommendations.append(HotelRecommendation(
                reason=f"{hotel.star_category}-star rating ensures quality service and comfort",
                category=REC_CATEGORY_RATING,
                sentiment=SENTIMENT_POSITIVE
            ))
        elif hotel.star_category <= 2:
            recommendations.append(HotelRecommendation(
                reason=f"{hotel.star_category}-star rating - basic accommodation with limited services",
                category=REC_CATEGORY_RATING,
                sentiment=SENTIMENT_NEUTRAL
            ))
        
        # Price recommendation
        if price_intel.price_category == PRICE_BUDGET:
            recommendations.append(HotelRecommendation(
                reason="Budget-friendly option for cost-conscious travelers",
                category=REC_CATEGORY_PRICE,
                sentiment=SENTIMENT_POSITIVE
            ))
        elif price_intel.price_category == PRICE_LUXURY:
            recommendations.append(HotelRecommendation(
                reason="Premium pricing - expect exceptional service and facilities",
                category=REC_CATEGORY_PRICE,
                sentiment=SENTIMENT_NEUTRAL
            ))
        
        # Amenities recommendation
        if amenities.total_amenities >= 8:
            recommendations.append(HotelRecommendation(
                reason=f"Excellent amenities ({amenities.total_amenities} available) for a comfortable stay",
                category=REC_CATEGORY_AMENITIES,
                sentiment=SENTIMENT_POSITIVE
            ))
        
        return recommendations
    
    def _determine_best_choice(self, enriched_hotels: List[EnrichedHotel]) -> str:
        """Determine and describe the best overall choice."""
        if not enriched_hotels:
            return None
        
        best = enriched_hotels[0]  # Already sorted by match_score
        hotel = best.hotel
        
        return (
            f"{hotel.name} (Rank #1) - {hotel.star_category}★ at ₹{hotel.price_per_night:,}/night "
            f"with {best.quality_score.overall_score:.1f}/10 quality score"
        )


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def enrich_hotels(
    hotels: List[HotelOption],
    preferences: Optional[Dict[str, Any]] = None
) -> EnrichmentResult:
    """
    Convenience function to enrich hotels.
    
    Args:
        hotels: List of hotel options
        preferences: Optional user preferences
    
    Returns:
        EnrichmentResult with enriched hotels and market analysis
    """
    engine = HotelIntelligenceEngine()
    return engine.enrich_hotels(hotels, preferences)


