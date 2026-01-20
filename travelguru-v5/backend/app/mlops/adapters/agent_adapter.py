# mlops/adapters/agent_adapter.py

from typing import Dict
import time
import logging
import requests
from pydantic import ValidationError

from contracts.agent_output_schema import AgentOutputSchema

logger = logging.getLogger(__name__)


def parse_duration_to_minutes(duration_str: str) -> int:
    """
    '2h 30m' -> 150
    '1h' -> 60
    '45m' -> 45
    """
    if not duration_str:
        return 0

    duration_str = duration_str.lower()

    hours = 0
    minutes = 0

    try:
        if "h" in duration_str:
            hours = int(duration_str.split("h")[0].strip())

        if "m" in duration_str:
            minutes = int(duration_str.split("m")[0].split()[-1].strip())
    except Exception:
        return 0

    return hours * 60 + minutes


def safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default


class AgentAdapter:
    def __init__(self, agent_endpoint: str, timeout_sec: int = 15):
        self.agent_endpoint = agent_endpoint
        self.timeout_sec = timeout_sec

    def call_agent(self, user_input: Dict) -> Dict:
        start = time.time()

        try:
            # 1️⃣ Call agent
            response = requests.post(
                self.agent_endpoint,
                json={"user_input": user_input},
                timeout=self.timeout_sec
            )
            response.raise_for_status()

            raw_output = response.json()

            # 2️⃣ Validate agent response
            validated = AgentOutputSchema(**raw_output)

            latency = round(time.time() - start, 3)
            logger.info(f"Agent success | latency={latency}s")

            # 3️⃣ Normalize FLIGHTS for ML
            normalized_flights = []

            for f in validated.flights:
                flight = f.model_dump()

                flight["duration_minutes"] = parse_duration_to_minutes(
                    flight.get("duration_time")
                )
                flight["price"] = safe_float(flight.get("price"), 0.0)
                flight["stops"] = safe_int(flight.get("stops"), 0)

                normalized_flights.append(flight)

            # 4️⃣ Normalize HOTELS for ML (FIXES rating/star errors)
            normalized_hotels = []

            for h in validated.hotels:
                hotel = h.model_dump()

                hotel["rating"] = safe_float(hotel.get("rating"), 3.5)

                # agent may send "stars", ML expects "star_category"
                hotel["star_category"] = safe_int(
                    hotel.get("star_category") or hotel.get("stars"),
                    3
                )

                hotel["price_per_night"] = safe_float(
                    hotel.get("price_per_night"), 0.0
                )

                normalized_hotels.append(hotel)

            # 5️⃣ Final ML-safe response
            return {
                "flights": normalized_flights,
                "hotels": normalized_hotels,
                "places": [p.model_dump() for p in validated.places] if validated.places else [],
                "weather": validated.weather.model_dump() if validated.weather else {},
                "agent_status": "success",
                "agent_latency": latency,
            }

        except (requests.RequestException, ValidationError, Exception) as e:
            latency = round(time.time() - start, 3)
            logger.error(f"Agent failed | latency={latency}s | error={e}")

            return {
                "flights": [],
                "hotels": [],
                "places": [],
                "weather": {},
                "agent_status": "failed",
                "agent_latency": latency,
                "fallback_used": True,
            }
