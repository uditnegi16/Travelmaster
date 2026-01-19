import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from backend.app.tools.places.service import search_places

def test_multiple_cities():
    """Test places search for multiple cities to ensure comprehensive fix."""
    cities_to_test = [
        ("Goa", 40),
        ("Delhi", 20),
        ("Mumbai", 15),
    ]
    
    for city, radius in cities_to_test:
        print(f"\n{'='*60}")
        print(f"Testing: {city} (radius={radius}km)")
        print('='*60)
        
        try:
            places = search_places(
                city=city,
                radius_km=radius,
                limit=5,
                min_rating=4.0,
            )
            
            print(f"✓ Successfully retrieved {len(places)} places")
            
            if places:
                print("\nTop 5 places:")
                for i, place in enumerate(places, 1):
                    print(f"{i}. {place.name}")
                    print(f"   Category: {place.category}")
                    print(f"   Rating: {place.rating}★")
            else:
                print("⚠ No places found matching criteria")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print(f"\n{'='*60}")
    print("COMPREHENSIVE TEST COMPLETE")
    print('='*60)


if __name__ == "__main__":
    test_multiple_cities()
