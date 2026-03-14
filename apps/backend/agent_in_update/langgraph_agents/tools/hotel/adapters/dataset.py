# ===== dataset.py =====
"""
Dataset adapter for hotel data.
Loads hotel data from JSON dataset file using functional approach.
"""

import json
from functools import lru_cache
from typing import List, Dict, Any, Optional
from pathlib import Path


@lru_cache(maxsize=1)
def _load_hotels_dataset(dataset_path: Path) -> List[Dict[str, Any]]:
    """
    Load and cache the hotels dataset from JSON file.
    
    Args:
        dataset_path: Path to the hotels.json dataset file
        
    Returns:
        List of raw hotel records
        
    Raises:
        FileNotFoundError: If dataset file doesn't exist
        ValueError: If dataset is invalid JSON
    """
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    try:
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("Invalid dataset format: expected array")
            
        return data
            
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in dataset: {e}") from e


def search_raw_hotels(
    dataset_path: Path,
    city: Optional[str] = None,
    min_stars: Optional[int] = None,
    max_price: Optional[int] = None,
    amenities: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Search for hotels in dataset matching criteria.
    
    Args:
        dataset_path: Path to the hotels.json dataset file
        city: Filter by city (case-insensitive)
        min_stars: Filter by minimum star rating
        max_price: Filter by maximum price per night
        amenities: Filter by required amenities (case-insensitive)
        
    Returns:
        List of raw hotel records matching criteria
    """
    # Load dataset with caching
    results = _load_hotels_dataset(dataset_path)
    
    # Apply filters
    if city:
        city_lower = city.lower()
        results = [
            h for h in results
            if str(h.get("city", "")).lower() == city_lower
        ]
    
    if min_stars is not None:
        results = [
            h for h in results
            if int(h.get("stars", 0)) >= min_stars
        ]
    
    if max_price is not None:
        results = [
            h for h in results
            if int(h.get("price_per_night", 0)) <= max_price
        ]
    
    if amenities:
        normalized_amenities = [a.lower() for a in amenities]
        results = [
            h for h in results
            if all(
                any(a.lower() == req for a in h.get("amenities", []))
                for req in normalized_amenities
            )
        ]
    
    return results
