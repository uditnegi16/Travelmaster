# __main__.py

import logging
import os

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv

from langgraph_remote_agent.agent_executor import BookingAgentExecutor

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    pass


def main():
    """Starts TravelGuru Booking & Logistics Agent server."""

    host = "localhost"
    port = 10004

    try:
        if not os.getenv("OPENWEATHERMAP_API_KEY"):
            raise MissingAPIKeyError("OPENWEATHERMAP_API_KEY not set.")

        capabilities = AgentCapabilities(streaming=True)

        skill = AgentSkill(
            id="booking_and_logistics",
            name="Booking & Travel Logistics",
            description="Helps with bookings, transport feasibility, weather, and packing suggestions.",
            tags=["travel", "booking", "logistics", "weather", "packing"],
            examples=[
                "Is it a good time to visit Manali in December?",
                "What should I pack for Paris in March?",
                "Is train or flight better from Bangalore to Delhi?",
            ],
        )

        agent_card = AgentCard(
            name="Booking Agent",
            description="Handles travel bookings, logistics, and weather-based guidance.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            capabilities=capabilities,
            skills=[skill],
        )

        request_handler = DefaultRequestHandler(
            agent_executor=BookingAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )

        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )

        logger.info("Starting Booking Agent on port %s", port)
        uvicorn.run(server.build(), host=host, port=port)

    except MissingAPIKeyError as e:
        logger.error(f"Startup error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected startup error: {e}")
        exit(1)


if __name__ == "__main__":
    main()


