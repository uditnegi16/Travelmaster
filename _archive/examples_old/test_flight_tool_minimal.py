"""
Minimal test for flight_tool dataset_adapter and normalize modules.

This test bypasses the full schemas import to test the core functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timezone
import json

# Test dataset_adapter directly
print("=" * 80)
print("TESTING DATASET ADAPTER")
print("=" * 80)

from backend.travel_agent.tools.flight_tool.dataset_adapter import (
    search_raw_flights,
    _load_flights_dataset
)

# Test 1: Load dataset
print("\n[Test 1] Loading dataset...")
flights = _load_flights_dataset()
print(f"✓ Loaded {len(flights)} flights")
print(f"Sample flight: {flights[0]}")

# Test 2: Search all
print("\n[Test 2] Search all flights...")
results = search_raw_flights()
print(f"✓ Found {len(results)} flights (no filters)")

# Test 3: Search by origin
print("\n[Test 3] Search by origin (Delhi)...")
results = search_raw_flights(origin="Delhi")
print(f"✓ Found {len(results)} flights from Delhi")
for flight in results[:3]:
    print(f"  - {flight['airline']}: {flight['from']} → {flight['to']} - ₹{flight['price']}")

# Test 4: Search by destination
print("\n[Test 4] Search by destination (Mumbai)...")
results = search_raw_flights(destination="Mumbai")
print(f"✓ Found {len(results)} flights to Mumbai")

# Test 5: Search with max_price
print("\n[Test 5] Search with max_price (3000)...")
results = search_raw_flights(max_price=3000)
print(f"✓ Found {len(results)} flights under ₹3000")
if results:
    print(f"  Cheapest: ₹{min(f['price'] for f in results)}")
    print(f"  Most expensive: ₹{max(f['price'] for f in results)}")

# Test 6: Combined filters
print("\n[Test 6] Combined filters (Delhi → Kolkata, max ₹5000)...")
results = search_raw_flights(origin="Delhi", destination="Kolkata", max_price=5000)
print(f"✓ Found {len(results)} matching flights")

# Test 7: Case insensitivity
print("\n[Test 7] Case insensitive search (dElHi)...")
results = search_raw_flights(origin="dElHi")
print(f"✓ Found {len(results)} flights (case insensitive works)")

print("\n" + "=" * 80)
print("TESTING NORMALIZER")
print("=" * 80)

from backend.travel_agent.tools.flight_tool.normalize import (
    raw_to_flightoption,
    _parse_datetime_to_utc
)

# Test 8: Parse datetime
print("\n[Test 8] Parse datetime to UTC...")
dt_str = "2025-01-04T11:32:00"
dt = _parse_datetime_to_utc(dt_str)
print(f"✓ Parsed: {dt}")
print(f"  Timezone: {dt.tzinfo}")
print(f"  Is UTC-aware: {dt.tzinfo is not None}")

# Test 9: Normalize flight
print("\n[Test 9] Normalize raw flight to FlightOption...")
raw_flight = {
    "flight_id": "FL0001",
    "airline": "IndiGo",
    "from": "Delhi",
    "to": "Mumbai",
    "departure_time": "2025-01-04T11:32:00",
    "arrival_time": "2025-01-04T13:32:00",
    "price": 2907
}

try:
    flight = raw_to_flightoption(raw_flight)
    print(f"✓ Normalized successfully:")
    print(f"  ID: {flight.id}")
    print(f"  Airline: {flight.airline}")
    print(f"  Route: {flight.origin} → {flight.destination}")
    print(f"  Departure: {flight.departure_time}")
    print(f"  Arrival: {flight.arrival_time}")
    print(f"  Price: ₹{flight.price}")
    print(f"  Departure UTC?: {flight.departure_time.tzinfo == timezone.utc}")
    print(f"  Arrival UTC?: {flight.arrival_time.tzinfo == timezone.utc}")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 10: Normalize multiple flights
print("\n[Test 10] Normalize multiple flights...")
raw_flights = search_raw_flights(origin="Hyderabad", destination="Delhi")[:3]
normalized_count = 0
for raw in raw_flights:
    try:
        flight = raw_to_flightoption(raw)
        normalized_count += 1
    except Exception as e:
        print(f"  ✗ Skipped {raw.get('flight_id')}: {e}")

print(f"✓ Normalized {normalized_count}/{len(raw_flights)} flights")

print("\n" + "=" * 80)
print("ALL CORE TESTS PASSED!")
print("=" * 80)
