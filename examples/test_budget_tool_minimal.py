"""
Minimal Unit Tests for Budget Tool Components

Tests individual functions in isolation:
- calculate_flight_cost
- calculate_hotel_cost
- calculate_activities_cost
- generate_warnings
- generate_recommendations
- Edge cases and validation
"""

import sys
import os
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from travel_agent.tools.budget_tool.budget_tool import (
    calculate_flight_cost,
    calculate_hotel_cost,
    calculate_activities_cost,
    generate_warnings,
    generate_recommendations
)
from travel_agent.schemas import FlightOption, HotelOption


def test_single_flight_cost():
    """Test flight cost with single outbound flight"""
    print("\n=== Test: Single Flight Cost ===")
    
    flight = FlightOption(
        id="FL001", airline="IndiGo", origin="DEL", destination="BOM",
        departure_time=datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2026, 3, 15, 12, 30, tzinfo=timezone.utc),
        price=5000
    )
    
    cost = calculate_flight_cost(outbound_flight=flight)
    assert cost == 5000
    print(f"✓ Single flight cost: ₹{cost:,}")


def test_round_trip_flight_cost():
    """Test flight cost with round trip"""
    print("\n=== Test: Round Trip Flight Cost ===")
    
    outbound = FlightOption(
        id="FL001", airline="IndiGo", origin="DEL", destination="BOM",
        departure_time=datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2026, 3, 15, 12, 30, tzinfo=timezone.utc),
        price=5000
    )
    
    return_flight = FlightOption(
        id="FL002", airline="IndiGo", origin="BOM", destination="DEL",
        departure_time=datetime(2026, 3, 20, 18, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2026, 3, 20, 20, 30, tzinfo=timezone.utc),
        price=4500
    )
    
    cost = calculate_flight_cost(outbound_flight=outbound, return_flight=return_flight)
    assert cost == 9500
    print(f"✓ Round trip cost: ₹{cost:,}")


def test_multiple_flights_cost():
    """Test flight cost with additional flights"""
    print("\n=== Test: Multiple Flights Cost ===")
    
    flight1 = FlightOption(
        id="FL001", airline="Air India", origin="DEL", destination="BOM",
        departure_time=datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2026, 5, 1, 10, 30, tzinfo=timezone.utc),
        price=5000
    )
    
    flight2 = FlightOption(
        id="FL002", airline="IndiGo", origin="BOM", destination="GOA",
        departure_time=datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2026, 5, 3, 13, 30, tzinfo=timezone.utc),
        price=3500
    )
    
    flight3 = FlightOption(
        id="FL003", airline="SpiceJet", origin="GOA", destination="DEL",
        departure_time=datetime(2026, 5, 6, 18, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2026, 5, 6, 20, 30, tzinfo=timezone.utc),
        price=4000
    )
    
    cost = calculate_flight_cost(
        outbound_flight=flight1,
        additional_flights=[flight2, flight3]
    )
    
    assert cost == 12500
    print(f"✓ Multiple flights cost: ₹{cost:,}")


def test_no_flights_cost():
    """Test flight cost with no flights"""
    print("\n=== Test: No Flights ===")
    
    cost = calculate_flight_cost()
    assert cost == 0
    print(f"✓ No flights cost: ₹{cost:,}")


def test_basic_hotel_cost():
    """Test basic hotel cost calculation"""
    print("\n=== Test: Basic Hotel Cost ===")
    
    hotel = HotelOption(
        id="H001", name="Hotel", city="Mumbai",
        stars=3, price_per_night=4000, amenities=[]
    )
    
    cost = calculate_hotel_cost(hotel=hotel, nights=3)
    assert cost == 12000
    print(f"✓ Hotel cost (3 nights): ₹{cost:,}")


def test_hotel_cost_zero_nights():
    """Test hotel cost with zero nights"""
    print("\n=== Test: Hotel Cost - Zero Nights ===")
    
    hotel = HotelOption(
        id="H001", name="Hotel", city="Mumbai",
        stars=3, price_per_night=4000, amenities=[]
    )
    
    cost = calculate_hotel_cost(hotel=hotel, nights=0)
    assert cost == 0
    print(f"✓ Zero nights cost: ₹{cost:,}")


