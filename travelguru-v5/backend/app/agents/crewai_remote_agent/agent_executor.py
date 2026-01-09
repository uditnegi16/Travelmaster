import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import InternalError, UnsupportedOperationError
from a2a.utils.errors import ServerError

from app.agents.crewai_remote_agent.explorer_agent import run_explorer_agent

logger = logging.getLogger(__name__)


class ExplorerAgentExecutor(AgentExecutor):
    """Executes Explorer CrewAI workflow for TravelGuru."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if not context.task_id or not context.context_id:
            raise ValueError("Missing task_id or context_id")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        if not context.current_task:
            await updater.submit()

        await updater.start_work()

        try:
            user_text = context.get_user_input()
            logger.info("Executor received input: %s", user_text)

            result = run_explorer_agent(user_text)

            await updater.add_artifact(
                result,
                name="explorer_result",
            )

            await updater.complete()

        except Exception as e:
            logger.exception("Explorer agent failure")
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())
