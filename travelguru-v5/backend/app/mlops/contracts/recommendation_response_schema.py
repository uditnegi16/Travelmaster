from typing import List
from pydantic import BaseModel

class RecommendationResponse(BaseModel):
    flights: list
    hotels: list
    cabs: list
    places: list
    weather: dict
