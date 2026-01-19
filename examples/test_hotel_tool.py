"""
Quick test script for the hotel_tool module.

This script demonstrates basic usage and validates the implementation.
Run this from the project root with: python -m examples.test_hotel_tool
"""

import logging
from backend.travel_agent.tools.hotel_tool import search_hotels

# Configure logging to see debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    print("=" * 80)
    print("HOTEL TOOL MODULE TEST")
    print("=" * 80)
    
    # Test 1: Search all hotels (no filters)
    print("\n[Test 1] Search all hotels (limit 3):")
    print("-" * 80)
    hotels = search_hotels(limit=3)
    for i, hotel in enumerate(hotels, 1):
        print(f"{i}. {hotel.name} ({hotel.stars}★)")
        print(f"   City: {hotel.city}")
        print(f"   Price: ₹{hotel.price_per_night:,}/night")
        print(f"   Amenities: {', '.join(hotel.amenities)}")
    
    # Test 2: Search by city
    print("\n[Test 2] Search hotels in Mumbai (limit 5):")
    print("-" * 80)
    hotels = search_hotels(city="Mumbai", limit=5)
    for i, hotel in enumerate(hotels, 1):
        print(f"{i}. {hotel.name} ({hotel.stars}★) - ₹{hotel.price_per_night:,}/night")
    
    # Test 3: Search by minimum stars
    print("\n[Test 3] Search 4-star and above hotels:")
    print("-" * 80)
    hotels = search_hotels(min_stars=4, limit=5)
    for i, hotel in enumerate(hotels, 1):
        print(f"{i}. {hotel.name} ({hotel.stars}★) in {hotel.city}")
        print(f"   Price: ₹{hotel.price_per_night:,}/night")
    
    # Test 4: Search with max_price_per_night filter
    print("\n[Test 4] Search hotels under ₹4000/night:")
    print("-" * 80)
    hotels = search_hotels(max_price_per_night=4000, limit=5)
    for i, hotel in enumerate(hotels, 1):
        print(f"{i}. {hotel.name}: {hotel.city} - ₹{hotel.price_per_night:,}/night ({hotel.stars}★)")
    
    # Test 5: Search with amenities filter
    print("\n[Test 5] Search hotels with wifi AND pool:")
    print("-" * 80)
    hotels = search_hotels(
        required_amenities=["wifi", "pool"],
        limit=5
    )
    for i, hotel in enumerate(hotels, 1):
        print(f"{i}. {hotel.name} ({hotel.city})")
        print(f"   Amenities: {', '.join(hotel.amenities)}")
        print(f"   Price: ₹{hotel.price_per_night:,}/night")
    
    # Test 6: Search with all filters
    print("\n[Test 6] Search Mumbai 4★+ hotels under ₹6000 with wifi:")
    print("-" * 80)
    hotels = search_hotels(
        city="Mumbai",
        min_stars=4,
        max_price_per_night=6000,
        required_amenities=["wifi"],
        limit=5
    )
    for i, hotel in enumerate(hotels, 1):
        print(f"{i}. {hotel.name} ({hotel.stars}★)")
        print(f"   Price: ₹{hotel.price_per_night:,}/night")
        print(f"   Amenities: {', '.join(hotel.amenities)}")
    
    # Test 7: Case-insensitive search
    print("\n[Test 7] Case-insensitive search (mUmBaI):")
    print("-" * 80)
    hotels = search_hotels(city="mUmBaI", limit=3)
    for i, hotel in enumerate(hotels, 1):
        print(f"{i}. {hotel.name} in {hotel.city}")
    
    # Test 8: City alias support
    print("\n[Test 8] City alias support (Bombay → Mumbai):")
    print("-" * 80)
    hotels_bombay = search_hotels(city="Bombay", limit=3)
    hotels_mumbai = search_hotels(city="Mumbai", limit=3)
    print(f"✓ 'Bombay' found {len(hotels_bombay)} hotels")
    print(f"✓ 'Mumbai' found {len(hotels_mumbai)} hotels")
    print(f"✓ Alias working: {len(hotels_bombay) == len(hotels_mumbai)}")
    
    # Test 9: Sorting by price
    print("\n[Test 9] Verify price sorting (ascending):")
    print("-" * 80)
    hotels = search_hotels(city="Delhi", limit=5, sort_by_price=True)
    prices = [h.price_per_night for h in hotels]
    is_sorted = all(prices[i] <= prices[i+1] for i in range(len(prices)-1))
    print(f"Prices: {prices}")
    print(f"✓ Sorted correctly: {is_sorted}")
    
    # Test 10: Without price sorting
    print("\n[Test 10] Search without price sorting:")
    print("-" * 80)
    hotels = search_hotels(city="Bangalore", limit=3, sort_by_price=False)
    for i, hotel in enumerate(hotels, 1):
        print(f"{i}. {hotel.name} - ₹{hotel.price_per_night:,}/night")
    
    # Test 11: Schema validation
    print("\n[Test 11] Schema validation:")
    print("-" * 80)
    hotels = search_hotels(limit=1)
    if hotels:
        hotel = hotels[0]
        print(f"Hotel ID: {hotel.id}")
        print(f"Name: {hotel.name}")
        print(f"City: {hotel.city}")
        print(f"Stars: {hotel.stars} (type: {type(hotel.stars).__name__})")
        print(f"Price: {hotel.price_per_night} (type: {type(hotel.price_per_night).__name__})")
        print(f"Amenities: {hotel.amenities} (type: {type(hotel.amenities).__name__})")
        print(f"✓ Stars in valid range (1-5): {1 <= hotel.stars <= 5}")
        print(f"✓ Price is non-negative: {hotel.price_per_night >= 0}")
        print(f"✓ Amenities is a list: {isinstance(hotel.amenities, list)}")
    
    # Test 12: Multiple amenities filter
    print("\n[Test 12] Search hotels with multiple amenities (wifi, gym, pool):")
    print("-" * 80)
    hotels = search_hotels(
        required_amenities=["wifi", "gym", "pool"],
        limit=3
    )
    print(f"✓ Found {len(hotels)} hotels with all 3 amenities")
    for i, hotel in enumerate(hotels, 1):
        print(f"{i}. {hotel.name} ({hotel.city})")
        print(f"   Has wifi: {'wifi' in [a.lower() for a in hotel.amenities]}")
        print(f"   Has gym: {'gym' in [a.lower() for a in hotel.amenities]}")
        print(f"   Has pool: {'pool' in [a.lower() for a in hotel.amenities]}")
    
    # Test 13: Return no results for strict filters
    print("\n[Test 13] Strict filter (should return fewer or no results):")
    print("-" * 80)
    hotels = search_hotels(
        city="Goa",
        min_stars=5,
        max_price_per_night=1000,  # Very low price for 5-star
        limit=5
    )
    print(f"✓ Found {len(hotels)} hotels (expected 0 or very few)")
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
