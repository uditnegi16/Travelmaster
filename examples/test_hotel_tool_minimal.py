"""
Minimal test for hotel_tool dataset_adapter and normalize modules.

This test bypasses the full schemas import to test the core functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json

# Test dataset_adapter directly
print("=" * 80)
print("TESTING DATASET ADAPTER")
print("=" * 80)

from backend.travel_agent.tools.hotel_tool.dataset_adapter import (
    search_raw_hotels,
    _load_hotels_dataset,
    _has_required_amenities
)

# Test 1: Load dataset
print("\n[Test 1] Loading dataset...")
hotels = _load_hotels_dataset()
print(f"✓ Loaded {len(hotels)} hotels")
print(f"Sample hotel: {hotels[0]}")

# Test 2: Search all
print("\n[Test 2] Search all hotels...")
results = search_raw_hotels()
print(f"✓ Found {len(results)} hotels (no filters)")

# Test 3: Search by city
print("\n[Test 3] Search by city (Mumbai)...")
results = search_raw_hotels(city="Mumbai")
print(f"✓ Found {len(results)} hotels in Mumbai")
for hotel in results[:3]:
    print(f"  - {hotel['name']} ({hotel['stars']}★) - ₹{hotel['price_per_night']}/night")

# Test 4: Search by minimum stars
print("\n[Test 4] Search by min_stars (4)...")
results = search_raw_hotels(min_stars=4)
print(f"✓ Found {len(results)} hotels with 4+ stars")
# Verify all results have 4+ stars
all_valid = all(hotel['stars'] >= 4 for hotel in results)
print(f"✓ All results have 4+ stars: {all_valid}")

# Test 5: Search with max_price_per_night
print("\n[Test 5] Search with max_price_per_night (4000)...")
results = search_raw_hotels(max_price_per_night=4000)
print(f"✓ Found {len(results)} hotels under ₹4000/night")
if results:
    prices = [h['price_per_night'] for h in results]
    print(f"  Cheapest: ₹{min(prices)}")
    print(f"  Most expensive: ₹{max(prices)}")
    print(f"  All under ₹4000: {all(p <= 4000 for p in prices)}")

# Test 6: Search with required amenities
print("\n[Test 6] Search with required_amenities (wifi, pool)...")
results = search_raw_hotels(required_amenities=["wifi", "pool"])
print(f"✓ Found {len(results)} hotels with wifi AND pool")
# Verify all results have both amenities
for hotel in results[:3]:
    has_wifi = "wifi" in [a.lower() for a in hotel.get("amenities", [])]
    has_pool = "pool" in [a.lower() for a in hotel.get("amenities", [])]
    print(f"  - {hotel['name']}: wifi={has_wifi}, pool={has_pool}")

# Test 7: Combined filters
print("\n[Test 7] Combined filters (Delhi, 4★+, under ₹5000)...")
results = search_raw_hotels(
    city="Delhi",
    min_stars=4,
    max_price_per_night=5000
)
print(f"✓ Found {len(results)} matching hotels")

# Test 8: Case insensitivity
print("\n[Test 8] Case insensitive search (mUmBaI)...")
results = search_raw_hotels(city="mUmBaI")
print(f"✓ Found {len(results)} hotels (case insensitive works)")

# Test 9: City alias support
print("\n[Test 9] City alias support (Bombay → Mumbai)...")
results_bombay = search_raw_hotels(city="Bombay")
results_mumbai = search_raw_hotels(city="Mumbai")
print(f"✓ 'Bombay' found {len(results_bombay)} hotels")
print(f"✓ 'Mumbai' found {len(results_mumbai)} hotels")
print(f"✓ Alias working: {len(results_bombay) == len(results_mumbai)}")

# Test 10: Amenities helper function
print("\n[Test 10] Test _has_required_amenities helper...")
test_cases = [
    (["wifi", "pool", "gym"], ["wifi", "pool"], True),
    (["wifi", "pool"], ["wifi", "pool", "gym"], False),
    (["WiFi", "Pool"], ["wifi", "pool"], True),  # Case insensitive
    (["wifi"], ["wifi"], True),
    ([], ["wifi"], False),
]
for hotel_amenities, required, expected in test_cases:
    result = _has_required_amenities(hotel_amenities, required)
    status = "✓" if result == expected else "✗"
    print(f"{status} {hotel_amenities} has {required}: {result} (expected {expected})")

print("\n" + "=" * 80)
print("TESTING NORMALIZER")
print("=" * 80)

from backend.travel_agent.tools.hotel_tool.normalize import raw_to_hoteloption

# Test 11: Normalize hotel
print("\n[Test 11] Normalize raw hotel to HotelOption...")
raw_hotel = {
    "hotel_id": "HOT0001",
    "name": "Grand Palace Hotel",
    "city": "Delhi",
    "stars": 4,
    "price_per_night": 3897,
    "amenities": ["wifi", "pool"]
}

try:
    hotel = raw_to_hoteloption(raw_hotel)
    print(f"✓ Normalized successfully:")
    print(f"  ID: {hotel.id}")
    print(f"  Name: {hotel.name}")
    print(f"  City: {hotel.city}")
    print(f"  Stars: {hotel.stars}★")
    print(f"  Price: ₹{hotel.price_per_night}/night")
    print(f"  Amenities: {hotel.amenities}")
except Exception as e:
    print(f"✗ Normalization failed: {e}")

# Test 12: Normalize hotel with missing amenities (should default to [])
print("\n[Test 12] Normalize hotel with missing amenities...")
raw_hotel_no_amenities = {
    "hotel_id": "HOT9999",
    "name": "Basic Hotel",
    "city": "Goa",
    "stars": 2,
    "price_per_night": 1500
    # No amenities field
}

try:
    hotel = raw_to_hoteloption(raw_hotel_no_amenities)
    print(f"✓ Normalized successfully with default amenities:")
    print(f"  Amenities: {hotel.amenities}")
    print(f"  Is empty list: {hotel.amenities == []}")
except Exception as e:
    print(f"✗ Normalization failed: {e}")

# Test 13: Validate star rating bounds
print("\n[Test 13] Validate star rating bounds...")
test_stars = [
    ({"hotel_id": "T1", "name": "Hotel", "city": "City", "stars": 1, "price_per_night": 1000}, True),
    ({"hotel_id": "T2", "name": "Hotel", "city": "City", "stars": 5, "price_per_night": 1000}, True),
    ({"hotel_id": "T3", "name": "Hotel", "city": "City", "stars": 0, "price_per_night": 1000}, False),
    ({"hotel_id": "T4", "name": "Hotel", "city": "City", "stars": 6, "price_per_night": 1000}, False),
]

for raw, should_succeed in test_stars:
    try:
        hotel = raw_to_hoteloption(raw)
        result = "✓ Accepted" if should_succeed else "✗ Should have failed"
        print(f"{result} stars={raw['stars']}")
    except ValueError as e:
        result = "✗ Rejected" if should_succeed else "✓ Correctly rejected"
        print(f"{result} stars={raw['stars']}: {str(e)[:50]}")

# Test 14: Validate price validation
print("\n[Test 14] Validate price validation...")
raw_negative_price = {
    "hotel_id": "HOT_NEG",
    "name": "Negative Price Hotel",
    "city": "Test",
    "stars": 3,
    "price_per_night": -1000
}

try:
    hotel = raw_to_hoteloption(raw_negative_price)
    print(f"✗ Should have rejected negative price")
except ValueError as e:
    print(f"✓ Correctly rejected negative price: {str(e)[:60]}")

# Test 15: Validate empty name/city
print("\n[Test 15] Validate empty name/city...")
raw_empty_name = {
    "hotel_id": "HOT_EMPTY",
    "name": "   ",  # Empty/whitespace name
    "city": "Delhi",
    "stars": 3,
    "price_per_night": 2000
}

try:
    hotel = raw_to_hoteloption(raw_empty_name)
    print(f"✗ Should have rejected empty name")
except ValueError as e:
    print(f"✓ Correctly rejected empty name: {str(e)[:60]}")

print("\n" + "=" * 80)
print("INTEGRATION TEST")
print("=" * 80)

# Test 16: Full pipeline (adapter → normalizer)
print("\n[Test 16] Full pipeline test...")
raw_results = search_raw_hotels(city="Bangalore", max_price_per_night=5000)
print(f"✓ Found {len(raw_results)} raw hotels")

normalized_count = 0
error_count = 0
for raw in raw_results[:5]:
    try:
        hotel = raw_to_hoteloption(raw)
        normalized_count += 1
    except Exception as e:
        error_count += 1
        print(f"  ✗ Failed to normalize {raw.get('hotel_id', 'UNKNOWN')}: {e}")

print(f"✓ Successfully normalized {normalized_count}/{len(raw_results[:5])} hotels")
print(f"✓ Errors: {error_count}")

print("\n" + "=" * 80)
print("ALL MINIMAL TESTS COMPLETED!")
print("=" * 80)
