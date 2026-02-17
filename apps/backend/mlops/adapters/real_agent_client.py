# mlops/adapters/real_agent_client.py

from agents.adk_travel_host.travel_orchestrator_agent import TravelOrchestratorAgent


class RealAgentClient:
    """
    Thin wrapper so MLOps never depends on agent internals
    """

    def __init__(self):
        self.agent = TravelOrchestratorAgent()

    def plan_trip(self, user_input: dict) -> dict:
        """
        MUST return:
        {
          flights: [],
          hotels: [],
          places: [],
          weather: {}
        }
        """
        return self.agent.run(user_input)
