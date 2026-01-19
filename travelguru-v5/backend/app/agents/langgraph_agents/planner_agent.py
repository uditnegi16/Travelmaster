"""
Planner Agent for TravelGuru v5.
This is the reasoning brain (LLM #1) that analyzes user intent and produces
a structured execution plan. It does NOT call tools directly.
"""

import json
import logging
from typing import Dict, Any

from openai import OpenAI

from backend.app.shared.schemas import PlannerOutput, ToolCallPlan
from backend.app.core.config import PLANNER_MODEL, OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# System prompt for the planner
SYSTEM_PROMPT = """You are an intelligent travel planning engine for TravelGuru.
Your task is to analyze user travel requests and output a structured execution plan as JSON.

Available tools:
1. search_flights - Search for flights between cities
   Arguments: from_city (str), to_city (str), date (str, optional), max_price (int, optional), limit (int, default 5), sort_by_price (bool, default true)

2. search_hotels - Search for hotels in a city
   Arguments: city (str), min_stars (int, optional), max_price (int, optional), amenities (list[str], optional), limit (int, default 5), sort_by_price (bool, default true)

3. search_places - Search for places/attractions in a city
   Arguments: city (str), category (str, optional), max_entry_fee (int, optional), limit (int, default 5), sort_by_fee (bool, default true)

4. get_weather - Get weather information for a city and month
   Arguments: city (str), month (int, 1-12)

5. compute_budget - Compute total budget for a trip
   Arguments: flight (dict or null), hotel (dict or null), nights (int), places (list[dict] or null)

Your output MUST be valid JSON matching this exact schema:
{
  "tool_calls": [
    {
      "tool_name": "search_flights",
      "arguments": {"from_city": "Delhi", "to_city": "Mumbai", "date": "2026-02-15"}
    }
  ],
  "reasoning": "Brief explanation of the plan"
}

Rules:
- Output MUST be valid JSON only (no markdown, no code blocks, no explanations outside JSON)
- tool_name MUST be one of: search_flights, search_hotels, search_places, get_weather, compute_budget
- arguments MUST be a valid object with appropriate fields for that tool
- Typical order: search_flights → search_hotels → get_weather → search_places → compute_budget
- Extract source city, destination city, dates, budget, and interests from user query
- reasoning should explain why you chose these tools and in this order

Analyze the user's request and determine which tools are needed."""


RETRY_PROMPT = """Your previous output was not valid JSON.

You MUST output ONLY valid JSON matching this exact schema:
{
  "tool_calls": [
    {
      "tool_name": "tool_name_here",
      "arguments": {"arg1": "value1"}
    }
  ],
  "reasoning": "explanation here"
}

Do NOT include markdown code blocks.
Do NOT include any text before or after the JSON.
Output ONLY the raw JSON object."""


def _build_user_prompt(user_query: str) -> str:
    """Build the user prompt with the query."""
    return f"""User request: {user_query}

Analyze this request and output the execution plan as JSON."""


def _call_llm(messages: list[Dict[str, str]]) -> str:
    """
    Call the LLM with the given messages.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        
    Returns:
        Raw LLM output string
        
    Raises:
        RuntimeError: If LLM call fails
    """
    try:
        response = client.chat.completions.create(
            model=PLANNER_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        raw_output = response.choices[0].message.content
        logger.debug(f"Raw LLM output: {raw_output}")
        return raw_output
    except Exception as e:
        logger.error(f"LLM call failed: {e}", exc_info=True)
        raise RuntimeError(f"LLM call failed: {e}") from e


def _parse_output(raw_output: str) -> PlannerOutput:
    """
    Parse and validate LLM output into PlannerOutput.
    
    Args:
        raw_output: Raw JSON string from LLM
        
    Returns:
        Validated PlannerOutput instance
        
    Raises:
        ValueError: If output is invalid JSON or doesn't match schema
    """
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise ValueError(f"Invalid JSON output: {e}") from e
    
    try:
        planner_output = PlannerOutput(**data)
        logger.debug(f"Parsed PlannerOutput: {planner_output.model_dump()}")
        return planner_output
    except Exception as e:
        logger.error(f"Failed to validate PlannerOutput schema: {e}")
        raise ValueError(f"Output doesn't match PlannerOutput schema: {e}") from e


def plan_trip(user_query: str) -> PlannerOutput:
    """
    Generate a structured travel execution plan from user query.
    
    This is the main entry point for the Planner Agent. It analyzes the user's
    travel request and produces a structured plan specifying which tools to call,
    in what order, and with what arguments.
    
    Args:
        user_query: The user's travel request in natural language
        
    Returns:
        PlannerOutput containing tool calls and reasoning
        
    Raises:
        ValueError: If user_query is empty
        RuntimeError: If planner fails to produce valid output after retry
    """
    # Validate input
    if not user_query or not user_query.strip():
        logger.error("Empty user query provided")
        raise ValueError("user_query cannot be empty")
    
    logger.info(f"Planning trip for query: {user_query}")
    
    # Build messages for first attempt
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(user_query)}
    ]
    
    # First attempt
    try:
        raw_output = _call_llm(messages)
        planner_output = _parse_output(raw_output)
        
        logger.info(f"Successfully generated plan with {len(planner_output.tool_calls)} tool calls")
        logger.info(f"Reasoning: {planner_output.reasoning}")
        
        return planner_output
    
    except ValueError as e:
        # Parsing/validation failed, retry with stricter prompt
        logger.warning(f"First attempt failed: {e}. Retrying with stricter prompt.")
        
        # Add the failed output and retry instruction
        messages.append({"role": "assistant", "content": raw_output})
        messages.append({"role": "user", "content": RETRY_PROMPT})
        
        try:
            raw_output_retry = _call_llm(messages)
            planner_output = _parse_output(raw_output_retry)
            
            logger.info(f"Retry successful: generated plan with {len(planner_output.tool_calls)} tool calls")
            logger.info(f"Reasoning: {planner_output.reasoning}")
            
            return planner_output
        
        except ValueError as e2:
            logger.error(f"Retry also failed: {e2}")
            raise RuntimeError(f"Planner failed to produce valid output after retry: {e2}") from e2
        except RuntimeError:
            # Re-raise LLM call errors
            raise
    
    except RuntimeError:
        # Re-raise LLM call errors from first attempt
        raise
