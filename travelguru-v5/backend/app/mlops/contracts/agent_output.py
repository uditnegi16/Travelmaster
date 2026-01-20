from typing import List, Optional
from pydantic import BaseModel

# ✈️ Flights
class FlightItem(BaseModel):
    id: str
    airline: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    duration_time: int
    stops: int
    price: float
    currency: str
    booking_link: Optional[str]

# 🏨 Hotels
class HotelItem(BaseModel):
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
    booking_link: Optional[str]

# 📍 Places
class PlaceItem(BaseModel):
    id: str
    name: str
    city: str
    category: str
    rating: float
    entry_fee: float

# 🌦 Weather
class WeatherInfo(BaseModel):
    max_temp: float
    min_temp: float
    feels_like_max: float
    feels_like_min: float
    rain_mm: float
    max_wind_kmh: float
