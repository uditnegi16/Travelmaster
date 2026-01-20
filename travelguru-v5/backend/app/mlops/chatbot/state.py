from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ConversationState:
    step: str = "greeting"

    # Flight
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    max_stops: Optional[int] = None
    flight_preference: Optional[str] = None

    # Hotel
    hotel_city: Optional[str] = None
    preferred_star_category: Optional[int] = None
    max_price_per_night: Optional[float] = None

    # Cab
    pickup_location: Optional[str] = None
    drop_location: Optional[str] = None
    cab_type: Optional[str] = None

    # Global
    budget: Optional[float] = None
    top_k: int = 5
