"""
Itinerary Enrichment Layer - Deterministic Day-by-Day Planning Engine

This is the FINAL intelligence layer that builds the actual trip itinerary.
It's a 100% deterministic, rule-based planning engine (NO LLM).

Architecture Flow:
Flight + Hotel + Places + Weather (all enriched) → Itinerary Planning → Day Plans

Intelligence Applied:
1. Flight timing respect (arrival/departure days = light plans)
2. Weather-based planning (bad weather → indoor, good → outdoor)
3. Priority-based scheduling (HIGH → must include, MEDIUM → if possible, LOW → optional)
4. Distance/clustering heuristics (group nearby places)
5. Pacing control (max 3-4 activities/day, balance heavy/light days)
6. Budget pressure (tight budget → fewer/cheaper activities)

Design Principle:
❗ NO LLM calls
❗ NO API calls
❗ 100% deterministic planning
❗ Only heuristics & rules
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from pydantic import BaseModel, Field

from backend.app.shared.schemas import (
    FlightOption,
    HotelOption,
    PlaceOption,
    WeatherSummary,
    DayPlan,
    TripPlan
)


# ============================================================================
# ITINERARY PLANNING CONSTANTS
# ============================================================================

# Day types
DAY_TYPE_ARRIVAL = "arrival"
DAY_TYPE_DEPARTURE = "departure"
DAY_TYPE_FULL = "full"
DAY_TYPE_PARTIAL = "partial"

# Activity intensity
INTENSITY_LIGHT = "light"  # 1-2 places
INTENSITY_MODERATE = "moderate"  # 2-3 places
INTENSITY_HEAVY = "heavy"  # 3-4 places
INTENSITY_PACKED = "packed"  # 4+ places

# Weather categories
WEATHER_GOOD = "good"  # Clear, sunny, pleasant
WEATHER_FAIR = "fair"  # Cloudy, mild
WEATHER_POOR = "poor"  # Rainy, stormy
WEATHER_EXTREME = "extreme"  # Very hot/cold, severe conditions

# Priority levels (from places enrichment)
PRIORITY_MUST_VISIT = "must-visit"
PRIORITY_HIGH = "highly-recommended"
PRIORITY_RECOMMENDED = "recommended"
PRIORITY_OPTIONAL = "optional"
PRIORITY_SKIPPABLE = "skippable"

# Distance/clustering categories
DISTANCE_SAME_CLUSTER = "cluster"  # Same area (<2 km)
DISTANCE_NEARBY = "nearby"  # Short distance (2-5 km)
DISTANCE_FAR = "far"  # Significant distance (5-15 km)
DISTANCE_ISOLATED = "isolated"  # Very far (>15 km)

# Zone/area clustering (for cities without coordinates)
ZONE_NORTH = "north"
ZONE_SOUTH = "south"
ZONE_EAST = "east"
ZONE_WEST = "west"
ZONE_CENTRAL = "central"

# Budget pressure levels
BUDGET_PRESSURE_NONE = "none"  # >20% buffer
BUDGET_PRESSURE_LOW = "low"  # 10-20% buffer
BUDGET_PRESSURE_MODERATE = "moderate"  # 5-10% buffer
BUDGET_PRESSURE_HIGH = "high"  # 0-5% buffer
BUDGET_PRESSURE_CRITICAL = "critical"  # Over budget

# Maximum activities per day
MAX_ACTIVITIES_ARRIVAL = 2
MAX_ACTIVITIES_DEPARTURE = 2
MAX_ACTIVITIES_FULL_DAY = 4
MAX_ACTIVITIES_LIGHT_DAY = 2
MAX_ACTIVITIES_MODERATE_DAY = 3

# Scoring weights (configurable constants)
SCORING_WEIGHTS = {
    "priority": 0.30,          # 30% weight on priority
    "weather": 0.35,           # 35% weight on weather fit (INCREASED for better weather adaptation)
    "timing": 0.15,            # 15% weight on timing fit
    "cluster": 0.10,           # 10% weight on clustering
    "hotel_proximity": 0.05,   # 5% weight on hotel proximity
}

# Time blocks in a day
TIME_EARLY_MORNING = "early_morning"  # 6-9 AM
TIME_MORNING = "morning"  # 9-12 PM
TIME_AFTERNOON = "afternoon"  # 12-3 PM
TIME_LATE_AFTERNOON = "late_afternoon"  # 3-5 PM
TIME_EVENING = "evening"  # 5-7 PM
TIME_SUNSET = "sunset"  # 6-7 PM (special)
TIME_NIGHT = "night"  # 7+ PM

# Place duration categories (in hours)
DURATION_QUICK = 1.0  # Quick visit: 1 hour
DURATION_SHORT = 1.5  # Short visit: 1-2 hours
DURATION_MEDIUM = 2.5  # Medium visit: 2-3 hours
DURATION_LONG = 3.5  # Long visit: 3-4 hours
DURATION_HALF_DAY = 5.0  # Half day: 4-6 hours


# ============================================================================
# ITINERARY PLANNING SCHEMAS
# ============================================================================

class DayCharacteristics(BaseModel):
    """Characteristics of a single day in the trip"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    day_number: int = Field(..., description="Day number in trip (1-indexed)")
    day_type: str = Field(..., description="arrival/departure/full/partial")
    weather_condition: str = Field(..., description="good/fair/poor/extreme")
    weather_summary: Optional[WeatherSummary] = Field(None, description="Weather data for this day")
    max_activities: int = Field(..., description="Maximum activities allowed this day")
    arrival_time: Optional[str] = Field(None, description="Flight arrival time if arrival day")
    departure_time: Optional[str] = Field(None, description="Flight departure time if departure day")
    available_hours: float = Field(..., description="Estimated available hours for activities")
    intensity_target: str = Field(..., description="light/moderate/heavy")
    
    model_config = {"extra": "forbid"}


class PlaceSchedulingScore(BaseModel):
    """Scoring for scheduling a place on a specific day"""
    place_id: str = Field(..., description="Place identifier")
    place_name: str = Field(..., description="Place name")
    base_priority: float = Field(..., description="Base priority score (0-100)")
    weather_fit: float = Field(..., description="Weather suitability score (0-100)")
    timing_fit: float = Field(..., description="Time-of-day fit score (0-100)")
    cluster_bonus: float = Field(..., description="Clustering bonus score (0-50)")
    hotel_proximity_bonus: float = Field(default=0.0, description="Hotel proximity bonus (0-30)")
    crowd_fit: float = Field(default=0.0, description="Crowd level fit score (0-20)")
    effort_reward_score: float = Field(default=0.0, description="Effort vs reward score (0-20)")
    budget_penalty: float = Field(..., description="Budget pressure penalty (0-30)")
    final_score: float = Field(..., description="Final composite score")
    reasoning: str = Field(..., description="Why this score")
    
    model_config = {"extra": "forbid"}


