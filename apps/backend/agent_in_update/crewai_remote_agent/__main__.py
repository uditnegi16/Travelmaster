# backend/app/agents/crewai_remote_agent/__main__.py

import logging
import os
import sys
import uvicorn
from typing import Iterable

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv

from crewai_remote_agent.agent_executor import ExplorerAgentExecutor

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    pass


def format_route_info(app) -> str:
    """Return a human-readable list of routes for debugging."""
    out_lines = []
    try:
        # Many ASGI frameworks expose router.routes or app.routes
        routes = getattr(app, "routes", None) or getattr(app, "router", None) and getattr(app.router, "routes", None)
        if not routes:
            return "No route information available (app.routes not found)."
        for r in routes:
            # different route objects expose different attributes; handle safely
            try:
                methods = getattr(r, "methods", None) or getattr(r, "methods", set())
                path = getattr(r, "path", None) or getattr(r, "path_regex", None) or getattr(r, "name", None)
                name = getattr(r, "name", None)
                out_lines.append(f"{methods}  ->  {path}  (name={name})")
            except Exception:
                out_lines.append(repr(r))
    except Exception as e:
        out_lines.append(f"Error while listing routes: {e}")
    return "\n".join(out_lines)


def main():
    host = "0.0.0.0"
    port = int(os.getenv("EXPLORER_PORT", 10002))

    try:
        if not os.getenv("GROQ_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
            # allow starting even without keys if you just want to inspect routes;
            # comment this raise if you prefer to run without keys temporarily.
            logger.warning("No LLM key found in env (GROQ_API_KEY or GOOGLE_API_KEY). Server will still start for route inspection.")
            # raise MissingAPIKeyError("Missing LLM API key")

        capabilities = AgentCapabilities(streaming=True, pushNotifications=False)

        skill = AgentSkill(
            id="travel_exploration",
            name="Travel Exploration & Discovery",
            description="Finds destinations, attractions, experiences, and travel routes.",
            tags=["travel", "exploration", "itinerary", "attractions"],
            examples=[
                "Suggest destinations near Bangalore for a weekend trip",
                "Find top attractions in Paris for 3 days",
            ],
        )

        agent_card = AgentCard(
            name="Explorer Agent",
            description="Specialist agent for travel discovery and attraction planning.",
            url=f"http://{host}:{port}",
            version="1.0.0",
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            capabilities=capabilities,
            skills=[skill],
        )

        request_handler = DefaultRequestHandler(
            agent_executor=ExplorerAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )

        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )

        # Build the ASGI app so we can introspect routes
        app = server.build()

        logger.info("🚀 Explorer Agent ASGI app built. Listing available routes below:\n")
        route_info = format_route_info(app)
        logger.info("\n%s\n", route_info or "No routes found")

        logger.info("Starting Explorer Agent on http://%s:%s", host, port)
        uvicorn.run(app, host=host, port=port)

    except MissingAPIKeyError as e:
        logger.error("Startup error: %s", e)
        sys.exit(1)
    except Exception:
        logger.exception("Unexpected startup error")
        sys.exit(1)


if __name__ == "__main__":
    main()


