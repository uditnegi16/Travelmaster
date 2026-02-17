"""
Planner Agent for TravelGuru v5.
Converts user natural language queries into strict, structured execution plans.
This is a pure planning compiler - no enrichment, no business logic, no tool calls.
"""

import json
import logging
from typing import Dict, Any, List
from pathlib import Path

from openai import OpenAI

from shared.schemas import PlannerOutput, ToolCallPlan
from core.config import PLANNER_MODEL, OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Allowed tools in strict order
ALLOWED_TOOLS = [
    "search_flights",
    "search_hotels",
    "search_places",
    "get_weather_forecast",
    "compute_budget"
]

# Tool order must be exactly this
EXPECTED_TOOL_ORDER = ALLOWED_TOOLS


def _load_system_prompt() -> str:
    """
    Load the planner system prompt from prompts/planner.txt.
    
    Returns:
        System prompt content
        
    Raises:
        RuntimeError: If prompt file not found
    """
    prompt_path = Path(__file__).parent / "prompts" / "planner.txt"
    if not prompt_path.exists():
        raise RuntimeError(f"Planner prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def _call_llm(user_query: str, system_prompt: str) -> str:
    """
    Call OpenAI LLM to generate execution plan.
    Retries once on failure with exponential backoff.
    
    Args:
        user_query: User's natural language travel request
        system_prompt: System prompt from planner.txt
        
    Returns:
        Raw LLM response string
        
    Raises:
        RuntimeError: If LLM call fails after retries
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    
    max_retries = 2
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=PLANNER_MODEL,
                messages=messages,
                temperature=0,
                stream=False
            )
            
            raw_output = response.choices[0].message.content
            if not raw_output:
                raise RuntimeError("LLM returned empty response")
            
            logger.debug(f"Raw LLM output: {raw_output[:200]}...")
            return raw_output
        
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}. Retrying...")
                import time
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
            else:
                logger.error(f"LLM call failed after {max_retries} attempts: {e}", exc_info=True)
    
    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_error}") from last_error


def _strip_markdown_fences(text: str) -> str:
    """
    Strip markdown code fences if present.
    
    Args:
        text: Raw text that may contain ```json ... ```
        
    Returns:
        Text with fences removed
    """
    text = text.strip()
    
    # Remove ```json ... ``` or ``` ... ```
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```)
        lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    
    return text.strip()


def _parse_json(raw_output: str) -> Dict[str, Any]:
    """
    Parse raw LLM output as JSON.
    
    Args:
        raw_output: Raw LLM response
        
    Returns:
        Parsed JSON as dict
        
    Raises:
        RuntimeError: If JSON parsing fails
    """
    # Strip markdown fences if present
    cleaned = _strip_markdown_fences(raw_output)
    
    try:
        data = json.loads(cleaned)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.error(f"Raw output: {raw_output}")
        raise RuntimeError(f"Failed to parse JSON: {e}. Raw output: {raw_output}") from e


def _validate_structure(data: Dict[str, Any]) -> None:
    """
    Validate that parsed JSON has required structure.
    
    Args:
        data: Parsed JSON dict
        
    Raises:
        RuntimeError: If structure is invalid
    """
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected dict, got {type(data).__name__}")
    
    if "tool_calls" not in data:
        raise RuntimeError("Missing 'tool_calls' key in response")
    
    if "reasoning" not in data:
        raise RuntimeError("Missing 'reasoning' key in response")
    
    if not isinstance(data["tool_calls"], list):
        raise RuntimeError(f"'tool_calls' must be list, got {type(data['tool_calls']).__name__}")
    
    if not isinstance(data["reasoning"], str):
        raise RuntimeError(f"'reasoning' must be string, got {type(data['reasoning']).__name__}")
    
    # Optional: Check for schema_version (future-proofing)
    if "schema_version" in data:
        if data["schema_version"] != "planner_v1":
            logger.warning(f"Unexpected schema_version: {data['schema_version']}. Expected: planner_v1")
    
    # Guard against extra keys
    expected_keys = {"tool_calls", "reasoning", "schema_version"}
    extra_keys = set(data.keys()) - expected_keys
    if extra_keys:
        logger.warning(f"Response contains unexpected extra keys: {extra_keys}")


def _validate_tool_call(tool_call: Dict[str, Any], index: int) -> None:
    """
    Validate a single tool call.
    
    Args:
        tool_call: Tool call dict
        index: Index in tool_calls array (for error messages)
        
    Raises:
        RuntimeError: If tool call is invalid
    """
    if not isinstance(tool_call, dict):
        raise RuntimeError(f"Tool call {index} must be dict, got {type(tool_call).__name__}")
    
    if "tool_name" not in tool_call:
        raise RuntimeError(f"Tool call {index} missing 'tool_name' key")
    
    if "arguments" not in tool_call:
        raise RuntimeError(f"Tool call {index} missing 'arguments' key")
    
    tool_name = tool_call["tool_name"]
    arguments = tool_call["arguments"]
    
    if not isinstance(tool_name, str):
        raise RuntimeError(f"Tool call {index} 'tool_name' must be string")
    
    if not isinstance(arguments, dict):
        raise RuntimeError(f"Tool call {index} 'arguments' must be dict")
    
    # Validate tool name is allowed
    if tool_name not in ALLOWED_TOOLS:
        raise RuntimeError(
            f"Tool call {index} has invalid tool name '{tool_name}'. "
            f"Allowed: {ALLOWED_TOOLS}"
        )
    
    # Validate no None values in arguments
    for key, value in arguments.items():
        if value is None:
            raise RuntimeError(
                f"Tool call {index} ({tool_name}) has None value for argument '{key}'"
            )


def _validate_tool_order(tool_calls: List[Dict[str, Any]]) -> None:
    """
    Validate that tools are in the expected strict order.
    
    Args:
        tool_calls: List of tool call dicts
        
    Raises:
        RuntimeError: If order is incorrect
    """
    if len(tool_calls) != len(EXPECTED_TOOL_ORDER):
        raise RuntimeError(
            f"Expected {len(EXPECTED_TOOL_ORDER)} tool calls, got {len(tool_calls)}. "
            f"Must call all tools: {EXPECTED_TOOL_ORDER}"
        )
    
    for i, (tool_call, expected_tool) in enumerate(zip(tool_calls, EXPECTED_TOOL_ORDER)):
        actual_tool = tool_call["tool_name"]
        if actual_tool != expected_tool:
            raise RuntimeError(
                f"Tool at position {i} should be '{expected_tool}', got '{actual_tool}'. "
                f"Expected order: {EXPECTED_TOOL_ORDER}"
            )


def _validate_plan(data: Dict[str, Any]) -> None:
    """
    Validate complete plan structure and content.
    
    Args:
        data: Parsed JSON plan
        
    Raises:
        RuntimeError: If validation fails
    """
    # Validate structure
    _validate_structure(data)
    
    tool_calls = data["tool_calls"]
    
    # Validate each tool call
    for i, tool_call in enumerate(tool_calls):
        _validate_tool_call(tool_call, i)
    
    # Validate tool order
    _validate_tool_order(tool_calls)
    
    logger.info(f"Plan validation passed: {len(tool_calls)} tools in correct order")


def plan_trip(user_query: str) -> PlannerOutput:
    """
    Generate structured execution plan from user's natural language query.
    
    This is a pure planning compiler that:
    1. Loads planner.txt as system prompt
    2. Calls LLM with temperature=0
    3. Parses and validates JSON output
    4. Returns structured PlannerOutput
    
    Args:
        user_query: User's natural language travel request
        
    Returns:
        PlannerOutput with validated tool calls and reasoning
        
    Raises:
        ValueError: If user_query is empty
        RuntimeError: If planning fails (LLM error, invalid JSON, validation failure)
    """
    # Validate input
    if not user_query or not user_query.strip():
        raise ValueError("user_query cannot be empty")
    
    logger.info(f"Planning trip for query: {user_query}")
    
    # Load system prompt
    system_prompt = _load_system_prompt()
    
    # Call LLM
    raw_output = _call_llm(user_query.strip(), system_prompt)
    
    # Parse JSON
    data = _parse_json(raw_output)
    
    # Validate plan
    _validate_plan(data)
    
    # Clean protocol metadata before domain validation
    cleaned_data = _clean_planner_payload(data)
    
    # Convert to PlannerOutput
    try:
        planner_output = PlannerOutput(**cleaned_data)
        logger.info(f"Successfully generated plan with {len(planner_output.tool_calls)} tool calls")
        logger.info(f"Reasoning: {planner_output.reasoning}")
        return planner_output
    
    except Exception as e:
        logger.error(f"Failed to create PlannerOutput from validated data: {e}")
        raise RuntimeError(f"Failed to create PlannerOutput: {e}") from e


def _clean_planner_payload(data: dict) -> dict:
    """
    Remove protocol metadata fields before domain model validation.
    
    The LLM may return fields like schema_version, version, _meta, etc.
    These are protocol-level fields and should not leak into domain models.
    
    Args:
        data: Raw planner payload from LLM
        
    Returns:
        Cleaned payload with only domain fields
    """
    cleaned = data.copy()
    
    # Remove protocol metadata fields
    protocol_fields = ['schema_version', 'version', '_meta', 'metadata']
    for field in protocol_fields:
        cleaned.pop(field, None)
    
    return cleaned
