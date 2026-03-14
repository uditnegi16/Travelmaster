"""Dataset adapter for places data."""

import json
import logging
from functools import lru_cache
from pathlib import Path

from core.config import PLACES_DATASET_PATH

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_places_dataset() -> list[dict]:
    """Load and cache the places dataset from JSON file."""
    try:
        path = Path(PLACES_DATASET_PATH)
        if not path.exists():
            logger.error(f"Places dataset not found at {PLACES_DATASET_PATH}")
            return []
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            logger.error("Places dataset must be a JSON array")
            return []
        
        logger.info(f"Loaded {len(data)} places from dataset")
        return data
    except Exception as e:
        logger.error(f"Failed to load places dataset: {e}")
        return []


def search_raw_places(
    city: str,
    category: str | None = None,
    max_entry_fee: int | None = None
) -> list[dict]:
    """
    Search places in the dataset.
    
    Args:
        city: City to search in (case-insensitive)
        category: Optional category filter (case-insensitive exact match)
        max_entry_fee: Optional maximum entry fee filter
    
    Returns:
        List of raw place dictionaries matching the criteria
    """
    dataset = _load_places_dataset()
    
    city_normalized = city.strip().lower()
    category_normalized = category.strip().lower() if category else None
    
    results = []
    
    for place in dataset:
        if not isinstance(place, dict):
            continue
        
        # City matching (case-insensitive)
        place_city = place.get("city", "").strip().lower()
        if place_city != city_normalized:
            continue
        
        # Category matching (case-insensitive exact match)
        if category_normalized:
            place_category = place.get("category", "").strip().lower()
            if place_category != category_normalized:
                continue
        
        # Entry fee filtering
        if max_entry_fee is not None:
            try:
                place_fee = int(place.get("entry_fee", 0))
                if place_fee > max_entry_fee:
                    continue
            except (ValueError, TypeError):
                logger.warning(f"Invalid entry_fee for place {place.get('place_id')}")
                continue
        
        results.append(place)
    
    logger.info(f"Found {len(results)} places for city={city}, category={category}, max_entry_fee={max_entry_fee}")
    return results
