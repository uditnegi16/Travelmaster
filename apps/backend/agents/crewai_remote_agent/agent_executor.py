import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError

from app.agents.crewai_remote_agent.explorer_agent import run_explorer_agent

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ExplorerAgentExecutor(AgentExecutor):
    """Executes Explorer CrewAI workflow for TravelGuru."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if not context.task_id or not context.context_id:
            raise ValueError("Missing task_id or context_id")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        if not context.current_task:
            await updater.submit()

        await updater.start_work()

        # ✅ CORRECT WAY to get user message
        query = context.get_user_input()

        logger.info("Explorer Agent received query: %s", query)

        try:
            result = run_explorer_agent({"query": query})

            text = result if isinstance(result, str) else str(result)

            parts = [Part(root=TextPart(text=text))]

            await updater.add_artifact(parts, name="exploration_result")
            await updater.complete()

        except Exception as e:
            logger.exception("Explorer agent execution failed")
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())
