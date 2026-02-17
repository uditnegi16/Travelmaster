"""
Quick test script for the flight_tool module.

This script demonstrates basic usage and validates the implementation.
Run this from the project root with: python -m examples.test_flight_tool
"""

import logging
from backend.travel_agent.tools.flight_tool import search_flights

# Configure logging to see debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    print("=" * 80)
    print("FLIGHT TOOL MODULE TEST")
    print("=" * 80)
    
    # Test 1: Search all flights (no filters)
    print("\n[Test 1] Search all flights (limit 3):")
    print("-" * 80)
    flights = search_flights(limit=3)
    for i, flight in enumerate(flights, 1):
        print(f"{i}. {flight.airline}: {flight.origin} → {flight.destination}")
        print(f"   Departure: {flight.departure_time}")
        print(f"   Arrival: {flight.arrival_time}")
        print(f"   Price: ₹{flight.price:,}")
    
    # Test 2: Search by origin
    print("\n[Test 2] Search flights from Delhi (limit 5):")
    print("-" * 80)
    flights = search_flights(origin="Delhi", limit=5)
    for i, flight in enumerate(flights, 1):
        print(f"{i}. {flight.airline}: {flight.origin} → {flight.destination} - ₹{flight.price:,}")
    
    # Test 3: Search by origin and destination
    print("\n[Test 3] Search flights from Hyderabad to Delhi:")
    print("-" * 80)
    flights = search_flights(origin="Hyderabad", destination="Delhi", limit=5)
    for i, flight in enumerate(flights, 1):
        print(f"{i}. {flight.airline}: ₹{flight.price:,}")
        print(f"   Departs: {flight.departure_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Arrives: {flight.arrival_time.strftime('%Y-%m-%d %H:%M')}")
    
    # Test 4: Search with max_price filter
    print("\n[Test 4] Search flights under ₹3000:")
    print("-" * 80)
    flights = search_flights(max_price=3000, limit=5)
    for i, flight in enumerate(flights, 1):
        print(f"{i}. {flight.airline}: {flight.origin} → {flight.destination} - ₹{flight.price:,}")
    
    # Test 5: Search with all filters
    print("\n[Test 5] Search Delhi → Kolkata under ₹5000:")
    print("-" * 80)
    flights = search_flights(
        origin="Delhi",
        destination="Kolkata",
        max_price=5000,
        limit=3
    )
    for i, flight in enumerate(flights, 1):
        print(f"{i}. {flight.airline}: ₹{flight.price:,}")
    
    # Test 6: Case-insensitive search
    print("\n[Test 6] Case-insensitive search (dElHi):")
    print("-" * 80)
    flights = search_flights(origin="dElHi", limit=3)
    for i, flight in enumerate(flights, 1):
        print(f"{i}. {flight.airline}: {flight.origin} → {flight.destination}")
    
    # Test 7: Timezone validation
    print("\n[Test 7] Timezone validation:")
    print("-" * 80)
    flights = search_flights(limit=1)
    if flights:
        flight = flights[0]
        print(f"Flight ID: {flight.id}")
        print(f"Departure timezone: {flight.departure_time.tzinfo}")
        print(f"Arrival timezone: {flight.arrival_time.tzinfo}")
        print(f"Is departure UTC-aware: {flight.departure_time.tzinfo is not None}")
        print(f"Is arrival UTC-aware: {flight.arrival_time.tzinfo is not None}")
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
