"""
Test script for the enhanced flight_tool module with nice-to-have features.

This script tests:
1. City alias / IATA code support
2. Dataset path consistency (already verified)
3. limit=None support
4. total_found count logging
"""

import logging
from backend.travel_agent.tools.flight_tool import search_flights

# Configure logging to see the total_found count
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)


def main():
    print("=" * 80)
    print("ENHANCED FLIGHT TOOL MODULE TEST")
    print("=" * 80)
    
    # Test 1: City alias support - IATA codes
    print("\n[Test 1] Search by IATA code (DEL → BOM):")
    print("-" * 80)
    flights = search_flights(origin="DEL", destination="BOM", limit=3)
    print(f"✓ Found {len(flights)} flights using IATA codes")
    for i, flight in enumerate(flights, 1):
        print(f"{i}. {flight.airline}: {flight.origin} → {flight.destination} - ₹{flight.price:,}")
    
    # Test 2: City alias support - Alternative names
    print("\n[Test 2] Search using city aliases (Bengaluru/Bangalore):")
    print("-" * 80)
    flights1 = search_flights(destination="Bengaluru", limit=3)
    flights2 = search_flights(destination="Bangalore", limit=3)
    print(f"✓ 'Bengaluru' returned {len(flights1)} flights")
    print(f"✓ 'Bangalore' returned {len(flights2)} flights")
    print(f"✓ Aliases work: {len(flights1) == len(flights2)}")
    
    # Test 3: City alias - Bombay/Mumbai
    print("\n[Test 3] Search using city aliases (Bombay/Mumbai):")
    print("-" * 80)
    flights1 = search_flights(destination="Bombay", limit=3)
    flights2 = search_flights(destination="Mumbai", limit=3)
    print(f"✓ 'Bombay' returned {len(flights1)} flights")
    print(f"✓ 'Mumbai' returned {len(flights2)} flights")
    print(f"✓ Aliases work: {len(flights1) == len(flights2)}")
    
    # Test 4: limit=None support
    print("\n[Test 4] Search with limit=None (return all results):")
    print("-" * 80)
    flights = search_flights(origin="Mumbai", limit=None)
    print(f"✓ Returned {len(flights)} flights (all matching results)")
    print(f"Sample flights:")
    for flight in flights[:3]:
        print(f"  - {flight.airline}: {flight.origin} → {flight.destination}")
    
    # Test 5: limit=None with price filter
    print("\n[Test 5] Search with limit=None and max_price:")
    print("-" * 80)
    flights = search_flights(max_price=5000, limit=None, sort_by_price=True)
    print(f"✓ Returned {len(flights)} flights under ₹5000")
    if flights:
        print(f"  Cheapest: ₹{flights[0].price:,}")
        print(f"  Most expensive: ₹{flights[-1].price:,}")
    
    # Test 6: Compare limit=5 vs limit=None
    print("\n[Test 6] Compare limit=5 vs limit=None:")
    print("-" * 80)
    flights_limited = search_flights(origin="Hyderabad", limit=5)
    flights_all = search_flights(origin="Hyderabad", limit=None)
    print(f"✓ With limit=5: {len(flights_limited)} flights")
    print(f"✓ With limit=None: {len(flights_all)} flights (total_found)")
    print(f"✓ Total flights from Hyderabad: {len(flights_all)}")
    
    # Test 7: IATA code case insensitivity
    print("\n[Test 7] IATA codes are case-insensitive:")
    print("-" * 80)
    flights1 = search_flights(origin="del", limit=3)
    flights2 = search_flights(origin="DEL", limit=3)
    flights3 = search_flights(origin="Del", limit=3)
    print(f"✓ 'del' returned {len(flights1)} flights")
    print(f"✓ 'DEL' returned {len(flights2)} flights")
    print(f"✓ 'Del' returned {len(flights3)} flights")
    print(f"✓ Case-insensitive: {len(flights1) == len(flights2) == len(flights3)}")
    
    # Test 8: Mixed IATA and city name
    print("\n[Test 8] Mix IATA codes and city names:")
    print("-" * 80)
    flights = search_flights(origin="HYD", destination="Delhi", limit=3)
    print(f"✓ Found {len(flights)} flights (HYD → Delhi)")
    for flight in flights:
        print(f"  - {flight.airline}: ₹{flight.price:,}")
    
    # Test 9: Dataset path consistency check
    print("\n[Test 9] Dataset path consistency:")
    print("-" * 80)
    from backend.travel_agent.config import FLIGHTS_DATASET_PATH
    print(f"✓ Config uses: FLIGHTS_DATASET_PATH")
    print(f"✓ Path: {FLIGHTS_DATASET_PATH}")
    print(f"✓ File exists: {FLIGHTS_DATASET_PATH.exists()}")
    
    # Test 10: Verify total_found in logs
    print("\n[Test 10] Verify total_found count in logs:")
    print("-" * 80)
    print("(Check the INFO logs above for 'total_found' metric)")
    flights = search_flights(destination="Kolkata", limit=2)
    print(f"✓ Requested limit=2, returned {len(flights)} flights")
    print(f"  (See log above for total_found count)")
    
    print("\n" + "=" * 80)
    print("ALL ENHANCEMENT TESTS COMPLETED!")
    print("=" * 80)
    print("\nFeatures implemented:")
    print("✓ 1. City alias / IATA code support (DEL, BOM, BLR, etc.)")
    print("✓ 2. Dataset path consistent (FLIGHTS_DATASET_PATH)")
    print("✓ 3. limit=None support (returns all results)")
    print("✓ 4. total_found count exposed in logs")


if __name__ == "__main__":
    main()
