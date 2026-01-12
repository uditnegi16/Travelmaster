"""
Example usage of the Travel Agent schemas.

This module demonstrates how to construct valid TripResponse objects
from sample FlightOption and HotelOption data, validating that adapters
produce correct outputs.
"""

from datetime import date, datetime, timezone

from backend.travel_agent.schemas import (
    BudgetSummary,
    DayPlan,
    FlightOption,
    HotelOption,
    PlaceOption,
    TripRequest,
    TripResponse,
)


def example_trip_request() -> TripRequest:
    """Create a sample trip request."""
    return TripRequest(
        origin_city="Mumbai",
        destination_city="Delhi",
        start_date=date(2026, 2, 15),
        end_date=date(2026, 2, 18),
        budget=50000,  # ₹50,000
        travelers=2,
        preferences=["cultural sites", "fine dining", "museums"],
    )


def example_flight_option() -> FlightOption:
    """Create a sample flight option from dataset-like data."""
    return FlightOption(
        id="FL0001",
        airline="IndiGo",
        origin="Mumbai",
        destination="Delhi",
        departure_time=datetime(2026, 2, 15, 10, 30, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2026, 2, 15, 12, 45, 0, tzinfo=timezone.utc),
        price=4500,  # ₹4,500
    )


def example_hotel_option() -> HotelOption:
    """Create a sample hotel option from dataset-like data."""
    return HotelOption(
        id="HOT0042",
        name="Grand Palace Hotel",
        city="Delhi",
        stars=4,
        price_per_night=3500,  # ₹3,500 per night
        amenities=["wifi", "pool", "breakfast", "gym"],
    )


def example_place_options() -> list[PlaceOption]:
    """Create sample place options for itinerary."""
    return [
        PlaceOption(
            id="PLC0001",
            name="Red Fort",
            city="Delhi",
            category="historical monument",
            rating=4.5,
            lat=28.6562,
            lon=77.2410,
        ),
        PlaceOption(
            id="PLC0002",
            name="India Gate",
            city="Delhi",
            category="monument",
            rating=4.3,
            lat=28.6129,
            lon=77.2295,
        ),
        PlaceOption(
            id="PLC0003",
            name="Qutub Minar",
            city="Delhi",
            category="historical monument",
            rating=4.4,
            lat=28.5245,
            lon=77.1855,
        ),
    ]


def example_trip_response() -> TripResponse:
    """
    Create a complete sample trip response.
    
    This demonstrates the full structure that the orchestrator should produce.
    """
    flight = example_flight_option()
    hotel = example_hotel_option()
    places = example_place_options()
    
    # 3-night trip (4 days: Feb 15-18)
    nights = 3
    hotel_cost = hotel.price_per_night * nights
    
    itinerary = [
        DayPlan(
            day_number=1,
            date=date(2026, 2, 15),
            places=[places[0]],
            notes="Arrival day - visit Red Fort in afternoon",
        ),
        DayPlan(
            day_number=2,
            date=date(2026, 2, 16),
            places=[places[1]],
            notes="Full day exploring India Gate area",
        ),
        DayPlan(
            day_number=3,
            date=date(2026, 2, 17),
            places=[places[2]],
            notes="Visit Qutub Minar complex",
        ),
        DayPlan(
            day_number=4,
            date=date(2026, 2, 18),
            places=[],
            notes="Departure day - morning checkout",
        ),
    ]
    
    budget_summary = BudgetSummary(
        flights_cost=flight.price,
        hotels_cost=hotel_cost,
        activities_cost=2000,  # ₹2,000 estimated
        total_cost=flight.price + hotel_cost + 2000,
    )
    
    return TripResponse(
        selected_flight=flight,
        selected_hotel=hotel,
        start_date=date(2026, 2, 15),
        end_date=date(2026, 2, 18),
        itinerary=itinerary,
        nights=nights,
        budget_summary=budget_summary,
        total_cost=budget_summary.total_cost,
        currency="INR",
        warnings=[
            "Budget allows for comfortable trip with some flexibility",
            "Book Red Fort tickets in advance to avoid queues",
        ],
        candidate_flights=None,  # Could include alternatives here
        candidate_hotels=None,
    )


def validate_example():
    """Run validation on example data to ensure schemas work correctly."""
    print("Creating example TripRequest...")
    request = example_trip_request()
    print(f"✓ TripRequest valid: {request.origin_city} → {request.destination_city}")
    
    print("\nCreating example FlightOption...")
    flight = example_flight_option()
    print(f"✓ FlightOption valid: {flight.airline} {flight.id}, ₹{flight.price}")
    
    print("\nCreating example HotelOption...")
    hotel = example_hotel_option()
    print(f"✓ HotelOption valid: {hotel.name}, {hotel.stars}★, ₹{hotel.price_per_night}/night")
    
    print("\nCreating example TripResponse...")
    response = example_trip_response()
    print(f"✓ TripResponse valid: {len(response.itinerary)} days, ₹{response.total_cost} total")
    print(f"  Flight: {response.selected_flight.airline}")
    print(f"  Hotel: {response.selected_hotel.name}")
    print(f"  Nights: {response.nights}")
    if response.budget_summary:
        print(f"  Budget breakdown:")
        print(f"    Flights: ₹{response.budget_summary.flights_cost}")
        print(f"    Hotels: ₹{response.budget_summary.hotels_cost}")
        print(f"    Activities: ₹{response.budget_summary.activities_cost}")
    
    print("\n✓ All schemas validated successfully!")
    return response


if __name__ == "__main__":
    # Run validation when script is executed directly
    validate_example()
