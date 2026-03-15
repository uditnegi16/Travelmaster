"""
Composer Agent for TravelGuru v5.
Pure presentation/narration agent that converts enriched trip data into beautiful narrative.
This is a FORMATTER, not a planner - it only serializes and beautifies, never modifies data.

# THIS AGENT NEVER CALLS TOOLS. NEVER MODIFIES DATA. ONLY NARRATES.
"""

import json
import logging
from typing import Any, Dict
from pathlib import Path

from openai import OpenAI

from shared.schemas import TripResponse
from core.config import COMPOSER_MODEL, OPENAI_API_KEY

logger = logging.getLogger(__name__)

# ADD THIS FUNCTION at the top of composer_agent.py (after imports)
def _truncate_for_llm(data: dict, max_chars: int = 8000) -> dict:
    """Truncate lists in data dict so JSON stays under max_chars."""
    import copy
    d = copy.deepcopy(data)
    # Trim long lists
    for key in ("flights", "hotels", "places", "weather", "days", "day_schedules"):
        if key in d and isinstance(d[key], list):
            d[key] = d[key][:3]
    # Trim nested itinerary days
    if "itinerary" in d and isinstance(d.get("itinerary"), dict):
        days = d["itinerary"].get("days") or d["itinerary"].get("day_schedules") or []
        d["itinerary"]["days"] = days[:3]
    # Hard truncate if still too big
    serialised = json.dumps(d, ensure_ascii=False)
    if len(serialised) > max_chars:
        # Last resort: truncate the string itself
        d = {"_truncated": True, "raw": serialised[:max_chars]}
    return d
