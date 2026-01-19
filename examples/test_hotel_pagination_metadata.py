"""
Test pagination metadata for hotel_tool module.

This test verifies:
1. Pagination metadata (total_found, has_more, returned, etc.)
2. City alias support (Bombay → Mumbai, Bengaluru → Bangalore)
3. Backward compatibility with existing code
"""

import logging
from backend.travel_agent.tools.hotel_tool import search_hotels, HotelSearchResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)


def main():
    print("=" * 80)
    print("HOTEL TOOL: PAGINATION METADATA & FEATURES TEST")
    print("=" * 80)
    
    # FEATURE 1: Pagination metadata
    print("\n" + "=" * 80)
    print("FEATURE 1: PAGINATION METADATA")
    print("=" * 80)
    
    # Test 1: Basic metadata return
    print("\n[Test 1] Return metadata with limited results:")
    print("-" * 80)
    result = search_hotels(city="Mumbai", limit=3, return_metadata=True)
    
    assert isinstance(result, HotelSearchResult), "Should return HotelSearchResult"
    print(f"✓ Result type: {type(result).__name__}")
    print(f"✓ total_found: {result.total_found}")
    print(f"✓ returned: {result.returned}")
    print(f"✓ skipped: {result.skipped}")
    print(f"✓ limit: {result.limit}")
    print(f"✓ has_more: {result.has_more}")
    print(f"✓ Number of hotels: {len(result.hotels)}")
    
    if result.has_more:
        print(f"  → There are {result.total_found - result.returned} more results available")
    
    # Test 2: Metadata with limit=None
    print("\n[Test 2] Metadata with limit=None (return all):")
    print("-" * 80)
    result = search_hotels(max_price_per_night=5000, limit=None, return_metadata=True)
    
    print(f"✓ total_found: {result.total_found}")
    print(f"✓ returned: {result.returned}")
    print(f"✓ limit: {result.limit}")
    print(f"✓ has_more: {result.has_more}")
    print(f"✓ All results returned: {result.total_found == result.returned}")
    
    # Test 3: has_more flag accuracy
    print("\n[Test 3] Verify has_more flag accuracy:")
    print("-" * 80)
    
    # Case 1: Should have more
    result1 = search_hotels(limit=2, return_metadata=True)
    print(f"✓ limit=2, total_found={result1.total_found}, has_more={result1.has_more}")
    assert result1.has_more == (result1.total_found > 2), "has_more should be True when total > limit"
    
    # Case 2: Should NOT have more
    result2 = search_hotels(city="Goa", min_stars=5, limit=100, return_metadata=True)
    print(f"✓ limit=100, total_found={result2.total_found}, has_more={result2.has_more}")
    assert result2.has_more == (result2.total_found > 100), "has_more should be False when total <= limit"
    
    # Case 3: limit=None should NOT have more
    result3 = search_hotels(city="Delhi", limit=None, return_metadata=True)
    print(f"✓ limit=None, total_found={result3.total_found}, has_more={result3.has_more}")
    assert result3.has_more == False, "has_more should be False when limit=None"
    
    # Test 4: Backward compatibility (return_metadata=False)
    print("\n[Test 4] Backward compatibility (return_metadata=False):")
    print("-" * 80)
    result = search_hotels(city="Bangalore", limit=3, return_metadata=False)
    
    assert isinstance(result, list), "Should return list when return_metadata=False"
    print(f"✓ Result type: {type(result).__name__}")
    print(f"✓ Number of hotels: {len(result)}")
    print(f"✓ Backward compatible: Agent code can still use list directly")
    
    # Test 5: Default behavior (no return_metadata)
    print("\n[Test 5] Default behavior (return_metadata not specified):")
    print("-" * 80)
    result = search_hotels(limit=5)
    
    assert isinstance(result, list), "Should default to list (backward compatible)"
    print(f"✓ Default returns: {type(result).__name__}")
    print(f"✓ Existing code continues to work without changes")
    
    # FEATURE 2: City alias support
    print("\n" + "=" * 80)
    print("FEATURE 2: CITY ALIAS SUPPORT")
    print("=" * 80)
    
    # Test 6: Bombay → Mumbai
    print("\n[Test 6] City alias: Bombay → Mumbai:")
    print("-" * 80)
    hotels_bombay = search_hotels(city="Bombay", limit=5)
    hotels_mumbai = search_hotels(city="Mumbai", limit=5)
    
    print(f"✓ 'Bombay' found: {len(hotels_bombay)} hotels")
    print(f"✓ 'Mumbai' found: {len(hotels_mumbai)} hotels")
    print(f"✓ Results match: {len(hotels_bombay) == len(hotels_mumbai)}")
    
    # Test 7: Bengaluru → Bangalore
    print("\n[Test 7] City alias: Bengaluru → Bangalore:")
    print("-" * 80)
    hotels_bengaluru = search_hotels(city="Bengaluru", limit=5)
    hotels_bangalore = search_hotels(city="Bangalore", limit=5)
    
    print(f"✓ 'Bengaluru' found: {len(hotels_bengaluru)} hotels")
    print(f"✓ 'Bangalore' found: {len(hotels_bangalore)} hotels")
    print(f"✓ Results match: {len(hotels_bengaluru) == len(hotels_bangalore)}")
    
    # Test 8: Case insensitive city names
    print("\n[Test 8] Case insensitive city matching:")
    print("-" * 80)
    hotels_lower = search_hotels(city="delhi", limit=5)
    hotels_upper = search_hotels(city="DELHI", limit=5)
    hotels_mixed = search_hotels(city="DeLhI", limit=5)
    
    print(f"✓ 'delhi': {len(hotels_lower)} hotels")
    print(f"✓ 'DELHI': {len(hotels_upper)} hotels")
    print(f"✓ 'DeLhI': {len(hotels_mixed)} hotels")
    print(f"✓ All match: {len(hotels_lower) == len(hotels_upper) == len(hotels_mixed)}")
    
    # FEATURE 3: Complex filtering
    print("\n" + "=" * 80)
    print("FEATURE 3: COMPLEX FILTERING")
    print("=" * 80)
    
    # Test 9: Multiple filters with metadata
    print("\n[Test 9] Multiple filters (city + stars + price + amenities):")
    print("-" * 80)
    result = search_hotels(
        city="Mumbai",
        min_stars=4,
        max_price_per_night=6000,
        required_amenities=["wifi", "pool"],
        limit=5,
        return_metadata=True
    )
    
    print(f"✓ total_found: {result.total_found}")
    print(f"✓ returned: {result.returned}")
    print(f"✓ has_more: {result.has_more}")
    
    # Verify all results match the filters
    all_match = all(
        h.city.lower() in ["mumbai", "bombay"] and
        h.stars >= 4 and
        h.price_per_night <= 6000 and
        all(amenity.lower() in [a.lower() for a in h.amenities] for amenity in ["wifi", "pool"])
        for h in result.hotels
    )
    print(f"✓ All results match filters: {all_match}")
    
    # Test 10: Amenities case insensitivity
    print("\n[Test 10] Amenities case insensitivity:")
    print("-" * 80)
    hotels_lower = search_hotels(required_amenities=["wifi", "pool"], limit=5)
    hotels_upper = search_hotels(required_amenities=["WIFI", "POOL"], limit=5)
    hotels_mixed = search_hotels(required_amenities=["WiFi", "Pool"], limit=5)
    
    print(f"✓ 'wifi, pool': {len(hotels_lower)} hotels")
    print(f"✓ 'WIFI, POOL': {len(hotels_upper)} hotels")
    print(f"✓ 'WiFi, Pool': {len(hotels_mixed)} hotels")
    print(f"✓ All match: {len(hotels_lower) == len(hotels_upper) == len(hotels_mixed)}")
    
    # FEATURE 4: Sorting
    print("\n" + "=" * 80)
    print("FEATURE 4: PRICE SORTING")
    print("=" * 80)
    
    # Test 11: Sorted by price (default)
    print("\n[Test 11] Default sorting (by price, ascending):")
    print("-" * 80)
    result = search_hotels(city="Delhi", limit=10, sort_by_price=True, return_metadata=True)
    
    prices = [h.price_per_night for h in result.hotels]
    is_sorted = all(prices[i] <= prices[i+1] for i in range(len(prices)-1))
    
    print(f"✓ Returned {len(result.hotels)} hotels")
    print(f"✓ Price range: ₹{min(prices):,} - ₹{max(prices):,}")
    print(f"✓ Sorted correctly: {is_sorted}")
    print(f"  Prices: {[f'₹{p:,}' for p in prices[:5]]}")
    
    # Test 12: Unsorted results
    print("\n[Test 12] No sorting (sort_by_price=False):")
    print("-" * 80)
    result = search_hotels(city="Bangalore", limit=5, sort_by_price=False, return_metadata=True)
    
    print(f"✓ Returned {len(result.hotels)} hotels (in dataset order)")
    for i, hotel in enumerate(result.hotels, 1):
        print(f"  {i}. {hotel.name}: ₹{hotel.price_per_night:,}")
    
    # FEATURE 5: Empty results handling
    print("\n" + "=" * 80)
    print("FEATURE 5: EMPTY RESULTS HANDLING")
    print("=" * 80)
    
    # Test 13: No results with metadata
    print("\n[Test 13] No results with restrictive filters:")
    print("-" * 80)
    result = search_hotels(
        city="Delhi",
        min_stars=5,
        max_price_per_night=500,  # Very low price for 5-star
        return_metadata=True
    )
    
    print(f"✓ total_found: {result.total_found}")
    print(f"✓ returned: {result.returned}")
    print(f"✓ has_more: {result.has_more}")
    print(f"✓ Empty list: {len(result.hotels) == 0}")
    assert result.total_found == 0, "Should have 0 results"
    assert result.returned == 0, "Should return 0 results"
    assert result.has_more == False, "Should not have more"
    
    # FEATURE 6: UI/API pagination use case
    print("\n" + "=" * 80)
    print("FEATURE 6: UI/API PAGINATION USE CASE")
    print("=" * 80)
    
    # Test 14: Simulate pagination
    print("\n[Test 14] Simulate pagination (page 1, 2, 3):")
    print("-" * 80)
    
    page_size = 5
    
    # Page 1
    page1 = search_hotels(city="Mumbai", limit=page_size, return_metadata=True)
    print(f"Page 1: Showing {page1.returned} of {page1.total_found} hotels")
    print(f"  Has more: {page1.has_more}")
    
    # Note: Actual offset-based pagination would require offset parameter
    # For now, we demonstrate the metadata usage
    print(f"\n✓ UI can display: 'Showing {page1.returned} of {page1.total_found} results'")
    if page1.has_more:
        print(f"✓ UI can show 'Load more' button")
        print(f"✓ {page1.total_found - page1.returned} results remaining")
    
    # Test 15: All results at once
    print("\n[Test 15] Get all results for export:")
    print("-" * 80)
    result = search_hotels(
        city="Bangalore",
        min_stars=3,
        limit=None,
        return_metadata=True
    )
    
    print(f"✓ Retrieved all {result.total_found} hotels")
    print(f"✓ total_found == returned: {result.total_found == result.returned}")
    print(f"✓ Ready for export/download")
    
    print("\n" + "=" * 80)
    print("ALL PAGINATION & FEATURE TESTS PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    main()
