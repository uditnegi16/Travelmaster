import requests
from typing import Dict

class AgentAdapter:
    def __init__(self, agent_url: str, timeout_sec: int = 900):
        self.agent_url = agent_url.rstrip("/")
        self.timeout_sec = timeout_sec

    def call_agent(self, user_input: Dict) -> Dict:
        try:
            resp = requests.post(
                f"{self.agent_url}/agent/plan-trip",
                json=user_input,
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            return resp.json()

        except Exception as e:
            return {
                "agent_status": "failed",
                "error": str(e),
                "fallback_used": True,
            }
