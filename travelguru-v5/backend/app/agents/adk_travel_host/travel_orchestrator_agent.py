# travel_orchestrator_agent.py

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, AsyncIterable, Dict, List

import httpx
import nest_asyncio
from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
)
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .remote_agent_connection import RemoteAgentConnections

# ✅ Parsing + schemas
from .adk_tools import (
    parse_explorer_response,
    parse_budget_response,
    parse_booking_response,
    AgentResponseFormatError,
    AgentSchemaValidationError,
)

load_dotenv()
nest_asyncio.apply()


# ============================================================
# HOST ORCHESTRATOR AGENT
# ============================================================

class HostAgent:
    """TravelGuru Host Orchestrator (Brain)."""

    def __init__(self):
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ""
        self._agent = self.create_agent()
        self._user_id = "host_agent"

        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    # ========================================================
    # REMOTE AGENT DISCOVERY
    # ========================================================

    async def _async_init_components(self, remote_agent_addresses: List[str]):
        async with httpx.AsyncClient(timeout=30) as client:
            for address in remote_agent_addresses:
                resolver = A2ACardResolver(client, address)
                try:
                    card = await resolver.get_agent_card()
                    remote_connection = RemoteAgentConnections(card, address)
                    self.remote_agent_connections[card.name] = remote_connection
                    self.cards[card.name] = card
                except Exception as e:
                    print(f"ERROR connecting to agent {address}: {e}")

        agent_info = [
            json.dumps({"name": c.name, "description": c.description})
            for c in self.cards.values()
        ]
        self.agents = "\n".join(agent_info) if agent_info else "No agents available"

    @classmethod
    async def create(cls, remote_agent_addresses: List[str]):
        instance = cls()
        await instance._async_init_components(remote_agent_addresses)
        return instance

    # ========================================================
    # AGENT DEFINITION
    # ========================================================

    def create_agent(self) -> Agent:
        return Agent(
            model="gemini-2.5-flash",
            name="TravelGuru_Host",
            instruction=self.root_instruction,
            description="Orchestrates Explorer, Budget and Booking agents to build full travel plans.",
            tools=[self.send_message],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        return f"""
ROLE:
You are TravelGuru Host Orchestrator.

You DO NOT answer travel questions yourself.
You only coordinate other expert agents.

Workflow:
1. Send task to Explorer Agent
2. Parse structured response
3. Send task to Budget Agent
4. Parse structured response
5. Send task to Booking Agent
6. Merge final plan

STRICT RULES:
- Never fabricate results
- Always wait for agent responses
- All responses must be JSON from agents

Today: {datetime.now().strftime("%Y-%m-%d")}

Available Agents:
{self.agents}
"""

    # ========================================================
    # STREAM ENTRYPOINT (FSM DRIVER)
    # ========================================================

    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:

        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )

        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )

        state = session.state

        # ================= INIT =================

        if "plan_state" not in state:
            state["plan_state"] = {
                "stage": "EXPLORER",
                "results": {
                    "explorer": None,
                    "budget": None,
                    "booking": None,
                },
                "errors": [],
            }
            state["pending_tasks"] = {}

            yield {
                "is_task_complete": False,
                "updates": "Starting destination research...",
            }

            await self.dispatch_explorer(query, state)
            return

        # ============== WAITING FOR AGENTS ==============

        yield {
            "is_task_complete": False,
            "updates": "Waiting for agent responses...",
        }

    # ========================================================
    # AGENT DISPATCHERS
    # ========================================================

    async def dispatch_explorer(self, query: str, state: dict):
        await self._dispatch(
            agent_name="Explorer Agent",
            task=f"Find destinations and attractions for: {query}",
            role="explorer",
            state=state,
        )

    async def dispatch_budget(self, state: dict):
        await self._dispatch(
            agent_name="Budget Agent",
            task="Estimate travel budget based on selected destinations.",
            role="budget",
            state=state,
        )

    async def dispatch_booking(self, state: dict):
        await self._dispatch(
            agent_name="Booking Agent",
            task="Suggest hotels, transport and weather-based packing tips.",
            role="booking",
            state=state,
        )

    async def _dispatch(self, agent_name: str, task: str, role: str, state: dict):
        tool_context = ToolContext(state=state)

        task_id = await self.send_message(
            agent_name=agent_name,
            task=task,
            tool_context=tool_context,
            role=role,
        )

        state["pending_tasks"][task_id] = role

    # ========================================================
    # SEND MESSAGE TO REMOTE AGENT
    # ========================================================

    async def send_message(
        self,
        agent_name: str,
        task: str,
        tool_context: ToolContext,
        role: str | None = None,
    ) -> str:

        if agent_name not in self.remote_agent_connections:
            raise ValueError(f"Agent {agent_name} not found")

        client = self.remote_agent_connections[agent_name]

        state = tool_context.state

        task_id = str(uuid.uuid4())
        context_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())

        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": task}],
                "messageId": message_id,
                "taskId": task_id,
                "contextId": context_id,
            },
        }

        message_request = SendMessageRequest(
            id=message_id, params=MessageSendParams.model_validate(payload)
        )

        send_response: SendMessageResponse = await client.send_message(message_request)

        if not isinstance(send_response.root, SendMessageSuccessResponse):
            raise RuntimeError("Agent did not accept task")

        return task_id


# ============================================================
# BOOTSTRAP HOST
# ============================================================

def _get_initialized_host_agent_sync():

    async def _async_main():
        agent_urls = [
            "http://localhost:10002",  # Budget Agent
            "http://localhost:10003",  # Booking Agent
            "http://localhost:10004",  # Explorer Agent
        ]

        host = await HostAgent.create(agent_urls)
        return host.create_agent()

    try:
        return asyncio.run(_async_main())
    except RuntimeError:
        return asyncio.get_event_loop().run_until_complete(_async_main())


root_agent = _get_initialized_host_agent_sync()
