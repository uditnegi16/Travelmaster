from fastapi import FastAPI
from app.api.v1 import a2a_endpoints, mlops_api

app = FastAPI(title='TravelGuru v5')

# Mount routers for A2A and B2C logic
app.include_router(a2a_endpoints.router, prefix='/api/v1/a2a')
app.include_router(mlops_api.router, prefix='/api/v1/mlops')
