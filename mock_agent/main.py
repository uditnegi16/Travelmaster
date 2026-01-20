from fastapi import FastAPI
from pydantic import BaseModel
from data import mock_agent_response

app = FastAPI()


class AgentRequest(BaseModel):
    user_input: dict


@app.post("/agent/plan-trip")
def plan_trip(request: AgentRequest):
    return mock_agent_response(request.user_input)
