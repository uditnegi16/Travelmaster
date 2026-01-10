# __main__.py

import logging
import os

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv

from agents.adk_travel_host import create_agent 
from agent_executor import BudgetAgentExecutor
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    pass


def main():
    """Starts Budget Optimization Agent server (TravelGuru)."""

    host = "localhost"
    port = 10003  # Budget Agent

    try:
        if not os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "TRUE":
            if not os.getenv("GOOGLE_API_KEY"):
                raise MissingAPIKeyError("GOOGLE_API_KEY not set.")

        capabilities = AgentCapabilities(streaming=True)

        skill = AgentSkill(
            id="budget_optimization",
            name="Travel Budget Optimization",
            description="Estimates trip cost, optimizes expenses, and suggests budget splits.",
            tags=["travel", "budget", "cost", "optimization"],
            examples=[
                "Estimate budget for 5-day trip to Goa for 2 people",
                "Cheapest way to travel from Bangalore to Chennai",
            ],
        )

        agent_card = AgentCard(
            name="Budget Agent",
            description="Specialist agent for travel cost estimation and budget optimization.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=["text/plain"],
            defaultOutputModes=["text/plain"],
            capabilities=capabilities,
            skills=[skill],
        )

        adk_agent = create_agent()

        runner = Runner(
            app_name=agent_card.name,
            agent=adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

        agent_executor = BudgetAgentExecutor(runner)

        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
        )

        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )

        logger.info("Starting Budget Agent on port %s", port)
        uvicorn.run(server.build(), host=host, port=port)

    except MissingAPIKeyError as e:
        logger.error(f"Startup error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected startup error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
