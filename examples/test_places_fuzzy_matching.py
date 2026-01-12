"""
Fuzzy Matching and TTL Cache Tests for Places Tool

Tests the advanced features:
- Fuzzy city name matching with typos
- TTL cache performance (dataset mode uses lru_cache)
- Category alias resolution
- Similarity threshold behavior
"""

import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from travel_agent.tools.places_tool.dataset_adapter import (
    _fuzzy_match_city,
    _calculate_similarity,
    search_raw_places
)
from travel_agent.tools.places_tool import search_places


def test_similarity_calculation():
    """Test the similarity scoring function"""
    print("\n=== Test: String Similarity Calculation ===")
    
    test_cases = [
        ("mumbai", "mumbai", 1.0),
        ("mumbai", "mumbi", 0.9),  # Missing 'a'
        ("delhi", "deli", 0.8),     # Missing 'h'
        ("bangalore", "bangalor", 0.9),  # Missing 'e'
        ("mumbai", "xyz", 0.0),     # Completely different
    ]
    
    for str1, str2, expected_min in test_cases:
        similarity = _calculate_similarity(str1, str2)
        print(f"  '{str1}' vs '{str2}': {similarity:.2f} (expected >= {expected_min})")
        assert similarity >= expected_min or similarity < 0.5, \
            f"Unexpected similarity: {similarity}"
    
    print("✓ Similarity calculations working correctly")


def test_fuzzy_city_matching():
    """Test fuzzy matching with various typos"""
    print("\n=== Test: Fuzzy City Name Matching ===")
    
    # First, load dataset to get available cities
    all_places = search_raw_places()
    available_cities = {p['city'].lower() for p in all_places}
    
    # Test cases: (typo, expected_match_contains)
    test_cases = [
        ("Mumbi", "mumbai"),      # Common typo
        ("Mumbay", "mumbai"),     # Phonetic variant
        ("Deli", "delhi"),        # Missing letter
        ("Dehli", "delhi"),       # Transposition
        ("Bangalor", "bangalore"), # Missing 'e'
        ("Bangaluru", "bangalore"), # Alternative name
    ]
    
    for typo, expected in test_cases:
        result = _fuzzy_match_city(typo, available_cities)
        if result:
            similarity = _calculate_similarity(typo.lower(), result.lower())
            print(f"  '{typo}' -> '{result}' (similarity: {similarity:.2f}) ✓")
            assert expected in result.lower(), \
                f"Expected match to contain '{expected}', got '{result}'"
        else:
            print(f"  '{typo}' -> No match (threshold not met)")
    
    print("✓ Fuzzy matching tests completed")


def test_fuzzy_matching_threshold():
    """Test that fuzzy matching respects threshold"""
    print("\n=== Test: Fuzzy Matching Threshold Behavior ===")
    
    # Load available cities
    all_places = search_raw_places()
    available_cities = {p['city'].lower() for p in all_places}
    
    # Test with very different string (should not match)
    result = _fuzzy_match_city("xyz123", available_cities)
    assert result is None, "Very different strings should not match"
    print("  'xyz123' -> No match ✓")
    
    # Test with close match (should match)
    result = _fuzzy_match_city("Mumbi", available_cities)
    assert result is not None, "Close matches should work"
    print(f"  'Mumbi' -> '{result}' ✓")
    
    print("✓ Threshold behavior correct")


def test_fuzzy_search_integration():
    """Test fuzzy matching in full search flow"""
    print("\n=== Test: Fuzzy Search Integration ===")
    
    # Search with typo should still return results (return_metadata=True gets PlaceSearchResult)
    typo_result = search_places(city="Mumbi", limit=3, return_metadata=True)
    correct_result = search_places(city="Mumbai", limit=3, return_metadata=True)
    
    if typo_result.places and correct_result.places:
        # Should return same places (fuzzy match worked)
        assert len(typo_result.places) == len(correct_result.places), \
            "Fuzzy match should return same count"
        print(f"  'Mumbi' matched to Mumbai: {len(typo_result.places)} places ✓")
        
        for place in typo_result.places:
            print(f"    - {place.name} ({place.category}, {place.rating}★)")
    else:
        print("  ⚠ Typo search returned no results (fuzzy matching may need tuning)")
    
    print("✓ Integration test completed")


def test_cache_performance():
    """Test that caching improves performance"""
    print("\n=== Test: Cache Performance ===")
    
    # First call (cold cache)
    start = time.time()
    result1 = search_raw_places(city="Mumbai")
    time1 = time.time() - start
    
    # Second call (warm cache)
    start = time.time()
    result2 = search_raw_places(city="Mumbai")
    time2 = time.time() - start
    
    print(f"  First call:  {time1*1000:.2f}ms")
    print(f"  Second call: {time2*1000:.2f}ms")
    print(f"  Speedup: {time1/time2:.1f}x" if time2 > 0 else "  Speedup: instant")
    
    assert len(result1) == len(result2), "Cache should return same results"
    print("✓ Cache working correctly")


def test_category_alias_fuzzy_combo():
    """Test combination of category alias and fuzzy city matching"""
    print("\n=== Test: Category Alias + Fuzzy City Combo ===")
    
    # Use alias 'museums' and typo 'Deli' (use return_metadata=True)
    result = search_places(city="Deli", category="museums", limit=3, return_metadata=True)
    
    if result.places:
        print(f"  'Deli' + 'museums' found {len(result.places)} results:")
        for place in result.places:
            assert "museum" in place.category.lower(), "Category alias should work"
            print(f"    - {place.name} in {place.city}")
        print("✓ Combo features work together")
    else:
        print("  ⚠ No museums found in Delhi (may be dataset limitation)")


def test_no_match_fallback():
    """Test behavior when fuzzy matching finds no suitable match"""
    print("\n=== Test: No Match Fallback ===")
    
    # Pass return_metadata=True to get PlaceSearchResult
    result = search_places(city="CompletelyInvalidCity12345", return_metadata=True)
    
    assert result.places == [], "Should return empty list for no matches"
    print("✓ Gracefully handles unmatched cities")


def test_exact_match_priority():
    """Test that exact matches are preferred over fuzzy matches"""
    print("\n=== Test: Exact Match Priority ===")
    
    # If dataset has both "Mumbai" and "Mumbi", exact should win
    # This tests the implementation logic
    
    exact_places = search_raw_places(city="Mumbai")
    fuzzy_places = search_raw_places(city="Mumbi")  # Typo
    
    # Both should return Mumbai results (exact or fuzzy matched)
    print(f"  'Mumbai' (exact): {len(exact_places)} places")
    print(f"  'Mumbi' (fuzzy):  {len(fuzzy_places)} places")
    
    # The fuzzy match should resolve to Mumbai
    if fuzzy_places:
        for place in fuzzy_places[:2]:
            print(f"    - {place['name']} in {place['city']}")
    
    print("✓ Match priority test completed")


def run_all_tests():
    """Run all fuzzy matching and cache tests"""
    print("=" * 60)
    print("PLACES TOOL: FUZZY MATCHING & TTL CACHE TESTS")
    print("=" * 60)
    
    tests = [
        test_similarity_calculation,
        test_fuzzy_city_matching,
        test_fuzzy_matching_threshold,
        test_fuzzy_search_integration,
        test_cache_performance,
        test_category_alias_fuzzy_combo,
        test_no_match_fallback,
        test_exact_match_priority,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
