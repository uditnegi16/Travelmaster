# api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    HotelRequest,
    FlightRequest,
    CabRequest,
)

from pipelines.pipelines import (
    recommend_hotels,
    recommend_flights,
    recommend_cabs,
)

from utils.db_utils import (
    load_hotels_from_db,
    load_flights_from_db,
    load_cabs_from_db,
)

from api.plan_trip import router as plan_trip_router

from api.user_routes import router as user_router
from api.session_routes import router as session_router
# -------------------------
# APP INIT
# -------------------------
app = FastAPI(
    title="TravelGuru Recommendation API"
)

# -------------------------
# CORS (VERY IMPORTANT)
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# ROUTERS
# -------------------------
app.include_router(plan_trip_router)
app.include_router(user_router)
app.include_router(session_router)

# -------------------------
# HOTEL
# -------------------------
@app.post("/recommend/hotels")
def recommend_hotels_api(request: HotelRequest):

    hotels_df = load_hotels_from_db()

    agent_output = {
        "hotel_preferences": {
            "preferred_city": request.city,
            "preferred_star_category": request.preferred_star_category,
        }
    }

    ranked_hotels = recommend_hotels(
        hotels_df=hotels_df,
        agent_output=agent_output,
        top_k=request.top_k
    )

    return {
        "recommended": ranked_hotels.to_dict(orient="records"),
        "count": len(ranked_hotels),
    }


# -------------------------
# FLIGHT
# -------------------------
@app.post("/recommend/flights")
def recommend_flights_api(request: FlightRequest):

    flights_df = load_flights_from_db()

    agent_output = {
        "origin": request.origin,
        "destination": request.destination,
    }

    ranked_flights = recommend_flights(
        flights_df=flights_df,
        agent_output=agent_output,
        top_k=request.top_k
    )

    return {
        "recommended": ranked_flights.to_dict(orient="records"),
        "count": len(ranked_flights),
    }


# -------------------------
# CAB
# -------------------------
@app.post("/recommend/cabs")
def recommend_cabs_api(request: CabRequest):

    cabs_df = load_cabs_from_db()

    agent_output = {
        "pickup_location": request.pickup_location,
        "drop_location": request.drop_location,
    }

    ranked_cabs = recommend_cabs(
        cabs_df=cabs_df,
        agent_output=agent_output,
        top_k=request.top_k
    )

    return {
        "recommended": ranked_cabs.to_dict(orient="records"),
        "count": len(ranked_cabs),
    }
@app.get("/")
def root():
    return {"status": "ok", "service": "mlops", "port": 8000}