class ScheduledActivity(BaseModel):
    """Activity with scheduling details"""
    place: PlaceOption = Field(..., description="The place")
    time_block: str = Field(..., description="When to visit")
    estimated_duration: float = Field(..., description="Estimated hours to spend")
    start_time_approx: Optional[str] = Field(None, description="Approximate start time")
    
    model_config = {"extra": "forbid"}


class DaySchedule(BaseModel):
    """Scheduled activities for a single day"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    day_number: int = Field(..., description="Day number in trip")
    day_type: str = Field(..., description="arrival/departure/full")
    activities: List[PlaceOption] = Field(default_factory=list, description="Scheduled places")
    scheduled_activities: List[ScheduledActivity] = Field(
        default_factory=list,
        description="Activities with scheduling details"
    )
    intensity: str = Field(..., description="light/moderate/heavy")
    total_entry_fees: int = Field(default=0, description="Total cost for this day")
    total_duration_hours: float = Field(default=0.0, description="Total duration of activities")
    time_blocks: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Activities grouped by time block (morning/afternoon/evening)"
    )
    weather_note: Optional[str] = Field(None, description="Weather consideration for this day")
    planning_notes: List[str] = Field(default_factory=list, description="Planning notes and tips")
    
    model_config = {"extra": "forbid"}


class ItineraryPlanningMetrics(BaseModel):
    """Metrics about the itinerary planning process"""
    total_days: int = Field(..., description="Total days in trip")
    full_days: int = Field(..., description="Number of full activity days")
    places_scheduled: int = Field(..., description="Total places scheduled")
    places_available: int = Field(..., description="Total places available")
    coverage_percentage: float = Field(..., description="Percentage of high-priority places covered")
    total_activity_cost: int = Field(..., description="Total entry fees for all activities")
    budget_remaining_after_activities: int = Field(..., description="Budget left after activities")
    average_daily_intensity: str = Field(..., description="Average intensity across days")
    heavy_days: int = Field(default=0, description="Number of heavy days")
    light_days: int = Field(default=0, description="Number of light days")
    weather_adapted_days: int = Field(default=0, description="Days where weather influenced planning")
    
    model_config = {"extra": "forbid"}


class EnrichedItinerary(BaseModel):
    """Complete enriched itinerary with day-by-day plans"""
    trip_summary: str = Field(..., description="One-line trip summary")
    day_schedules: List[DaySchedule] = Field(..., description="Day-by-day schedules")
    planning_metrics: ItineraryPlanningMetrics = Field(..., description="Planning metrics")
    general_tips: List[str] = Field(default_factory=list, description="General trip tips")
    packing_suggestions: List[str] = Field(default_factory=list, description="What to pack")
    budget_note: Optional[str] = Field(None, description="Budget consideration note")
    
    model_config = {"extra": "forbid"}


# ============================================================================
# HELPER FUNCTIONS - WEATHER ANALYSIS
# ============================================================================

def categorize_weather(weather: Optional[WeatherSummary]) -> str:
    """
    Categorize weather into travel-friendly categories.
    
    Args:
        weather: Weather summary for a day
        
    Returns:
        Weather category: good/fair/poor/extreme
    """
    if not weather:
        return WEATHER_FAIR
    
    condition = weather.condition.lower()
    temp_avg = weather.temp_avg_c
    rain_chance = weather.rain_chance
    
    # Check for extreme conditions
    if temp_avg < 5 or temp_avg > 40:
        return WEATHER_EXTREME
    
    # Check for poor weather
    if rain_chance > 0.6 or "storm" in condition or "heavy rain" in condition:
        return WEATHER_POOR
    
    # Check for good weather
    if rain_chance < 0.2 and ("clear" in condition or "sunny" in condition):
        if 15 <= temp_avg <= 30:
            return WEATHER_GOOD
    
    # Default to fair
    return WEATHER_FAIR


def is_outdoor_friendly(weather_category: str) -> bool:
    """Check if weather is suitable for outdoor activities."""
    return weather_category in [WEATHER_GOOD, WEATHER_FAIR]


def is_indoor_preferred(weather_category: str) -> bool:
    """Check if indoor activities are preferred due to weather."""
    return weather_category in [WEATHER_POOR, WEATHER_EXTREME]


# ============================================================================
# HELPER FUNCTIONS - PRIORITY MAPPING
# ============================================================================

def get_priority_score(priority_str: str) -> float:
    """
    Convert priority string to numerical score.
    
    Args:
        priority_str: Priority level string
        
    Returns:
        Score from 0-100
    """
    priority_map = {
        PRIORITY_MUST_VISIT: 100.0,
        PRIORITY_HIGH: 80.0,
        PRIORITY_RECOMMENDED: 60.0,
        PRIORITY_OPTIONAL: 40.0,
        PRIORITY_SKIPPABLE: 20.0,
    }
    return priority_map.get(priority_str, 50.0)


def is_high_priority(priority_str: str) -> bool:
    """Check if place is high priority."""
    return priority_str in [PRIORITY_MUST_VISIT, PRIORITY_HIGH]


# ============================================================================
# HELPER FUNCTIONS - DISTANCE/CLUSTERING
# ============================================================================

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Distance in kilometers
    """
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


def get_place_coordinates(place: PlaceOption) -> Optional[Tuple[float, float]]:
    """
    Extract coordinates from enriched place object.
    
    Args:
        place: Place option (already enriched with coordinates if available)
        
    Returns:
        (lat, lng) tuple or None
    """
    # Try from place coordinates field (primary)
    if hasattr(place, 'coordinates') and place.coordinates:
        if isinstance(place.coordinates, dict):
            lat = place.coordinates.get('lat') or place.coordinates.get('latitude')
            lng = place.coordinates.get('lng') or place.coordinates.get('longitude')
            if lat and lng:
                return (float(lat), float(lng))
    
    # Try from enriched latitude/longitude attributes
    if hasattr(place, 'latitude') and hasattr(place, 'longitude'):
        if place.latitude and place.longitude:
            return (float(place.latitude), float(place.longitude))
    
    return None


