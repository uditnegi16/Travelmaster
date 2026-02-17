import os
import json
import logging
from typing import Dict, Any

from crewai import Agent, Task, Crew, LLM

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================
# LLM CONFIG — GROQ ONLY (NO OPENAI)
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set in environment")

llm = LLM(
    model="qwen/qwen3-32b",
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

# ============================================================
# CREW BUILDER
# ============================================================


def build_explorer_crew(user_query: str) -> Crew:
    explorer = Agent(
        role="Travel Explorer",
        goal="Find best attractions, experiences and travel suitability for a destination",
        backstory=(
            "You are an expert travel planner who helps families and solo travelers "
            "choose attractions, routes, and activities. You consider weather, safety, "
            "and cultural highlights."
        ),
        llm=llm,
        verbose=True,
    )

    task = Task(
        description=(
            f"User query:\n{user_query}\n\n"
            "Respond strictly in JSON with fields:\n"
            "{\n"
            "  destination: string,\n"
            "  top_attractions: [{name, reason}],\n"
            "  best_time: string,\n"
            "  tips: [string]\n"
            "}\n"
        ),
        expected_output="Valid JSON object only",
        agent=explorer,
    )

    return Crew(
        agents=[explorer],
        tasks=[task],
        verbose=True,
    )


# ============================================================
# MAIN ENTRY FOR A2A EXECUTOR
# ============================================================


def run_explorer_agent(inputs: Dict[str, Any]) -> Dict[str, Any]:
    user_query = inputs.get("query") or ""

    if not user_query:
        return {"success": False, "error": "Empty user query"}

    logger.info("Explorer Agent running CrewAI")

    try:
        crew = build_explorer_crew(user_query)
        result = crew.kickoff()

        if isinstance(result, str):
            try:
                parsed = json.loads(result)
            except Exception:
                parsed = {"raw_output": result}
        else:
            parsed = result

        return {
            "success": True,
            "result": parsed,
        }

    except Exception as e:
        logger.exception("CrewAI execution failed")
        return {
            "success": False,
            "error": str(e),
        }
