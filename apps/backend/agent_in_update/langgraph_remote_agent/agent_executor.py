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

from agent_in_update.langgraph_remote_agent.booking_agent import BookingAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BookingAgentExecutor(AgentExecutor):
    """Executes LangGraph-based Booking & Logistics Agent."""

    def __init__(self):
        self.agent = BookingAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if not context.task_id or not context.context_id:
            raise ValueError("Missing task_id or context_id")
        if not context.message:
            raise ValueError("Missing message")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        if not context.current_task:
            await updater.submit()
        await updater.start_work()

        query = context.get_user_input()

        try:
            async for item in self.agent.stream(query, context.context_id):
                parts = [Part(root=TextPart(text=item["content"]))]

                if not item["is_task_complete"]:
                    await updater.update_status(
                        TaskState.working,
                        message=updater.new_agent_message(parts),
                    )
                else:
                    await updater.add_artifact(parts, name="booking_result")
                    await updater.complete()
                    break

        except Exception as e:
            logger.exception("Booking Agent error")
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())