def get_place_zone(place: PlaceOption) -> Optional[str]:
    """
    Extract zone/area tag from enriched place object.
    
    Args:
        place: Place option (already enriched with zone if available)
        
    Returns:
        Zone string (north/south/east/west/central) or None
    """
    # Try from enriched zone attribute
    if hasattr(place, 'zone') and place.zone:
        return place.zone.lower()
    
    # Try from enriched area attribute
    if hasattr(place, 'area') and place.area:
        area_lower = place.area.lower()
        if 'north' in area_lower:
            return ZONE_NORTH
        elif 'south' in area_lower:
            return ZONE_SOUTH
        elif 'east' in area_lower:
            return ZONE_EAST
        elif 'west' in area_lower:
            return ZONE_WEST
        elif 'central' in area_lower or 'center' in area_lower:
            return ZONE_CENTRAL
    
    return None


def get_distance_category(place1: PlaceOption, place2: PlaceOption) -> str:
    """
    Determine distance category between two places.
    Uses coordinates if available, falls back to zone tags.
    
    Args:
        place1, place2: Places to compare (already enriched)
        
    Returns:
        Distance category: cluster/nearby/far/isolated
    """
    # Try coordinate-based distance
    coords1 = get_place_coordinates(place1)
    coords2 = get_place_coordinates(place2)
    
    if coords1 and coords2:
        distance_km = calculate_haversine_distance(coords1[0], coords1[1], coords2[0], coords2[1])
        
        if distance_km < 2:
            return DISTANCE_SAME_CLUSTER
        elif distance_km < 5:
            return DISTANCE_NEARBY
        elif distance_km < 15:
            return DISTANCE_FAR
        else:
            return DISTANCE_ISOLATED
    
    # Fall back to zone-based clustering
    zone1 = get_place_zone(place1)
    zone2 = get_place_zone(place2)
    
    if zone1 and zone2:
        if zone1 == zone2:
            return DISTANCE_SAME_CLUSTER
        else:
            return DISTANCE_NEARBY  # Different zones but same city
    
    # Try distance_category from enriched place attribute
    if hasattr(place1, 'distance_category') and place1.distance_category:
        return place1.distance_category
    
    # Default: assume nearby
    return DISTANCE_NEARBY


def calculate_cluster_bonus(places_scheduled: List[PlaceOption], 
                           candidate: PlaceOption) -> float:
    """
    Calculate bonus score for clustering nearby places.
    
    Args:
        places_scheduled: Places already scheduled for this day (already enriched)
        candidate: Candidate place to add (already enriched)
        
    Returns:
        Bonus score (0-50)
    """
    if not places_scheduled:
        return 0.0
    
    max_bonus = 0.0
    for scheduled in places_scheduled:
        # Places are already enriched with coordinates/zones
        distance_cat = get_distance_category(scheduled, candidate)
        
        if distance_cat == DISTANCE_SAME_CLUSTER:
            max_bonus = max(max_bonus, 50.0)
        elif distance_cat == DISTANCE_NEARBY:
            max_bonus = max(max_bonus, 30.0)
        elif distance_cat == DISTANCE_FAR:
            max_bonus = max(max_bonus, 10.0)
    
    return max_bonus


def calculate_hotel_proximity_bonus(place: PlaceOption, 
                                   hotel: Optional[HotelOption],
                                   is_first_activity: bool) -> float:
    """
    Calculate bonus for places near hotel (especially for first activity of day).
    
    Args:
        place: Place to check (already enriched with coordinates if available)
        hotel: Hotel option
        is_first_activity: Whether this is first activity of the day
        
    Returns:
        Proximity bonus (0-30)
    """
    if not hotel:
        return 0.0
    
    # Try coordinate-based distance
    # Places are already enriched with coordinates/zones if available
    place_coords = get_place_coordinates(place)
    # Hotel typically doesn't have coordinates in schema, use city match
    
    # Simple heuristic: if place is in same city as hotel
    if place.city.lower() == hotel.city.lower():
        # Higher bonus for first activity
        if is_first_activity:
            return 30.0
        else:
            return 15.0
    
    return 0.0


# ============================================================================
# HELPER FUNCTIONS - DURATION & TIME BLOCKS
# ============================================================================

def get_place_duration_hours(place: PlaceOption, enrichment: Optional[Dict[str, Any]] = None) -> float:
    """
    Extract estimated visit duration for a place.
    
    Args:
        place: Place option
        enrichment: Optional enrichment data
        
    Returns:
        Duration in hours
    """
    # Try from enrichment timing_intelligence
    if enrichment and 'timing_intelligence' in enrichment:
        duration_str = enrichment['timing_intelligence'].get('recommended_duration', '')
        if duration_str:
            # Parse duration string like "1-2 hours", "2-3 hours", "Half day"
            duration_lower = duration_str.lower()
            if 'half day' in duration_lower or '4-6' in duration_lower:
                return DURATION_HALF_DAY
            elif '3-4' in duration_lower or '3 hours' in duration_lower:
                return DURATION_LONG
            elif '2-3' in duration_lower or '2 hours' in duration_lower:
                return DURATION_MEDIUM
            elif '1-2' in duration_lower:
                return DURATION_SHORT
            elif '1 hour' in duration_lower or '30 min' in duration_lower:
                return DURATION_QUICK
    
    # Try from place.recommended_duration field
    if hasattr(place, 'recommended_duration') and place.recommended_duration:
        duration_str = place.recommended_duration.lower()
        if 'half day' in duration_str or '4-6' in duration_str:
            return DURATION_HALF_DAY
        elif '3-4' in duration_str:
            return DURATION_LONG
        elif '2-3' in duration_str:
            return DURATION_MEDIUM
        elif '1-2' in duration_str:
            return DURATION_SHORT
        elif '1 hour' in duration_str:
            return DURATION_QUICK
    
    # Default based on category
    category = place.category.lower() if place.category else ""
    if 'museum' in category or 'palace' in category or 'fort' in category:
        return DURATION_MEDIUM  # 2-3 hours for museums/palaces
    elif 'temple' in category or 'monument' in category:
        return DURATION_SHORT  # 1-2 hours
    elif 'park' in category or 'garden' in category:
        return DURATION_SHORT
    elif 'market' in category or 'mall' in category:
        return DURATION_MEDIUM
    else:
        return DURATION_SHORT  # Default 1.5 hours


