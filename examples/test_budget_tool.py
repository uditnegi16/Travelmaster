"""
Comprehensive Integration Tests for Budget Tool

Tests the complete budget calculation functionality including:
- Flight cost calculations
- Hotel cost calculations
- Activities budget allocation
- Budget validation
- Multi-city trip scenarios
- Warnings and recommendations
- Schema compliance
"""

import sys
import os
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from travel_agent.tools.budget_tool import calculate_budget
from travel_agent.schemas import FlightOption, HotelOption


def test_basic_flight_calculation():
    """Test basic flight cost calculation"""
    print("\n=== Test: Basic Flight Calculation ===")
    
    outbound = FlightOption(
        id="FL001",
        airline="Air India",
        origin="DEL",
        destination="BOM",
        departure_time=datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2026, 3, 15, 12, 30, tzinfo=timezone.utc),
        price=5000
    )
    
    return_flight = FlightOption(
        id="FL002",
        airline="Air India",
        origin="BOM",
        destination="DEL",
        departure_time=datetime(2026, 3, 20, 18, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2026, 3, 20, 20, 30, tzinfo=timezone.utc),
        price=4500
    )
    
    result = calculate_budget(outbound_flight=outbound, return_flight=return_flight)
    
    assert result.budget_summary.flights_cost == 9500, "Flight cost should be 9500"
    assert result.total_cost == 9500, "Total should equal flights only"
    print(f"✓ Flights cost: ₹{result.budget_summary.flights_cost:,}")


def test_basic_hotel_calculation():
    """Test basic hotel cost calculation"""
    print("\n=== Test: Basic Hotel Calculation ===")
    
    hotel = HotelOption(
        id="H001",
        name="Taj Hotel",
        city="Mumbai",
        stars=5,
        price_per_night=8000,
        amenities=["WiFi", "Pool"]
    )
    
    result = calculate_budget(hotel=hotel, nights=3)
    
    assert result.budget_summary.hotels_cost == 24000, "Hotel cost should be 8000*3"
    assert result.total_cost == 24000, "Total should equal hotel only"
    print(f"✓ Hotel cost: ₹{result.budget_summary.hotels_cost:,}")

def test_complete_trip_budget():
    """Test complete trip with all components"""
    print("\n=== Test: Complete Trip Budget ===")
    
    outbound = FlightOption(
        id="FL001", airline="IndiGo", origin="DEL", destination="GOA",
        departure_time=datetime(2026, 4, 1, 8, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2026, 4, 1, 11, 0, tzinfo=timezone.utc),
        price=6000
    )
    
    return_flight = FlightOption(
        id="FL002", airline="IndiGo", origin="GOA", destination="DEL",
        departure_time=datetime(2026, 4, 5, 20, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2026, 4, 5, 23, 0, tzinfo=timezone.utc),
        price=5500
    )
    
    hotel = HotelOption(
        id="H001", name="Beach Resort", city="Goa",
        stars=4, price_per_night=5000, amenities=["WiFi", "Pool", "Beach"]
    )
    
    result = calculate_budget(
        outbound_flight=outbound,
        return_flight=return_flight,
        hotel=hotel,
        nights=4,
        activities_budget=8000,
        user_budget=50000
    )
    
    expected_flights = 11500
    expected_hotel = 20000
    expected_activities = 8000
    expected_total = 39500
    
    assert result.budget_summary.flights_cost == expected_flights
    assert result.budget_summary.hotels_cost == expected_hotel
    assert result.budget_summary.activities_cost == expected_activities
    assert result.total_cost == expected_total
    assert result.is_within_budget is True
    assert result.budget_remaining == 10500
    
    print(f"✓ Flights: ₹{result.budget_summary.flights_cost:,}")
    print(f"✓ Hotel: ₹{result.budget_summary.hotels_cost:,}")
    print(f"✓ Activities: ₹{result.budget_summary.activities_cost:,}")
    print(f"✓ Total: ₹{result.total_cost:,}")
    print(f"✓ Within budget: {result.is_within_budget}")
    print(f"✓ Remaining: ₹{result.budget_remaining:,}")


