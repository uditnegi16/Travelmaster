from mangum import Mangum
from langgraph_agents.api import app

handler = Mangum(app, lifespan="off")