def get_best_time_blocks(place: PlaceOption) -> List[str]:
    """
    Get best time blocks for visiting a place.
    
    Args:
        place: Place option (already enriched with best_time_to_visit if available)
        
    Returns:
        List of suitable time blocks
    """
    # Try from enriched best_time_to_visit attribute
    if hasattr(place, 'best_time_to_visit') and place.best_time_to_visit:
        best_time_lower = place.best_time_to_visit.lower()
        if 'early' in best_time_lower or 'sunrise' in best_time_lower:
            return [TIME_EARLY_MORNING, TIME_MORNING]
        elif 'morning' in best_time_lower:
            return [TIME_MORNING, TIME_LATE_AFTERNOON]
        elif 'afternoon' in best_time_lower or 'noon' in best_time_lower:
            return [TIME_AFTERNOON, TIME_LATE_AFTERNOON]
        elif 'sunset' in best_time_lower:
            return [TIME_SUNSET, TIME_EVENING]
        elif 'evening' in best_time_lower:
            return [TIME_EVENING, TIME_LATE_AFTERNOON]
        elif 'night' in best_time_lower:
            return [TIME_NIGHT]
    
    # Try from enriched time_block attribute (if available)
    if hasattr(place, 'time_block') and place.time_block:
        return [place.time_block]
    
    # Default: flexible (works in multiple blocks)
    return [TIME_MORNING, TIME_AFTERNOON, TIME_EVENING]


# ============================================================================
# HELPER FUNCTIONS - BUDGET PRESSURE
# ============================================================================

def calculate_budget_pressure(
    budget_remaining: int,
    days_remaining: int,
    estimated_daily_need: int
) -> str:
    """
    Calculate budget pressure level.
    
    Args:
        budget_remaining: Remaining budget
        days_remaining: Remaining trip days
        estimated_daily_need: Estimated daily spending needed
        
    Returns:
        Pressure level: none/low/moderate/high/critical
    """
    if days_remaining <= 0:
        return BUDGET_PRESSURE_NONE
    
    # Prevent division by zero
    daily_total = days_remaining * estimated_daily_need
    if daily_total <= 0:
        return BUDGET_PRESSURE_NONE
    
    buffer_percentage = ((budget_remaining - daily_total) / daily_total * 100)
    
    if budget_remaining < 0:
        return BUDGET_PRESSURE_CRITICAL
    if buffer_percentage < 5:
        return BUDGET_PRESSURE_HIGH
    if buffer_percentage < 10:
        return BUDGET_PRESSURE_MODERATE
    if buffer_percentage < 20:
        return BUDGET_PRESSURE_LOW
    
    return BUDGET_PRESSURE_NONE


def calculate_budget_penalty(budget_pressure: str, entry_fee: int) -> float:
    """
    Calculate penalty score based on budget pressure and entry fee.
    
    Args:
        budget_pressure: Budget pressure level
        entry_fee: Entry fee for the place
        
    Returns:
        Penalty score (0-30)
    """
    # No penalty for free places
    if entry_fee == 0:
        return 0.0
    
    # Base penalty by budget pressure
    pressure_penalties = {
        BUDGET_PRESSURE_CRITICAL: 30.0,
        BUDGET_PRESSURE_HIGH: 20.0,
        BUDGET_PRESSURE_MODERATE: 10.0,
        BUDGET_PRESSURE_LOW: 5.0,
        BUDGET_PRESSURE_NONE: 0.0,
    }
    
    base_penalty = pressure_penalties.get(budget_pressure, 0.0)
    
    # Additional penalty for expensive places
    if entry_fee > 500:
        base_penalty += 10.0
    elif entry_fee > 200:
        base_penalty += 5.0
    
    return min(base_penalty, 30.0)


# ============================================================================
# HELPER FUNCTIONS - FLIGHT TIME ANALYSIS
# ============================================================================

def get_available_hours_on_arrival(arrival_time_str: str) -> float:
    """
    Calculate available hours for activities on arrival day.
    
    Args:
        arrival_time_str: Arrival time in ISO format or HH:MM format
        
    Returns:
        Available hours (accounting for check-in, rest, etc.)
    """
    try:
        # Parse time
        if "T" in arrival_time_str:
            arrival_time = datetime.fromisoformat(arrival_time_str.replace("Z", "+00:00"))
            hour = arrival_time.hour
        else:
            hour = int(arrival_time_str.split(":")[0])
        
        # Early morning arrival (before 9 AM) → ~6 hours available
        if hour < 9:
            return 6.0
        # Morning arrival (9-12) → ~5 hours
        elif hour < 12:
            return 5.0
        # Afternoon arrival (12-15) → ~3 hours
        elif hour < 15:
            return 3.0
        # Late afternoon/evening (15-18) → ~2 hours
        elif hour < 18:
            return 2.0
        # Night arrival → ~0 hours (rest)
        else:
            return 0.5
    except:
        # Default: moderate arrival
        return 3.0


def get_available_hours_before_departure(departure_time_str: str) -> float:
    """
    Calculate available hours for activities before departure.
    
    Args:
        departure_time_str: Departure time in ISO format or HH:MM format
        
    Returns:
        Available hours (accounting for check-out, travel to airport, etc.)
    """
    try:
        # Parse time
        if "T" in departure_time_str:
            departure_time = datetime.fromisoformat(departure_time_str.replace("Z", "+00:00"))
            hour = departure_time.hour
        else:
            hour = int(departure_time_str.split(":")[0])
        
        # Night/early morning departure (before 6 AM) → ~0 hours
        if hour < 6:
            return 0.0
        # Morning departure (6-9) → ~1 hour
        elif hour < 9:
            return 1.0
        # Mid-morning (9-12) → ~3 hours
        elif hour < 12:
            return 3.0
        # Afternoon (12-15) → ~4 hours
        elif hour < 15:
            return 4.0
        # Late afternoon/evening (15-20) → ~6 hours
        elif hour < 20:
            return 6.0
        # Night departure → ~8 hours (full day)
        else:
            return 8.0
    except:
        # Default: mid-day departure
        return 3.0


# ============================================================================
# HELPER FUNCTIONS - WEATHER MATCHING
# ============================================================================

def calculate_weather_fit_score(place: PlaceOption, weather_category: str) -> float:
    """
    Calculate how well a place fits the weather conditions.
    
    Args:
        place: Place option
        weather_category: Weather category for the day
        
    Returns:
        Fit score (0-100)
    """
    # Get weather sensitivity from place
    weather_sensitivity = getattr(place, "weather_sensitivity", None)
    if not weather_sensitivity:
        weather_sensitivity = "outdoor"  # Default assumption
    
    sensitivity_lower = weather_sensitivity.lower()
    
    # Perfect fits
    if weather_category == WEATHER_GOOD:
        if "outdoor" in sensitivity_lower or "beach" in sensitivity_lower:
            return 100.0
        elif "indoor" in sensitivity_lower:
            return 80.0
        else:
            return 90.0
    
    elif weather_category == WEATHER_FAIR:
        # Fair weather works for most things
        return 85.0
    
    elif weather_category == WEATHER_POOR:
        if "indoor" in sensitivity_lower or "weather-proof" in sensitivity_lower:
            return 100.0
        elif "outdoor" in sensitivity_lower:
            return 30.0
        else:
            return 60.0
    
    elif weather_category == WEATHER_EXTREME:
        if "indoor" in sensitivity_lower or "weather-proof" in sensitivity_lower:
            return 100.0
        else:
            return 20.0
    
    return 70.0  # Default neutral score


