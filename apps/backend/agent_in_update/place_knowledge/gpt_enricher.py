"""
GPT Enricher
Generates or summarizes tourist place knowledge using GPT/LLM
"""

import logging
import json
from typing import Optional
from datetime import datetime

from openai import OpenAI
from pydantic import ValidationError

from .schemas import PlaceKnowledge, WikipediaPage
from .client_factory import get_openai_client

logger = logging.getLogger(__name__)
import os

class GPTPlaceEnricher:
    """
    Uses GPT to:
    1. Summarize good Wikipedia content into structured tourist knowledge
    2. Generate knowledge from scratch when Wikipedia is missing/weak
    """
    
    def __init__(self, client: Optional[OpenAI] = None):
        """
        Initialize with OpenAI client.
        If client not provided, auto-initializes from core.config.
        """
        self.client = get_openai_client(client)
    
    def summarize_from_wikipedia(
        self,
        wikipedia_page: WikipediaPage,
        place_name: str,
        city: str,
        category: str
    ) -> Optional[PlaceKnowledge]:
        """
        Convert high-quality Wikipedia content into structured tourist knowledge.
        
        This is used when Wikipedia has good information - we just need to
        extract and structure it for tourist purposes.
        
        Args:
            wikipedia_page: Good quality Wikipedia page
            place_name: Name of the place
            city: City name
            category: Place category
        
        Returns:
            Structured PlaceKnowledge or None if generation fails
        """
        logger.info(f"📝 Summarizing Wikipedia content for: {place_name}")
        
        system_prompt = self._get_summarization_system_prompt()
        user_prompt = self._get_summarization_user_prompt(
            wikipedia_page,
            place_name,
            city,
            category
        )
        
        return self._generate_knowledge_with_gpt(
            system_prompt,
            user_prompt,
            place_name,
            city,
            category,
            source="hybrid"  # Wikipedia + GPT summarization
        )
    
    def generate_from_scratch(
        self,
        place_name: str,
        city: str,
        category: str
    ) -> Optional[PlaceKnowledge]:
        """
        Generate tourist knowledge from scratch using GPT's knowledge.
        
        Used when Wikipedia is missing, weak, or not tourist-focused.
        
        Args:
            place_name: Name of the place
            city: City name
            category: Place category
        
        Returns:
            Structured PlaceKnowledge or None if generation fails
        """
        logger.info(f"🤖 Generating knowledge from scratch for: {place_name}")
        
        system_prompt = self._get_generation_system_prompt()
        user_prompt = self._get_generation_user_prompt(place_name, city, category)
        
        return self._generate_knowledge_with_gpt(
            system_prompt,
            user_prompt,
            place_name,
            city,
            category,
            source="gpt"  # Pure GPT generation
        )
    
    # ============================================================================
    # GPT INTERACTION
    # ============================================================================
    
    def _generate_knowledge_with_gpt(
        self,
        system_prompt: str,
        user_prompt: str,
        place_name: str,
        city: str,
        category: str,
        source: str
    ) -> Optional[PlaceKnowledge]:
        """Core GPT interaction with structured output"""
        if self.client is None:
            logger.error("OpenAI client not initialized")
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("COMPOSER_MODEL") or os.getenv("PLANNER_MODEL") or "gpt-4o", # Use best model for quality
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Balance creativity and accuracy
                response_format={"type": "json_object"},  # Force JSON output
                max_tokens=2000
            )
            
            # Parse response
            content = response.choices[0].message.content
            knowledge_dict = json.loads(content)
            
            # Add metadata
            knowledge_dict["name"] = place_name
            knowledge_dict["city"] = city
            knowledge_dict["category"] = category
            knowledge_dict["source"] = source
            knowledge_dict["last_updated"] = datetime.utcnow().isoformat()
            
            # Validate with Pydantic
            knowledge = PlaceKnowledge(**knowledge_dict)
            
            logger.info(f"✅ Successfully generated knowledge for: {place_name}")
            return knowledge
        
        except ValidationError as e:
            logger.error(f"Validation error in GPT response: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"GPT enrichment error: {e}")
            return None
    
    # ============================================================================
    # PROMPT ENGINEERING
    # ============================================================================
    
    def _get_summarization_system_prompt(self) -> str:
        """System prompt for Wikipedia summarization"""
        return """You are a professional travel content writer who converts Wikipedia articles into tourist-friendly guides.

Your task is to extract and structure tourist-relevant information from Wikipedia content.

**Output Format**: Return a JSON object with these exact fields:
- short_summary: One-line summary (50-100 chars)
- long_description: Comprehensive 3-5 sentence description
- why_visit: Array of 3-5 compelling reasons to visit
- famous_for: Array of 2-5 things this place is famous for
- best_time_to_visit: When to visit (time of day, season, tips for avoiding crowds)
- time_required: How long to spend (e.g., "1-2 hours", "Half day")
- suitable_for: Object with keys: couples, families, kids, solo, elderly - each value is a STRING like "Excellent - romantic sunset views" or "Good - spacious for kids to play"
- historical_significance: 2-3 sentences (or null if not applicable)
- cultural_significance: 2-3 sentences (or null if not applicable)
- interesting_facts: Array of 3-5 fascinating facts
- tips: Array of 3-5 practical visitor tips
- crowd_info: Expected crowd levels and patterns
- weather_dependency: Weather sensitivity and recommendations
- confidence_score: Your confidence in the information accuracy (0.0-1.0)

**Guidelines**:
- Focus on tourist value, not academic details
- Be specific and actionable
- Highlight what makes this place unique
- Include practical tips visitors actually need
- Make it engaging and informative
- Use conversational but professional tone

Return ONLY valid JSON, no other text."""
    
    def _get_summarization_user_prompt(
        self,
        wikipedia_page: WikipediaPage,
        place_name: str,
        city: str,
        category: str
    ) -> str:
        """User prompt for Wikipedia summarization"""
        return f"""Convert this Wikipedia article into a tourist guide.

**Place Details**:
- Name: {place_name}
- City: {city}
- Category: {category}

**Wikipedia Content**:
Title: {wikipedia_page.title}

Summary:
{wikipedia_page.summary}

Full Content:
{wikipedia_page.content[:4000]}  # Limit to prevent token overflow

**Task**: Extract and structure this information into the required JSON format.
Focus on tourist value: why visit, when to visit, who should visit, practical tips, interesting facts.

Return the JSON object now:"""
    
    def _get_generation_system_prompt(self) -> str:
        """System prompt for generating knowledge from scratch"""
        return """You are a professional travel content writer who creates comprehensive tourist guides.

Your task is to generate detailed tourist information about a place based on your knowledge.

**Output Format**: Return a JSON object with these exact fields:
- short_summary: One-line summary (50-100 chars)
- long_description: Comprehensive 3-5 sentence description
- why_visit: Array of 3-5 compelling reasons to visit
- famous_for: Array of 2-5 things this place is famous for
- best_time_to_visit: When to visit (time of day, season, crowd avoidance)
- time_required: How long to spend (e.g., "1-2 hours", "2-3 hours", "Half day")
- suitable_for: Object with keys: couples, families, kids, solo, elderly - each value is a STRING like "Excellent - romantic ambiance and quiet setting" or "Fair - limited activities for kids"
- historical_significance: 2-3 sentences about historical background (or null if not significant)
- cultural_significance: 2-3 sentences about cultural/religious importance (or null if not applicable)
- interesting_facts: Array of 3-5 fascinating facts tourists would find interesting
- tips: Array of 3-5 practical tips (entry, timing, what to bring, what to avoid)
- crowd_info: Expected crowd levels and patterns (e.g., "Very crowded on weekends", "Peaceful in mornings")
- weather_dependency: Weather sensitivity (e.g., "Indoor - weather proof", "Best avoided during rain")
- confidence_score: Your confidence in this information (0.0-1.0)

**Guidelines**:
- Be specific and accurate - use your knowledge about this place
- Focus on tourist value and practical information
- If you're not certain about details, be conservative in confidence_score
- Highlight unique features and must-see elements
- Include actionable tips visitors need
- Make it engaging and informative
- For suitable_for, provide specific reasons (e.g., "Excellent - romantic sunset views and quiet ambiance")

Return ONLY valid JSON, no other text."""
    
    def _get_generation_user_prompt(
        self,
        place_name: str,
        city: str,
        category: str
    ) -> str:
        """User prompt for generating knowledge from scratch"""
        return f"""Generate a comprehensive tourist guide for this place:

**Place Details**:
- Name: {place_name}
- City: {city}
- Category: {category}

**Task**: Create detailed tourist information based on your knowledge.
Include: what it is, why visit, when to visit, who should visit, historical/cultural context, interesting facts, practical tips.

If you don't have specific information about this exact place, you can:
1. Use general knowledge about this type of place in this city
2. Set a lower confidence_score to reflect uncertainty
3. Focus on category-typical information

Return the JSON object now:"""


# Convenience functions
def summarize_wikipedia_to_knowledge(
    wikipedia_page: WikipediaPage,
    place_name: str,
    city: str,
    category: str,
    client: Optional[OpenAI] = None
) -> Optional[PlaceKnowledge]:
    """
    Convenience function to summarize Wikipedia into knowledge.
    
    Example:
        >>> wiki_page = fetch_place_wikipedia("India Gate", "Delhi")
        >>> knowledge = summarize_wikipedia_to_knowledge(
        ...     wiki_page, "India Gate", "Delhi", "monument"
        ... )
    """
    enricher = GPTPlaceEnricher(client)
    return enricher.summarize_from_wikipedia(wikipedia_page, place_name, city, category)


def generate_knowledge_from_scratch(
    place_name: str,
    city: str,
    category: str,
    client: Optional[OpenAI] = None
) -> Optional[PlaceKnowledge]:
    """
    Convenience function to generate knowledge from scratch.
    
    Example:
        >>> knowledge = generate_knowledge_from_scratch(
        ...     "Local Temple", "Mumbai", "temple"
        ... )
    """
    enricher = GPTPlaceEnricher(client)
    return enricher.generate_from_scratch(place_name, city, category)


