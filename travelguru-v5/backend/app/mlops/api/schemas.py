# api/schemas.py
from pydantic import BaseModel
from typing import List, Optional


# -------- HOTEL --------
class HotelRequest(BaseModel):
    city: str
    preferred_star_category: Optional[int] = None
    top_k: int = 5


class HotelOption(BaseModel):
    city: str
    rating: float
    price_per_night: float
    star_category: int
    score: float


# -------- FLIGHT --------
class FlightRequest(BaseModel):
    origin: str
    destination: str
    top_k: int = 5


# -------- CAB --------
class CabRequest(BaseModel):
    pickup_location: str
    drop_location: str
    top_k: int = 5
# api/schemas.py
# api/schemas.py
from pydantic import BaseModel
from typing import Optional


class UserInput(BaseModel):
    origin: str
    date: str
    airline: Optional[str] = None
    max_price: str
    stops: str
    amenities: Optional[str] = None
    cab_type: Optional[str] = None
    departure_time: Optional[str] = None
    drop: Optional[str] = None
    hotel_price: Optional[str] = None
    hotel_star: Optional[str] = None
    pickup: Optional[str] = None
    provider: Optional[str] = None

from pydantic import BaseModel
from typing import Dict, List, Optional


class PlanTripRequest(BaseModel):
    user_input: Dict

    top_k_hotels: int = 3
    top_k_flights: int = 3




