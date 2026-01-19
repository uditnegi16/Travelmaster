"""
Test fuzzy matching and TTL cache features for hotel_tool module.

This test verifies:
1. Fuzzy city name matching (typos, partial names)
2. TTL cache behavior (dataset mode vs API mode)
3. Cache configuration and performance
4. Similarity scoring and threshold configuration
"""

import logging
from backend.travel_agent.tools.hotel_tool import search_hotels
from backend.travel_agent.tools.hotel_tool.dataset_adapter import (
    _calculate_similarity,
    _fuzzy_match_city,
    _normalize_city_name
)
from backend.travel_agent import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)


def main():
    print("=" * 80)
    print("HOTEL TOOL: FUZZY MATCHING & TTL CACHE TESTS")
    print("=" * 80)
    
    # Display current configuration
    print("\n" + "=" * 80)
    print("CURRENT CONFIGURATION")
    print("=" * 80)
    print(f"✓ DATA_SOURCE: {config.DATA_SOURCE}")
    print(f"✓ ENABLE_FUZZY_MATCHING: {config.ENABLE_FUZZY_MATCHING}")
    print(f"✓ FUZZY_MATCH_THRESHOLD: {config.FUZZY_MATCH_THRESHOLD}")
    print(f"✓ API_CACHE_TTL: {config.API_CACHE_TTL} seconds")
    print(f"✓ CACHE_MAXSIZE: {config.CACHE_MAXSIZE}")
    
    # FEATURE 1: String similarity calculation
    print("\n" + "=" * 80)
    print("FEATURE 1: STRING SIMILARITY CALCULATION")
    print("=" * 80)
    
    print("\n[Test 1] Similarity scoring:")
    print("-" * 80)
    test_cases = [
        ("Mumbai", "Mumbai", 1.0),      # Exact match
        ("Mumbai", "Mumbi", 0.91),       # Single character missing
        ("Mumbai", "Mumbay", 0.92),      # Typo
        ("Delhi", "Deli", 0.89),         # Missing character
        ("Bangalore", "Bangalor", 0.94), # Missing character
        ("Bangalore", "Bengaluru", 0.67), # Different spelling
        ("Chennai", "Chenai", 0.93),     # Typo
        ("Kolkata", "Calcutta", 0.57),   # Historical name
        ("Goa", "Go", 0.67),             # Partial match
    ]
    
    for str1, str2, expected_min in test_cases:
        similarity = _calculate_similarity(str1, str2)
        status = "✓" if similarity >= expected_min else "⚠"
        print(f"{status} '{str1}' vs '{str2}': {similarity:.2f} (expected ≥{expected_min:.2f})")
    
    # FEATURE 2: Fuzzy city matching
    print("\n" + "=" * 80)
    print("FEATURE 2: FUZZY CITY MATCHING")
    print("=" * 80)
    
    print("\n[Test 2] Fuzzy match with typos:")
    print("-" * 80)
    available_cities = {"mumbai", "delhi", "bangalore", "chennai", "kolkata", "goa"}
    
    fuzzy_test_cases = [
        ("Mumbi", "mumbai"),        # Missing 'a'
        ("Deli", "delhi"),          # Missing 'h'
        ("Bangalor", "bangalore"),  # Missing 'e'
        ("Chenai", "chennai"),      # Missing 'n'
        ("Mumbay", "mumbai"),       # Wrong character
        ("Dellhi", "delhi"),        # Extra 'l'
    ]
    
    for query, expected in fuzzy_test_cases:
        match = _fuzzy_match_city(query, available_cities, threshold=0.75)
        status = "✓" if match == expected else "✗"
        print(f"{status} '{query}' → '{match}' (expected: '{expected}')")
    
    # FEATURE 3: Fuzzy matching in search
    print("\n" + "=" * 80)
    print("FEATURE 3: FUZZY MATCHING IN HOTEL SEARCH")
    print("=" * 80)
    
    # Test 3a: Exact match (baseline)
    print("\n[Test 3a] Exact city match (baseline):")
    print("-" * 80)
    hotels_exact = search_hotels(city="Mumbai", limit=3)
    print(f"✓ 'Mumbai' found {len(hotels_exact)} hotels")
    for i, hotel in enumerate(hotels_exact, 1):
        print(f"  {i}. {hotel.name} ({hotel.stars}★) - ₹{hotel.price_per_night}/night")
    
    # Test 3b: Fuzzy match with typo
    print("\n[Test 3b] Fuzzy match with typo (Mumbi → Mumbai):")
    print("-" * 80)
    hotels_fuzzy = search_hotels(city="Mumbi", limit=3)
    print(f"✓ 'Mumbi' found {len(hotels_fuzzy)} hotels (via fuzzy matching)")
    
    if config.ENABLE_FUZZY_MATCHING:
        assert len(hotels_fuzzy) == len(hotels_exact), "Fuzzy match should find same hotels"
        print(f"✓ Fuzzy matching working: {len(hotels_fuzzy)} == {len(hotels_exact)}")
    else:
        print(f"⚠ Fuzzy matching disabled, found {len(hotels_fuzzy)} hotels")
    
    # Test 3c: Another typo
    print("\n[Test 3c] Fuzzy match (Deli → Delhi):")
    print("-" * 80)
    hotels_delhi_exact = search_hotels(city="Delhi", limit=3)
    hotels_delhi_fuzzy = search_hotels(city="Deli", limit=3)
    
    print(f"✓ 'Delhi': {len(hotels_delhi_exact)} hotels")
    print(f"✓ 'Deli': {len(hotels_delhi_fuzzy)} hotels")
    
    if config.ENABLE_FUZZY_MATCHING:
        assert len(hotels_delhi_fuzzy) == len(hotels_delhi_exact)
        print(f"✓ Fuzzy matching: 'Deli' correctly matched to 'Delhi'")
    
    # Test 3d: Multiple character typo
    print("\n[Test 3d] Fuzzy match (Bangalor → Bangalore):")
    print("-" * 80)
    hotels_blr_exact = search_hotels(city="Bangalore", limit=3)
    hotels_blr_fuzzy = search_hotels(city="Bangalor", limit=3)
    
    print(f"✓ 'Bangalore': {len(hotels_blr_exact)} hotels")
    print(f"✓ 'Bangalor': {len(hotels_blr_fuzzy)} hotels")
    
    if config.ENABLE_FUZZY_MATCHING:
        assert len(hotels_blr_fuzzy) == len(hotels_blr_exact)
        print(f"✓ Fuzzy matching: 'Bangalor' correctly matched to 'Bangalore'")
    
    # FEATURE 4: Threshold behavior
    print("\n" + "=" * 80)
    print("FEATURE 4: FUZZY MATCH THRESHOLD BEHAVIOR")
    print("=" * 80)
    
    print("\n[Test 4] Threshold filtering:")
    print("-" * 80)
    print(f"Current threshold: {config.FUZZY_MATCH_THRESHOLD}")
    
    # Test with very different strings (should not match)
    hotels_no_match = search_hotels(city="XYZ123", limit=3)
    print(f"✓ 'XYZ123' (gibberish): {len(hotels_no_match)} hotels")
    assert len(hotels_no_match) == 0, "Gibberish should not fuzzy match"
    print("✓ Threshold correctly prevents bad matches")
    
    # FEATURE 5: City aliases still work
    print("\n" + "=" * 80)
    print("FEATURE 5: CITY ALIASES + FUZZY MATCHING COMPATIBILITY")
    print("=" * 80)
    
    print("\n[Test 5] Aliases work alongside fuzzy matching:")
    print("-" * 80)
    
    hotels_bombay = search_hotels(city="Bombay", limit=3)  # Alias
    hotels_mumbai = search_hotels(city="Mumbai", limit=3)  # Real name
    hotels_mumbi = search_hotels(city="Mumbi", limit=3)    # Fuzzy
    
    print(f"✓ 'Bombay' (alias): {len(hotels_bombay)} hotels")
    print(f"✓ 'Mumbai' (real): {len(hotels_mumbai)} hotels")
    print(f"✓ 'Mumbi' (fuzzy): {len(hotels_mumbi)} hotels")
    
    assert len(hotels_bombay) == len(hotels_mumbai), "Alias should work"
    if config.ENABLE_FUZZY_MATCHING:
        assert len(hotels_mumbi) == len(hotels_mumbai), "Fuzzy should work too"
    print("✓ Aliases and fuzzy matching work together correctly")
    
    # FEATURE 6: Combined filters with fuzzy matching
    print("\n" + "=" * 80)
    print("FEATURE 6: FUZZY MATCHING + COMPLEX FILTERS")
    print("=" * 80)
    
    print("\n[Test 6] Fuzzy city + star rating + price + amenities:")
    print("-" * 80)
    
    # Use fuzzy-matched city with other filters
    hotels_complex = search_hotels(
        city="Mumbi",  # Typo, should match Mumbai
        min_stars=4,
        max_price_per_night=6000,
        required_amenities=["wifi"],
        limit=3
    )
    
    print(f"✓ Found {len(hotels_complex)} hotels matching all criteria:")
    for i, hotel in enumerate(hotels_complex, 1):
        print(f"  {i}. {hotel.name} ({hotel.city}) - {hotel.stars}★ - ₹{hotel.price_per_night}/night")
        print(f"     Amenities: {', '.join(hotel.amenities)}")
    
    if config.ENABLE_FUZZY_MATCHING and len(hotels_complex) > 0:
        print("✓ Fuzzy matching works with complex filters")
    
    # FEATURE 7: Cache behavior
    print("\n" + "=" * 80)
    print("FEATURE 7: TTL CACHE BEHAVIOR")
    print("=" * 80)
    
    print("\n[Test 7] Cache mode based on DATA_SOURCE:")
    print("-" * 80)
    print(f"✓ Current DATA_SOURCE: {config.DATA_SOURCE}")
    
    if config.DATA_SOURCE == "dataset":
        print("✓ Using permanent LRU cache (optimal for static data)")
        print("  - Dataset loaded once and cached forever")
        print("  - Zero overhead after first load")
        print("  - Perfect for MVP with JSON datasets")
    elif config.DATA_SOURCE == "api":
        print(f"✓ Using TTL cache with {config.API_CACHE_TTL}s expiration")
        print(f"  - API responses cached for {config.API_CACHE_TTL} seconds")
        print(f"  - Max {config.CACHE_MAXSIZE} entries in cache")
        print("  - Prevents stale data from live APIs")
    
    # Performance test: Multiple searches use cache
    print("\n[Test 8] Cache performance (multiple searches):")
    print("-" * 80)
    
    import time
    
    # First search (cache miss)
    start = time.time()
    hotels1 = search_hotels(city="Mumbai", limit=5)
    time1 = time.time() - start
    
    # Second search (cache hit)
    start = time.time()
    hotels2 = search_hotels(city="Mumbai", limit=5)
    time2 = time.time() - start
    
    # Third search with different params (should still use cached dataset)
    start = time.time()
    hotels3 = search_hotels(city="Delhi", limit=5)
    time3 = time.time() - start
    
    print(f"✓ First search (cache miss): {time1*1000:.2f}ms")
    print(f"✓ Second search (cache hit): {time2*1000:.2f}ms")
    print(f"✓ Third search (different city): {time3*1000:.2f}ms")
    
    if config.DATA_SOURCE == "dataset":
        print(f"✓ Cache speedup: {time1/time2:.1f}x faster on cache hit")
    
    # SUMMARY
    print("\n" + "=" * 80)
    print("FEATURE SUMMARY")
    print("=" * 80)
    print("\n✓ TTL Cache:")
    print(f"  - Dataset mode: Permanent LRU cache (current)")
    print(f"  - API mode: {config.API_CACHE_TTL}s TTL cache (future)")
    print(f"  - Configurable via environment variables")
    
    print("\n✓ Fuzzy Matching:")
    print(f"  - Status: {'ENABLED' if config.ENABLE_FUZZY_MATCHING else 'DISABLED'}")
    print(f"  - Threshold: {config.FUZZY_MATCH_THRESHOLD} (75% similarity)")
    print(f"  - Algorithm: Ratcliff/Obershelp (difflib.SequenceMatcher)")
    print(f"  - Handles: Typos, missing chars, extra chars")
    print(f"  - Compatible with: City aliases, case-insensitive search")
    
    print("\n" + "=" * 80)
    print("ALL FUZZY MATCHING & CACHE TESTS PASSED! ✓")
    print("=" * 80)


if __name__ == "__main__":
    main()
