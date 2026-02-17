"""
Weather Enrichment Layer - Intelligence + Travel Suitability + Risk Analysis

This is NOT formatting. This is NOT API processing.
This is where TravelGuru becomes smart for weather-based travel planning.

Architecture Flow:
Weather API → Normalize → WeatherSummary Objects → Enrichment → Travel Intelligence

Enrichment = Intelligence + Risk Analysis + Comfort Scoring + Packing Advice

This layer transforms raw List[WeatherSummary] into travel-ready weather intelligence
with comfort scores, suitability ratings, risk alerts, and packing recommendations.

CRITICAL: Uses deterministic logic ONLY. NO LLM calls. NO API calls.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import statistics

from pydantic import BaseModel, Field

from shared.schemas import WeatherSummary
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
    # Scoring ranges
    SCORE_MIN,
    SCORE_MAX,
)


# ============================================================================
# WEATHER-SPECIFIC CONSTANTS
# ============================================================================

# Weather condition categories
CONDITION_CLEAR = "clear"
CONDITION_SUNNY = "sunny"
CONDITION_CLOUDY = "cloudy"
CONDITION_RAINY = "rainy"
CONDITION_STORMY = "stormy"
CONDITION_SNOWY = "snowy"
CONDITION_FOGGY = "foggy"

# Comfort levels
COMFORT_EXCELLENT = "excellent"
COMFORT_GOOD = "good"
COMFORT_MODERATE = "moderate"
COMFORT_POOR = "poor"
COMFORT_CHALLENGING = "challenging"

# Travel suitability levels
SUITABILITY_IDEAL = "ideal"
SUITABILITY_GOOD = "good"
SUITABILITY_FAIR = "fair"
SUITABILITY_CHALLENGING = "challenging"
SUITABILITY_DIFFICULT = "difficult"

# Risk levels
RISK_NONE = "none"
RISK_LOW = "low"
RISK_MODERATE = "moderate"
RISK_HIGH = "high"
RISK_SEVERE = "severe"

# Activity suitability
ACTIVITY_OUTDOOR = "outdoor-activities"
ACTIVITY_SIGHTSEEING = "sightseeing"
ACTIVITY_INDOOR = "indoor-activities"
ACTIVITY_BEACH = "beach-activities"
ACTIVITY_HIKING = "hiking"

# Wind speed categories (km/h)
WIND_CALM = "calm"  # 0-10 km/h
WIND_LIGHT = "light"  # 10-20 km/h
WIND_MODERATE = "moderate"  # 20-40 km/h
WIND_STRONG = "strong"  # 40-60 km/h
WIND_VERY_STRONG = "very-strong"  # 60+ km/h

# Humidity comfort levels (%)
HUMIDITY_LOW = "low"  # <30%
HUMIDITY_COMFORTABLE = "comfortable"  # 30-60%
HUMIDITY_MODERATE = "moderate"  # 60-70%
HUMIDITY_HIGH = "high"  # 70-80%
HUMIDITY_OPPRESSIVE = "oppressive"  # 80%+

# UV index levels
UV_LOW = "low"  # 0-2
UV_MODERATE = "moderate"  # 3-5
UV_HIGH = "high"  # 6-7
UV_VERY_HIGH = "very-high"  # 8-10
UV_EXTREME = "extreme"  # 11+

# AQI (Air Quality Index) levels
AQI_GOOD = "good"  # 0-50
AQI_MODERATE = "moderate"  # 51-100
AQI_UNHEALTHY_SENSITIVE = "unhealthy-for-sensitive"  # 101-150
AQI_UNHEALTHY = "unhealthy"  # 151-200
AQI_VERY_UNHEALTHY = "very-unhealthy"  # 201-300
AQI_HAZARDOUS = "hazardous"  # 301+

# Trip types for weighted suitability
TRIP_TYPE_BEACH = "beach"
TRIP_TYPE_BUSINESS = "business"
TRIP_TYPE_TREK = "trek"
TRIP_TYPE_SIGHTSEEING = "sightseeing"
TRIP_TYPE_ADVENTURE = "adventure"

# Wind speed categories (km/h)
WIND_CALM = "calm"  # 0-10 km/h
WIND_LIGHT = "light"  # 10-20 km/h
WIND_MODERATE = "moderate"  # 20-40 km/h
WIND_STRONG = "strong"  # 40-60 km/h
WIND_VERY_STRONG = "very-strong"  # 60+ km/h

# Humidity comfort levels (%)
HUMIDITY_LOW = "low"  # <30%
HUMIDITY_COMFORTABLE = "comfortable"  # 30-60%
HUMIDITY_MODERATE = "moderate"  # 60-70%
HUMIDITY_HIGH = "high"  # 70-80%
HUMIDITY_OPPRESSIVE = "oppressive"  # 80%+

# UV index levels
UV_LOW = "low"  # 0-2
UV_MODERATE = "moderate"  # 3-5
UV_HIGH = "high"  # 6-7
UV_VERY_HIGH = "very-high"  # 8-10
UV_EXTREME = "extreme"  # 11+

# AQI (Air Quality Index) levels
AQI_GOOD = "good"  # 0-50
AQI_MODERATE = "moderate"  # 51-100
AQI_UNHEALTHY_SENSITIVE = "unhealthy-for-sensitive"  # 101-150
AQI_UNHEALTHY = "unhealthy"  # 151-200
AQI_VERY_UNHEALTHY = "very-unhealthy"  # 201-300
AQI_HAZARDOUS = "hazardous"  # 301+

# Trip types for weighted suitability
TRIP_TYPE_BEACH = "beach"
TRIP_TYPE_BUSINESS = "business"
TRIP_TYPE_TREK = "trek"
TRIP_TYPE_SIGHTSEEING = "sightseeing"
TRIP_TYPE_ADVENTURE = "adventure"


# ============================================================================
# ENRICHED OUTPUT SCHEMAS
# ============================================================================

class WeatherInsight(BaseModel):
    """
    Represents an intelligent insight about weather conditions.
    These help travelers make informed decisions about their trip.
    """
    type: str = Field(..., description=f"Type of insight: '{INSIGHT_TYPE_ADVANTAGE}', '{INSIGHT_TYPE_CONSIDERATION}', '{INSIGHT_TYPE_TIP}', '{INSIGHT_TYPE_WARNING}'")
    message: str = Field(..., description="Human-readable insight message")
    priority: int = Field(default=1, description="Priority level (1=low, 5=critical)")
    
    model_config = {"extra": "forbid"}


class WindImpact(BaseModel):
    """
    Assessment of wind speed impact on travel activities.
    """
    speed_kmh: Optional[float] = Field(None, description="Wind speed in km/h")
    category: str = Field(..., description=f"Wind category: '{WIND_CALM}', '{WIND_LIGHT}', '{WIND_MODERATE}', '{WIND_STRONG}', '{WIND_VERY_STRONG}'")
    impact_score: int = Field(..., ge=SCORE_MIN, le=SCORE_MAX, description="Impact on activities (0=severe impact, 10=no impact)")
    considerations: List[str] = Field(default_factory=list, description="Wind-specific travel considerations")
    
    model_config = {"extra": "forbid"}


class HumidityComfort(BaseModel):
    """
    Assessment of humidity comfort levels.
    """
    humidity_percent: Optional[float] = Field(None, description="Relative humidity percentage")
    category: str = Field(..., description=f"Humidity level: '{HUMIDITY_LOW}', '{HUMIDITY_COMFORTABLE}', '{HUMIDITY_MODERATE}', '{HUMIDITY_HIGH}', '{HUMIDITY_OPPRESSIVE}'")
    comfort_score: int = Field(..., ge=SCORE_MIN, le=SCORE_MAX, description="Comfort rating (0=oppressive, 10=ideal)")
    health_notes: List[str] = Field(default_factory=list, description="Health and comfort considerations")
    
    model_config = {"extra": "forbid"}


class UVIndexAssessment(BaseModel):
    """
    UV index risk assessment and sun protection advice.
    """
    uv_index: Optional[float] = Field(None, description="UV index value")
    category: str = Field(..., description=f"UV level: '{UV_LOW}', '{UV_MODERATE}', '{UV_HIGH}', '{UV_VERY_HIGH}', '{UV_EXTREME}'")
    risk_level: str = Field(..., description=f"Risk level: '{RISK_NONE}', '{RISK_LOW}', '{RISK_MODERATE}', '{RISK_HIGH}', '{RISK_SEVERE}'")
    protection_advice: List[str] = Field(default_factory=list, description="Sun protection recommendations")
    
    model_config = {"extra": "forbid"}


class AirQualityAssessment(BaseModel):
    """
    Air quality assessment and health recommendations.
    """
    aqi_value: Optional[int] = Field(None, description="Air Quality Index value")
    category: str = Field(..., description=f"AQI category: '{AQI_GOOD}', '{AQI_MODERATE}', '{AQI_UNHEALTHY_SENSITIVE}', '{AQI_UNHEALTHY}', '{AQI_VERY_UNHEALTHY}', '{AQI_HAZARDOUS}'")
    health_impact: str = Field(..., description="Impact on health and activities")
    recommendations: List[str] = Field(default_factory=list, description="Activity and health recommendations")
    
    model_config = {"extra": "forbid"}


class WindImpact(BaseModel):
    """
    Assessment of wind speed impact on travel activities.
    """
    speed_kmh: Optional[float] = Field(None, description="Wind speed in km/h")
    category: str = Field(..., description=f"Wind category: '{WIND_CALM}', '{WIND_LIGHT}', '{WIND_MODERATE}', '{WIND_STRONG}', '{WIND_VERY_STRONG}'")
    impact_score: int = Field(..., ge=SCORE_MIN, le=SCORE_MAX, description="Impact on activities (0=severe impact, 10=no impact)")
    considerations: List[str] = Field(default_factory=list, description="Wind-specific travel considerations")
    
    model_config = {"extra": "forbid"}


class HumidityComfort(BaseModel):
    """
    Assessment of humidity comfort levels.
    """
    humidity_percent: Optional[float] = Field(None, description="Relative humidity percentage")
    category: str = Field(..., description=f"Humidity level: '{HUMIDITY_LOW}', '{HUMIDITY_COMFORTABLE}', '{HUMIDITY_MODERATE}', '{HUMIDITY_HIGH}', '{HUMIDITY_OPPRESSIVE}'")
    comfort_score: int = Field(..., ge=SCORE_MIN, le=SCORE_MAX, description="Comfort rating (0=oppressive, 10=ideal)")
    health_notes: List[str] = Field(default_factory=list, description="Health and comfort considerations")
    
    model_config = {"extra": "forbid"}


class UVIndexAssessment(BaseModel):
    """
    UV index risk assessment and sun protection advice.
    """
    uv_index: Optional[float] = Field(None, description="UV index value")
    category: str = Field(..., description=f"UV level: '{UV_LOW}', '{UV_MODERATE}', '{UV_HIGH}', '{UV_VERY_HIGH}', '{UV_EXTREME}'")
    risk_level: str = Field(..., description=f"Risk level: '{RISK_NONE}', '{RISK_LOW}', '{RISK_MODERATE}', '{RISK_HIGH}', '{RISK_SEVERE}'")
    protection_advice: List[str] = Field(default_factory=list, description="Sun protection recommendations")
    
    model_config = {"extra": "forbid"}


class AirQualityAssessment(BaseModel):
    """
    Air quality assessment and health recommendations.
    """
    aqi_value: Optional[int] = Field(None, description="Air Quality Index value")
    category: str = Field(..., description=f"AQI category: '{AQI_GOOD}', '{AQI_MODERATE}', '{AQI_UNHEALTHY_SENSITIVE}', '{AQI_UNHEALTHY}', '{AQI_VERY_UNHEALTHY}', '{AQI_HAZARDOUS}'")
    health_impact: str = Field(..., description="Impact on health and activities")
    recommendations: List[str] = Field(default_factory=list, description="Activity and health recommendations")
    
    model_config = {"extra": "forbid"}


class ComfortScore(BaseModel):
    """
    Quantifies weather comfort for travel activities.
    """
    overall_score: float = Field(..., description=f"Overall comfort score ({SCORE_MIN}-{SCORE_MAX})")
    temperature_comfort: float = Field(..., description=f"Temperature comfort ({SCORE_MIN}-{SCORE_MAX})")
    precipitation_comfort: float = Field(..., description=f"Precipitation comfort ({SCORE_MIN}-{SCORE_MAX})")
    comfort_level: str = Field(..., description=f"Comfort category: {COMFORT_EXCELLENT}, {COMFORT_GOOD}, {COMFORT_MODERATE}, {COMFORT_POOR}, {COMFORT_CHALLENGING}")
    explanation: str = Field(..., description="Human-readable explanation")
    
    model_config = {"extra": "forbid"}


class TravelSuitability(BaseModel):
    """
    Analyzes how suitable the weather is for different travel activities.
    """
    overall_rating: str = Field(..., description=f"Overall suitability: {SUITABILITY_IDEAL}, {SUITABILITY_GOOD}, {SUITABILITY_FAIR}, {SUITABILITY_CHALLENGING}, {SUITABILITY_DIFFICULT}")
    outdoor_score: float = Field(..., description=f"Suitability for outdoor activities ({SCORE_MIN}-{SCORE_MAX})")
    sightseeing_score: float = Field(..., description=f"Suitability for sightseeing ({SCORE_MIN}-{SCORE_MAX})")
    beach_score: float = Field(..., description=f"Suitability for beach activities ({SCORE_MIN}-{SCORE_MAX})")
    best_activities: List[str] = Field(default_factory=list, description="Recommended activities for this weather")
    avoid_activities: List[str] = Field(default_factory=list, description="Activities to avoid")
    
    model_config = {"extra": "forbid"}


class WeatherRisk(BaseModel):
    """
    Identifies weather-related risks and safety concerns.
    """
    risk_level: str = Field(..., description=f"Overall risk: {RISK_NONE}, {RISK_LOW}, {RISK_MODERATE}, {RISK_HIGH}, {RISK_SEVERE}")
    rain_risk: bool = Field(default=False, description="Risk of rain")
    extreme_heat: bool = Field(default=False, description="Extreme heat warning")
    extreme_cold: bool = Field(default=False, description="Extreme cold warning")
    storm_risk: bool = Field(default=False, description="Storm or severe weather risk")
    warnings: List[str] = Field(default_factory=list, description="Specific weather warnings")
    precautions: List[str] = Field(default_factory=list, description="Recommended precautions")
    
    model_config = {"extra": "forbid"}


class PackingAdvice(BaseModel):
    """
    Smart packing recommendations based on weather conditions.
    """
    essential_items: List[str] = Field(default_factory=list, description="Must-have items")
    recommended_items: List[str] = Field(default_factory=list, description="Recommended items")
    clothing_suggestions: List[str] = Field(default_factory=list, description="Clothing recommendations")
    accessories: List[str] = Field(default_factory=list, description="Useful accessories")
    
    model_config = {"extra": "forbid"}


class EnrichedWeatherDay(BaseModel):
    """
    An enriched daily weather forecast with intelligence and travel insights.
    """
    # Original weather data
    weather: WeatherSummary = Field(..., description="Original weather summary")
    
    # Intelligence layers
    comfort_score: ComfortScore = Field(..., description="Weather comfort analysis")
    travel_suitability: TravelSuitability = Field(..., description="Activity suitability assessment")
    risk_assessment: WeatherRisk = Field(..., description="Weather risk analysis")
    packing_advice: PackingAdvice = Field(..., description="Packing recommendations")
    
    # Advanced assessments (future enhancements)
    wind_impact: Optional[WindImpact] = Field(None, description="Wind speed impact assessment")
    humidity_comfort: Optional[HumidityComfort] = Field(None, description="Humidity comfort assessment")
    uv_assessment: Optional[UVIndexAssessment] = Field(None, description="UV index risk assessment")
    air_quality: Optional[AirQualityAssessment] = Field(None, description="Air quality assessment")
    
    # UX layer
    daily_summary: str = Field(..., description="One-line weather summary")
    insights: List[WeatherInsight] = Field(default_factory=list, description="Intelligent insights")
    best_time_of_day: str = Field(..., description="Best time for outdoor activities")
    
    model_config = {"extra": "forbid"}


class TripWeatherAnalysis(BaseModel):
    """
    Comprehensive trip-level weather intelligence.
    """
    enriched_days: List[EnrichedWeatherDay] = Field(..., description="Per-day enriched forecasts")
    trip_summary: str = Field(..., description="Overall trip weather summary")
    best_day: Optional[str] = Field(None, description="Best weather day for outdoor activities")
    worst_day: Optional[str] = Field(None, description="Most challenging weather day")
    overall_comfort: str = Field(..., description="Overall trip comfort level")
    packing_checklist: List[str] = Field(default_factory=list, description="Consolidated packing list for entire trip")
    trip_insights: List[WeatherInsight] = Field(default_factory=list, description="Trip-level insights")
    travel_tips: List[str] = Field(default_factory=list, description="Weather-specific travel tips")
    
    model_config = {"extra": "forbid"}


# ============================================================================
# WEATHER INTELLIGENCE ENGINE
# ============================================================================

class WeatherIntelligenceEngine:
    """
    Core intelligence engine for weather enrichment.
    
    Uses deterministic logic to analyze weather forecasts and provide:
    - Comfort scoring
    - Travel suitability ratings
    - Risk assessments
    - Packing recommendations
    - Activity suggestions
    
    NO LLM calls. NO API calls. Pure algorithmic analysis.
    """
    
    def __init__(self):
        """Initialize the weather intelligence engine."""
        # Temperature comfort ranges (Celsius)
        self.temp_ideal_min = 18
        self.temp_ideal_max = 28
        self.temp_comfortable_min = 12
        self.temp_comfortable_max = 32
        self.temp_extreme_cold = 5
        self.temp_extreme_hot = 35
        
        # Condition mapping to normalized categories
        self.condition_mapping = {
            "clear": CONDITION_CLEAR,
            "sunny": CONDITION_SUNNY,
            "clouds": CONDITION_CLOUDY,
            "cloudy": CONDITION_CLOUDY,
            "rain": CONDITION_RAINY,
            "drizzle": CONDITION_RAINY,
            "thunderstorm": CONDITION_STORMY,
            "storm": CONDITION_STORMY,
            "snow": CONDITION_SNOWY,
            "fog": CONDITION_FOGGY,
            "mist": CONDITION_FOGGY,
        }
    
    def enrich_forecast(
        self,
        forecast: List[WeatherSummary],
        trip_context: Optional[Dict[str, Any]] = None
    ) -> TripWeatherAnalysis:
        """
        Main enrichment method - transforms raw weather into travel intelligence.
        
        Args:
            forecast: List of WeatherSummary objects (daily forecasts)
            trip_context: Optional context like trip type, traveler preferences
            
        Returns:
            TripWeatherAnalysis with enriched daily forecasts and trip-level insights
        """
        if not forecast:
            return TripWeatherAnalysis(
                enriched_days=[],
                trip_summary="No weather data available",
                overall_comfort=COMFORT_MODERATE,
                packing_checklist=[],
                trip_insights=[],
                travel_tips=[]
            )
        
        # Enrich each day
        enriched_days = []
        trip_type = trip_context.get("trip_type") if trip_context else None
        
        for day_weather in forecast:
            enriched_day = self._enrich_single_day(day_weather, trip_type=trip_type)
            enriched_days.append(enriched_day)
        
        # Trip-level analysis
        trip_summary = self._generate_trip_summary(enriched_days)
        best_day = self._identify_best_day(enriched_days)
        worst_day = self._identify_worst_day(enriched_days)
        overall_comfort = self._calculate_overall_comfort(enriched_days)
        packing_checklist = self._generate_packing_checklist(enriched_days)
        trip_insights = self._generate_trip_insights(enriched_days)
        travel_tips = self._generate_travel_tips(enriched_days, trip_context)
        
        return TripWeatherAnalysis(
            enriched_days=enriched_days,
            trip_summary=trip_summary,
            best_day=best_day,
            worst_day=worst_day,
            overall_comfort=overall_comfort,
            packing_checklist=packing_checklist,
            trip_insights=trip_insights,
            travel_tips=travel_tips
        )
    
    def _enrich_single_day(
        self, 
        weather: WeatherSummary, 
        trip_type: Optional[str] = None
    ) -> EnrichedWeatherDay:
        """Enrich a single day's weather with intelligence."""
        # Comfort scoring
        comfort_score = self._calculate_comfort_score(weather)
        
        # Travel suitability (with trip type weighting)
        travel_suitability = self._assess_travel_suitability(weather, trip_type=trip_type)
        
        # Risk assessment
        risk_assessment = self._assess_weather_risks(weather)
        
        # Packing advice
        packing_advice = self._generate_packing_advice(weather)
        
        # Advanced assessments (with default values since data not yet in WeatherSummary)
        wind_impact = self._assess_wind_impact()  # Will use default until wind data available
        humidity_comfort = self._assess_humidity_comfort()  # Will use default until humidity data available
        uv_assessment = self._assess_uv_index()  # Will use default until UV data available
        air_quality = self._assess_air_quality()  # Will use default until AQI data available
        
        # Daily summary
        daily_summary = self._generate_daily_summary(weather, comfort_score)
        
        # Insights
        insights = self._generate_daily_insights(weather, comfort_score, risk_assessment)
        
        # Best time of day
        best_time = self._determine_best_time(weather)
        
        return EnrichedWeatherDay(
            weather=weather,
            comfort_score=comfort_score,
            travel_suitability=travel_suitability,
            risk_assessment=risk_assessment,
            packing_advice=packing_advice,
            wind_impact=wind_impact,
            humidity_comfort=humidity_comfort,
            uv_assessment=uv_assessment,
            air_quality=air_quality,
            daily_summary=daily_summary,
            insights=insights,
            best_time_of_day=best_time
        )
    
    # ========================================================================
    # REALISTIC COMFORT MODELS - Travel Decision Engine
    # ========================================================================
    
    def _temperature_comfort(self, temp_c: float) -> float:
        """
        Refined realistic temperature comfort curve.
        Uses bell curve with nuanced penalties for heat and cold.
        
        Refined for better granularity in 30-36°C range.
        33°C in Goa is hot but usable with planning, not "poor".
        
        Returns: Base comfort score (1.5-10.0) before other penalties
        """
        # Ideal zone: 22-27°C → 10.0/10 (Perfect weather)
        if 22 <= temp_c <= 27:
            return 10.0
        
        # Slightly warm/cool: 27-30°C → 8.0/10 (Still very comfortable)
        if 27 < temp_c <= 30:
            return 8.0
        
        # Getting warm: 30-32°C → 6.5/10 (Moderate, planning needed)
        if 30 < temp_c <= 32:
            return 6.5
        
        # Hot but usable: 32-34°C → 5.5/10 (Uncomfortable but manageable)
        if 32 < temp_c <= 34:
            return 5.5
        
        # Very hot: 34-36°C → 4.0/10 (Limit outdoor exposure)
        if 34 < temp_c <= 36:
            return 4.0
        
        # Extreme heat: 36-38°C → 2.5/10 (Dangerous)
        if 36 < temp_c <= 38:
            return 2.5
        
        # Emergency heat or extreme cold: >38°C or <10°C → 1.5/10
        if temp_c > 38 or temp_c < 10:
            return 1.5
        
        # Cool but manageable: 10-22°C → 5.0-8.5/10
        if 10 <= temp_c < 18:
            return 5.0
        if 18 <= temp_c < 22:
            return 8.5
        
        return 5.0
    
    def _humidity_penalty(self, humidity: Optional[float]) -> float:
        """
        Humidity makes heat feel worse.
        
        Returns: Penalty value (0 to -3.0)
        """
        if humidity is None:
            return 0.0
        
        if humidity < 50:
            return 0.0
        if 50 <= humidity < 70:
            return -0.5
        if 70 <= humidity < 85:
            return -1.5
        # Oppressive humidity
        return -3.0
    
    def _rain_penalty(self, rain_prob: float) -> float:
        """
        Rain ruins outdoor plans.
        
        Args:
            rain_prob: Probability as fraction (0-1)
        
        Returns: Penalty value (0 to -5.0)
        """
        rain_pct = rain_prob * 100
        
        if rain_pct < 10:
            return 0.0
        if rain_pct < 30:
            return -1.0
        if rain_pct < 60:
            return -3.0
        # High rain probability
        return -5.0
    
    def _wind_penalty(self, wind_kph: Optional[float]) -> float:
        """
        Strong wind impacts comfort and activities.
        
        Returns: Penalty value (0 to -3.0)
        """
        if wind_kph is None:
            return 0.0
        
        if wind_kph < 15:
            return 0.0
        if wind_kph < 30:
            return -0.5
        if wind_kph < 45:
            return -1.5
        # Very strong wind
        return -3.0
    
    def _cloud_penalty(self, condition: str) -> float:
        """
        Cloud cover and poor conditions reduce comfort.
        
        Returns: Penalty value (0 to -3.0)
        """
        condition_lower = condition.lower()
        
        if "clear" in condition_lower or "sunny" in condition_lower:
            return 0.0
        if "cloud" in condition_lower or "partly" in condition_lower:
            return -0.5
        if "overcast" in condition_lower:
            return -1.0
        if "rain" in condition_lower or "storm" in condition_lower or "drizzle" in condition_lower:
            return -3.0
        
        return 0.0
    
    def _compute_realistic_comfort(
        self,
        temp: float,
        humidity: Optional[float],
        rain_prob: float,
        wind_kph: Optional[float],
        condition: str
    ) -> float:
        """
        Compute realistic comfort score combining all factors.
        
        Includes heat caps for extreme temperatures to prevent
        any scenario from scoring too high on dangerous heat days.
        
        Returns: Final comfort score (1.0 - 10.0)
        """
        # Start with temperature-based comfort
        base = self._temperature_comfort(temp)
        
        # Apply all penalties
        penalty = 0.0
        penalty += self._humidity_penalty(humidity)
        penalty += self._rain_penalty(rain_prob)
        penalty += self._wind_penalty(wind_kph)
        penalty += self._cloud_penalty(condition)
        
        # Combine and clamp
        final = base + penalty
        final = max(1.0, min(10.0, final))
        
        # Apply heat caps for extreme temperatures
        # These override optimistic scores for dangerous heat
        if temp >= 38:
            # Emergency heat - cap at 3.0 maximum
            final = min(final, 3.0)
        elif temp >= 35:
            # Extreme heat - cap at 5.0 maximum
            final = min(final, 5.0)
        
        return round(final, 1)
    
    def _activity_adjusted_score(self, base_score: float, activity: str, temp: float) -> float:
        """
        Adjust comfort score based on activity type.
        Different activities have different heat/cold tolerances.
        
        Args:
            base_score: Base comfort score
            activity: Activity type (beach, sightseeing, trekking)
            temp: Temperature in Celsius
        
        Returns: Activity-adjusted score (1.0 - 10.0)
        """
        adjusted = base_score
        
        if activity == "beach":
            # Beach activities tolerate more heat
            if temp > 30:
                adjusted = min(10, base_score + 0.5)
        
        elif activity == "sightseeing":
            # Walking around cities - heat is worse
            if temp > 28:
                adjusted = max(1, base_score - 0.5)
        
        elif activity == "trekking":
            # Physical exertion - heat is MUCH worse
            if temp > 26:
                adjusted = max(1, base_score - 1.5)
        
        return round(adjusted, 1)
    
    def _calculate_comfort_score(self, weather: WeatherSummary) -> ComfortScore:
        """
        Calculate weather comfort scores using realistic comfort models.
        
        CRITICAL FIX: Uses MAX temperature for daytime comfort scoring.
        Why? Because 20-36°C averaging to 27°C is NOT "excellent" - 
        travelers experience the 36°C peak heat during daytime activities.
        
        "Worst realistic exposure determines comfort" - not average.
        """
        temp_avg = weather.temp_avg_c
        temp_max = weather.temp_max_c  # CRITICAL: Peak heat exposure
        rain_chance = weather.rain_chance
        condition = weather.condition
        
        # Get humidity and wind from weather data (with defaults)
        # TODO: Update when WeatherSummary includes humidity and wind fields
        humidity = None  # Will be populated when API provides it
        wind_kph = None  # Will be populated when API provides it
        
        # Use MAX temperature for realistic daytime comfort
        # Travelers will experience peak heat, not average!
        daytime_exposure_temp = temp_max
        
        # Compute realistic overall comfort based on WORST exposure
        overall = self._compute_realistic_comfort(
            temp=daytime_exposure_temp,
            humidity=humidity,
            rain_prob=rain_chance,
            wind_kph=wind_kph,
            condition=condition
        )
        
        # Temperature comfort using realistic curve with MAX temp
        temp_comfort = self._temperature_comfort(daytime_exposure_temp)
        
        # Precipitation comfort (kept for backward compatibility)
        if rain_chance == 0:
            precip_comfort = 10.0
        elif rain_chance < 0.3:
            precip_comfort = 8.0
        elif rain_chance < 0.5:
            precip_comfort = 6.0
        elif rain_chance < 0.7:
            precip_comfort = 4.0
        else:
            precip_comfort = 2.0
        
        # Comfort level based on REALISTIC overall score
        if overall >= 8.5:
            comfort_level = COMFORT_EXCELLENT
        elif overall >= 7.0:
            comfort_level = COMFORT_GOOD
        elif overall >= 5.0:
            comfort_level = COMFORT_MODERATE
        elif overall >= 3.0:
            comfort_level = COMFORT_POOR
        else:
            comfort_level = COMFORT_CHALLENGING
        
        # Explanation
        explanation = self._generate_comfort_explanation(weather, temp_comfort, precip_comfort)
        
        return ComfortScore(
            overall_score=overall,
            temperature_comfort=temp_comfort,
            precipitation_comfort=precip_comfort,
            comfort_level=comfort_level,
            explanation=explanation
        )
    
    def _generate_comfort_explanation(self, weather: WeatherSummary, temp_comfort: float, precip_comfort: float) -> str:
        """Generate human-readable comfort explanation."""
        parts = []
        
        # Temperature
        temp_avg = weather.temp_avg_c
        if temp_comfort >= 8:
            parts.append(f"pleasant {temp_avg:.0f}°C")
        elif temp_comfort >= 5:
            parts.append(f"comfortable {temp_avg:.0f}°C")
        elif temp_avg < self.temp_comfortable_min:
            parts.append(f"cool {temp_avg:.0f}°C")
        else:
            parts.append(f"warm {temp_avg:.0f}°C")
        
        # Precipitation
        if weather.rain_chance > 0.7:
            parts.append("high rain probability")
        elif weather.rain_chance > 0.5:
            parts.append("moderate rain chance")
        elif weather.rain_chance > 0.3:
            parts.append("slight rain possibility")
        
        # Condition
        condition = self._normalize_condition(weather.condition)
        if condition in [CONDITION_CLEAR, CONDITION_SUNNY]:
            parts.append("clear skies")
        elif condition == CONDITION_CLOUDY:
            parts.append("cloudy")
        
        return f"{', '.join(parts)}".capitalize()
    
    def _assess_travel_suitability(
        self, 
        weather: WeatherSummary, 
        trip_type: Optional[str] = None
    ) -> TravelSuitability:
        """
        Assess suitability for different travel activities using realistic comfort models.
        
        CRITICAL: Uses MAX temperature for daytime activity assessment.
        Travelers do outdoor activities during peak heat, not average temp.
        
        Args:
            weather: Weather summary
            trip_type: Optional trip type for weighted scoring (beach, business, trek, sightseeing, adventure)
        """
        temp_avg = weather.temp_avg_c
        temp_max = weather.temp_max_c  # Peak daytime heat exposure
        rain_chance = weather.rain_chance
        condition = self._normalize_condition(weather.condition)
        
        # Get base realistic comfort score using MAX temperature
        humidity = None  # TODO: Update when available in WeatherSummary
        wind_kph = None  # TODO: Update when available in WeatherSummary
        
        # Use MAX temp for daytime activities (critical fix!)
        daytime_temp = temp_max
        
        base_comfort = self._compute_realistic_comfort(
            temp=daytime_temp,
            humidity=humidity,
            rain_prob=rain_chance,
            wind_kph=wind_kph,
            condition=condition
        )
        
        # Activity-specific scores using realistic models with MAX temp
        # OUTDOOR ACTIVITIES - General outdoor comfort
        outdoor_score = self._activity_adjusted_score(base_comfort, "sightseeing", daytime_temp)
        if rain_chance > 0.5:
            outdoor_score = max(1, outdoor_score - 4)
        if condition == CONDITION_STORMY:
            outdoor_score = max(1, outdoor_score - 5)
        outdoor_score = round(max(1, min(10, outdoor_score)), 1)
        
        # SIGHTSEEING - Walking around cities (heat sensitivity)
        sightseeing_score = self._activity_adjusted_score(base_comfort, "sightseeing", daytime_temp)
        if rain_chance > 0.6:
            sightseeing_score = max(1, sightseeing_score - 3)
        if condition == CONDITION_FOGGY:
            sightseeing_score = max(1, sightseeing_score - 2)
        sightseeing_score = round(max(1, min(10, sightseeing_score)), 1)
        
        # BEACH - Heat tolerant, needs sun
        beach_score = self._activity_adjusted_score(base_comfort, "beach", daytime_temp)
        # Beach prefers warmer weather
        if daytime_temp < 24:
            beach_score = max(1, beach_score - (24 - daytime_temp) * 0.5)
        if rain_chance > 0.4:
            beach_score = max(1, beach_score - 5)
        if condition not in [CONDITION_CLEAR, CONDITION_SUNNY]:
            beach_score = max(1, beach_score - 2)
        beach_score = round(max(1, min(10, beach_score)), 1)
        
        # Overall rating - weighted by trip type if provided
        if trip_type == TRIP_TYPE_BEACH:
            # Beach trips prioritize beach score heavily
            avg_score = (beach_score * 0.7) + (outdoor_score * 0.2) + (sightseeing_score * 0.1)
        elif trip_type == TRIP_TYPE_BUSINESS:
            # Business trips less affected by weather, but prefer no rain
            avg_score = (sightseeing_score * 0.6) + (outdoor_score * 0.4)
            # Business travelers are more tolerant
            avg_score = min(10.0, avg_score + 1.0)
        elif trip_type in [TRIP_TYPE_TREK, TRIP_TYPE_ADVENTURE]:
            # Trek/adventure trips prioritize outdoor conditions with heat penalty
            trek_score = self._activity_adjusted_score(base_comfort, "trekking", daytime_temp)
            avg_score = (trek_score * 0.5) + (outdoor_score * 0.3) + (sightseeing_score * 0.2)
        elif trip_type == TRIP_TYPE_SIGHTSEEING:
            # Sightseeing trips prioritize visibility and comfort
            avg_score = (sightseeing_score * 0.7) + (outdoor_score * 0.3)
        else:
            # Default balanced scoring using realistic models
            avg_score = (outdoor_score + sightseeing_score) / 2
        
        avg_score = round(avg_score, 1)
        
        # Map to suitability levels
        if avg_score >= 8:
            overall_rating = SUITABILITY_IDEAL
        elif avg_score >= 6:
            overall_rating = SUITABILITY_GOOD
        elif avg_score >= 4:
            overall_rating = SUITABILITY_FAIR
        elif avg_score >= 2:
            overall_rating = SUITABILITY_CHALLENGING
        else:
            overall_rating = SUITABILITY_DIFFICULT
        
        # Best activities - customized by trip type
        best_activities = []
        avoid_activities = []
        
        if trip_type == TRIP_TYPE_BEACH:
            if beach_score >= 7:
                best_activities.extend(["beach activities", "swimming", "water sports"])
            elif beach_score < 4:
                avoid_activities.extend(["beach activities", "water sports"])
                best_activities.append("indoor resort activities")
        elif trip_type == TRIP_TYPE_BUSINESS:
            if outdoor_score >= 7:
                best_activities.append("outdoor networking events")
            best_activities.append("indoor meetings and conferences")
        elif trip_type in [TRIP_TYPE_TREK, TRIP_TYPE_ADVENTURE]:
            if outdoor_score >= 7 and daytime_temp <= 28:
                best_activities.extend(["hiking", "trekking", "outdoor adventures"])
            elif outdoor_score < 4 or daytime_temp > 32:
                avoid_activities.extend(["hiking", "outdoor adventures"])
                best_activities.append("rest day or light indoor activities")
        else:
            # Default activity recommendations
            if outdoor_score >= 7:
                best_activities.append("outdoor activities")
            elif outdoor_score < 4:
                avoid_activities.append("outdoor activities")
            
            if sightseeing_score >= 7:
                best_activities.append("sightseeing")
            
            if beach_score >= 7:
                best_activities.append("beach activities")
            elif beach_score < 4:
                avoid_activities.append("beach activities")
        
        if rain_chance > 0.5 and not best_activities:
            best_activities.extend(["indoor activities", "museums and galleries"])
        
        return TravelSuitability(
            overall_rating=overall_rating,
            outdoor_score=outdoor_score,
            sightseeing_score=sightseeing_score,
            beach_score=beach_score,
            best_activities=best_activities,
            avoid_activities=avoid_activities
        )
    
    def _assess_weather_risks(self, weather: WeatherSummary) -> WeatherRisk:
        """Assess weather-related risks and warnings."""
        temp_avg = weather.temp_avg_c
        temp_max = weather.temp_max_c
        temp_min = weather.temp_min_c
        rain_chance = weather.rain_chance
        condition = self._normalize_condition(weather.condition)
        
        rain_risk = rain_chance > 0.5
        extreme_heat = temp_max > self.temp_extreme_hot
        extreme_cold = temp_min < self.temp_extreme_cold
        storm_risk = condition == CONDITION_STORMY
        
        # Risk level
        risk_count = sum([rain_risk, extreme_heat, extreme_cold, storm_risk])
        if storm_risk or (extreme_heat and rain_risk):
            risk_level = RISK_SEVERE
        elif risk_count >= 2:
            risk_level = RISK_HIGH
        elif risk_count == 1:
            risk_level = RISK_MODERATE if (rain_risk and rain_chance > 0.7) else RISK_LOW
        else:
            risk_level = RISK_NONE
        
        # Warnings
        warnings = []
        if extreme_heat:
            warnings.append(f"Extreme heat: {temp_max:.0f}°C expected")
        if extreme_cold:
            warnings.append(f"Cold temperatures: {temp_min:.0f}°C expected")
        if storm_risk:
            warnings.append("Storm or severe weather possible")
        if rain_chance > 0.7:
            warnings.append(f"High rain probability: {rain_chance*100:.0f}%")
        
        # Precautions
        precautions = []
        if extreme_heat:
            precautions.append("Stay hydrated, use sunscreen, avoid midday sun")
        if extreme_cold:
            precautions.append("Dress in warm layers, protect extremities")
        if rain_risk:
            precautions.append("Carry rain protection, plan indoor alternatives")
        if storm_risk:
            precautions.append("Monitor weather updates, avoid outdoor exposure")
        
        return WeatherRisk(
            risk_level=risk_level,
            rain_risk=rain_risk,
            extreme_heat=extreme_heat,
            extreme_cold=extreme_cold,
            storm_risk=storm_risk,
            warnings=warnings,
            precautions=precautions
        )
    
    def _generate_packing_advice(self, weather: WeatherSummary) -> PackingAdvice:
        """Generate smart packing recommendations."""
        temp_avg = weather.temp_avg_c
        temp_min = weather.temp_min_c
        temp_max = weather.temp_max_c
        rain_chance = weather.rain_chance
        
        essential_items = []
        recommended_items = []
        clothing_suggestions = []
        accessories = []
        
        # Temperature-based clothing
        if temp_avg >= 25:
            clothing_suggestions.extend(["Light, breathable clothing", "Shorts and t-shirts"])
            essential_items.append("Sunscreen SPF 30+")
            accessories.append("Hat or cap")
        elif temp_avg >= 18:
            clothing_suggestions.extend(["Comfortable casual wear", "Light layers"])
            recommended_items.append("Light jacket for evenings")
        elif temp_avg >= 10:
            clothing_suggestions.extend(["Long pants", "Long-sleeve shirts", "Light jacket or sweater"])
            recommended_items.append("Scarf")
        else:
            clothing_suggestions.extend(["Warm jacket or coat", "Thermal layers"])
            essential_items.extend(["Warm clothing", "Gloves and warm hat"])
        
        # Temperature range consideration
        if (temp_max - temp_min) > 10:
            clothing_suggestions.append("Layered clothing for temperature changes")
        
        # Rain protection
        if rain_chance > 0.5:
            essential_items.extend(["Umbrella", "Rain jacket or waterproof outer layer"])
            recommended_items.append("Waterproof bag")
        elif rain_chance > 0.3:
            recommended_items.append("Compact umbrella")
        
        # Sun protection
        if temp_max > 25:
            essential_items.append("Sunglasses")
            recommended_items.append("After-sun lotion")
        
        # General travel items
        accessories.extend(["Comfortable walking shoes", "Daypack or backpack"])
        
        return PackingAdvice(
            essential_items=essential_items,
            recommended_items=recommended_items,
            clothing_suggestions=clothing_suggestions,
            accessories=accessories
        )
    
    def _assess_wind_impact(self, wind_speed_kmh: Optional[float] = None) -> WindImpact:
        """
        Assess wind speed impact on travel activities.
        Note: Since WeatherSummary doesn't include wind data yet, this uses estimated/default values.
        """
        # Default to moderate wind if not provided
        if wind_speed_kmh is None:
            # Return a default "data unavailable" assessment
            return WindImpact(
                speed_kmh=None,
                category=WIND_LIGHT,
                impact_score=8,
                considerations=["Wind data not available - assuming light conditions"]
            )
        
        # Categorize wind speed
        if wind_speed_kmh < 10:
            category = WIND_CALM
            impact_score = 10
            considerations = ["Calm conditions ideal for all activities"]
        elif wind_speed_kmh < 20:
            category = WIND_LIGHT
            impact_score = 9
            considerations = ["Light breeze, comfortable for most activities"]
        elif wind_speed_kmh < 40:
            category = WIND_MODERATE
            impact_score = 7
            considerations = [
                "Moderate wind may affect outdoor dining",
                "Beach umbrellas may need securing"
            ]
        elif wind_speed_kmh < 60:
            category = WIND_STRONG
            impact_score = 4
            considerations = [
                "Strong winds may affect outdoor activities",
                "Not ideal for beach or water activities",
                "Secure loose items"
            ]
        else:
            category = WIND_VERY_STRONG
            impact_score = 1
            considerations = [
                "Very strong winds - avoid exposed areas",
                "Outdoor activities not recommended",
                "Stay indoors if possible"
            ]
        
        return WindImpact(
            speed_kmh=wind_speed_kmh,
            category=category,
            impact_score=impact_score,
            considerations=considerations
        )
    
    def _assess_humidity_comfort(self, humidity_percent: Optional[float] = None) -> HumidityComfort:
        """
        Assess humidity comfort levels.
        Note: Since WeatherSummary doesn't include humidity yet, this uses estimated/default values.
        """
        if humidity_percent is None:
            # Return default assessment
            return HumidityComfort(
                humidity_percent=None,
                category=HUMIDITY_COMFORTABLE,
                comfort_score=7,
                health_notes=["Humidity data not available - assuming moderate levels"]
            )
        
        # Categorize humidity
        if humidity_percent < 30:
            category = HUMIDITY_LOW
            comfort_score = 7
            health_notes = [
                "Low humidity may cause dry skin",
                "Stay hydrated",
                "Consider moisturizer"
            ]
        elif humidity_percent < 60:
            category = HUMIDITY_COMFORTABLE
            comfort_score = 10
            health_notes = ["Comfortable humidity levels"]
        elif humidity_percent < 70:
            category = HUMIDITY_MODERATE
            comfort_score = 7
            health_notes = [
                "Moderate humidity - slightly sticky",
                "Light, breathable clothing recommended"
            ]
        elif humidity_percent < 80:
            category = HUMIDITY_HIGH
            comfort_score = 5
            health_notes = [
                "High humidity - may feel sticky and uncomfortable",
                "Pace activities to avoid overexertion",
                "Stay well hydrated"
            ]
        else:
            category = HUMIDITY_OPPRESSIVE
            comfort_score = 3
            health_notes = [
                "Oppressive humidity - very uncomfortable",
                "Limit strenuous activities",
                "Seek air-conditioned spaces",
                "Drink plenty of water"
            ]
        
        return HumidityComfort(
            humidity_percent=humidity_percent,
            category=category,
            comfort_score=comfort_score,
            health_notes=health_notes
        )
    
    def _assess_uv_index(self, uv_index: Optional[float] = None) -> UVIndexAssessment:
        """
        Assess UV index and provide sun protection advice.
        Note: Since WeatherSummary doesn't include UV data yet, this uses estimated/default values.
        """
        if uv_index is None:
            # Return default moderate UV assessment
            return UVIndexAssessment(
                uv_index=None,
                category=UV_MODERATE,
                risk_level=RISK_LOW,
                protection_advice=["UV data not available - use standard sun protection"]
            )
        
        # Categorize UV index
        if uv_index <= 2:
            category = UV_LOW
            risk_level = RISK_NONE
            protection_advice = ["Minimal sun protection needed"]
        elif uv_index <= 5:
            category = UV_MODERATE
            risk_level = RISK_LOW
            protection_advice = [
                "Wear sunscreen SPF 30+",
                "Sunglasses recommended"
            ]
        elif uv_index <= 7:
            category = UV_HIGH
            risk_level = RISK_MODERATE
            protection_advice = [
                "Sunscreen SPF 30+ essential",
                "Wear hat and sunglasses",
                "Seek shade during midday (11am-3pm)"
            ]
        elif uv_index <= 10:
            category = UV_VERY_HIGH
            risk_level = RISK_HIGH
            protection_advice = [
                "Sunscreen SPF 50+ essential - reapply every 2 hours",
                "Wear protective clothing, hat, and sunglasses",
                "Avoid sun exposure 11am-3pm",
                "Seek shade whenever possible"
            ]
        else:
            category = UV_EXTREME
            risk_level = RISK_SEVERE
            protection_advice = [
                "Extreme UV - minimize sun exposure",
                "Sunscreen SPF 50+ essential - reapply hourly",
                "Full protective clothing, wide-brimmed hat required",
                "Stay indoors 11am-3pm if possible",
                "UV-blocking sunglasses essential"
            ]
        
        return UVIndexAssessment(
            uv_index=uv_index,
            category=category,
            risk_level=risk_level,
            protection_advice=protection_advice
        )
    
    def _assess_air_quality(self, aqi_value: Optional[int] = None) -> AirQualityAssessment:
        """
        Assess air quality and provide health recommendations.
        Note: Since WeatherSummary doesn't include AQI yet, this uses estimated/default values.
        """
        if aqi_value is None:
            # Return default good air quality
            return AirQualityAssessment(
                aqi_value=None,
                category=AQI_GOOD,
                health_impact="Air quality data not available - assuming normal conditions",
                recommendations=["No air quality restrictions"]
            )
        
        # Categorize AQI
        if aqi_value <= 50:
            category = AQI_GOOD
            health_impact = "Air quality is satisfactory"
            recommendations = ["No health concerns - enjoy outdoor activities"]
        elif aqi_value <= 100:
            category = AQI_MODERATE
            health_impact = "Acceptable air quality"
            recommendations = [
                "Unusually sensitive people should limit prolonged outdoor exertion"
            ]
        elif aqi_value <= 150:
            category = AQI_UNHEALTHY_SENSITIVE
            health_impact = "Unhealthy for sensitive groups"
            recommendations = [
                "Children, elderly, and people with respiratory conditions should limit outdoor activities",
                "General public can enjoy normal activities"
            ]
        elif aqi_value <= 200:
            category = AQI_UNHEALTHY
            health_impact = "Unhealthy for all groups"
            recommendations = [
                "Everyone should limit prolonged outdoor exertion",
                "Sensitive groups should avoid outdoor activities",
                "Consider wearing a mask outdoors"
            ]
        elif aqi_value <= 300:
            category = AQI_VERY_UNHEALTHY
            health_impact = "Very unhealthy - health alert"
            recommendations = [
                "Everyone should avoid outdoor exertion",
                "Sensitive groups should remain indoors",
                "Wear N95 mask if going outside",
                "Use air purifiers indoors"
            ]
        else:
            category = AQI_HAZARDOUS
            health_impact = "Hazardous - health emergency"
            recommendations = [
                "Everyone should avoid all outdoor activities",
                "Remain indoors with windows closed",
                "Use air purifiers",
                "Wear N95 mask if must go outside",
                "Consider relocating if conditions persist"
            ]
        
        return AirQualityAssessment(
            aqi_value=aqi_value,
            category=category,
            health_impact=health_impact,
            recommendations=recommendations
        )
    
    def _generate_daily_summary(self, weather: WeatherSummary, comfort: ComfortScore) -> str:
        """Generate one-line daily summary."""
        date_obj = datetime.strptime(weather.date, "%Y-%m-%d")
        day_name = date_obj.strftime("%A")
        
        temp_range = f"{weather.temp_min_c:.0f}-{weather.temp_max_c:.0f}°C"
        condition = weather.condition.title()
        
        rain_text = ""
        if weather.rain_chance > 0.5:
            rain_text = f", {weather.rain_chance*100:.0f}% rain"
        
        comfort_emoji = {
            COMFORT_EXCELLENT: "☀️",
            COMFORT_GOOD: "🌤️",
            COMFORT_MODERATE: "⛅",
            COMFORT_POOR: "🌧️",
            COMFORT_CHALLENGING: "⚠️"
        }.get(comfort.comfort_level, "")
        
        return f"{day_name}: {condition}, {temp_range}{rain_text} {comfort_emoji}"
    
    def _generate_daily_insights(
        self,
        weather: WeatherSummary,
        comfort: ComfortScore,
        risk: WeatherRisk
    ) -> List[WeatherInsight]:
        """Generate intelligent insights for the day."""
        insights = []
        
        # Comfort insights
        if comfort.comfort_level == COMFORT_EXCELLENT:
            insights.append(WeatherInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message="Perfect weather conditions for all outdoor activities",
                priority=4
            ))
        elif comfort.comfort_level == COMFORT_CHALLENGING:
            insights.append(WeatherInsight(
                type=INSIGHT_TYPE_WARNING,
                message="Challenging weather - plan indoor alternatives",
                priority=4
            ))
        
        # Temperature insights
        if weather.temp_max_c > 30:
            insights.append(WeatherInsight(
                type=INSIGHT_TYPE_TIP,
                message=f"Hot day expected ({weather.temp_max_c:.0f}°C) - plan activities for early morning or evening",
                priority=3
            ))
        elif weather.temp_min_c < 10:
            insights.append(WeatherInsight(
                type=INSIGHT_TYPE_TIP,
                message=f"Cool temperatures ({weather.temp_min_c:.0f}°C) - bring warm clothing",
                priority=3
            ))
        
        # Rain insights
        if weather.rain_chance > 0.7:
            insights.append(WeatherInsight(
                type=INSIGHT_TYPE_CONSIDERATION,
                message="High chance of rain - carry umbrella and plan flexible schedule",
                priority=4
            ))
        elif weather.rain_chance > 0.4:
            insights.append(WeatherInsight(
                type=INSIGHT_TYPE_TIP,
                message="Moderate rain possibility - pack rain protection just in case",
                priority=2
            ))
        
        # Risk warnings
        if risk.risk_level in [RISK_HIGH, RISK_SEVERE]:
            for warning in risk.warnings:
                insights.append(WeatherInsight(
                    type=INSIGHT_TYPE_WARNING,
                    message=warning,
                    priority=5
                ))
        
        return insights
    
    def _determine_best_time(self, weather: WeatherSummary) -> str:
        """
        Determine best time of day for activities.
        
        CRITICAL: Uses MAX temperature for heat recommendations.
        For 33°C+ days, recommend avoiding midday heat.
        """
        temp_max = weather.temp_max_c
        rain_chance = weather.rain_chance
        
        # Heat takes priority - use max temp for realistic recommendations
        if temp_max >= 33:
            return "Early morning or after sunset"
        elif rain_chance > 0.5:
            return "Check hourly forecast, plan indoor backup activities"
        elif temp_max < 15:
            return "Midday (11 AM - 3 PM) when temperatures are warmest"
        else:
            return "Anytime during daylight hours"
    
    def _normalize_condition(self, condition: str) -> str:
        """Normalize weather condition to standard categories."""
        condition_lower = condition.lower()
        for key, value in self.condition_mapping.items():
            if key in condition_lower:
                return value
        return CONDITION_CLOUDY  # Default
    
    def _generate_trip_summary(self, days: List[EnrichedWeatherDay]) -> str:
        """Generate overall trip weather summary."""
        if not days:
            return "No weather forecast available"
        
        avg_temp = statistics.mean([d.weather.temp_avg_c for d in days])
        avg_rain_chance = statistics.mean([d.weather.rain_chance for d in days])
        avg_comfort = statistics.mean([d.comfort_score.overall_score for d in days])
        
        rainy_days = sum(1 for d in days if d.weather.rain_chance > 0.5)
        pleasant_days = sum(1 for d in days if d.comfort_score.comfort_level in [COMFORT_EXCELLENT, COMFORT_GOOD])
        
        summary_parts = [
            f"{len(days)}-day forecast",
            f"average {avg_temp:.0f}°C",
        ]
        
        if pleasant_days >= len(days) * 0.7:
            summary_parts.append(f"{pleasant_days} pleasant days")
        
        if rainy_days > 0:
            summary_parts.append(f"{rainy_days} day(s) with rain likely")
        
        if avg_comfort >= 7:
            summary_parts.append("- excellent conditions overall")
        elif avg_comfort >= 5:
            summary_parts.append("- good weather expected")
        else:
            summary_parts.append("- variable conditions")
        
        return ", ".join(summary_parts).capitalize()
    
    def _identify_best_day(self, days: List[EnrichedWeatherDay]) -> Optional[str]:
        """Identify the best weather day."""
        if not days:
            return None
        
        best_day = max(days, key=lambda d: d.comfort_score.overall_score)
        date_obj = datetime.strptime(best_day.weather.date, "%Y-%m-%d")
        day_name = date_obj.strftime("%A, %B %d")
        
        return f"{day_name} ({best_day.comfort_score.comfort_level} comfort, {best_day.weather.temp_avg_c:.0f}°C)"
    
    def _identify_worst_day(self, days: List[EnrichedWeatherDay]) -> Optional[str]:
        """Identify the most challenging weather day."""
        if not days:
            return None
        
        worst_day = min(days, key=lambda d: d.comfort_score.overall_score)
        date_obj = datetime.strptime(worst_day.weather.date, "%Y-%m-%d")
        day_name = date_obj.strftime("%A, %B %d")
        
        challenges = []
        if worst_day.weather.rain_chance > 0.6:
            challenges.append("rain likely")
        if worst_day.weather.temp_max_c > 33:
            challenges.append("very hot")
        elif worst_day.weather.temp_min_c < 8:
            challenges.append("cold")
        
        challenge_text = ", ".join(challenges) if challenges else "lower comfort"
        
        return f"{day_name} ({challenge_text})"
    
    def _calculate_overall_comfort(self, days: List[EnrichedWeatherDay]) -> str:
        """
        Calculate overall trip comfort level.
        
        IMPROVED LOGIC: Counts day quality distribution instead of just averaging.
        This properly reflects when a trip has multiple poor/challenging days.
        
        Classification:
        - 2+ poor days (score < 5.0) → "mixed or challenging"
        - 4+ good days (score >= 7.0) → "excellent"
        - Otherwise → "good"
        """
        if not days:
            return COMFORT_MODERATE
        
        # Count days by quality
        excellent_days = 0  # 8.5+
        good_days = 0       # 7.0 - 8.5
        moderate_days = 0   # 5.0 - 7.0
        poor_days = 0       # < 5.0
        
        for day in days:
            score = day.comfort_score.overall_score
            if score >= 8.5:
                excellent_days += 1
                good_days += 1  # Excellent counts as good too
            elif score >= 7.0:
                good_days += 1
            elif score >= 5.0:
                moderate_days += 1
            else:
                poor_days += 1
        
        # Apply improved classification logic
        # Priority: Poor days heavily impact overall verdict
        if poor_days >= 2:
            return "mixed or challenging"
        elif good_days >= 4:
            return COMFORT_EXCELLENT
        else:
            return COMFORT_GOOD
    
    def _generate_packing_checklist(self, days: List[EnrichedWeatherDay]) -> List[str]:
        """Generate consolidated packing list for entire trip."""
        all_essential = set()
        all_recommended = set()
        all_clothing = set()
        all_accessories = set()
        
        for day in days:
            all_essential.update(day.packing_advice.essential_items)
            all_recommended.update(day.packing_advice.recommended_items)
            all_clothing.update(day.packing_advice.clothing_suggestions)
            all_accessories.update(day.packing_advice.accessories)
        
        # Combine and prioritize
        checklist = []
        checklist.append("=== ESSENTIAL ===")
        checklist.extend(sorted(all_essential))
        
        if all_clothing:
            checklist.append("=== CLOTHING ===")
            checklist.extend(sorted(all_clothing))
        
        if all_recommended:
            checklist.append("=== RECOMMENDED ===")
            checklist.extend(sorted(all_recommended))
        
        if all_accessories:
            checklist.append("=== ACCESSORIES ===")
            checklist.extend(sorted(all_accessories))
        
        return checklist
    
    def _generate_trip_insights(self, days: List[EnrichedWeatherDay]) -> List[WeatherInsight]:
        """Generate trip-level weather insights."""
        insights = []
        
        if not days:
            return insights
        
        # Temperature variation
        all_temps = [d.weather.temp_avg_c for d in days]
        temp_range = max(all_temps) - min(all_temps)
        if temp_range > 10:
            insights.append(WeatherInsight(
                type=INSIGHT_TYPE_TIP,
                message=f"Significant temperature variation ({temp_range:.0f}°C range) - pack versatile layers",
                priority=3
            ))
        
        # Rain analysis
        rainy_days = [d for d in days if d.weather.rain_chance > 0.5]
        if len(rainy_days) >= len(days) * 0.5:
            insights.append(WeatherInsight(
                type=INSIGHT_TYPE_CONSIDERATION,
                message=f"Rain expected on {len(rainy_days)} days - plan indoor activities and flexible itinerary",
                priority=4
            ))
        
        # Excellent days
        excellent_days = [d for d in days if d.comfort_score.comfort_level == COMFORT_EXCELLENT]
        if len(excellent_days) >= 2:
            insights.append(WeatherInsight(
                type=INSIGHT_TYPE_ADVANTAGE,
                message=f"{len(excellent_days)} days with excellent weather - perfect for outdoor exploration",
                priority=4
            ))
        
        # High risk days
        high_risk_days = [d for d in days if d.risk_assessment.risk_level in [RISK_HIGH, RISK_SEVERE]]
        if high_risk_days:
            insights.append(WeatherInsight(
                type=INSIGHT_TYPE_WARNING,
                message=f"{len(high_risk_days)} day(s) with weather risks - monitor forecasts closely",
                priority=5
            ))
        
        return insights
    
    def _generate_travel_tips(
        self,
        days: List[EnrichedWeatherDay],
        trip_context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate weather-specific travel tips."""
        tips = []
        
        if not days:
            return tips
        
        # General weather preparedness
        tips.append("Check weather forecast daily for any last-minute changes")
        
        # Rain-related tips
        rainy_days_count = sum(1 for d in days if d.weather.rain_chance > 0.4)
        if rainy_days_count > 0:
            tips.append("Download offline maps in case of connectivity issues during rain")
            tips.append("Research indoor attractions as backup options")
        
        # Temperature tips
        max_temp = max(d.weather.temp_max_c for d in days)
        min_temp = min(d.weather.temp_min_c for d in days)
        
        if max_temp > 30:
            tips.append("Stay hydrated - carry water bottle and refill regularly")
            tips.append("Plan outdoor activities early morning or late afternoon")
        
        if min_temp < 15:
            tips.append("Mornings and evenings will be cool - pack layers")
        
        # Activity-specific tips
        avg_outdoor_score = statistics.mean([d.travel_suitability.outdoor_score for d in days])
        if avg_outdoor_score >= 7:
            tips.append("Great conditions for outdoor sightseeing and walking tours")
        
        # General travel wisdom
        tips.append("Keep important items in waterproof bags")
        tips.append("Purchase travel insurance that covers weather-related disruptions")
        
        return tips


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def enrich_weather_forecast(
    forecast: List[WeatherSummary],
    trip_context: Optional[Dict[str, Any]] = None
) -> TripWeatherAnalysis:
    """
    Convenience function to enrich weather forecast.
    
    Args:
        forecast: List of WeatherSummary objects
        trip_context: Optional trip context for personalization
    
    Returns:
        TripWeatherAnalysis with enriched forecasts and trip-level intelligence
    
    Example:
        >>> forecast = [WeatherSummary(...), WeatherSummary(...)]
        >>> analysis = enrich_weather_forecast(forecast)
        >>> print(analysis.trip_summary)
        >>> for day in analysis.enriched_days:
        ...     print(day.daily_summary)
    """
    engine = WeatherIntelligenceEngine()
    return engine.enrich_forecast(forecast, trip_context)


# ============================================================================
# EXAMPLE USAGE & TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Example usage demonstrating the enrichment layer.
    """
    # Sample weather forecast for testing
    sample_forecast = [
        WeatherSummary(
            city="Mumbai",
            date="2026-02-15",
            temp_min_c=22.0,
            temp_max_c=30.0,
            temp_avg_c=26.0,
            condition="Clear",
            rain_chance=0.1
        ),
        WeatherSummary(
            city="Mumbai",
            date="2026-02-16",
            temp_min_c=23.0,
            temp_max_c=31.0,
            temp_avg_c=27.0,
            condition="Cloudy",
            rain_chance=0.4
        ),
        WeatherSummary(
            city="Mumbai",
            date="2026-02-17",
            temp_min_c=24.0,
            temp_max_c=29.0,
            temp_avg_c=26.5,
            condition="Rain",
            rain_chance=0.8
        ),
    ]
    
    # Enrich forecast
    analysis = enrich_weather_forecast(sample_forecast)
    
    print("=" * 80)
    print("WEATHER ENRICHMENT RESULTS")
    print("=" * 80)
    
    print(f"\nTrip Summary: {analysis.trip_summary}")
    print(f"Overall Comfort: {analysis.overall_comfort}")
    print(f"Best Day: {analysis.best_day}")
    print(f"Worst Day: {analysis.worst_day}")
    
    print(f"\n{'-' * 80}")
    print("DAILY FORECASTS")
    print(f"{'-' * 80}")
    
    for day in analysis.enriched_days:
        print(f"\n{day.daily_summary}")
        print(f"  Comfort: {day.comfort_score.comfort_level} ({day.comfort_score.overall_score}/10)")
        print(f"  Suitability: {day.travel_suitability.overall_rating}")
        print(f"  Risk Level: {day.risk_assessment.risk_level}")
        print(f"  Best Time: {day.best_time_of_day}")
        
        if day.insights:
            print(f"  Insights:")
            for insight in day.insights[:2]:
                print(f"    • [{insight.type.upper()}] {insight.message}")
    
    print(f"\n{'-' * 80}")
    print("TRIP INSIGHTS")
    print(f"{'-' * 80}")
    for insight in analysis.trip_insights:
        print(f"  • [{insight.type.upper()}] {insight.message}")
    
    print(f"\n{'-' * 80}")
    print("TRAVEL TIPS")
    print(f"{'-' * 80}")
    for tip in analysis.travel_tips[:5]:
        print(f"  • {tip}")
    
    print(f"\n{'-' * 80}")
    print("PACKING CHECKLIST")
    print(f"{'-' * 80}")
    for item in analysis.packing_checklist[:15]:
        print(f"  {item}")
