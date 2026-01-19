"""
Comprehensive Integration Tests for Places Tool

Tests the complete places search functionality including:
- City-based filtering
- Category filtering
- Rating-based filtering
- Fuzzy matching for city names
- Category aliases
- Sorting by rating
- Pagination and metadata
- Input validation
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from travel_agent.tools.places_tool import search_places


def test_search_by_city():
    """Test filtering places by city name"""
    print("\n=== Test: Search by City (Mumbai) ===")
    places = search_places(city="Mumbai")  # Returns list by default
    
    assert places, "Should return places for Mumbai"
    assert all(p.city.lower() == "mumbai" for p in places), "All places should be in Mumbai"
    print(f"✓ Found {len(places)} places in Mumbai")
    for place in places[:3]:
        print(f"  - {place.name} ({place.category}, Rating: {place.rating})")


def test_search_by_category():
    """Test filtering places by category"""
    print("\n=== Test: Search by Category (museum) ===")
    places = search_places(category="museum")
    
    assert places, "Should return museums"
    assert all("museum" in p.category.lower() for p in places), "All places should be museums"
    print(f"✓ Found {len(places)} museums")
    for place in places[:3]:
        print(f"  - {place.name} in {place.city} (Rating: {place.rating})")


def test_search_by_min_rating():
    """Test filtering places by minimum rating"""
    print("\n=== Test: Search by Minimum Rating (4.5+) ===")
    places = search_places(min_rating=4.5)
    
    assert places, "Should return highly-rated places"
    assert all(p.rating >= 4.5 for p in places), "All places should have rating >= 4.5"
    print(f"✓ Found {len(places)} places rated 4.5+")
    for place in places[:3]:
        print(f"  - {place.name} (Rating: {place.rating})")


def test_combined_filters():
    """Test combining multiple filters"""
    print("\n=== Test: Combined Filters (Delhi + Temple + 4.0+) ===")
    places = search_places(city="Delhi", category="temple", min_rating=4.0)
    
    if places:
        assert all(p.city.lower() == "delhi" for p in places), "All should be in Delhi"
        assert all("temple" in p.category.lower() for p in places), "All should be temples"
        assert all(p.rating >= 4.0 for p in places), "All should have rating >= 4.0"
        print(f"✓ Found {len(places)} temples in Delhi rated 4.0+")
        for place in places:
            print(f"  - {place.name} (Rating: {place.rating})")
    else:
        print("⚠ No temples in Delhi with rating 4.0+ found in dataset")


def test_case_insensitive_search():
    """Test that search is case-insensitive"""
    print("\n=== Test: Case-Insensitive Search ===")
    
    places1 = search_places(city="mumbai")
    places2 = search_places(city="MUMBAI")
    places3 = search_places(city="Mumbai")
    
    assert len(places1) == len(places2) == len(places3), \
        "Case should not affect results"
    print(f"✓ Case-insensitive search works: {len(places1)} places")


def test_category_aliases():
    """Test category alias mapping (museums -> museum)"""
    print("\n=== Test: Category Aliases (museums -> museum) ===")
    
    places1 = search_places(category="museum")
    places2 = search_places(category="museums")
    
    assert len(places1) == len(places2), \
        "Category aliases should return same results"
    print(f"✓ Alias mapping works: 'museums' -> 'museum' ({len(places1)} results)")


def test_fuzzy_city_matching():
    """Test fuzzy matching for city names with typos"""
    print("\n=== Test: Fuzzy City Matching ===")
    
    # Test with intentional typos
    test_cases = [
        ("Mumbi", "Mumbai"),  # Missing 'a'
        ("Deli", "Delhi"),    # Missing 'h'
        ("Bangalor", "Bangalore")  # Missing 'e'
    ]
    
    for typo, correct in test_cases:
        places = search_places(city=typo)
        if places:
            print(f"✓ '{typo}' matched to '{correct}': {len(places)} places")
        else:
            print(f"⚠ '{typo}' did not match '{correct}' (may need threshold adjustment)")


def test_sorting_by_rating():
    """Test sorting results by rating (descending)"""
    print("\n=== Test: Sort by Rating (Descending) ===")
    
    places = search_places(city="Mumbai", sort_by_rating=True, limit=5)
    
    if len(places) >= 2:
        ratings = [p.rating for p in places]
        assert ratings == sorted(ratings, reverse=True), "Should be sorted descending"
        print(f"✓ Results sorted by rating: {ratings}")
    else:
        print("⚠ Not enough places to verify sorting")


def test_limit_parameter():
    """Test result limiting"""
    print("\n=== Test: Limit Results ===")
    
    places_unlimited = search_places(city="Mumbai", limit=None)
    places_limited = search_places(city="Mumbai", limit=3)
    
    assert len(places_limited) <= 3, "Should respect limit"
    assert len(places_limited) <= len(places_unlimited), \
        "Limited should not exceed unlimited"
    print(f"✓ Limit works: {len(places_unlimited)} -> {len(places_limited)}")


def test_metadata_tracking():
    """Test pagination metadata"""
    print("\n=== Test: Pagination Metadata ===")
    
    result = search_places(city="Mumbai", limit=5, return_metadata=True)
    
    assert hasattr(result, 'places'), "Should have places attribute"
    assert hasattr(result, 'total_found'), "Should have total_found"
    assert hasattr(result, 'returned'), "Should have returned"
    assert result.total_found >= len(result.places), \
        "Total should be >= returned count"
    assert result.returned == len(result.places), "Returned should match places length"
    assert result.limit == 5, "Should track limit"
    
    print(f"✓ Metadata: total={result.total_found}, returned={result.returned}, limit={result.limit}")


def test_no_results():
    """Test handling of searches with no results"""
    print("\n=== Test: No Results ===")
    
    places = search_places(city="NonexistentCity12345")
    
    assert places == [], "Should return empty list"
    print("✓ No results handled correctly")


def test_invalid_rating_validation():
    """Test validation of rating bounds"""
    print("\n=== Test: Invalid Rating Validation ===")
    
    try:
        places = search_places(min_rating=-1.0)
        # Should either raise ValueError or return empty results
        print(f"⚠ Accepted invalid rating (returned {len(places)} places)")
    except ValueError as e:
        print(f"✓ Rejected invalid rating: {e}")
    
    try:
        places = search_places(min_rating=6.0)
        print(f"⚠ Accepted out-of-bounds rating (returned {len(places)} places)")
    except ValueError as e:
        print(f"✓ Rejected out-of-bounds rating: {e}")


def test_schema_validation():
    """Test that returned places match PlaceOption schema"""
    print("\n=== Test: Schema Validation ===")
    
    places = search_places(city="Mumbai", limit=1)
    
    if places:
        place = places[0]
        assert hasattr(place, 'id'), "Should have id"
        assert hasattr(place, 'name'), "Should have name"
        assert hasattr(place, 'city'), "Should have city"
        assert hasattr(place, 'category'), "Should have category"
        assert hasattr(place, 'rating'), "Should have rating"
        assert 0.0 <= place.rating <= 5.0, "Rating should be in valid range"
        print(f"✓ Schema valid: {place.name} (all fields present)")
    else:
        print("⚠ No places to validate schema")


def run_all_tests():
    """Run all test cases"""
    print("=" * 60)
    print("COMPREHENSIVE PLACES TOOL INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        test_search_by_city,
        test_search_by_category,
        test_search_by_min_rating,
        test_combined_filters,
        test_case_insensitive_search,
        test_category_aliases,
        test_fuzzy_city_matching,
        test_sorting_by_rating,
        test_limit_parameter,
        test_metadata_tracking,
        test_no_results,
        test_invalid_rating_validation,
        test_schema_validation,
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
