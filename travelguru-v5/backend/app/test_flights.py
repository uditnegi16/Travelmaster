import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from backend.app.tools.flight.service import search_flights

if __name__ == "__main__":
    try:
        print("Searching for flights...")
        res = search_flights(
            from_city="Goa",
            to_city="Mumbai",
            date="2026-01-14",
            max_price=None,
            limit=5,
        )

        print("TOTAL OPTIONS:", len(res))
        
        if len(res) > 0:
            print(f"First flight price: {res[0].price}")

        for f in res:
            print("----")
            print(f)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()