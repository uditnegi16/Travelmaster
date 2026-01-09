import os
import json
import logging
from typing import Dict, Any

from crewai import Agent, Task, Crew, LLM
from dotenv import load_dotenv
load_dotenv()


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================
# LLM CONFIG — GROQ ONLY
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "groq/llama-3.1-70b-versatile")

llm = LLM(model=GROQ_API_KEY)

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
            "Provide JSON with:\n"
            "- destination\n"
            "- top_attractions: list of {name, reason}\n"
            "- best_time\n"
            "- tips\n"
        ),
        expected_output="Valid JSON only",
        agent=explorer,
    )

    crew = Crew(
        agents=[explorer],
        tasks=[task],
        verbose=True,
    )

    return crew


# ============================================================
# ENTRY CALLED BY AGENT EXECUTOR
# ============================================================


def run_explorer_agent(user_query: str) -> Dict[str, Any]:
    logger.info("Explorer Agent received query: %s", user_query)

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
            "type": "ExplorerResponse",
            "success": True,
            "result": parsed,
        }

    except Exception as e:
        logger.exception("Explorer agent failed")

        return {
            "type": "ExplorerResponse",
            "success": False,
            "error": str(e),
        }
