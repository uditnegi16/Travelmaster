from fastapi import APIRouter, HTTPException
import mlflow

from api.schemas import PlanTripRequest
from pipelines.pipelines import recommend_hotels, recommend_flights
from adapters.agent_adapter import AgentAdapter
import pandas as pd

AGENT_ENDPOINT = "http://127.0.0.1:9000/agent/plan-trip"
agent_adapter = AgentAdapter(agent_endpoint=AGENT_ENDPOINT)

router = APIRouter()


@router.post("/plan-trip")
def plan_trip(request: PlanTripRequest):
    try:
        with mlflow.start_run(run_name="online_plan_trip"):

            agent_output = agent_adapter.call_agent(request.user_input)
            if agent_output["agent_status"] != "success":
                raise HTTPException(
                    status_code=503,
                    detail="Agent unavailable"
                )

            import pandas as pd
            agent_output["flights"] = pd.DataFrame(agent_output["flights"])
            agent_output["hotels"] = pd.DataFrame(agent_output["hotels"])

            ranked_flights = recommend_flights(
                flights_df=agent_output["flights"],
                agent_output=request.user_input,
                top_k=request.top_k_flights
            )

            ranked_hotels = recommend_hotels(
                hotels_df=agent_output["hotels"],
                agent_output=request.user_input,
                top_k=request.top_k_hotels
            )

            return {
                "recommended": {
                    "flights": ranked_flights.to_dict(orient="records"),
                    "hotels": ranked_hotels.to_dict(orient="records"),
                },
                "others": {
                    "places": agent_output.get("places", []),
                    "weather": agent_output.get("weather", {})
                }
            }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
