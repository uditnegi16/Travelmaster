"""
Unit tests for Travel Agent schemas.

Run with: pytest tests/test_schemas.py
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

project_root = Path(__file__).resolve().parents[1] / "travelguru-v5" / "backend"
sys.path.insert(0, str(project_root))

from app.shared.schemas import (
    BudgetSummary,
    DayPlan,
    FlightOption,
    HotelOption,
    PlaceOption,
    TripRequest,
    TripResponse,
    TripPlan,
)


class TestFlightOption:
    """Tests for FlightOption schema."""
    
    def test_valid_flight(self):
        """Test creating a valid flight option."""
        flight = FlightOption(
            id="FL001",
            airline="IndiGo",
            origin="BOM",
            destination="DEL",
            departure_time="2026-02-15T10:00:00Z",
            arrival_time="2026-02-15T12:00:00Z",
            price=4500,
        )
        assert flight.id == "FL001"
        assert flight.price == 4500
        assert flight.origin == "BOM"
    
    def test_flight_with_optional_fields(self):
        """Test creating a flight with all fields."""
        flight = FlightOption(
            id="FL001",
            airline="IndiGo",
            origin="BOM",
            destination="DEL",
            departure_time="2026-02-15T10:00:00Z",
            arrival_time="2026-02-15T12:00:00Z",
            duration="2h 0m",
            stops=0,
            price=4500,
            currency="INR",
        )
        assert flight.duration == "2h 0m"
        assert flight.stops == 0
    
    def test_flight_immutability(self):
        """Test that FlightOption is immutable (frozen)."""
        flight = FlightOption(
            id="FL001",
            airline="IndiGo",
            origin="BOM",
            destination="DEL",
            departure_time="2026-02-15T10:00:00Z",
            arrival_time="2026-02-15T12:00:00Z",
            price=4500,
        )
        with pytest.raises(ValidationError):
            flight.price = 5000  # Should fail because model is frozen


class TestHotelOption:
    """Tests for HotelOption schema."""
    
    def test_valid_hotel(self):
        """Test creating a valid hotel option."""
        hotel = HotelOption(
            id="HOT001",
            name="Grand Hotel",
            city="Delhi",
            stars=4,
            price_per_night=3500,
            amenities=["wifi", "pool"],
            check_in="2026-02-15",
            check_out="2026-02-18",
        )
        assert hotel.stars == 4
        assert "wifi" in hotel.amenities
        assert hotel.check_in == "2026-02-15"
    
    def test_hotel_without_optional_fields(self):
        """Test creating a hotel without check-in/check-out dates."""
        hotel = HotelOption(
            id="HOT001",
            name="Grand Hotel",
            city="Delhi",
            stars=4,
            price_per_night=3500,
        )
        assert hotel.check_in is None
        assert hotel.check_out is None
    
    def test_hotel_immutability(self):
        """Test that HotelOption is immutable (frozen)."""
        hotel = HotelOption(
            id="HOT001",
            name="Grand Hotel",
            city="Delhi",
            stars=4,
            price_per_night=3500,
        )
        with pytest.raises(ValidationError):
            hotel.stars = 5  # Should fail because model is frozen


class TestPlaceOption:
    """Tests for PlaceOption schema."""
    
    def test_valid_place(self):
        """Test creating a valid place option."""
        place = PlaceOption(
            id="PLC001",
            name="Red Fort",
            city="Delhi",
            category="monument",
            rating=4.5,
            entry_fee=50,
            opening_hours="9:00 AM - 6:00 PM",
            best_time_to_visit="morning",
            recommended_duration="2-3 hours",
            address="Netaji Subhash Marg, Chandni Chowk, New Delhi",
            coordinates={"lat": 28.6562, "lng": 77.2410},
            transport_modes=["metro", "cab"],
            description="Historic 17th-century fort complex",
            special_notes="Closed on Mondays",
            weather_sensitivity="outdoor",
            crowd_level="crowded",
        )
        assert place.rating == 4.5
        assert place.coordinates is not None
        assert place.coordinates["lat"] == 28.6562
        assert place.entry_fee == 50
    
    def test_place_with_minimal_fields(self):
        """Test creating a place with only required fields."""
        place = PlaceOption(
            id="PLC001",
            name="Red Fort",
            city="Delhi",
            category="monument",
            rating=4.5,
        )
        assert place.entry_fee == 0  # Default value
        assert place.opening_hours is None
    
    def test_place_immutability(self):
        """Test that PlaceOption is immutable (frozen)."""
        place = PlaceOption(
            id="PLC001",
            name="Red Fort",
            city="Delhi",
            category="monument",
            rating=4.5,
        )
        with pytest.raises(ValidationError):
            place.rating = 5.0  # Should fail because model is frozen


class TestTripRequest:
    """Tests for TripRequest schema."""
    
    def test_valid_request(self):
        """Test creating a valid trip request."""
        request = TripRequest(
            from_city="Mumbai",
            to_city="Delhi",
            start_date="2026-02-15",
            end_date="2026-02-18",
            budget=50000,
            travelers=2,
        )
        assert request.budget == 50000
        assert request.travelers == 2
        assert request.from_city == "Mumbai"
        assert request.to_city == "Delhi"
    
    def test_request_with_preferences(self):
        """Test creating a request with preferences."""
        request = TripRequest(
            from_city="Mumbai",
            to_city="Delhi",
            start_date="2026-02-15",
            end_date="2026-02-18",
            budget=50000,
            travelers=2,
            preferences={"hotel_amenities": ["wifi", "pool"], "activity_types": ["cultural", "historical"]},
        )
        assert request.preferences is not None
        assert "hotel_amenities" in request.preferences
    
    def test_default_travelers(self):
        """Test that default travelers is 1."""
        request = TripRequest(
            from_city="Mumbai",
            to_city="Delhi",
            start_date="2026-02-15",
            end_date="2026-02-18",
            budget=50000,
        )
        assert request.travelers == 1


class TestDayPlan:
    """Tests for DayPlan schema."""
    
    def test_valid_day_plan(self):
        """Test creating a valid day plan."""
        day = DayPlan(
            date="2026-02-15",
            activities=[
                PlaceOption(
                    id="PLC001",
                    name="Red Fort",
                    city="Delhi",
                    category="monument",
                    rating=4.5,
                ),
            ],
        )
        assert day.date == "2026-02-15"
        assert len(day.activities) == 1
    
    def test_empty_activities(self):
        """Test creating a day plan with no activities."""
        day = DayPlan(date="2026-02-15")
        assert len(day.activities) == 0


class TestTripResponse:
    """Tests for TripResponse schema."""
    
    def test_valid_response(self):
        """Test creating a valid trip response."""
        flight = FlightOption(
            id="FL001",
            airline="IndiGo",
            origin="BOM",
            destination="DEL",
            departure_time="2026-02-15T10:00:00Z",
            arrival_time="2026-02-15T12:00:00Z",
            price=4500,
        )
        
        hotel = HotelOption(
            id="HOT001",
            name="Grand Hotel",
            city="Delhi",
            stars=4,
            price_per_night=3500,
            check_in="2026-02-15",
            check_out="2026-02-18",
        )
        
        trip_plan = TripPlan(
            flight=flight,
            hotel=hotel,
            days=[
                DayPlan(date="2026-02-15", activities=[]),
                DayPlan(date="2026-02-16", activities=[]),
            ],
        )
        
        budget_summary = BudgetSummary(
            flights_cost=4500,
            hotel_cost=10500,
            activities_cost=2000,
            total_cost=17000,
            currency="INR",
        )
        
        response = TripResponse(
            trip_plan=trip_plan,
            budget_summary=budget_summary,
            total_cost=17000,
            currency="INR",
            narrative="Your trip from Mumbai to Delhi is planned.",
        )
        
        assert response.currency == "INR"
        assert response.total_cost == 17000
        assert response.narrative is not None
    
    def test_response_with_enrichment(self):
        """Test creating a response with analysis fields."""
        flight = FlightOption(
            id="FL001",
            airline="IndiGo",
            origin="BOM",
            destination="DEL",
            departure_time="2026-02-15T10:00:00Z",
            arrival_time="2026-02-15T12:00:00Z",
            price=4500,
        )
        
        trip_plan = TripPlan(flight=flight)
        budget_summary = BudgetSummary(
            flights_cost=4500,
            hotel_cost=0,
            activities_cost=0,
            total_cost=4500,
            currency="INR",
        )
        
        response = TripResponse(
            trip_plan=trip_plan,
            budget_summary=budget_summary,
            total_cost=4500,
            currency="INR",
            narrative="Flight booked successfully.",
            flight_analysis={"cheapest": True, "market_position": "budget"},
            budget_analysis={"within_budget": True},
        )
        
        assert response.flight_analysis is not None
        assert response.budget_analysis is not None


class TestBudgetSummary:
    """Tests for BudgetSummary schema."""
    
    def test_valid_summary(self):
        """Test creating a valid budget summary."""
        summary = BudgetSummary(
            flights_cost=4500,
            hotel_cost=10500,
            activities_cost=2000,
            total_cost=17000,
            currency="INR",
        )
        assert summary.total_cost == 17000
        assert summary.currency == "INR"
    
    def test_summary_with_enrichment(self):
        """Test creating a budget summary with enrichment."""
        summary = BudgetSummary(
            flights_cost=4500,
            hotel_cost=10500,
            activities_cost=2000,
            total_cost=17000,
            currency="INR",
        )
        # Enrichment would be added by the budget agent
        assert summary.enrichment is None  # By default

