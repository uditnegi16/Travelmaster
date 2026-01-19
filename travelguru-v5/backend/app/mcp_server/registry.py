from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="TravelGuru MCP Server")

# =====================================================
# HEALTH
# =====================================================

@app.get("/health")
def health():
    return {"status": "ok"}

# =====================================================
# REQUEST MODELS
# =====================================================

class WeatherRequest(BaseModel):
    city: str


class FlightSearchRequest(BaseModel):
    from_city: str
    to_city: str
    people: int


class HotelSearchRequest(BaseModel):
    city: str
    nights: int
    budget_level: str


class BudgetEstimateRequest(BaseModel):
    city: str
    days: int
    people: int


# =====================================================
# WEATHER TOOL
# =====================================================

OPENWEATHER_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

@app.post("/tools/weather")
def get_weather(req: WeatherRequest):

    if not OPENWEATHER_KEY:
        raise HTTPException(status_code=500, detail="OPENWEATHERMAP_API_KEY not set")

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": req.city,
        "appid": OPENWEATHER_KEY,
        "units": "metric",
    }

    r = requests.get(url, params=params)
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail="Weather API failed")

    data = r.json()

    return {
        "city": req.city,
        "temp_c": data["main"]["temp"],
        "condition": data["weather"][0]["description"],
        "packing_suggestions": [
            "Light cotton clothes",
            "Sunscreen",
            "Cap or hat",
        ],
    }

# =====================================================
# MOCK FLIGHT SEARCH
# =====================================================

@app.post("/tools/flight_search")
def flight_search(req: FlightSearchRequest):
    return {
        "flights": [
            {
                "airline": "IndiGo",
                "price": 4500 * req.people,
                "duration": "1h 20m",
            },
            {
                "airline": "Vistara",
                "price": 5200 * req.people,
                "duration": "1h 15m",
            },
        ]
    }

# =====================================================
# MOCK HOTEL SEARCH
# =====================================================

@app.post("/tools/hotel_search")
def hotel_search(req: HotelSearchRequest):
    return {
        "hotels": [
            {
                "name": "Sea Breeze Resort",
                "price_per_night": 2200,
                "rating": 4.2,
            },
            {
                "name": "Palm Stay Inn",
                "price_per_night": 1800,
                "rating": 3.9,
            },
        ]
    }

# =====================================================
# MOCK BUDGET ESTIMATE
# =====================================================

@app.post("/tools/budget_estimate")
def budget_estimate(req: BudgetEstimateRequest):
    total = (req.days * 3000) + (req.people * 5000)

    return {
        "total_estimate": total,
        "breakdown": {
            "stay": req.days * 2000,
            "food": req.days * 800,
            "local_transport": req.days * 200,
        },
        "savings_tips": ["Book flights early", "Use local buses"],
        "upgrade_options": ["Beach resort upgrade"],
    }
