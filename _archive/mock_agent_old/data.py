import pandas as pd
def to_py(val):
    if hasattr(val, "item"):
        return val.item()
    return val

def mock_agent_response(user_input: dict):
    return {
        "flights": [
            {
                "id": "AI-203",
                "airline": "Air India",
                "origin": user_input.get("origin", "DEL"),
                "destination": user_input.get("destination", "BLR"),
                "departure_time": "10:00",
                "arrival_time": "12:30",
                "duration_time": "2h 30m",
                "stops": to_py(0),
                "price": to_py(6200),
                "currency": "INR",
                "booking_link": "https://airindia.com/book"
            }
        ],
        "hotels": [
            {
                "id": "HTL-11",
                "name": "Taj Hotel",
                "city": user_input.get("destination", "BLR"),
                "stars": to_py(5),
                "price_per_night": to_py(14500),
                "amenities": ["wifi", "pool", "breakfast"],
                "provider": "Taj",
                "latitude": to_py(12.97),
                "longitude": to_py(77.59),
                "currency": "INR",
                "booking_link": "https://tajhotels.com"
            }
        ],
        "places": [
            {
                "id": "PLC-1",
                "name": "Lalbagh",
                "city": "Bangalore",
                "category": "Park",
                "rating": to_py(4.6),
                "entry_fee": to_py(30)
            }
        ],
        "weather": {
            "max_temp": to_py(32),
            "min_temp": to_py(22),
            "feels_like_max": to_py(34),
            "feels_like_min": to_py(23),
            "rain_mm": to_py(0),
            "max_wind_kmh": to_py(12),
            "date": user_input.get("date", "2026-02-01")
        }
    }
