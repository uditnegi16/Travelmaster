"""
Place Knowledge Integration Module
Integrates place knowledge system with enrichment layer
"""

import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI

from backend.app.shared.schemas import PlaceOption
from .orchestrator import get_place_knowledge

logger = logging.getLogger(__name__)


def create_knowledge_enhanced_contextual_info(
    place: PlaceOption,
    profile: Dict[str, Any],
    openai_client: Optional[OpenAI] = None,
    use_knowledge_system: bool = True
) -> Dict[str, Any]:
    """
    Create knowledge-enhanced contextual information for a place.
    
    This integrates the Wikipedia + GPT knowledge system with the enrichment layer.
    Falls back to basic enrichment if knowledge system fails.
    
    Args:
        place: Place to enrich
        profile: Category profile with baseline intelligence
        openai_client: OpenAI client instance
        use_knowledge_system: Whether to use knowledge system
    
    Returns:
        Dictionary with contextual info fields compatible with ContextualInfo schema
    """
    if not use_knowledge_system:
        return _create_basic_contextual_info(place, profile)
    
    try:
        knowledge = get_place_knowledge(
            place_name=place.name,
            city=place.city,
            category=place.category,
            openai_client=openai_client
        )
        
        if knowledge:
            return {
                "place_name": place.name,
                "category": place.category,
                "short_summary": knowledge.short_summary or f"{place.rating}★ rated {place.category} in {place.city}",
                "detailed_description": knowledge.long_description or f"{place.name} is a renowned {place.category} located in {place.city}, attracting visitors with its {place.rating}★ rating and cultural appeal.",
                "historical_significance": knowledge.historical_significance,
                "cultural_significance": knowledge.cultural_significance,
                "architectural_significance": None,
                "why_visit": knowledge.why_visit or [],
                "what_makes_special": _extract_special_from_famous_for(knowledge.famous_for) or _get_basic_special_features(place),
                "famous_for": knowledge.famous_for or [],
                "experience_type": profile.get("experience", "cultural"),
                "must_see_features": [],
                "interesting_facts": knowledge.interesting_facts or []
            }
        else:
            logger.warning(f"Knowledge system returned None for {place.name}, using basic info")
            return _create_basic_contextual_info(place, profile)
            
    except Exception as e:
        logger.warning(f"Knowledge enrichment failed for {place.name}: {e}")
        return _create_basic_contextual_info(place, profile)


def _create_basic_contextual_info(place: PlaceOption, profile: Dict[str, Any]) -> Dict[str, Any]:
    """Create basic contextual info without knowledge system."""
    return {
        "place_name": place.name,
        "category": place.category,
        "short_summary": f"{place.rating}★ rated {place.category} in {place.city}",
        "detailed_description": f"{place.name} is a renowned {place.category} located in {place.city}, attracting visitors with its {place.rating}★ rating and cultural appeal.",
        "historical_significance": None,
        "cultural_significance": None,
        "architectural_significance": None,
        "why_visit": [f"Highly rated {place.category}", f"{place.rating}★ rating"],
        "what_makes_special": _get_basic_special_features(place),
        "famous_for": [],
        "experience_type": profile.get("experience", "cultural"),
        "must_see_features": [],
        "interesting_facts": []
    }


def _get_basic_special_features(place: PlaceOption) -> str:
    """Generate basic special features from place data."""
    features = []
    
    if place.rating >= 4.5:
        features.append(f"Exceptional {place.rating}★ rating")
    elif place.rating >= 4.0:
        features.append(f"High {place.rating}★ rating")
    
    if place.entry_fee == 0:
        features.append("free entry")
    
    if not features:
        features.append(f"Popular {place.category}")
    
    return ", ".join(features)


def _extract_special_from_famous_for(famous_for: List[str]) -> str:
    """Extract what makes place special from famous_for list."""
    if not famous_for:
        return ""
    return ", ".join(famous_for[:3])