class ComposerAgent:
    """
    Composer agent that transforms enriched trip data into narrative text.
    
    This is a pure presentation layer:
    - NO tool calls
    - NO ranking, scoring, filtering, computing
    - NO data modification
    - ONLY serialization + LLM narration
    """
    
    # def __init__(self):
    #     """Initialize the composer agent with OpenAI client and system prompt."""
    #     self.client = OpenAI(api_key=OPENAI_API_KEY)
    #     self.model = COMPOSER_MODEL
    #     self.system_prompt = self._load_system_prompt()
    #     logger.info(f"ComposerAgent initialized with model: {self.model}")
    def __init__(self):
        """Initialize the composer agent with OpenAI client and system prompt."""
        from core.config import OPENAI_BASE_URL
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL or None,
        )
        self.model = COMPOSER_MODEL
        self.system_prompt = self._load_system_prompt()
        logger.info(f"ComposerAgent initialized with model: {self.model}")
    def _load_system_prompt(self) -> str:
        """
        Load composer system prompt from prompts/composer.txt.
        
        Returns:
            System prompt content
            
        Raises:
            RuntimeError: If prompt file not found
        """
        prompt_path = Path(__file__).parent / "prompts" / "composer.txt"
        if not prompt_path.exists():
            raise RuntimeError(f"Composer prompt file not found: {prompt_path}")
        
        prompt = prompt_path.read_text(encoding="utf-8")
        logger.debug(f"Loaded system prompt from {prompt_path}")
        logger.warning(f"USING COMPOSER PROMPT: {prompt_path}")
        return prompt
    
    def _get_embedded_enhanced_prompt(self) -> str:
        """Get embedded enhanced prompt if file doesn't exist."""
        return """You are a MULTI-AGENT TRAVEL INTELLIGENCE COMPOSER.

You receive COMPLETE ANALYSIS from multiple specialized AI agents. Your job is to EXPLAIN EACH AGENT'S REASONING (NOT just decisions).

Your narrative MUST include these sections in order:

1️⃣ FLIGHT SELECTION ANALYSIS
   - Explain market analysis (price range, distribution)
   - Why this specific flight was chosen
   - Value proposition (savings, percentile ranking)
   - Convenience scores and timing analysis
   - Deal detection and booking advice

2️⃣ HOTEL SELECTION ANALYSIS
   - Quality vs value tradeoff
   - Why this hotel fits the budget/preference profile
   - Amenities scoring and location benefits
   - Price positioning in market

3️⃣ PLACES CURATION LOGIC
   - Why these specific places were chosen
   - Match scores and priority rankings
   - Audience suitability analysis
   - Best visit times and duration recommendations

4️⃣ WEATHER IMPACT ANALYSIS
   - Daily forecasts with impact assessment
   - How weather influenced scheduling decisions
   - Activity recommendations based on conditions

5️⃣ BUDGET HEALTH & TRADEOFFS
   - Financial breakdown and health analysis
   - Budget pressure assessment
   - Spending optimization recommendations
   - Tradeoffs made (e.g., cheaper hotel → more activities)

6️⃣ DAY-BY-DAY ITINERARY
   - Scheduling intelligence and pacing decisions
   - Why activities were placed on specific days/times
   - Intensity balancing and rest periods
   - Practical planning notes

CRITICAL RULES:
- NEVER just list data — ALWAYS explain WHY
- Use specific numbers from enrichment (percentiles, scores, savings)
- Highlight tradeoffs explicitly
- Explain scheduling logic (why this place at this time on this day)
- Show agent intelligence ("The system identified...", "Analysis revealed...")
- Be specific, not generic ("18% below market average" not "good deal")
- Use emojis sparingly for visual appeal
- Structure with clear section headers
- Total length: 800-1200 words
"""
    
    def _load_enhanced_system_prompt(self) -> str:
        """
        Load enhanced multi-agent composer prompt.
        
        Returns:
            Enhanced system prompt with multi-agent awareness
        """
        prompt_path = Path(__file__).parent / "prompts" / "composer_multiagent.txt"
        if prompt_path.exists():
            prompt = prompt_path.read_text(encoding="utf-8")
            logger.debug(f"Loaded enhanced system prompt from {prompt_path}")
            return prompt
        else:
            # Fallback to embedded prompt if file doesn't exist
            logger.warning(f"Enhanced prompt file not found: {prompt_path}, using embedded")
            return self._get_embedded_enhanced_prompt()
    
    def _serialize_trip(self, trip: TripResponse) -> Dict[str, Any]:
        """
        Serialize TripResponse to JSON-safe dict WITH all enrichment analyses.
        
        Converts all nested Pydantic models into dict structure suitable for LLM.
        CRITICAL: Includes all agent analyses for multi-agent reasoning explanation.
        
        Args:
            trip: TripResponse with enriched data and all agent analyses
            
        Returns:
            JSON-safe dict with all trip data + enrichment
            
        Raises:
            RuntimeError: If serialization fails
        """
        try:
            # Use Pydantic's model_dump for clean serialization
            serialized = trip.model_dump(mode="json")
            
            # Log what enrichment data is available
            enrichment_fields = []
            if serialized.get("flight_analysis"):
                enrichment_fields.append("flight_analysis")
            if serialized.get("hotel_analysis"):
                enrichment_fields.append("hotel_analysis")
            if serialized.get("places_analysis"):
                enrichment_fields.append("places_analysis")
            if serialized.get("weather_analysis"):
                enrichment_fields.append("weather_analysis")
            if serialized.get("budget_analysis"):
                enrichment_fields.append("budget_analysis")
            if serialized.get("itinerary_enrichment"):
                enrichment_fields.append("itinerary_enrichment")
            
            logger.debug(
                f"Serialized trip: {len(json.dumps(serialized))} bytes with enrichment: "
                f"{', '.join(enrichment_fields) if enrichment_fields else 'none'}"
            )
            return serialized
        
        except Exception as e:
            logger.error(f"Failed to serialize trip: {e}", exc_info=True)
            raise RuntimeError(f"Trip serialization failed: {e}") from e
    
    def _call_llm_streaming(self, messages: list, context: str = "chunk") -> str:
        """
        Call LLM with streaming to handle large outputs.
        
        Args:
            messages: List of message dicts for the LLM
            context: Description of what's being generated (for logging)
            
        Returns:
            Generated narrative text
            
        Raises:
            RuntimeError: If LLM call fails
        """
        try:
            logger.debug(f"Generating {context} with streaming...")
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=True
            )
            
            narrative_chunks = []
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    narrative_chunks.append(chunk.choices[0].delta.content)
            
            narrative = "".join(narrative_chunks)
            
            if not narrative:
                raise RuntimeError(f"LLM returned empty response for {context}")
            
            logger.debug(f"Generated {context}: {len(narrative)} characters")
            return narrative
        
        except Exception as e:
            logger.error(f"LLM streaming call failed for {context}: {e}", exc_info=True)
            raise RuntimeError(f"LLM call failed for {context}: {e}") from e
    
    def _generate_pass_1_intro(self, serialized_trip: Dict[str, Any]) -> str:
        """
        PASS 1: Generate Summary + ALL Flight Options + ALL Hotel Options.
        
        Args:
            serialized_trip: Full trip data
            
        Returns:
            Narrative for intro sections
        """
        logger.info("PASS 1: Generating Summary + Flights + Hotels...")
        
        # Extract only the data needed for this pass
        pass_1_data = {
            "user_query": serialized_trip.get("trip_plan", {}).get("user_query", ""),
            "origin": "Delhi",  # Extract from trip
            "destination": "Goa",  # Extract from trip
            "dates": {
                "start": serialized_trip.get("trip_plan", {}).get("start_date"),
                "end": serialized_trip.get("trip_plan", {}).get("end_date"),
            },
            "num_travelers": serialized_trip.get("trip_plan", {}).get("num_adults", 2),
            "flight_analysis": serialized_trip.get("flight_analysis"),
            "hotel_analysis": serialized_trip.get("hotel_analysis"),
            "selected_flight": serialized_trip.get("trip_plan", {}).get("flight"),
            "selected_hotel": serialized_trip.get("trip_plan", {}).get("hotel"),
        }
        
        prompt = f"""You are composing PASS 1 of a comprehensive travel itinerary.

TASK: Generate ONLY these sections (400-500 words EACH):
1. SHORT SUMMARY (400-500 words)
2. ALL FLIGHT OPTIONS (150-200 words PER flight - list EVERY flight)
3. ALL HOTEL OPTIONS (150-200 words PER hotel - list EVERY hotel)

DO NOT generate day-by-day itinerary, weather, budget, or tips. Those come in later passes.

BE VERBOSE. WRITE LONG. Each flight/hotel needs 150-200 words minimum.

Data:
{json.dumps(_truncate_for_llm(pass_1_data), indent=2, ensure_ascii=False)}

Follow the comprehensive structure from your system prompt for these sections ONLY."""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        return self._call_llm_streaming(messages, "PASS 1: Intro + Flights + Hotels")
    
    def _generate_pass_2_day(self, serialized_trip: Dict[str, Any], day_number: int) -> str:
        """
        PASS 2-N: Generate ONE day of itinerary (400-600 words).
        
        Args:
            serialized_trip: Full trip data
            day_number: Which day to generate (1-indexed)
            
        Returns:
            Narrative for this day
        """
        logger.info(f"PASS {day_number + 1}: Generating Day {day_number}...")
        
        # Extract data for this specific day ONLY
        days = serialized_trip.get("trip_plan", {}).get("days", [])
        if day_number - 1 >= len(days):
            logger.warning(f"Day {day_number} not found in trip plan")
            return ""
        
        day_data = days[day_number - 1]
        
        # Extract ONLY place IDs mentioned in this day
        place_ids_for_day = set()
        for period in ['morning', 'afternoon', 'evening']:
            period_data = day_data.get(period, {})
            activities = period_data.get('activities', [])
            for activity in activities:
                if isinstance(activity, dict) and 'place_id' in activity:
                    place_ids_for_day.add(activity['place_id'])
        
        # Filter places_analysis to ONLY include places mentioned in this day
        places_analysis = serialized_trip.get("places_analysis", {})
        filtered_places = {}
        if isinstance(places_analysis, dict):
            for place_id in place_ids_for_day:
                if place_id in places_analysis:
                    filtered_places[place_id] = places_analysis[place_id]
        
        # Minimal weather context (just the day summary, not full data)
        weather_analysis = serialized_trip.get("weather_analysis", {})
        weather_summary = ""
        if isinstance(weather_analysis, dict):
            day_key = f"day_{day_number}"
            if day_key in weather_analysis:
                weather_summary = weather_analysis.get(day_key, {}).get("summary", "")
        
        pass_day_data = {
            "day_number": day_number,
            "day_data": day_data,
            "places_for_this_day": filtered_places,
            "weather_summary": weather_summary,
        }
        
        prompt = f"""You are composing PASS {day_number + 1} of a comprehensive travel itinerary.

TASK: Generate ONLY Day {day_number} of the day-by-day itinerary (400-600 words MINIMUM).

Write a COMPREHENSIVE, STORY-LIKE narrative for this SINGLE day including:
- Morning activities (with full sensory descriptions)
- Afternoon activities (with full sensory descriptions)  
- Evening activities (with full sensory descriptions)
- Weather context and how it influenced planning
- Why this order and pace makes sense
- Daily budget breakdown

BE VERBOSE. WRITE LONG. This ONE day should be 400-600 words minimum.
Paint vivid pictures. Make readers FEEL the experience.

Data for Day {day_number}:
{json.dumps(pass_day_data, indent=2, ensure_ascii=False)}

Follow the comprehensive day-by-day structure from your system prompt."""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        return self._call_llm_streaming(messages, f"PASS {day_number + 1}: Day {day_number}")
    
    def _generate_pass_final_closing(self, serialized_trip: Dict[str, Any]) -> str:
        """
        PASS FINAL: Generate Weather + Budget + Tips + Thank You.
        
        Args:
            serialized_trip: Full trip data
            
        Returns:
            Narrative for closing sections
        """
        num_days = len(serialized_trip.get("trip_plan", {}).get("days", []))
        logger.info(f"PASS {num_days + 2}: Generating Weather + Budget + Tips + Closing...")
        
        pass_final_data = {
            "weather_analysis": serialized_trip.get("weather_analysis"),
            "budget_analysis": serialized_trip.get("budget_analysis"),
            "budget_summary": serialized_trip.get("budget_summary"),
            "total_cost": serialized_trip.get("total_cost"),
            "currency": serialized_trip.get("currency"),
        }
        
        prompt = f"""You are composing the FINAL PASS of a comprehensive travel itinerary.

TASK: Generate ONLY these closing sections:
1. COMPREHENSIVE WEATHER INTELLIGENCE (200-300 words)
2. FULL BUDGET BREAKDOWN (400-500 words)
3. TRAVEL AGENT TIPS & RECOMMENDATIONS (200-300 words with 8-20 specific tips)
4. WARM THANK YOU & CLOSING (200-300 words)

BE VERBOSE. WRITE LONG. Each section needs to meet its word budget.

Data:
{json.dumps(_truncate_for_llm(pass_final_data), indent=2, ensure_ascii=False)}

Follow the comprehensive structure from your system prompt for these sections ONLY."""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        return self._call_llm_streaming(messages, f"PASS FINAL: Weather + Budget + Tips + Closing")
    
    
    
    def _generate_compact_narrative(self, serialized_trip: Dict[str, Any]) -> str:
        """
        Generate a single compact narrative (200–350 words).
        Flights/hotels should NOT be described here; UI + ranking handles that.
        """
        compact_data = {
            "user_query": serialized_trip.get("trip_plan", {}).get("user_query", ""),
            "origin": serialized_trip.get("trip_plan", {}).get("from_city"),
            "destination": serialized_trip.get("trip_plan", {}).get("to_city"),
            "start_date": serialized_trip.get("trip_plan", {}).get("start_date"),
            "end_date": serialized_trip.get("trip_plan", {}).get("end_date"),
            "travelers": serialized_trip.get("trip_plan", {}).get("num_adults") or serialized_trip.get("trip_plan", {}).get("travelers"),
            "itinerary": serialized_trip.get("trip_plan", {}).get("days", []),
            "places_analysis": serialized_trip.get("places_analysis"),
            "weather_analysis": serialized_trip.get("weather_analysis"),
            "budget_summary": serialized_trip.get("budget_summary"),
            "total_cost": serialized_trip.get("total_cost"),
            "currency": serialized_trip.get("currency"),
        }

        prompt = f"""
    Write ONE compact narrative (200–350 words) using the SYSTEM rules.

    Data:
    {json.dumps(_truncate_for_llm(compact_data), indent=2, ensure_ascii=False)}
    """.strip()

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        return self._call_llm_streaming(messages, "COMPACT: Narrative")


    def compose(self, trip: TripResponse) -> str:
        """
        Generate a compact narrative (200–350 words) for chat UI.
        """
        try:
            serialized_trip = self._serialize_trip(trip)
            narrative = self._generate_compact_narrative(serialized_trip)
            self._validate_output(narrative)
            return narrative.strip()
        except Exception as e:
            logger.error(f"Compact composition failed: {e}", exc_info=True)
            raise RuntimeError(f"Compact composition failed: {e}") from e
    
    def _validate_output(self, narrative: str) -> None:
        """
        Validate LLM output.
        
        Args:
            narrative: Generated narrative text
            
        Raises:
            RuntimeError: If output is invalid
        """
        if not isinstance(narrative, str):
            raise RuntimeError(f"Expected string output, got {type(narrative).__name__}")
        
        if not narrative.strip():
            raise RuntimeError("Composer produced empty output")
        words = len(narrative.split())
        
        if words > 380:
            logger.warning(f"Composer output too long ({words} words). Trimming risk.")
        if len(narrative.strip()) < 100:
            logger.warning(
                f"Composer produced suspiciously short output ({len(narrative)} chars). "
                "This may indicate an issue."
            )


