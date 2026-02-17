"""
Minimal Unit Tests for Places Tool Components

Tests individual components in isolation:
- Dataset adapter
- Normalizer
- Helper functions
- Edge cases
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from travel_agent.tools.places_tool.dataset_adapter import (
    search_raw_places,
    _normalize_category,
    _fuzzy_match_city
)
from travel_agent.tools.places_tool.normalize import raw_to_placeoption


def test_dataset_adapter_basic():
    """Test basic dataset loading"""
    print("\n=== Test: Dataset Adapter - Basic Load ===")
    
    places = search_raw_places()
    assert isinstance(places, list), "Should return a list"
    assert len(places) > 0, "Should load places from dataset"
    print(f"✓ Loaded {len(places)} places from dataset")


def test_dataset_adapter_city_filter():
    """Test city filtering in dataset adapter"""
    print("\n=== Test: Dataset Adapter - City Filter ===")
    
    all_places = search_raw_places()
    mumbai_places = search_raw_places(city="Mumbai")
    
    assert len(mumbai_places) < len(all_places), "Filtered should be less than all"
    assert all(p['city'].lower() == 'mumbai' for p in mumbai_places), \
        "All should be in Mumbai"
    print(f"✓ City filter: {len(all_places)} -> {len(mumbai_places)} places")


def test_dataset_adapter_category_filter():
    """Test category filtering in dataset adapter"""
    print("\n=== Test: Dataset Adapter - Category Filter ===")
    
    all_places = search_raw_places()
    museums = search_raw_places(category="museum")
    
    assert len(museums) < len(all_places), "Filtered should be less than all"
    assert all("museum" in p['type'].lower() for p in museums), \
        "All should be museums"
    print(f"✓ Category filter: {len(all_places)} -> {len(museums)} museums")


def test_dataset_adapter_rating_filter():
    """Test rating filtering in dataset adapter"""
    print("\n=== Test: Dataset Adapter - Rating Filter ===")
    
    all_places = search_raw_places()
    high_rated = search_raw_places(min_rating=4.5)
    
    assert len(high_rated) < len(all_places), "Filtered should be less than all"
    assert all(p['rating'] >= 4.5 for p in high_rated), \
        "All should have rating >= 4.5"
    print(f"✓ Rating filter: {len(all_places)} -> {len(high_rated)} high-rated")


def test_normalize_category_function():
    """Test category normalization helper"""
    print("\n=== Test: Normalize Category Helper ===")
    
    test_cases = [
        ("museum", "museum"),
        ("museums", "museum"),
        ("MuSeUmS", "museum"),
        ("gardens", "park"),
        ("GARDENS", "park"),
        ("temple", "temple"),
        ("unknown", "unknown"),
    ]
    
    for input_cat, expected in test_cases:
        result = _normalize_category(input_cat)
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print(f"  '{input_cat}' -> '{result}' ✓")
    
    print(f"✓ All {len(test_cases)} category normalizations passed")


def test_fuzzy_match_city():
    """Test fuzzy city matching"""
    print("\n=== Test: Fuzzy City Matching ===")
    
    # Load dataset to get available cities
    all_places = search_raw_places()
    available_cities = {p['city'].lower() for p in all_places}
    
    test_cases = [
        ("mumbai", "mumbai"),
        ("Mumbay", "mumbai"),
        ("deli", "delhi"),
        ("dehli", "delhi"),
    ]
    
    for input_city, expected_contains in test_cases:
        result = _fuzzy_match_city(input_city, available_cities)
        if result:
            assert expected_contains in result.lower(), \
                f"Expected match to contain '{expected_contains}', got '{result}'"
            print(f"  '{input_city}' -> '{result}' ✓")
        else:
            print(f"  '{input_city}' -> No match (threshold not met)")
    
    print("✓ Fuzzy matching tests completed")


def test_normalizer_valid_data():
    """Test normalizer with valid place data"""
    print("\n=== Test: Normalizer - Valid Data ===")
    
    raw_place = {
        'place_id': 'p123',
        'name': 'Gateway of India',
        'city': 'Mumbai',
        'type': 'monument',
        'rating': 4.5
    }
    
    place = raw_to_placeoption(raw_place)
    
    assert place.id == 'p123', "ID should match"
    assert place.name == 'Gateway of India', "Name should match"
    assert place.city == 'Mumbai', "City should match"
    assert place.category == 'monument', "Category should map from type"
    assert place.rating == 4.5, "Rating should match"
    
    print(f"✓ Normalized: {place.name} ({place.category}, {place.rating}★)")


def test_normalizer_rating_validation():
    """Test normalizer rating bounds validation"""
    print("\n=== Test: Normalizer - Rating Validation ===")
    
    # Test lower bound
    raw_place_low = {
        'place_id': 'p1',
        'name': 'Test Place',
        'city': 'Mumbai',
        'type': 'park',
        'rating': -1.0
    }
    
    try:
        place = raw_to_placeoption(raw_place_low)
        print(f"⚠ Accepted invalid rating: {place.rating}")
    except ValueError as e:
        print(f"✓ Rejected low rating: {e}")
    
    # Test upper bound
    raw_place_high = {
        'place_id': 'p2',
        'name': 'Test Place',
        'city': 'Mumbai',
        'type': 'park',
        'rating': 6.0
    }
    
    try:
        place = raw_to_placeoption(raw_place_high)
        print(f"⚠ Accepted invalid rating: {place.rating}")
    except ValueError as e:
        print(f"✓ Rejected high rating: {e}")


def test_normalizer_missing_fields():
    """Test normalizer with missing required fields"""
    print("\n=== Test: Normalizer - Missing Fields ===")
    
    incomplete_place = {
        'place_id': 'p123',
        'name': 'Incomplete Place',
        # Missing: city, type, rating
    }
    
    try:
        place = raw_to_placeoption(incomplete_place)
        print(f"⚠ Accepted incomplete data: {place}")
    except (KeyError, ValueError) as e:
        print(f"✓ Rejected incomplete data: {type(e).__name__}")


def test_normalizer_type_to_category_mapping():
    """Test that 'type' field maps to 'category' in schema"""
    print("\n=== Test: Normalizer - Type to Category Mapping ===")
    
    raw_place = {
        'place_id': 'p456',
        'name': 'Test Museum',
        'city': 'Delhi',
        'type': 'museum',  # Dataset uses 'type'
        'rating': 4.0
    }
    
    place = raw_to_placeoption(raw_place)
    
    assert hasattr(place, 'category'), "Should have 'category' attribute"
    assert not hasattr(place, 'type'), "Should not have 'type' attribute"
    assert place.category == 'museum', "Category should match type value"
    
    print(f"✓ 'type' -> 'category' mapping works")


def test_empty_search_results():
    """Test handling of empty search results"""
    print("\n=== Test: Empty Search Results ===")
    
    places = search_raw_places(city="NonexistentCity12345")
    
    assert isinstance(places, list), "Should return list"
    assert len(places) == 0, "Should be empty"
    print("✓ Empty results handled correctly")


def test_case_sensitivity():
    """Test case-insensitive filtering"""
    print("\n=== Test: Case Sensitivity ===")
    
    lower = search_raw_places(city="mumbai")
    upper = search_raw_places(city="MUMBAI")
    mixed = search_raw_places(city="MuMbAi")
    
    assert len(lower) == len(upper) == len(mixed), \
        "Case should not affect results"
    print(f"✓ Case-insensitive: all returned {len(lower)} results")


def test_multiple_filters_combined():
    """Test combining multiple filters"""
    print("\n=== Test: Multiple Filters Combined ===")
    
    all_places = search_raw_places()
    filtered = search_raw_places(city="Mumbai", category="temple", min_rating=4.0)
    
    assert len(filtered) <= len(all_places), "Filtered should be <= all"
    
    for place in filtered:
        assert place['city'].lower() == 'mumbai', "City filter failed"
        assert 'temple' in place['type'].lower(), "Category filter failed"
        assert place['rating'] >= 4.0, "Rating filter failed"
    
    print(f"✓ Combined filters work: {len(all_places)} -> {len(filtered)}")


def test_dataset_structure():
    """Test that dataset has expected structure"""
    print("\n=== Test: Dataset Structure ===")
    
    places = search_raw_places()
    
    if places:
        place = places[0]
        required_fields = ['place_id', 'name', 'city', 'type', 'rating']
        
        for field in required_fields:
            assert field in place, f"Missing required field: {field}"
        
        assert isinstance(place['rating'], (int, float)), "Rating should be numeric"
        assert isinstance(place['name'], str), "Name should be string"
        
        print(f"✓ Dataset structure valid (checked {len(required_fields)} fields)")
    else:
        print("⚠ No places in dataset to validate structure")


def test_rating_range_validation():
    """Test that all ratings are in valid range"""
    print("\n=== Test: Rating Range Validation ===")
    
    places = search_raw_places()
    
    for place in places:
        rating = place['rating']
        assert 0.0 <= rating <= 5.0, \
            f"Invalid rating {rating} for {place['name']}"
    
    print(f"✓ All {len(places)} places have valid ratings (0.0-5.0)")


def test_category_alias_in_search():
    """Test that category aliases work in search"""
    print("\n=== Test: Category Alias in Search ===")
    
    museums_singular = search_raw_places(category="museum")
    museums_plural = search_raw_places(category="museums")
    
    assert len(museums_singular) == len(museums_plural), \
        "Alias should return same results"
    print(f"✓ Alias works: 'museums' -> 'museum' ({len(museums_singular)} results)")


def run_all_tests():
    """Run all minimal unit tests"""
    print("=" * 60)
    print("MINIMAL PLACES TOOL UNIT TESTS")
    print("=" * 60)
    
    tests = [
        test_dataset_adapter_basic,
        test_dataset_adapter_city_filter,
        test_dataset_adapter_category_filter,
        test_dataset_adapter_rating_filter,
        test_normalize_category_function,
        test_fuzzy_match_city,
        test_normalizer_valid_data,
        test_normalizer_rating_validation,
        test_normalizer_missing_fields,
        test_normalizer_type_to_category_mapping,
        test_empty_search_results,
        test_case_sensitivity,
        test_multiple_filters_combined,
        test_dataset_structure,
        test_rating_range_validation,
        test_category_alias_in_search,
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
