import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from backend.app.tools.places.service import search_places

def main():
    print("=== PLACES SEARCH TEST ===")

    try:
        places = search_places(
            city="New Delhi",
            radius_km=10,
            limit=10,
            min_rating=4.0,
        )

        print("TOTAL PLACES:", len(places))

        for i, p in enumerate(places, 1):
            print(f"\nPlace #{i}")
            print(p)

    except Exception as e:
        print("ERROR:", e)


if __name__ == "__main__":
    main()
