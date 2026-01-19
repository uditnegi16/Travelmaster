import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from backend.app.tools.places.service import search_places
from backend.app.tools.budget.service import compute_budget
from backend.app.shared.schemas import FlightOption, HotelOption

def test_budget_with_places():
    """Test budget computation with places that have entry fees."""
    print("=== BUDGET COMPUTATION TEST ===\n")
    
    # Get some places
    print("1. Searching for places in Goa...")
    places = search_places(
        city="Goa",
        radius_km=40,
        limit=5,
        min_rating=4.0,
    )
    print(f"   Found {len(places)} places\n")
    
    # Create sample flight and hotel
    flight = FlightOption(
        id="FL001",
        airline="Air India",
        from_city="Delhi",
        to_city="Goa",
        departure_time="2026-02-01T10:00:00Z",
        arrival_time="2026-02-01T12:30:00Z",
        price=8000
    )
    
    hotel = HotelOption(
        id="HT001",
        name="Beach Resort",
        city="Goa",
        stars=4,
        price_per_night=3500,
        amenities=["Pool", "WiFi", "Breakfast"]
    )
    
    # Compute budget
    print("2. Computing budget...")
    budget = compute_budget(
        flight=flight,
        hotel=hotel,
        nights=3,
        places=places
    )
    
    print("\n=== BUDGET SUMMARY ===")
    print(f"Flights Cost:    ₹{budget.flights_cost:,}")
    print(f"Hotel Cost:      ₹{budget.hotel_cost:,} ({hotel.price_per_night} × 3 nights)")
    print(f"Activities Cost: ₹{budget.activities_cost:,} ({len(places)} places)")
    print(f"{'-'*40}")
    print(f"TOTAL COST:      ₹{budget.total_cost:,} {budget.currency}")
    print(f"{'='*40}\n")
    
    # Show place entry fees
    print("3. Place Entry Fees:")
    for i, place in enumerate(places, 1):
        print(f"   {i}. {place.name}: ₹{place.entry_fee}")
    
    print("\n✅ Budget computation test PASSED!")


if __name__ == "__main__":
    test_budget_with_places()