def test_budget_exceeded():
    """Test budget validation when cost exceeds budget"""
    print("\n=== Test: Budget Exceeded ===")
    
    hotel = HotelOption(
        id="H001", name="Luxury Resort", city="Maldives",
        stars=5, price_per_night=15000, amenities=["All Inclusive"]
    )
    
    result = calculate_budget(
        hotel=hotel,
        nights=5,
        user_budget=50000
    )
    
    assert result.total_cost == 75000
    assert result.is_within_budget is False
    assert result.budget_remaining == -25000
    assert len(result.warnings) > 0
    assert len(result.recommendations) > 0
    
    print(f"✓ Total: ₹{result.total_cost:,}")
    print(f"✓ Budget: ₹{result.user_budget:,}")
    print(f"✓ Over by: ₹{abs(result.budget_remaining):,}")
    print(f"✓ Warnings: {len(result.warnings)}")
    print(f"✓ Recommendations: {len(result.recommendations)}")
    
    for warning in result.warnings:
        print(f"  ⚠ {warning}")


def test_no_budget_specified():
    """Test calculation without user budget"""
    print("\n=== Test: No Budget Specified ===")
    
    hotel = HotelOption(
        id="H001", name="Hotel", city="Delhi",
        stars=3, price_per_night=3000, amenities=["WiFi"]
    )
    
    result = calculate_budget(hotel=hotel, nights=2)
    
    assert result.user_budget is None
    assert result.is_within_budget is True  # No budget = no constraint
    assert result.budget_utilization_percent == 0.0
    assert "No budget specified" in result.warnings[0]
    
    print(f"✓ Total: ₹{result.total_cost:,}")
    print(f"✓ No budget validation (as expected)")


def test_multi_city_trip():
    """Test multi-city trip with multiple flights and hotels"""
    print("\n=== Test: Multi-City Trip ===")
    
    # Main segment
    flight1 = FlightOption(
        id="FL001", airline="Air India", origin="DEL", destination="BOM",
        departure_time=datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2026, 5, 1, 10, 30, tzinfo=timezone.utc),
        price=5000
    )
    
    hotel1 = HotelOption(
        id="H001", name="Mumbai Hotel", city="Mumbai",
        stars=4, price_per_night=6000, amenities=["WiFi"]
    )
    
    # Additional segments
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
    
    hotel2 = HotelOption(
        id="H002", name="Goa Resort", city="Goa",
        stars=5, price_per_night=8000, amenities=["Pool", "Beach"]
    )
    
    result = calculate_budget(
        outbound_flight=flight1,
        hotel=hotel1,
        nights=2,
        additional_flights=[flight2, flight3],
        additional_hotels=[(hotel2, 3)],
        user_budget=60000
    )
    
    expected_flights = 5000 + 3500 + 4000  # 12500
    expected_hotels = (6000 * 2) + (8000 * 3)  # 12000 + 24000 = 36000
    expected_total = 48500
    
    assert result.budget_summary.flights_cost == expected_flights
    assert result.budget_summary.hotels_cost == expected_hotels
    assert result.total_cost == expected_total
    assert result.is_within_budget is True
    
    print(f"✓ Multi-city flights: ₹{result.budget_summary.flights_cost:,}")
    print(f"✓ Multi-city hotels: ₹{result.budget_summary.hotels_cost:,}")
    print(f"✓ Total: ₹{result.total_cost:,}")


def test_activities_budget_allocation():
    """Test activities budget calculation"""
    print("\n=== Test: Activities Budget Allocation ===")
    
    # Explicit activities budget
    result1 = calculate_budget(activities_budget=10000)
    assert result1.budget_summary.activities_cost == 10000
    print(f"✓ Explicit activities budget: ₹{result1.budget_summary.activities_cost:,}")
    
    # No activities budget
    result2 = calculate_budget()
    assert result2.budget_summary.activities_cost == 0
    print(f"✓ No activities budget: ₹{result2.budget_summary.activities_cost:,}")


def test_zero_nights_hotel():
    """Test hotel calculation with zero nights"""
    print("\n=== Test: Zero Nights Hotel ===")
    
    hotel = HotelOption(
        id="H001", name="Hotel", city="Delhi",
        stars=3, price_per_night=3000, amenities=[]
    )
    
    result = calculate_budget(hotel=hotel, nights=0)
    
    assert result.budget_summary.hotels_cost == 0
    print(f"✓ Zero nights: ₹{result.budget_summary.hotels_cost:,}")


