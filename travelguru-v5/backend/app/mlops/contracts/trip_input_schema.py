from pydantic import BaseModel
from typing import Optional

class TripInput(BaseModel):
    # Flight
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    max_stops: int
    flight_preference: str  # cheapest | balanced | fastest

    # Hotel
    hotel_city: str
    preferred_star_category: Optional[int]
    max_price_per_night: Optional[float]

    # Cab
    pickup_location: str
    drop_location: str
    cab_type: Optional[str]

    # Global
    budget: float
    top_k: int = 5
    currency: str = "INR"
