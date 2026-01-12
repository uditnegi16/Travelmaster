"""
Script to build a comprehensive worldwide airports database using Amadeus API.

This script fetches airport data for major cities around the world and saves
it to a JSON file that can be used by the IATA resolver.

Usage:
    python build_airports_db.py

Requirements:
    - Amadeus API credentials set as environment variables:
      AMADEUS_CLIENT_ID
      AMADEUS_CLIENT_SECRET
    
    - Install amadeus package:
      pip install amadeus

Output:
    - airports_worldwide.json: Complete database of airports
    - airports_cache.json: Cache file for faster lookups
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.app.core.amadeus_iata import (
    search_airports,
    resolve_city_to_airport,
    save_cache_to_file,
    clear_cache,
)
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


# Major cities and airports worldwide (expandable list)
MAJOR_CITIES = [
    # Asia
    "Delhi",
    "Mumbai",
    "Bangalore",
    "Chennai",
    "Kolkata",
    "Hyderabad",
    "Pune",
    "Ahmedabad",
    "Jaipur",
    "Kochi",
    "Goa",
    "Tokyo",
    "Seoul",
    "Beijing",
    "Shanghai",
    "Hong Kong",
    "Singapore",
    "Bangkok",
    "Kuala Lumpur",
    "Jakarta",
    "Manila",
    "Taipei",
    "Dubai",
    "Abu Dhabi",
    "Doha",
    "Istanbul",
    "Tel Aviv",
    "Riyadh",
    "Kuwait City",
    "Muscat",
    # Europe
    "London",
    "Paris",
    "Berlin",
    "Madrid",
    "Rome",
    "Amsterdam",
    "Brussels",
    "Vienna",
    "Zurich",
    "Copenhagen",
    "Stockholm",
    "Oslo",
    "Helsinki",
    "Prague",
    "Budapest",
    "Warsaw",
    "Athens",
    "Lisbon",
    "Dublin",
    "Munich",
    "Frankfurt",
    "Milan",
    "Barcelona",
    "Manchester",
    "Edinburgh",
    # North America
    "New York",
    "Los Angeles",
    "Chicago",
    "Houston",
    "Phoenix",
    "Philadelphia",
    "San Antonio",
    "San Diego",
    "Dallas",
    "San Jose",
    "Austin",
    "Jacksonville",
    "San Francisco",
    "Seattle",
    "Denver",
    "Washington",
    "Boston",
    "Las Vegas",
    "Miami",
    "Atlanta",
    "Toronto",
    "Montreal",
    "Vancouver",
    "Calgary",
    "Mexico City",
    "Guadalajara",
    "Monterrey",
    # South America
    "Sao Paulo",
    "Rio de Janeiro",
    "Buenos Aires",
    "Lima",
    "Bogota",
    "Santiago",
    "Caracas",
    "Quito",
    "La Paz",
    "Montevideo",
    # Africa
    "Cairo",
    "Lagos",
    "Johannesburg",
    "Cape Town",
    "Nairobi",
    "Addis Ababa",
    "Casablanca",
    "Algiers",
    "Tunis",
    "Accra",
    # Oceania
    "Sydney",
    "Melbourne",
    "Brisbane",
    "Perth",
    "Auckland",
    "Wellington",
    "Christchurch",
]


def build_airports_database(
    cities: List[str], output_path: Path, batch_size: int = 10
) -> Dict[str, Dict]:
    """
    Build a comprehensive airports database from a list of cities.

    Args:
        cities: List of city names to fetch
        output_path: Path where the database will be saved
        batch_size: Number of cities to process before saving checkpoint

    Returns:
        Dictionary mapping normalized city names to airport data
    """
    database = {}
    failed_cities = []
    
    logger.info(f"Building airports database for {len(cities)} cities...")
    
    for idx, city in enumerate(cities, 1):
        try:
            logger.info(f"[{idx}/{len(cities)}] Fetching: {city}")
            
            airport_info = resolve_city_to_airport(city, use_cache=True)
            
            # Normalize city name for key
            normalized_key = city.strip().lower()
            
            database[normalized_key] = {
                "iata": airport_info["iata"],
                "city": airport_info["city"],
                "country": airport_info["country"],
                "airport": airport_info["airport"],
                "latitude": airport_info.get("latitude"),
                "longitude": airport_info.get("longitude"),
                "country_code": airport_info.get("country_code"),
            }
            
            # Save checkpoint every batch_size cities
            if idx % batch_size == 0:
                logger.info(f"Checkpoint: Saving {len(database)} entries...")
                save_database(database, output_path)
            
        except Exception as e:
            logger.error(f"Failed to fetch {city}: {e}")
            failed_cities.append(city)
            continue
    
    logger.info(f"Successfully fetched {len(database)} airports")
    
    if failed_cities:
        logger.warning(f"Failed to fetch {len(failed_cities)} cities: {failed_cities}")
    
    return database


def save_database(database: Dict, output_path: Path) -> None:
    """Save the database to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Saved {len(database)} entries to {output_path}")


def main():
    """Main execution function."""
    # Check for Amadeus credentials
    if not os.getenv("AMADEUS_CLIENT_ID") or not os.getenv("AMADEUS_CLIENT_SECRET"):
        logger.error(
            "Missing Amadeus credentials. Please set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET"
        )
        sys.exit(1)
    
    # Define output paths
    script_dir = Path(__file__).parent
    output_dir = script_dir / "data"
    airports_db_path = output_dir / "airports_worldwide.json"
    cache_path = output_dir / "airports_cache.json"
    
    logger.info("=" * 60)
    logger.info("Building Worldwide Airports Database")
    logger.info("=" * 60)
    logger.info(f"Total cities to fetch: {len(MAJOR_CITIES)}")
    logger.info(f"Output path: {airports_db_path}")
    logger.info("=" * 60)
    
    # Clear cache to start fresh
    clear_cache()
    
    # Build database
    database = build_airports_database(
        cities=MAJOR_CITIES,
        output_path=airports_db_path,
        batch_size=10,
    )
    
    # Final save
    save_database(database, airports_db_path)
    
    # Save cache for future use
    save_cache_to_file(cache_path)
    
    logger.info("=" * 60)
    logger.info("Database build complete!")
    logger.info(f"Total airports: {len(database)}")
    logger.info(f"Database file: {airports_db_path}")
    logger.info(f"Cache file: {cache_path}")
    logger.info("=" * 60)
    
    # Display sample entries
    logger.info("\nSample entries:")
    for idx, (city, data) in enumerate(list(database.items())[:5], 1):
        logger.info(f"{idx}. {city} -> {data['iata']} ({data['airport']})")


if __name__ == "__main__":
    main()