def test_negative_nights_validation():
    """Test validation for negative nights"""
    print("\n=== Test: Negative Nights Validation ===")
    
    hotel = HotelOption(
        id="H001", name="Hotel", city="Delhi",
        stars=3, price_per_night=3000, amenities=[]
    )
    
    try:
        result = calculate_budget(hotel=hotel, nights=-1)
        print("✗ Should have raised ValueError for negative nights")
    except ValueError as e:
        print(f"✓ Rejected negative nights: {e}")


def test_negative_budget_validation():
    """Test validation for negative budget"""
    print("\n=== Test: Negative Budget Validation ===")
    
    try:
        result = calculate_budget(user_budget=-5000)
        print("✗ Should have raised ValueError for negative budget")
    except ValueError as e:
        print(f"✓ Rejected negative budget: {e}")


def test_budget_utilization_calculation():
    """Test budget utilization percentage"""
    print("\n=== Test: Budget Utilization Percentage ===")
    
    hotel = HotelOption(
        id="H001", name="Hotel", city="Delhi",
        stars=3, price_per_night=4000, amenities=[]
    )
    
    # 80% utilization
    result = calculate_budget(hotel=hotel, nights=2, user_budget=10000)
    assert result.total_cost == 8000
    assert result.budget_utilization_percent == 80.0
    print(f"✓ 80% utilization: {result.budget_utilization_percent:.1f}%")
    
    # >95% utilization (should trigger warning)
    result2 = calculate_budget(hotel=hotel, nights=2, user_budget=8200)
    assert result2.budget_utilization_percent > 95.0
    assert any("95%" in w for w in result2.warnings)
    print(f"✓ High utilization warning: {result2.budget_utilization_percent:.1f}%")


def test_schema_validation():
    """Test BudgetSummary schema compliance"""
    print("\n=== Test: Schema Validation ===")
    
    hotel = HotelOption(
        id="H001", name="Hotel", city="Mumbai",
        stars=4, price_per_night=5000, amenities=[]
    )
    
    result = calculate_budget(hotel=hotel, nights=2, activities_budget=3000)
    
    # Check BudgetSummary has required fields
    assert hasattr(result.budget_summary, 'flights_cost')
    assert hasattr(result.budget_summary, 'hotels_cost')
    assert hasattr(result.budget_summary, 'activities_cost')
    assert hasattr(result.budget_summary, 'total_cost')
    
    assert result.budget_summary.total_cost == result.total_cost
    
    print(f"✓ BudgetSummary schema valid")
    print(f"  - flights_cost: ₹{result.budget_summary.flights_cost:,}")
    print(f"  - hotels_cost: ₹{result.budget_summary.hotels_cost:,}")
    print(f"  - activities_cost: ₹{result.budget_summary.activities_cost:,}")
    print(f"  - total_cost: ₹{result.budget_summary.total_cost:,}")


def test_recommendations_generation():
    """Test that recommendations are generated for over-budget trips"""
    print("\n=== Test: Recommendations Generation ===")
    
    outbound = FlightOption(
        id="FL001", airline="Air India", origin="DEL", destination="BOM",
        departure_time=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2026, 6, 1, 12, 30, tzinfo=timezone.utc),
        price=20000
    )
    
    hotel = HotelOption(
        id="H001", name="Hotel", city="Mumbai",
        stars=5, price_per_night=10000, amenities=[]
    )
    
    result = calculate_budget(
        outbound_flight=outbound,
        hotel=hotel,
        nights=3,
        activities_budget=5000,
        user_budget=40000
    )
    
    # Total: 20000 + 30000 + 5000 = 55000 (over budget)
    assert result.is_within_budget is False
    assert len(result.recommendations) > 0
    
    print(f"✓ Generated {len(result.recommendations)} recommendations:")
    for rec in result.recommendations:
        print(f"  💡 {rec}")


def run_all_tests():
    """Run all test cases"""
    print("=" * 60)
    print("COMPREHENSIVE BUDGET TOOL INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        test_basic_flight_calculation,
        test_basic_hotel_calculation,
        test_complete_trip_budget,
        test_budget_exceeded,
        test_no_budget_specified,
        test_multi_city_trip,
        test_activities_budget_allocation,
        test_zero_nights_hotel,
        test_negative_nights_validation,
        test_negative_budget_validation,
        test_budget_utilization_calculation,
        test_schema_validation,
        test_recommendations_generation,
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
