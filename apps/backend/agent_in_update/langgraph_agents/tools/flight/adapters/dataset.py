"""
Dataset adapter for flight data.
Loads flight data from JSON dataset file using functional approach.
"""

import json
from functools import lru_cache
from typing import List, Dict, Any, Optional
from pathlib import Path


@lru_cache(maxsize=1)
def _load_flights_dataset(dataset_path: Path) -> List[Dict[str, Any]]:
    """
    Load and cache the flights dataset from JSON file.
    
    Args:
        dataset_path: Path to the flights.json dataset file
        
    Returns:
        List of raw flight records
        
    Raises:
        FileNotFoundError: If dataset file doesn't exist
        ValueError: If dataset is invalid JSON
    """
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    try:
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Handle both array format and object with flights key
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "flights" in data:
            return data["flights"]
        else:
            raise ValueError("Invalid dataset format")
            
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in dataset: {e}") from e


def search_raw_flights(
    dataset_path: Path,
    from_city: Optional[str] = None,
    to_city: Optional[str] = None,
    max_price: Optional[int] = None,
    date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for flights in dataset matching criteria.
    
    Args:
        dataset_path: Path to the flights.json dataset file
        from_city: Filter by departure city (case-insensitive)
        to_city: Filter by arrival city (case-insensitive)
        max_price: Filter by maximum price
        date: Filter by departure date (ISO format prefix match)
        
    Returns:
        List of raw flight records matching criteria
    """
    # Load dataset with caching
    results = _load_flights_dataset(dataset_path)
    
    # Apply filters
    if from_city:
        from_city_lower = from_city.lower()
        results = [
            f for f in results
            if str(f.get("from", f.get("from_city", ""))).lower() == from_city_lower
        ]
    
    if to_city:
        to_city_lower = to_city.lower()
        results = [
            f for f in results
            if str(f.get("to", f.get("to_city", ""))).lower() == to_city_lower
        ]
    
    if max_price is not None:
        results = [
            f for f in results
            if int(f.get("price", 0)) <= max_price
        ]
    
    if date:
        results = [
            f for f in results
            if str(f.get("departure_time", "")).startswith(date)
        ]
    
    return results


