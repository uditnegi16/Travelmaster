"""
Unit tests for Travel Agent schemas.

Run with: pytest tests/test_schemas.py
"""

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from backend.travel_agent.schemas import (
    BudgetSummary,
    DayPlan,
    FlightOption,
    HotelOption,
    PlaceOption,
    TripRequest,
    TripResponse,
)


class TestFlightOption:
    """Tests for FlightOption schema."""
    
    def test_valid_flight(self):
        """Test creating a valid flight option."""
        flight = FlightOption(
            id="FL001",
            airline="IndiGo",
            origin="Mumbai",
            destination="Delhi",
            departure_time=datetime(2026, 2, 15, 10, 0, tzinfo=timezone.utc),
            arrival_time=datetime(2026, 2, 15, 12, 0, tzinfo=timezone.utc),
            price=4500,
        )
        assert flight.id == "FL001"
        assert flight.price == 4500
    
    def test_negative_price_rejected(self):
        """Test that negative prices are rejected."""
        with pytest.raises(ValidationError):
            FlightOption(
                id="FL001",
                airline="IndiGo",
                origin="Mumbai",
                destination="Delhi",
                departure_time=datetime(2026, 2, 15, 10, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2026, 2, 15, 12, 0, tzinfo=timezone.utc),
                price=-100,  # Invalid
            )
    
    def test_arrival_before_departure_rejected(self):
        """Test that arrival before departure is rejected."""
        with pytest.raises(ValidationError):
            FlightOption(
                id="FL001",
                airline="IndiGo",
                origin="Mumbai",
                destination="Delhi",
                departure_time=datetime(2026, 2, 15, 12, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2026, 2, 15, 10, 0, tzinfo=timezone.utc),  # Before departure
                price=4500,
            )


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
        )
        assert hotel.stars == 4
        assert "wifi" in hotel.amenities
    
    def test_invalid_star_rating(self):
        """Test that star ratings outside 1-5 are rejected."""
        with pytest.raises(ValidationError):
            HotelOption(
                id="HOT001",
                name="Grand Hotel",
                city="Delhi",
                stars=6,  # Invalid - max is 5
                price_per_night=3500,
            )
        
        with pytest.raises(ValidationError):
            HotelOption(
                id="HOT001",
                name="Grand Hotel",
                city="Delhi",
                stars=0,  # Invalid - min is 1
                price_per_night=3500,
            )


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
            lat=28.6562,
            lon=77.2410,
        )
        assert place.rating == 4.5
        assert place.lat == 28.6562
    
    def test_rating_bounds(self):
        """Test that ratings outside 0-5 are rejected."""
        with pytest.raises(ValidationError):
            PlaceOption(
                id="PLC001",
                name="Red Fort",
                city="Delhi",
                category="monument",
                rating=5.5,  # Invalid - max is 5.0
            )


class TestTripRequest:
    """Tests for TripRequest schema."""
    
    def test_valid_request(self):
        """Test creating a valid trip request."""
        request = TripRequest(
            origin_city="Mumbai",
            destination_city="Delhi",
            start_date=date(2026, 2, 15),
            end_date=date(2026, 2, 18),
            budget=50000,
            travelers=2,
        )
        assert request.budget == 50000
        assert request.travelers == 2
    
    def test_end_before_start_rejected(self):
        """Test that end date before start date is rejected."""
        with pytest.raises(ValidationError):
            TripRequest(
                origin_city="Mumbai",
                destination_city="Delhi",
                start_date=date(2026, 2, 18),
                end_date=date(2026, 2, 15),  # Before start
                budget=50000,
                travelers=2,
            )


