"""
Composer Agent for TravelGuru v5.
Uses GPT-4o-mini to transform structured trip data into beautiful narrative text.
"""

import json
import logging
from typing import Any, Dict

from openai import OpenAI

from backend.app.shared.schemas import TripPlan, BudgetSummary, TripResponse
from backend.app.core.config import COMPOSER_MODEL, OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# System prompt for the composer
SYSTEM_PROMPT = """You are a professional travel planner crafting personalized itineraries.

Your task is to take structured trip data (flights, hotels, activities, weather, budget) and create a beautiful, human-friendly travel itinerary description.

Your output should be:
- Friendly and engaging
- Clear and well-structured
- Professional yet warm
- Easy to read and follow

Structure your response with clear sections:
1. **Trip Overview** - Summarize the journey
2. **Flight Details** - Include airline, times, price
3. **Accommodation** - Hotel name, location, amenities, price
4. **Day-by-Day Itinerary** - Activities for each day
5. **Weather Information** - Expected weather conditions
6. **Budget Breakdown** - Clear cost summary
7. **Closing Note** - Friendly farewell with travel tips

Use markdown-style formatting:
- Use **bold** for headings
- Use bullet points for lists
- Keep paragraphs short and readable
- Include relevant emojis sparingly for visual appeal

Be concise but informative. Focus on helping the traveler feel excited and prepared."""


def compose_trip(
    trip_plan: TripPlan,
    budget_summary: BudgetSummary
) -> TripResponse:
    """
    Generate a beautiful narrative trip description from structured data.
    
    Args:
        trip_plan: Structured trip plan with flights, hotels, activities, weather
        budget_summary: Budget breakdown with costs
        
    Returns:
        TripResponse with complete trip data and narrative text
        
    Raises:
        RuntimeError: If composer produces empty or invalid output
    """
    # Extract metadata for logging
    from_city = trip_plan.flight.from_city if trip_plan.flight else "Unknown"
    to_city = trip_plan.flight.to_city if trip_plan.flight else "Unknown"
    num_days = len(trip_plan.days)
    
    logger.info(
        f"Composing trip narrative: {from_city} → {to_city}, "
        f"{num_days} days, budget {budget_summary.total_cost} {budget_summary.currency}"
    )
    
    # Prepare structured data as JSON for the LLM
    trip_data = {
        "trip_plan": trip_plan.model_dump(),
        "budget_summary": budget_summary.model_dump()
    }
    
    user_prompt = f"""Create a beautiful travel itinerary based on this data:

{json.dumps(trip_data, indent=2, ensure_ascii=False)}

Generate a comprehensive, engaging narrative that presents this information in a traveler-friendly format."""
    
    try:
        # Call OpenAI API using Responses API
        response = client.responses.create(
            model=COMPOSER_MODEL,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        # Extract narrative text from response
        narrative = response.output_text
        
        # Validate output is a non-empty string
        if not isinstance(narrative, str):
            logger.error(f"Composer produced non-string output: {type(narrative)}")
            raise RuntimeError("Composer produced invalid output: not a string")
        
        if not narrative.strip():
            logger.error("Composer produced empty output")
            raise RuntimeError("Composer produced empty output")
        
        # Additional sanity check: ensure reasonable length
        if len(narrative.strip()) < 100:
            logger.warning(
                f"Composer produced suspiciously short output ({len(narrative)} chars). "
                "Proceeding but this may indicate an issue."
            )
        
        logger.info(f"Generated narrative with {len(narrative)} characters")
        
        # Create TripResponse
        trip_response = TripResponse(
            trip_plan=trip_plan,
            budget_summary=budget_summary,
            total_cost=budget_summary.total_cost,
            currency=budget_summary.currency,
            narrative=narrative.strip()
        )
        
        return trip_response
    
    except RuntimeError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Failed to compose trip narrative: {e}")
        raise RuntimeError(f"Failed to compose trip narrative: {e}") from e


def compose_itinerary(
    user_query: str,
    plan: Any,
    tool_results: Dict[str, Any]
) -> str:
    """
    Generate travel itinerary narrative from user query, plan, and tool results.
    
    This is a simplified composer for the new architecture that takes raw tool results
    and generates a natural language itinerary.
    
    Args:
        user_query: Original user query
        plan: PlannerOutput with tool calls and reasoning
        tool_results: Dictionary of tool results keyed by tool name
        
    Returns:
        Natural language itinerary narrative
        
    Raises:
        RuntimeError: If composition fails
    """
    logger.info("Composing itinerary from tool results")
    
    # Prepare structured data for the LLM
    composition_data = {
        "user_query": user_query,
        "plan_reasoning": plan.reasoning if plan else "No planning reasoning available",
        "tool_results": tool_results
    }
    
    user_prompt = f"""Create a beautiful travel itinerary based on the following information:

User Request: {user_query}

Planning Reasoning: {composition_data['plan_reasoning']}

Tool Results:
{json.dumps(tool_results, indent=2, ensure_ascii=False, default=str)}

Generate a comprehensive, engaging narrative that presents this information in a traveler-friendly format.
Include all relevant details from the tool results and make it actionable and exciting for the traveler."""
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model=COMPOSER_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        # Extract narrative text
        narrative = response.choices[0].message.content
        
        # Validate output
        if not isinstance(narrative, str) or not narrative.strip():
            raise RuntimeError("Composer produced empty or invalid output")
        
        if len(narrative.strip()) < 100:
            logger.warning(f"Composer produced short output ({len(narrative)} chars)")
        
        logger.info(f"Generated itinerary with {len(narrative)} characters")
        
        return narrative.strip()
    
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Failed to compose itinerary: {e}", exc_info=True)
        raise RuntimeError(f"Failed to compose itinerary: {e}") from e