# ============================================================================
# HELPER FUNCTIONS - TIME-OF-DAY MATCHING
# ============================================================================

def calculate_timing_fit_score(place: PlaceOption, time_block: str) -> float:
    """
    Calculate how well a place fits a specific time block.
    Uses best_time_to_visit from enriched place object.
    
    Args:
        place: Place option (already enriched with best_time_to_visit if available)
        time_block: Time block to check
        
    Returns:
        Fit score (0-100)
    """
    # Access best time blocks directly from enriched place object
    best_blocks = get_best_time_blocks(place)
    
    # Perfect match
    if time_block in best_blocks:
        return 100.0
    
    # Adjacent blocks get partial credit
    if time_block == TIME_MORNING and TIME_EARLY_MORNING in best_blocks:
        return 85.0
    if time_block == TIME_AFTERNOON and (TIME_MORNING in best_blocks or TIME_LATE_AFTERNOON in best_blocks):
        return 80.0
    if time_block == TIME_EVENING and (TIME_LATE_AFTERNOON in best_blocks or TIME_SUNSET in best_blocks):
        return 85.0
    
    # Default: okay but not ideal
    return 60.0


# ============================================================================
# CORE PLANNING FUNCTIONS
# ============================================================================

def analyze_day_characteristics(
    dates: List[str],
    flight: Optional[FlightOption],
    weather_summaries: List[WeatherSummary]
) -> List[DayCharacteristics]:
    """
    Analyze characteristics of each day in the trip.
    
    Args:
        dates: List of dates in the trip
        flight: Flight option (if any)
        weather_summaries: Weather data for each day
        
    Returns:
        List of day characteristics
    """
    characteristics = []
    weather_by_date = {w.date: w for w in weather_summaries}
    
    for idx, date in enumerate(dates):
        day_num = idx + 1
        weather = weather_by_date.get(date)
        weather_cat = categorize_weather(weather)
        
        # Initialize times to None
        arrival_time = None
        departure_time = None
        
        # Determine day type
        is_first = (idx == 0)
        is_last = (idx == len(dates) - 1)
        
        if is_first and flight:
            day_type = DAY_TYPE_ARRIVAL
            arrival_time = flight.arrival_time
            available_hours = get_available_hours_on_arrival(arrival_time)
            max_activities = MAX_ACTIVITIES_ARRIVAL
            intensity = INTENSITY_LIGHT
        elif is_last and flight:
            day_type = DAY_TYPE_DEPARTURE
            departure_time = flight.departure_time if hasattr(flight, 'departure_time') else None
            available_hours = get_available_hours_before_departure(departure_time) if departure_time else 4.0
            max_activities = MAX_ACTIVITIES_DEPARTURE
            intensity = INTENSITY_LIGHT
        else:
            day_type = DAY_TYPE_FULL
            available_hours = 10.0  # Full day ~10 hours
            max_activities = MAX_ACTIVITIES_FULL_DAY
            
            # Vary intensity across days (don't make all days heavy)
            if idx % 3 == 0:
                intensity = INTENSITY_MODERATE
            elif idx % 3 == 1:
                intensity = INTENSITY_HEAVY
            else:
                intensity = INTENSITY_LIGHT
        
        char = DayCharacteristics(
            date=date,
            day_number=day_num,
            day_type=day_type,
            weather_condition=weather_cat,
            weather_summary=weather,
            max_activities=max_activities,
            arrival_time=arrival_time if is_first and flight else None,
            departure_time=departure_time if is_last and flight and hasattr(flight, 'departure_time') else None,
            available_hours=available_hours,
            intensity_target=intensity
        )
        characteristics.append(char)
    
    return characteristics