class TestTripResponse:
    """Tests for TripResponse schema."""
    
    def test_valid_response(self):
        """Test creating a valid trip response."""
        flight = FlightOption(
            id="FL001",
            airline="IndiGo",
            origin="Mumbai",
            destination="Delhi",
            departure_time=datetime(2026, 2, 15, 10, 0, tzinfo=timezone.utc),
            arrival_time=datetime(2026, 2, 15, 12, 0, tzinfo=timezone.utc),
            price=4500,
        )
        
        hotel = HotelOption(
            id="HOT001",
            name="Grand Hotel",
            city="Delhi",
            stars=4,
            price_per_night=3500,
        )
        
        response = TripResponse(
            selected_flight=flight,
            selected_hotel=hotel,
            total_cost=15000,
            currency="INR",
        )
        
        assert response.currency == "INR"
        assert response.total_cost == 15000
    
    def test_currency_uppercase_conversion(self):
        """Test that currency code is converted to uppercase."""
        flight = FlightOption(
            id="FL001",
            airline="IndiGo",
            origin="Mumbai",
            destination="Delhi",
            departure_time=datetime(2026, 2, 15, 10, 0, tzinfo=timezone.utc),
            arrival_time=datetime(2026, 2, 15, 12, 0, tzinfo=timezone.utc),
            price=4500,
        )
        
        hotel = HotelOption(
            id="HOT001",
            name="Grand Hotel",
            city="Delhi",
            stars=4,
            price_per_night=3500,
        )
        
        response = TripResponse(
            selected_flight=flight,
            selected_hotel=hotel,
            total_cost=15000,
            currency="inr",  # lowercase
        )
        
        assert response.currency == "INR"  # Should be uppercase
    
    def test_itinerary_validation_strict(self):
        """Test that strict itinerary validation works."""
        flight = FlightOption(
            id="FL001",
            airline="IndiGo",
            origin="Mumbai",
            destination="Delhi",
            departure_time=datetime(2026, 2, 15, 10, 0, tzinfo=timezone.utc),
            arrival_time=datetime(2026, 2, 15, 12, 0, tzinfo=timezone.utc),
            price=4500,
        )
        
        hotel = HotelOption(
            id="HOT001",
            name="Grand Hotel",
            city="Delhi",
            stars=4,
            price_per_night=3500,
        )
        
        # Invalid: day numbers not sequential
        with pytest.raises(ValidationError):
            TripResponse(
                selected_flight=flight,
                selected_hotel=hotel,
                itinerary=[
                    DayPlan(day_number=1, date=date(2026, 2, 15), places=[]),
                    DayPlan(day_number=3, date=date(2026, 2, 16), places=[]),  # Skips day 2
                ],
                total_cost=15000,
                strict_itinerary_validation=True,
            )
    
    def test_itinerary_validation_flexible(self):
        """Test that flexible itinerary validation allows gaps."""
        flight = FlightOption(
            id="FL001",
            airline="IndiGo",
            origin="Mumbai",
            destination="Delhi",
            departure_time=datetime(2026, 2, 15, 10, 0, tzinfo=timezone.utc),
            arrival_time=datetime(2026, 2, 15, 12, 0, tzinfo=timezone.utc),
            price=4500,
        )
        
        hotel = HotelOption(
            id="HOT001",
            name="Grand Hotel",
            city="Delhi",
            stars=4,
            price_per_night=3500,
        )
        
        # Should work with strict_itinerary_validation=False
        response = TripResponse(
            selected_flight=flight,
            selected_hotel=hotel,
            itinerary=[
                DayPlan(day_number=1, date=date(2026, 2, 15), places=[]),
                DayPlan(day_number=3, date=date(2026, 2, 17), places=[]),  # Gap is OK
            ],
            total_cost=15000,
            strict_itinerary_validation=False,  # Flexible mode
        )
        
        assert len(response.itinerary) == 2


class TestBudgetSummary:
    """Tests for BudgetSummary schema."""
    
    def test_valid_summary(self):
        """Test creating a valid budget summary."""
        summary = BudgetSummary(
            flights_cost=4500,
            hotels_cost=10500,
            activities_cost=2000,
            total_cost=17000,
        )
        assert summary.total_cost == 17000
    
    def test_negative_costs_rejected(self):
        """Test that negative costs are rejected."""
        with pytest.raises(ValidationError):
            BudgetSummary(
                flights_cost=-100,  # Invalid
                hotels_cost=10500,
                total_cost=10400,
            )
