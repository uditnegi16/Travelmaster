from typing import Dict, Any
import time
import logging
import requests

logger = logging.getLogger(__name__)


class LangGraphA2AAdapter:
    """
    Adapter that talks DIRECTLY to LangGraph Agent API
    """

    def __init__(self, agent_base_url: str, timeout_sec: int = 900):
        self.base_url = agent_base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    def call_agent(self, payload: Dict) -> Dict[str, Any]:
        start = time.time()

        try:
            response = requests.post(
                f"{self.base_url}/agent/plan-trip",
                json=payload,
                timeout=self.timeout_sec,
            )

            response.raise_for_status()
            data = response.json()

            latency = round(time.time() - start, 3)

            logger.info(f"LangGraph agent success | latency={latency}s")

            return {
                **data,
                "agent_status": "success",
                "agent_latency": latency,
            }

        except Exception as e:
            latency = round(time.time() - start, 3)
            logger.exception("LangGraph agent failed")

            return {
                "agent_status": "failed",
                "agent_latency": latency,
                "fallback_used": True,
                "error": str(e),
            }