def score_place_for_day(
    place: PlaceOption,
    day_char: DayCharacteristics,
    already_scheduled: List[PlaceOption],
    budget_pressure: str,
    hotel: Optional[HotelOption] = None
) -> PlaceSchedulingScore:
    """
    Score how well a place fits a specific day.
    Uses RICH enrichment signals: priority, skip_if, crowd_level, weather_dependency, effort_reward.
    
    Args:
        place: Place to score (already enriched with attributes)
        day_char: Day characteristics
        already_scheduled: Places already scheduled for this day
        budget_pressure: Current budget pressure level
        hotel: Hotel option for proximity bonus
        
    Returns:
        Scheduling score
        
    Note:
        PlaceOption objects are already mutated by enrich_places() with enriched
        attributes directly attached, so no separate enrichment dict is needed.
    """
    # Extract priority from enrichment (RICHER SIGNALS)
    # PlaceOption objects are already enriched with priority, skip_if, etc.
    priority_str = PRIORITY_RECOMMENDED
    skip_if_conditions = []
    
    # Try to get enriched priority from place object
    if hasattr(place, "priority"):
        priority_str = place.priority
    
    # Try to get skip conditions from place object
    if hasattr(place, "skip_if"):
        skip_if_conditions = place.skip_if
        
        # Check skip conditions
        for skip_condition in skip_if_conditions:
            condition_lower = skip_condition.lower()
            if "budget" in condition_lower and budget_pressure in [BUDGET_PRESSURE_HIGH, BUDGET_PRESSURE_CRITICAL]:
                priority_str = PRIORITY_SKIPPABLE
            elif "time" in condition_lower and day_char.day_type != DAY_TYPE_FULL:
                priority_str = PRIORITY_OPTIONAL
    
    # Fallback: Infer from rating if no enriched priority
    if not hasattr(place, "priority"):
        if place.rating >= 4.5:
            priority_str = PRIORITY_HIGH
        elif place.rating >= 4.0:
            priority_str = PRIORITY_RECOMMENDED
        else:
            priority_str = PRIORITY_OPTIONAL
    
    # Calculate component scores
    base_priority = get_priority_score(priority_str)
    
    # Weather fit (access weather_dependency directly from enriched place object)
    weather_fit = 50.0  # Default neutral score
    if hasattr(place, 'weather_dependency'):
        weather_dep = place.weather_dependency
        if weather_dep == 'indoor':
            weather_fit = 100.0 if day_char.weather_condition in [WEATHER_POOR, WEATHER_EXTREME] else 80.0
        elif weather_dep == 'outdoor':
            weather_fit = 100.0 if day_char.weather_condition == WEATHER_GOOD else 40.0
        else:
            weather_fit = calculate_weather_fit_score(place, day_char.weather_condition)
    else:
        weather_fit = calculate_weather_fit_score(place, day_char.weather_condition)
    
    # Timing fit (use best time blocks from enriched place object)
    timing_fit = calculate_timing_fit_score(place, TIME_MORNING)
    
    # Cluster bonus (use real coordinates/zones from enriched place objects)
    cluster_bonus = calculate_cluster_bonus(already_scheduled, place)
    
    # Hotel proximity bonus (first activity should be near hotel)
    is_first = len(already_scheduled) == 0
    hotel_proximity_bonus = calculate_hotel_proximity_bonus(place, hotel, is_first)
    
    # Crowd fit (prefer peaceful places when many are already scheduled)
    crowd_fit = 0.0
    if hasattr(place, 'crowd_level'):
        crowd_level = place.crowd_level
        if crowd_level == 'peaceful' or crowd_level == 'moderate':
            crowd_fit = 20.0
        elif crowd_level == 'very-crowded' and len(already_scheduled) >= 2:
            crowd_fit = -10.0
    
    # Effort vs reward (access directly from enriched place object)
    effort_reward_score = 0.0
    if hasattr(place, 'effort_reward'):
        effort_reward = place.effort_reward
        if effort_reward >= 7.0:  # High value
            effort_reward_score = 10.0
        elif effort_reward >= 5.0:  # Moderate value
            effort_reward_score = 5.0
        elif effort_reward < 3.0:  # Poor value
            effort_reward_score = -10.0
    
    # Budget penalty
    budget_penalty = calculate_budget_penalty(budget_pressure, place.entry_fee)
    
    # Calculate final score with weighted components (using constants)
    final_score = (
        base_priority * SCORING_WEIGHTS["priority"] +
        weather_fit * SCORING_WEIGHTS["weather"] +
        timing_fit * SCORING_WEIGHTS["timing"] +
        cluster_bonus * SCORING_WEIGHTS["cluster"] +
        hotel_proximity_bonus * SCORING_WEIGHTS["hotel_proximity"] +
        crowd_fit +
        effort_reward_score +
        - budget_penalty
    )
    
    reasoning_parts = [
        f"Priority: {priority_str} ({base_priority:.0f})",
        f"Weather: {weather_fit:.0f}",
        f"Timing: {timing_fit:.0f}",
        f"Cluster: +{cluster_bonus:.0f}",
    ]
    if hotel_proximity_bonus > 0:
        reasoning_parts.append(f"Hotel: +{hotel_proximity_bonus:.0f}")
    if crowd_fit != 0:
        reasoning_parts.append(f"Crowd: {crowd_fit:+.0f}")
    if effort_reward_score != 0:
        reasoning_parts.append(f"Effort/Reward: {effort_reward_score:+.0f}")
    if budget_penalty > 0:
        reasoning_parts.append(f"Budget: -{budget_penalty:.0f}")
    
    reasoning = ", ".join(reasoning_parts)
    
    return PlaceSchedulingScore(
        place_id=place.id,
        place_name=place.name,
        base_priority=base_priority,
        weather_fit=weather_fit,
        timing_fit=timing_fit,
        cluster_bonus=cluster_bonus,
        hotel_proximity_bonus=hotel_proximity_bonus,
        crowd_fit=crowd_fit,
        effort_reward_score=effort_reward_score,
        budget_penalty=budget_penalty,
        final_score=final_score,
        reasoning=reasoning
    )


def allocate_time_blocks(places: List[PlaceOption], 
                         available_hours: float,
                         enrichments: Optional[Dict[str, Any]] = None) -> List[ScheduledActivity]:
    """
    Allocate places to time blocks based on best_time_to_visit and duration.
    
    Args:
        places: Places to schedule (already sorted by priority)
        available_hours: Hours available for activities
        enrichments: Optional enrichment data
        
    Returns:
        List of scheduled activities with time blocks
    """
    scheduled_activities = []
    time_budget = available_hours
    current_time = 9.0  # Start at 9 AM
    
    # Define time block ranges
    time_block_ranges = {
        TIME_EARLY_MORNING: (6.0, 9.0),
        TIME_MORNING: (9.0, 12.0),
        TIME_AFTERNOON: (12.0, 15.0),
        TIME_LATE_AFTERNOON: (15.0, 17.0),
        TIME_EVENING: (17.0, 19.0),
        TIME_SUNSET: (18.0, 19.0),
        TIME_NIGHT: (19.0, 22.0),
    }
    
    for place in places:
        enrichment = enrichments.get(place.id) if enrichments else None
        
        # Get duration
        duration = get_place_duration_hours(place, enrichment)
        
        # Check if we have time
        if time_budget < duration * 0.5:
            break
        
        # Get best time blocks for this place
        best_blocks = get_best_time_blocks(place)
        
        # Find best matching time block based on current time
        chosen_block = None
        for block in best_blocks:
            if block in time_block_ranges:
                start, end = time_block_ranges[block]
                if start <= current_time < end:
                    chosen_block = block
                    break
        
        # If no perfect match, use the first best block that's still available
        if not chosen_block:
            for block in best_blocks:
                if block in time_block_ranges:
                    start, end = time_block_ranges[block]
                    if current_time < end:
                        chosen_block = block
                        current_time = start
                        break
        
        # If still no match, use current time block
        if not chosen_block:
            if current_time < 9:
                chosen_block = TIME_EARLY_MORNING
            elif current_time < 12:
                chosen_block = TIME_MORNING
            elif current_time < 15:
                chosen_block = TIME_AFTERNOON
            elif current_time < 17:
                chosen_block = TIME_LATE_AFTERNOON
            elif current_time < 19:
                chosen_block = TIME_EVENING
            else:
                chosen_block = TIME_NIGHT
        
        # Create scheduled activity
        start_time_str = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
        
        scheduled_activities.append(ScheduledActivity(
            place=place,
            time_block=chosen_block,
            estimated_duration=duration,
            start_time_approx=start_time_str
        ))
        
        # Update time budget and current time
        time_budget -= duration
        current_time += duration
        current_time += 0.5
        time_budget -= 0.5
        
        if time_budget <= 0:
            break
    
    return scheduled_activities


