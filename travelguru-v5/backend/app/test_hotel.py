import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from backend.app.tools.hotel.service import search_hotels

def main():
    print("=== HOTEL SEARCH TEST ===")

    try:
        hotels = search_hotels(
            city="Goa",
            max_price=None,
            limit=5,
        )

        print("TOTAL HOTELS:", len(hotels))

        for i, h in enumerate(hotels, 1):
            print(f"\nHotel #{i}")
            print(h)

    except Exception as e:
        print("ERROR:", e)


if __name__ == "__main__":
    main()