def test_hotel_cost_negative_nights():
    """Test hotel cost validation for negative nights"""
    print("\n=== Test: Hotel Cost - Negative Nights ===")
    
    hotel = HotelOption(
        id="H001", name="Hotel", city="Mumbai",
        stars=3, price_per_night=4000, amenities=[]
    )
    
    try:
        cost = calculate_hotel_cost(hotel=hotel, nights=-2)
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Rejected negative nights: {e}")


def test_multiple_hotels_cost():
    """Test hotel cost with additional hotels"""
    print("\n=== Test: Multiple Hotels Cost ===")
    
    hotel1 = HotelOption(
        id="H001", name="Mumbai Hotel", city="Mumbai",
        stars=4, price_per_night=6000, amenities=[]
    )
    
    hotel2 = HotelOption(
        id="H002", name="Goa Resort", city="Goa",
        stars=5, price_per_night=8000, amenities=[]
    )
    
    cost = calculate_hotel_cost(
        hotel=hotel1,
        nights=2,
        additional_hotels=[(hotel2, 3)]
    )
    
    expected = (6000 * 2) + (8000 * 3)  # 12000 + 24000 = 36000
    assert cost == expected
    print(f"✓ Multiple hotels cost: ₹{cost:,}")


def test_no_hotel_cost():
    """Test hotel cost with no hotel"""
    print("\n=== Test: No Hotel ===")
    
    cost = calculate_hotel_cost()
    assert cost == 0
    print(f"✓ No hotel cost: ₹{cost:,}")


def test_explicit_activities_budget():
    """Test activities cost with explicit budget"""
    print("\n=== Test: Explicit Activities Budget ===")
    
    cost = calculate_activities_cost(activities_budget=8000)
    assert cost == 8000
    print(f"✓ Explicit activities budget: ₹{cost:,}")


def test_percentage_activities_budget():
    """Test activities cost with percentage allocation"""
    print("\n=== Test: Percentage Activities Budget ===")
    
    cost = calculate_activities_cost(
        percentage_of_budget=0.15,
        base_amount=20000
    )
    
    assert cost == 3000  # 15% of 20000
    print(f"✓ Percentage-based budget (15% of ₹20,000): ₹{cost:,}")


def test_no_activities_budget():
    """Test activities cost with no budget specified"""
    print("\n=== Test: No Activities Budget ===")
    
    cost = calculate_activities_cost()
    assert cost == 0
    print(f"✓ No activities budget: ₹{cost:,}")


def test_negative_activities_validation():
    """Test activities budget validation for negative values"""
    print("\n=== Test: Negative Activities Validation ===")
    
    try:
        cost = calculate_activities_cost(activities_budget=-500)
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Rejected negative activities budget: {e}")


def test_invalid_percentage_validation():
    """Test percentage validation for out-of-range values"""
    print("\n=== Test: Invalid Percentage Validation ===")
    
    try:
        cost = calculate_activities_cost(percentage_of_budget=1.5, base_amount=10000)
        print("✗ Should have raised ValueError for percentage > 1.0")
    except ValueError as e:
        print(f"✓ Rejected invalid percentage: {e}")
    
    try:
        cost = calculate_activities_cost(percentage_of_budget=-0.1, base_amount=10000)
        print("✗ Should have raised ValueError for negative percentage")
    except ValueError as e:
        print(f"✓ Rejected negative percentage: {e}")


def test_warnings_over_budget():
    """Test warning generation for over-budget trips"""
    print("\n=== Test: Warnings - Over Budget ===")
    
    warnings = generate_warnings(
        total_cost=60000,
        user_budget=50000,
        flights_cost=20000,
        hotel_cost=30000,
        nights=5
    )
    
    assert len(warnings) > 0
    assert any("exceeds budget" in w.lower() for w in warnings)
    print(f"✓ Generated {len(warnings)} warnings for over-budget trip")
    for w in warnings:
        print(f"  ⚠ {w}")