# ============================================================================
# Legacy function interfaces for backward compatibility
# TODO: Remove after travel_planner_graph.py is fully migrated to ComposerAgent
# In final v5, only ComposerAgent().compose(trip_response) should be used
# ============================================================================

# Initialize singleton instance
_composer_agent = ComposerAgent()


def compose_itinerary(
    user_query: str,
    plan: Any,
    tool_results: Dict[str, Any],
    enriched_itinerary: Dict[str, Any] | None = None
) -> str:
    """
    Legacy interface for compose_itinerary (backward compatibility).
    
    Wraps the new ComposerAgent.compose() method.
    Constructs a minimal TripResponse from the provided data.
    
    Args:
        user_query: Original user query
        plan: PlannerOutput with tool calls and reasoning
        tool_results: Dictionary of tool results
        enriched_itinerary: Enriched itinerary structure (if available)
        
    Returns:
        Natural language itinerary narrative
        
    Raises:
        RuntimeError: If composition fails
    """
    logger.info("compose_itinerary called (legacy interface)")
    
    # For now, just serialize and compose with available data
    # This is a temporary bridge until full TripResponse integration
    composition_data = {
        "user_query": user_query,
        "plan_reasoning": plan.reasoning if plan else "",
        "tool_results": tool_results,
        "enriched_itinerary": enriched_itinerary
    }
    
    user_message = json.dumps(composition_data, indent=2, ensure_ascii=False, default=str)
    
    try:
        response = _composer_agent.client.chat.completions.create(
            model=_composer_agent.model,
            messages=[
                {"role": "system", "content": _composer_agent.system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            stream=False
        )
        
        narrative = response.choices[0].message.content
        
        if not narrative or not narrative.strip():
            raise RuntimeError("Composer produced empty output")
        
        logger.info(f"Generated itinerary: {len(narrative)} characters")
        return narrative.strip()
    
    except Exception as e:
        logger.error(f"Failed to compose itinerary: {e}", exc_info=True)
        raise RuntimeError(f"Failed to compose itinerary: {e}") from e
def compose_mlops(self, *, places: list[dict], weather: list[dict], budget: dict, trip_request: dict | None = None) -> str:
    """
    200–350 words, itinerary + places + budget ONLY.
    Must NOT mention ranking, best, recommended flights/hotels, or selection analysis.
    """
    system = (
        "You are TravelGuru. Write a concise travel narrative.\n"
        "Rules:\n"
        "- 200 to 350 words.\n"
        "- Mention: itinerary flow, top places, weather overview, budget breakdown.\n"
        "- DO NOT mention flights/hotels comparisons or recommendations.\n"
        "- NO bullet lists. Write in 2–4 short paragraphs.\n"
    )

    user = {
        "trip_request": trip_request or {},
        "places": places[:10],
        "weather": weather[:7],
        "budget": budget or {},
    }

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Trip data:\n{json.dumps(user, ensure_ascii=False, indent=2)}"},
    ]

    # Use your existing internal LLM caller (streaming or non-streaming)
    text = self._call_llm(messages, context="mlops_narrative")
    return text.strip()