def build_day_schedule(
    day_char: DayCharacteristics,
    available_places: List[PlaceOption],
    budget_pressure: str,
    hotel: Optional[HotelOption] = None,
    places_enrichment: Optional[Dict[str, Any]] = None
) -> DaySchedule:
    """
    Build schedule for a single day with duration-based planning.
    
    Args:
        day_char: Day characteristics
        available_places: Places available to schedule
        budget_pressure: Current budget pressure level
        hotel: Hotel option for proximity
        places_enrichment: Optional enrichment data for places
        
    Returns:
        Day schedule
    """
    scheduled = []
    scheduled_activities = []
    total_fees = 0
    total_duration = 0.0
    planning_notes = []
    
    # Score all places for this day
    scores = []
    for place in available_places:
        score = score_place_for_day(place, day_char, scheduled, budget_pressure, hotel)
        scores.append((score, place))
    
    # Sort by score (highest first)
    scores.sort(key=lambda x: x[0].final_score, reverse=True)
    
    # Select places based on available time (not just count)
    available_hours = day_char.available_hours
    time_used = 0.0
    
    for score_obj, place in scores:
        enrichment = places_enrichment.get(place.id) if places_enrichment else None
        duration = get_place_duration_hours(place, enrichment)
        
        # Check if we have time (with 0.5h buffer for travel)
        if time_used + duration + 0.5 > available_hours:
            if len(scheduled) == 0:  # At least include one place
                pass
            else:
                planning_notes.append(f"Skipped {place.name} - insufficient time (needs {duration}h)")
                continue
        
        # Budget check
        if budget_pressure == BUDGET_PRESSURE_CRITICAL and place.entry_fee > 0:
            planning_notes.append(f"Skipped {place.name} due to budget constraints")
            continue
        
        # Add to schedule
        scheduled.append(place)
        total_fees += place.entry_fee
        time_used += duration + 0.5  # Include travel buffer
        
        # Respect max activities limit
        if len(scheduled) >= day_char.max_activities:
            break
    
    # PLACE EXHAUSTION STRATEGY: Handle when available places run out
    if len(scheduled) == 0 and len(available_places) > 0:
        # If no places met criteria, relax constraints and try again
        # Allow optional/low-priority places or even revisits
        planning_notes.append("Relaxed constraints - including optional activities")
        for place in available_places[:day_char.max_activities]:
            enrichment = places_enrichment.get(place.id) if places_enrichment else None
            duration = get_place_duration_hours(place, enrichment)
            
            scheduled.append(place)
            total_fees += place.entry_fee
            if len(scheduled) >= 2:  # At least 2 for a non-empty day
                break
    
    # LEISURE / BUFFER DAY INSERTION: If still no places and it's a light day with low budget pressure
    if len(scheduled) == 0 and day_char.intensity_target == INTENSITY_LIGHT and budget_pressure != BUDGET_PRESSURE_CRITICAL:
        planning_notes.append("Free exploration / beach / cafe hopping - leisure day")
        # This is a buffer/rest day - no structured activities
    
    # Allocate to time blocks intelligently
    scheduled_activities = allocate_time_blocks(scheduled, day_char.available_hours, places_enrichment)
    
    # Calculate total duration
    total_duration = sum(act.estimated_duration for act in scheduled_activities)
    
    # Determine actual intensity based on duration and count
    if total_duration <= 3 or len(scheduled) <= 2:
        actual_intensity = INTENSITY_LIGHT
    elif total_duration <= 6 or len(scheduled) == 3:
        actual_intensity = INTENSITY_MODERATE
    else:
        actual_intensity = INTENSITY_HEAVY
    
    # Add weather note
    weather_note = None
    if day_char.weather_condition == WEATHER_POOR:
        weather_note = "Rainy day - indoor activities prioritized"
    elif day_char.weather_condition == WEATHER_EXTREME:
        weather_note = "Extreme weather - stay indoors or reschedule outdoor activities"
    elif day_char.weather_condition == WEATHER_GOOD:
        weather_note = "Perfect weather for outdoor activities"
    
    # Add day-type specific notes
    if day_char.day_type == DAY_TYPE_ARRIVAL:
        planning_notes.append(f"Arrival day - light schedule with ~{day_char.available_hours:.0f} hours available")
    elif day_char.day_type == DAY_TYPE_DEPARTURE:
        planning_notes.append(f"Departure day - limited time with ~{day_char.available_hours:.0f} hours available")
    
    # Build time_blocks dictionary
    time_blocks = defaultdict(list)
    for activity in scheduled_activities:
        time_blocks[activity.time_block].append(activity.place.name)
    
    return DaySchedule(
        date=day_char.date,
        day_number=day_char.day_number,
        day_type=day_char.day_type,
        activities=scheduled,
        scheduled_activities=scheduled_activities,
        intensity=actual_intensity,
        total_entry_fees=total_fees,
        total_duration_hours=total_duration,
        time_blocks=dict(time_blocks),
        weather_note=weather_note,
        planning_notes=planning_notes
    )


# ============================================================================
# MAIN ENRICHMENT FUNCTION
# ============================================================================