def test_warnings_high_utilization():
    """Test warning generation for high budget utilization"""
    print("\n=== Test: Warnings - High Utilization ===")
    
    warnings = generate_warnings(
        total_cost=48000,
        user_budget=50000,
        flights_cost=20000,
        hotel_cost=28000,
        nights=5
    )
    
    # 96% utilization should trigger warning
    assert any("95%" in w for w in warnings)
    print(f"✓ High utilization warning generated (96%)")


def test_warnings_no_budget():
    """Test warning generation when no budget specified"""
    print("\n=== Test: Warnings - No Budget ===")
    
    warnings = generate_warnings(
        total_cost=30000,
        user_budget=None,
        flights_cost=15000,
        hotel_cost=15000,
        nights=3
    )
    
    assert any("no budget" in w.lower() for w in warnings)
    print(f"✓ Warning for missing budget")


def test_warnings_no_flights():
    """Test warning generation when no flights selected"""
    print("\n=== Test: Warnings - No Flights ===")
    
    warnings = generate_warnings(
        total_cost=10000,
        user_budget=50000,
        flights_cost=0,
        hotel_cost=10000,
        nights=2
    )
    
    assert any("no flights" in w.lower() for w in warnings)
    print(f"✓ Warning for missing flights")


def test_warnings_no_hotels():
    """Test warning generation when no hotels for multi-night trip"""
    print("\n=== Test: Warnings - No Hotels ===")
    
    warnings = generate_warnings(
        total_cost=10000,
        user_budget=50000,
        flights_cost=10000,
        hotel_cost=0,
        nights=3
    )
    
    assert any("no hotels" in w.lower() for w in warnings)
    print(f"✓ Warning for missing hotels (3 nights)")


def test_recommendations_within_budget():
    """Test recommendations when within budget"""
    print("\n=== Test: Recommendations - Within Budget ===")
    
    recommendations = generate_recommendations(
        total_cost=40000,
        user_budget=50000,
        flights_cost=15000,
        hotel_cost=20000,
        activities_cost=5000
    )
    
    # Should suggest using remaining budget
    assert len(recommendations) > 0
    assert any("remaining" in r.lower() for r in recommendations)
    print(f"✓ Generated suggestions for remaining budget")
    for r in recommendations:
        print(f"  💡 {r}")


def test_recommendations_over_budget():
    """Test recommendations when over budget"""
    print("\n=== Test: Recommendations - Over Budget ===")
    
    recommendations = generate_recommendations(
        total_cost=60000,
        user_budget=50000,
        flights_cost=30000,  # 50% of total
        hotel_cost=25000,    # 42% of total
        activities_cost=5000
    )
    
    # Should suggest cost reductions
    assert len(recommendations) > 0
    assert any("exceeded" in r.lower() for r in recommendations)
    print(f"✓ Generated {len(recommendations)} cost reduction suggestions")
    for r in recommendations:
        print(f"  💡 {r}")


def test_recommendations_no_budget():
    """Test recommendations when no budget specified"""
    print("\n=== Test: Recommendations - No Budget ===")
    
    recommendations = generate_recommendations(
        total_cost=40000,
        user_budget=None,
        flights_cost=15000,
        hotel_cost=20000,
        activities_cost=5000
    )
    
    # Should return empty list when no budget
    assert len(recommendations) == 0
    print(f"✓ No recommendations when budget not specified")


def run_all_tests():
    """Run all minimal unit tests"""
    print("=" * 60)
    print("MINIMAL BUDGET TOOL UNIT TESTS")
    print("=" * 60)
    
    tests = [
        test_single_flight_cost,
        test_round_trip_flight_cost,
        test_multiple_flights_cost,
        test_no_flights_cost,
        test_basic_hotel_cost,
        test_hotel_cost_zero_nights,
        test_hotel_cost_negative_nights,
        test_multiple_hotels_cost,
        test_no_hotel_cost,
        test_explicit_activities_budget,
        test_percentage_activities_budget,
        test_no_activities_budget,
        test_negative_activities_validation,
        test_invalid_percentage_validation,
        test_warnings_over_budget,
        test_warnings_high_utilization,
        test_warnings_no_budget,
        test_warnings_no_flights,
        test_warnings_no_hotels,
        test_recommendations_within_budget,
        test_recommendations_over_budget,
        test_recommendations_no_budget,
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
