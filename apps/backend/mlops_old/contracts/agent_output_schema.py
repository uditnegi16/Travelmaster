from pydantic import BaseModel
from typing import List, Optional


class FlightAgentItem(BaseModel):
    id: str
    airline: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    duration_time: str   # ✅ FIXED (was int)
    stops: int
    price: float
    currency: str
    booking_link: Optional[str] = None


class HotelAgentItem(BaseModel):
    id: str
    name: str
    city: str
    stars: int
    price_per_night: float
    amenities: List[str]
    provider: str
    latitude: float
    longitude: float
    currency: str
    booking_link: Optional[str] = None


class PlaceAgentItem(BaseModel):
    id: str
    name: str
    city: str
    category: str
    rating: float
    entry_fee: Optional[float] = None


class WeatherAgentItem(BaseModel):
    max_temp: float
    min_temp: float
    feels_like_max: float
    feels_like_min: float
    rain_mm: float
    max_wind_kmh: float
    date: str


class AgentOutputSchema(BaseModel):
    flights: List[FlightAgentItem]
    hotels: List[HotelAgentItem]
    places: Optional[List[PlaceAgentItem]] = []
    weather: Optional[WeatherAgentItem] = None
