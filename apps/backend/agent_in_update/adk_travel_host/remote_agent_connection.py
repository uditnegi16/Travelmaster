import asyncio
import json
import logging
from typing import Dict, Optional

import httpx
from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ============================================================
# REMOTE AGENT CONNECTION MANAGER
# ============================================================

class RemoteAgentConnections:
    """
    Manages A2A connections to all remote agents and routes
    task completion events back to Host Orchestrator.
    """

    def __init__(self):
        self.http = httpx.AsyncClient(timeout=60)

        self.clients: Dict[str, A2AClient] = {}
        self.agent_cards: Dict[str, AgentCard] = {}

        # task_id -> host_session
        self.task_session_map: Dict[str, object] = {}

        # host agent reference
        self.host_agent = None

        # hardcoded for now — can move to config later
        self.agent_urls = {
            "explorer": "http://localhost:10004",
            "budget": "http://localhost:10002",
            "booking": "http://localhost:10003",
        }

    # --------------------------------------------------------
    # HOST REGISTRATION
    # --------------------------------------------------------

    def register_host(self, host_agent):
        """Attach host agent callback handler"""
        self.host_agent = host_agent

    # --------------------------------------------------------
    # INITIALIZE AGENT CONNECTIONS
    # --------------------------------------------------------

    async def initialize(self):
        logger.info("Initializing remote agent connections")

        for role, url in self.agent_urls.items():
            try:
                card = await self._fetch_agent_card(url)
                client = A2AClient(self.http, card, url=url)

                self.clients[role] = client
                self.agent_cards[role] = card

                logger.info("Connected to %s agent: %s", role, card.name)

            except Exception as e:
                logger.error("Failed to connect to %s agent: %s", role, e)

    async def _fetch_agent_card(self, url: str) -> AgentCard:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{url}/.well-known/agent.json")
            resp.raise_for_status()
            return AgentCard.model_validate(resp.json())

    # ========================================================
    # SEND TASKS
    # ========================================================

    async def send_to_explorer(self, payload: dict) -> str:
        return await self._send("explorer", payload)

    async def send_to_budget(self, payload: dict) -> str:
        return await self._send("budget", payload)

    async def send_to_booking(self, payload: dict) -> str:
        return await self._send("booking", payload)

    async def _send(self, role: str, payload: dict) -> str:
        if role not in self.clients:
            raise RuntimeError(f"No client for agent role: {role}")

        client = self.clients[role]

        message_id = self._uuid()
        task_id = self._uuid()
        context_id = self._uuid()

        message = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": json.dumps(payload)}],
                "messageId": message_id,
                "taskId": task_id,
                "contextId": context_id,
            }
        }

        request = SendMessageRequest(
            id=message_id,
            params=MessageSendParams.model_validate(message),
        )

        response: SendMessageResponse = await client.send_message(request)

        if not isinstance(response.root, SendMessageSuccessResponse):
            raise RuntimeError("Agent did not accept task")

        if not isinstance(response.root.result, Task):
            raise RuntimeError("Agent did not return Task object")

        self.task_session_map[task_id] = None  # filled by host

        # start background listener
        asyncio.create_task(self._listen_for_task_updates(client, task_id))

        return task_id

    # ========================================================
    # LISTEN FOR ARTIFACT EVENTS
    # ========================================================

    async def _listen_for_task_updates(self, client: A2AClient, task_id: str):
        logger.info("Listening for updates on task %s", task_id)

        async for event in client.subscribe_task(task_id):
            if isinstance(event, TaskArtifactUpdateEvent):
                await self._handle_artifact(event)
            elif isinstance(event, TaskStatusUpdateEvent):
                logger.debug("Task %s status: %s", task_id, event.state)

    async def _handle_artifact(self, event: TaskArtifactUpdateEvent):
        try:
            parts = event.artifact.parts
            if not parts:
                return

            text = ""
            for p in parts:
                if p.get("type") == "text":
                    text += p.get("text", "")

            if not text:
                return

            task_id = event.taskId

            logger.info("Artifact received for task %s", task_id)

            if not self.host_agent:
                logger.error("Host agent not registered")
                return

            # forward to host orchestrator
            await self.host_agent.on_task_artifact(
                session=self.host_agent.current_session,
                task_id=task_id,
                artifact_text=text,
            )

        except Exception as e:
            logger.exception("Artifact handling failed: %s", e)

    # ========================================================
    # UTILS
    # ========================================================

    def _uuid(self) -> str:
        import uuid
        return str(uuid.uuid4())


