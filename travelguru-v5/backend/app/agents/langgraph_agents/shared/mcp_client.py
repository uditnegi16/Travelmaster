import os
import asyncio
import logging
from typing import Dict, Any, Optional, List

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================
# CONFIG
# ============================================================

DEFAULT_TIMEOUT = 15.0
DEFAULT_RETRIES = 2

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:5000")

# ============================================================
# MCP CLIENT
# ============================================================

class MCPClient:
    """
    MCP FastAPI client.
    Supports BOTH async and sync usage safely.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
    ):
        self.base_url = (base_url or MCP_SERVER_URL).rstrip("/")
        self.timeout = timeout
        self.retries = retries

        self._async_client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[httpx.Client] = None

    # ========================================================
    # ASYNC CLIENT
    # ========================================================

    async def __aenter__(self):
        self._async_client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._async_client:
            await self._async_client.aclose()

    async def _get_async_client(self) -> httpx.AsyncClient:
        if not self._async_client:
            self._async_client = httpx.AsyncClient(timeout=self.timeout)
        return self._async_client

    # ========================================================
    # SYNC CLIENT
    # ========================================================

    def _get_sync_client(self) -> httpx.Client:
        if not self._sync_client:
            self._sync_client = httpx.Client(timeout=self.timeout)
        return self._sync_client

    # ========================================================
    # ASYNC TOOL CALL
    # ========================================================

    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/tools/{tool_name}"
        client = await self._get_async_client()

        for attempt in range(self.retries + 1):
            try:
                resp = await client.post(url, json=args)
                resp.raise_for_status()
                return resp.json()

            except httpx.HTTPStatusError as e:
                try:
                    detail = e.response.json()
                except Exception:
                    detail = e.response.text

                logger.error(
                    "MCP async tool %s failed (%s): %s",
                    tool_name,
                    e.response.status_code,
                    detail,
                )
                if attempt >= self.retries:
                    raise RuntimeError(f"MCP tool call failed: {detail}") from e

            except Exception as e:
                logger.warning(
                    "MCP async tool %s call error (attempt %s): %s",
                    tool_name,
                    attempt + 1,
                    e,
                )
                if attempt >= self.retries:
                    raise

                await asyncio.sleep(1)

        raise RuntimeError("MCP async call failed after retries")

    # ========================================================
    # SYNC TOOL CALL (NO EVENT LOOP)
    # ========================================================

    def call_tool_sync(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/tools/{tool_name}"
        client = self._get_sync_client()

        for attempt in range(self.retries + 1):
            try:
                resp = client.post(url, json=args)
                resp.raise_for_status()
                return resp.json()

            except httpx.HTTPStatusError as e:
                try:
                    detail = e.response.json()
                except Exception:
                    detail = e.response.text

                logger.error(
                    "MCP sync tool %s failed (%s): %s",
                    tool_name,
                    e.response.status_code,
                    detail,
                )
                if attempt >= self.retries:
                    raise RuntimeError(f"MCP tool call failed: {detail}") from e

            except Exception as e:
                logger.warning(
                    "MCP sync tool %s call error (attempt %s): %s",
                    tool_name,
                    attempt + 1,
                    e,
                )
                if attempt >= self.retries:
                    raise

        raise RuntimeError("MCP sync call failed after retries")


# ============================================================
# SINGLETON
# ============================================================

_default_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    global _default_client
    if not _default_client:
        _default_client = MCPClient()
    return _default_client
