"""
Place Knowledge Schemas
Production-grade structured knowledge representation for tourist places
"""

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field


class PlaceKnowledge(BaseModel):
    """
    Comprehensive structured knowledge about a tourist place.
    This is the single source of truth for all place information.
    """
    # Identity
    name: str = Field(..., description="Official name of the place")
    city: str = Field(..., description="City where the place is located")
    category: str = Field(..., description="Category (e.g., temple, museum, park, monument)")
    
    # Core descriptions
    short_summary: str = Field(..., description="One-line summary (50-100 chars)")
    long_description: str = Field(..., description="Comprehensive 3-5 sentence description")
    
    # Why visit
    why_visit: List[str] = Field(
        default_factory=list,
        description="Top 3-5 compelling reasons to visit",
        min_length=3,
        max_length=5
    )
    famous_for: List[str] = Field(
        default_factory=list,
        description="What this place is famous for (architecture, history, views, etc.)",
        min_length=2,
        max_length=5
    )
    
    # When to visit
    best_time_to_visit: str = Field(
        ...,
        description="Best time to visit (e.g., 'Early morning for sunrise', 'October-March', 'Weekdays to avoid crowds')"
    )
    time_required: str = Field(
        ...,
        description="How much time to allocate (e.g., '1-2 hours', '2-3 hours', 'Half day')"
    )
    
    # Who should visit
    suitable_for: Dict[str, str] = Field(
        default_factory=dict,
        description="""
        Suitability for different traveler types with reasons.
        Keys: couples, families, kids, solo, elderly
        Values: rating with reason (e.g., 'Excellent - romantic ambiance and scenic views')
        """
    )
    
    # Historical & cultural context
    historical_significance: Optional[str] = Field(
        None,
        description="Historical background and importance (2-3 sentences)"
    )
    cultural_significance: Optional[str] = Field(
        None,
        description="Cultural or religious importance (2-3 sentences)"
    )
    
    # Interesting details
    interesting_facts: List[str] = Field(
        default_factory=list,
        description="3-5 fascinating facts that tourists would find interesting",
        max_length=5
    )
    tips: List[str] = Field(
        default_factory=list,
        description="Practical tips for visitors (best entry, what to bring, what to avoid)",
        max_length=5
    )
    
    # Crowd & weather
    crowd_info: str = Field(
        ...,
        description="Expected crowd levels and patterns (e.g., 'Very crowded on weekends', 'Peaceful in mornings')"
    )
    weather_dependency: str = Field(
        ...,
        description="Weather sensitivity (e.g., 'Indoor - weather proof', 'Best avoided during rain', 'Hot in afternoons')"
    )
    
    # Meta information
    source: Literal["wikipedia", "gpt", "hybrid"] = Field(
        ...,
        description="Source of this knowledge"
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the information quality (0.0 - 1.0)"
    )
    last_updated: Optional[str] = Field(
        None,
        description="ISO timestamp when this knowledge was generated/updated"
    )
    
    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "name": "Taj Mahal",
                "city": "Agra",
                "category": "monument",
                "short_summary": "Iconic white marble mausoleum and UNESCO World Heritage Site",
                "long_description": "The Taj Mahal is an ivory-white marble mausoleum commissioned by Mughal emperor Shah Jahan for his wife Mumtaz Mahal. It's considered the jewel of Muslim art in India and one of the universally admired masterpieces of world heritage. The monument stands on the south bank of Yamuna river and attracts millions of visitors annually.",
                "why_visit": [
                    "One of the Seven Wonders of the World",
                    "Breathtaking Mughal architecture and intricate marble inlay work",
                    "Symbol of eternal love and romance",
                    "UNESCO World Heritage Site with stunning gardens",
                    "Best example of Indo-Islamic architectural fusion"
                ],
                "famous_for": [
                    "White marble architecture that changes color with sunlight",
                    "Intricate semi-precious stone inlay work",
                    "Perfectly symmetrical design",
                    "Romantic history of Shah Jahan and Mumtaz Mahal"
                ],
                "best_time_to_visit": "Early morning (sunrise) or late afternoon for best light and fewer crowds. October to March for pleasant weather.",
                "time_required": "2-3 hours",
                "suitable_for": {
                    "couples": "Excellent - world's most romantic monument with beautiful ambiance",
                    "families": "Very Good - educational and awe-inspiring for all ages",
                    "kids": "Good - impressive but requires patience for queues and rules",
                    "solo": "Excellent - perfect for photography and peaceful contemplation",
                    "elderly": "Good - wheelchair accessible but involves some walking"
                },
                "historical_significance": "Built between 1632-1653 by Mughal Emperor Shah Jahan as a tomb for his beloved wife Mumtaz Mahal who died during childbirth. It represents the zenith of Mughal architecture and employed over 20,000 artisans.",
                "cultural_significance": "Represents the pinnacle of Mughal art and architecture. It's a UNESCO World Heritage Site and considered India's most precious cultural treasure, symbolizing love, beauty, and architectural excellence.",
                "interesting_facts": [
                    "Over 1,000 elephants were used to transport building materials",
                    "The white marble appears pink in morning, white in day, and golden at sunset",
                    "The four minarets are slightly tilted outward to protect the main tomb in case of earthquake",
                    "No photography allowed inside the main mausoleum",
                    "It took 22 years and 20,000 workers to complete"
                ],
                "tips": [
                    "Buy tickets online to skip long queues",
                    "Arrive 30 minutes before opening for best experience",
                    "Wear comfortable shoes - significant walking involved",
                    "Carry valid photo ID - mandatory for entry",
                    "Avoid Fridays (closed for prayers)",
                    "Hire audio guide for detailed historical context"
                ],
                "crowd_info": "Very crowded on weekends and holidays. Least crowded on weekdays during monsoon season. Expect 2-3 hour queues during peak season (Oct-Feb).",
                "weather_dependency": "Outdoor monument - very hot in summer (April-June). Best visited in winter (Oct-March). Stunning during full moon nights.",
                "source": "hybrid",
                "confidence_score": 0.95
            }
        }
    }


class WikipediaPage(BaseModel):
    """Raw Wikipedia page data"""
    title: str = Field(..., description="Wikipedia page title")
    summary: str = Field(..., description="Page summary/intro section")
    content: str = Field(..., description="Full page content")
    url: str = Field(..., description="Wikipedia URL")
    sections: Optional[List[str]] = Field(
        None,
        description="List of section titles in the article"
    )
    
    model_config = {"extra": "forbid"}


class KnowledgeGenerationRequest(BaseModel):
    """Request to generate place knowledge"""
    place_name: str
    city: str
    category: str
    force_regenerate: bool = Field(
        default=False,
        description="Force regeneration even if cached"
    )
    
    model_config = {"extra": "forbid"}


class KnowledgeQualityMetrics(BaseModel):
    """Quality metrics for generated knowledge"""
    completeness_score: float = Field(ge=0.0, le=1.0)
    detail_richness_score: float = Field(ge=0.0, le=1.0)
    factual_confidence: float = Field(ge=0.0, le=1.0)
    source_reliability: Literal["high", "medium", "low"]
    
    overall_quality: Literal["excellent", "good", "fair", "poor"]
    
    model_config = {"extra": "forbid"}