def enrich_itinerary(
    dates: List[str],
    flight: Optional[FlightOption],
    hotel: Optional[HotelOption],
    places: List[PlaceOption],
    weather_summaries: List[WeatherSummary],
    budget_total: int,
    budget_spent_on_flight_hotel: int
) -> EnrichedItinerary:
    """
    Main function to build enriched itinerary with day-by-day plans.
    
    Args:
        dates: List of dates in the trip (YYYY-MM-DD format)
        flight: Selected flight (if any)
        hotel: Selected hotel (if any)
        places: List of available places (already enriched by enrich_places)
        weather_summaries: Weather data for trip dates
        budget_total: Total trip budget
        budget_spent_on_flight_hotel: Budget already spent on flight/hotel
        
    Returns:
        Enriched itinerary with complete day plans
        
    Note:
        PlaceOption objects are already mutated by enrich_places() with enriched
        attributes (priority, crowd_level, weather_dependency, etc.), so no
        separate enrichment dict is needed.
    """
    # Analyze each day
    day_characteristics = analyze_day_characteristics(dates, flight, weather_summaries)
    
    # Calculate budget pressure
    budget_for_activities = budget_total - budget_spent_on_flight_hotel
    avg_daily_need = budget_for_activities / len(dates) if dates else 0
    
    # Build schedule for each day
    day_schedules = []
    places_used = set()
    total_activity_cost = 0
    heavy_days = 0
    light_days = 0
    weather_adapted = 0
    
    for day_char in day_characteristics:
        # Filter out already used places
        available = [p for p in places if p.id not in places_used]
        
        # PLACE EXHAUSTION STRATEGY: If running low on places, allow revisits
        if len(available) < 2 and len(places) > 0:
            # Allow revisiting places (use all places again)
            available = places.copy()
            if day_char.day_number > 1:  # Don't note this on first day
                pass  # Silently allow revisits
        
        # Calculate current budget pressure
        days_remaining = len(dates) - (day_char.day_number - 1)
        budget_remaining = budget_for_activities - total_activity_cost
        pressure = calculate_budget_pressure(budget_remaining, days_remaining, int(avg_daily_need))
        
        # Build schedule (pass hotel for location bias)
        # Note: places are already enriched, so enrichment data is directly accessible
        schedule = build_day_schedule(day_char, available, pressure, hotel)
        day_schedules.append(schedule)
        
        # Track used places (but allow reuse if exhausted)
        for activity in schedule.activities:
            places_used.add(activity.id)
        
        # Update metrics
        total_activity_cost += schedule.total_entry_fees
        if schedule.intensity == INTENSITY_HEAVY:
            heavy_days += 1
        elif schedule.intensity == INTENSITY_LIGHT:
            light_days += 1
        
        if day_char.weather_condition in [WEATHER_POOR, WEATHER_EXTREME]:
            weather_adapted += 1
    
    # Calculate coverage
    high_priority_places = [p for p in places if getattr(p, "rating", 0) >= 4.0]
    high_priority_scheduled = len([p for p in places if p.id in places_used and p.rating >= 4.0])
    coverage = (high_priority_scheduled / len(high_priority_places) * 100) if high_priority_places else 0
    
    # Determine average intensity
    intensity_counts = defaultdict(int)
    for schedule in day_schedules:
        intensity_counts[schedule.intensity] += 1
    avg_intensity = max(intensity_counts, key=intensity_counts.get) if intensity_counts else INTENSITY_MODERATE
    
    # Build metrics
    metrics = ItineraryPlanningMetrics(
        total_days=len(dates),
        full_days=len([d for d in day_characteristics if d.day_type == DAY_TYPE_FULL]),
        places_scheduled=len(places_used),
        places_available=len(places),
        coverage_percentage=coverage,
        total_activity_cost=total_activity_cost,
        budget_remaining_after_activities=budget_for_activities - total_activity_cost,
        average_daily_intensity=avg_intensity,
        heavy_days=heavy_days,
        light_days=light_days,
        weather_adapted_days=weather_adapted
    )
    
    # General tips
    general_tips = []
    if heavy_days > len(dates) / 2:
        general_tips.append("Consider adding rest breaks - many heavy activity days scheduled")
    if weather_adapted > 0:
        general_tips.append(f"Itinerary adapted for weather on {weather_adapted} day(s)")
    if coverage < 70:
        general_tips.append("Some popular attractions couldn't be fit into schedule - consider extending trip")
    
    # Packing suggestions based on weather
    packing = []
    weather_conditions = [d.weather_condition for d in day_characteristics]
    if WEATHER_POOR in weather_conditions or WEATHER_EXTREME in weather_conditions:
        packing.append("Umbrella and rain gear")
    if WEATHER_GOOD in weather_conditions:
        packing.append("Sunscreen, sunglasses, and hat")
    packing.extend(["Comfortable walking shoes", "Water bottle", "Camera", "Power bank"])
    
    # Budget note
    budget_note = None
    if metrics.budget_remaining_after_activities < 0:
        budget_note = "⚠️ Activities exceed remaining budget - consider cheaper alternatives"
    elif metrics.budget_remaining_after_activities < avg_daily_need:
        budget_note = "Budget is tight - minimal buffer for unexpected expenses"
    elif budget_for_activities > 0:
        buffer_pct = (metrics.budget_remaining_after_activities / budget_for_activities) * 100
        budget_note = f"✓ {buffer_pct:.0f}% budget buffer remaining for meals, transport, and extras"
    else:
        budget_note = "Budget information not available"
    
    # Trip summary
    destination = hotel.city if hotel else "destination"
    trip_summary = f"{len(dates)}-day trip to {destination} with {len(places_used)} attractions planned"
    
    return EnrichedItinerary(
        trip_summary=trip_summary,
        day_schedules=day_schedules,
        planning_metrics=metrics,
        general_tips=general_tips,
        packing_suggestions=packing,
        budget_note=budget_note
    )


# ============================================================================
# UTILITY FUNCTIONS FOR INTEGRATION
# ============================================================================

def generate_trip_dates(start_date: str, end_date: str) -> List[str]:
    """
    Generate list of dates between start and end (inclusive).
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        List of date strings
    """
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    return dates


def convert_to_trip_plan(enriched_itinerary: EnrichedItinerary, 
                        flight: Optional[FlightOption],
                        hotel: Optional[HotelOption],
                        weather_summaries: List[WeatherSummary]) -> TripPlan:
    """
    Convert enriched itinerary to standard TripPlan schema.
    
    Args:
        enriched_itinerary: Enriched itinerary
        flight: Flight option
        hotel: Hotel option
        weather_summaries: Weather summaries
        
    Returns:
        TripPlan object
    """
    # Convert day schedules to DayPlan objects
    day_plans = []
    for schedule in enriched_itinerary.day_schedules:
        day_plan = DayPlan(
            date=schedule.date,
            activities=schedule.activities
        )
        day_plans.append(day_plan)
    
    # Build notes
    notes_parts = []
    notes_parts.append(enriched_itinerary.trip_summary)
    notes_parts.append("")
    notes_parts.append("Planning Metrics:")
    notes_parts.append(f"- {enriched_itinerary.planning_metrics.places_scheduled} places scheduled")
    notes_parts.append(f"- Coverage: {enriched_itinerary.planning_metrics.coverage_percentage:.0f}%")
    notes_parts.append(f"- Total activity cost: ₹{enriched_itinerary.planning_metrics.total_activity_cost}")
    if enriched_itinerary.budget_note:
        notes_parts.append("")
        notes_parts.append(enriched_itinerary.budget_note)
    if enriched_itinerary.general_tips:
        notes_parts.append("")
        notes_parts.append("Tips:")
        for tip in enriched_itinerary.general_tips:
            notes_parts.append(f"- {tip}")
    
    notes = "\n".join(notes_parts)
    
    # Convert weather summaries to WeatherInfo (simplified)
    from backend.app.shared.schemas import WeatherInfo
    weather_info = [
        WeatherInfo(
            city=w.city,
            date=w.date,
            condition=w.condition,
            temperature_c=w.temp_avg_c
        )
        for w in weather_summaries
    ]
    
    return TripPlan(
        flight=flight,
        hotel=hotel,
        days=day_plans,
        weather=weather_info,
        notes=notes
    )
