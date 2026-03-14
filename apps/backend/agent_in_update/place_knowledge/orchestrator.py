"""
Place Knowledge Orchestrator
Main workflow coordinator for the hybrid Wikipedia + GPT knowledge system
"""

import logging
from typing import Optional
from datetime import datetime

from openai import OpenAI

from .schemas import PlaceKnowledge, KnowledgeGenerationRequest
from .wikipedia_fetcher import WikipediaFetcher
from .quality_checker import WikipediaQualityChecker
from .gpt_enricher import GPTPlaceEnricher
from .cache import PlaceKnowledgeCache, get_global_cache
from .client_factory import get_openai_client

logger = logging.getLogger(__name__)


class PlaceKnowledgeOrchestrator:
    """
    Main orchestrator for place knowledge generation.
    
    Workflow:
    1. Check cache → return if valid
    2. Try Wikipedia → fetch page
    3. Quality check → is Wikipedia good enough?
    4. If good → summarize with GPT
    5. If poor → generate from scratch with GPT
    6. Save to cache → return
    
    This ensures:
    - Fast responses (cache first)
    - Cost efficiency (avoid duplicate GPT calls)
    - High quality (Wikipedia when available, GPT otherwise)
    - Reliability (fallback to GPT if Wikipedia fails)
    """
    
    def __init__(
        self,
        openai_client: Optional[OpenAI] = None,
        cache: Optional[PlaceKnowledgeCache] = None,
        use_cache: bool = True
    ):
        """
        Initialize orchestrator with dependencies.
        
        Args:
            openai_client: OpenAI client for GPT operations (auto-initializes from config if None)
            cache: Cache instance (uses global cache if None)
            use_cache: Whether to use caching (disable for testing)
        """
        self.openai_client = get_openai_client(openai_client)
        self.use_cache = use_cache
        
        # Initialize components
        self.cache = cache if cache is not None else get_global_cache()
        self.wikipedia_fetcher = WikipediaFetcher()
        self.quality_checker = WikipediaQualityChecker()
        self.gpt_enricher = GPTPlaceEnricher(client=openai_client)
        
        logger.info("✅ PlaceKnowledgeOrchestrator initialized")
    
    def get_place_knowledge(
        self,
        place_name: str,
        city: str,
        category: str,
        force_regenerate: bool = False
    ) -> Optional[PlaceKnowledge]:
        """
        Get comprehensive place knowledge using hybrid Wikipedia + GPT approach.
        
        This is the main entry point for getting place information.
        
        Args:
            place_name: Name of the place
            city: City name
            category: Place category (temple, museum, park, etc.)
            force_regenerate: Skip cache and regenerate knowledge
        
        Returns:
            PlaceKnowledge object with comprehensive information
        
        Example:
            >>> orchestrator = PlaceKnowledgeOrchestrator(openai_client)
            >>> knowledge = orchestrator.get_place_knowledge(
            ...     "Taj Mahal", "Agra", "monument"
            ... )
            >>> print(knowledge.why_visit)
            ['One of the Seven Wonders', 'Breathtaking architecture', ...]
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 Fetching knowledge: {place_name}, {city} ({category})")
        logger.info(f"{'='*60}")
        
        # STEP 1: Check cache (unless force regenerate)
        if self.use_cache and not force_regenerate:
            cached = self.cache.get(place_name, city)
            if cached:
                logger.info(f"✅ CACHE HIT - Returning cached knowledge")
                logger.info(f"   Source: {cached.source}")
                logger.info(f"   Confidence: {cached.confidence_score}")
                return cached
            logger.info(f"❌ Cache miss - Proceeding to generation")
        else:
            logger.info(f"⚠️ Cache bypassed (force_regenerate={force_regenerate})")
        
        # STEP 2: Try Wikipedia
        logger.info(f"\n📖 STEP 1: Fetching Wikipedia...")
        wikipedia_page = self.wikipedia_fetcher.fetch(place_name, city, category)
        
        # STEP 3: Quality check
        knowledge = None
        
        if wikipedia_page:
            logger.info(f"✅ Wikipedia page found: {wikipedia_page.title}")
            logger.info(f"   Content length: {len(wikipedia_page.content)} chars")
            
            is_good = self.quality_checker.is_good_enough(wikipedia_page)
            
            if is_good:
                # STEP 4A: Wikipedia is good → Summarize
                logger.info(f"\n✨ STEP 2: Wikipedia quality is GOOD → Summarizing with GPT")
                knowledge = self.gpt_enricher.summarize_from_wikipedia(
                    wikipedia_page, place_name, city, category
                )
                if knowledge:
                    logger.info(f"✅ Successfully summarized Wikipedia content")
            else:
                logger.info(f"\n⚠️ STEP 2: Wikipedia quality is POOR → Generating from scratch")
                # STEP 4B: Wikipedia is poor → Generate from scratch
                knowledge = self.gpt_enricher.generate_from_scratch(
                    place_name, city, category
                )
                if knowledge:
                    logger.info(f"✅ Successfully generated knowledge from scratch")
        else:
            # STEP 4C: No Wikipedia → Generate from scratch
            logger.info(f"\n❌ No Wikipedia page found")
            logger.info(f"🤖 STEP 2: Generating knowledge from scratch with GPT")
            knowledge = self.gpt_enricher.generate_from_scratch(
                place_name, city, category
            )
            if knowledge:
                logger.info(f"✅ Successfully generated knowledge from scratch")
        
        # STEP 5: Save to cache
        if knowledge and self.use_cache:
            logger.info(f"\n💾 STEP 3: Saving to cache...")
            saved = self.cache.save(knowledge)
            if saved:
                logger.info(f"✅ Knowledge cached successfully")
            else:
                logger.warning(f"⚠️ Failed to cache knowledge")
        
        # Final result
        if knowledge:
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ FINAL RESULT:")
            logger.info(f"   Name: {knowledge.name}")
            logger.info(f"   Source: {knowledge.source}")
            logger.info(f"   Confidence: {knowledge.confidence_score}")
            logger.info(f"   Why visit: {len(knowledge.why_visit)} reasons")
            logger.info(f"   Tips: {len(knowledge.tips)} tips")
            logger.info(f"{'='*60}\n")
        else:
            logger.error(f"\n{'='*60}")
            logger.error(f"❌ FAILED to generate knowledge for: {place_name}")
            logger.error(f"{'='*60}\n")
        
        return knowledge
    
    def get_knowledge_batch(
        self,
        places: list[tuple[str, str, str]],
        force_regenerate: bool = False
    ) -> dict[str, Optional[PlaceKnowledge]]:
        """
        Get knowledge for multiple places in batch.
        
        Args:
            places: List of (place_name, city, category) tuples
            force_regenerate: Skip cache for all places
        
        Returns:
            Dictionary mapping place names to PlaceKnowledge objects
        
        Example:
            >>> places = [
            ...     ("Taj Mahal", "Agra", "monument"),
            ...     ("India Gate", "Delhi", "monument"),
            ...     ("Gateway of India", "Mumbai", "monument")
            ... ]
            >>> results = orchestrator.get_knowledge_batch(places)
        """
        results = {}
        
        logger.info(f"\n🔄 Batch processing {len(places)} places...")
        
        for i, (place_name, city, category) in enumerate(places, 1):
            logger.info(f"\n[{i}/{len(places)}] Processing: {place_name}")
            
            knowledge = self.get_place_knowledge(
                place_name, city, category, force_regenerate
            )
            
            results[place_name] = knowledge
        
        success_count = sum(1 for k in results.values() if k is not None)
        logger.info(f"\n✅ Batch complete: {success_count}/{len(places)} successful")
        
        return results
    
    def invalidate_cache(self, place_name: str, city: str) -> bool:
        """
        Remove place from cache (useful when information is outdated).
        
        Args:
            place_name: Name of the place
            city: City name
        
        Returns:
            True if invalidated successfully
        """
        if not self.use_cache:
            logger.warning("Cache is disabled")
            return False
        
        logger.info(f"🗑️ Invalidating cache for: {place_name}, {city}")
        return self.cache.invalidate(place_name, city)
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        if not self.use_cache:
            return {"status": "cache_disabled"}
        
        return self.cache.get_stats()
    
    def cleanup_cache(self) -> int:
        """Clean up expired cache entries"""
        if not self.use_cache:
            return 0
        
        logger.info("🧹 Cleaning up expired cache entries...")
        count = self.cache.cleanup_expired()
        logger.info(f"✅ Cleaned {count} expired entries")
        return count


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global orchestrator instance (singleton)
_global_orchestrator: Optional[PlaceKnowledgeOrchestrator] = None


def get_global_orchestrator(openai_client: Optional[OpenAI] = None) -> PlaceKnowledgeOrchestrator:
    """
    Get or create global orchestrator instance.
    
    Args:
        openai_client: OpenAI client (auto-initializes from config if None)
    
    Returns:
        Global orchestrator instance
    """
    global _global_orchestrator
    
    if _global_orchestrator is None:
        _global_orchestrator = PlaceKnowledgeOrchestrator(openai_client)
    
    return _global_orchestrator


def get_place_knowledge(
    place_name: str,
    city: str,
    category: str,
    openai_client: Optional[OpenAI] = None,
    force_regenerate: bool = False
) -> Optional[PlaceKnowledge]:
    """
    Convenience function to get place knowledge.
    Uses global orchestrator instance.
    
    Example:
        >>> # No client needed - auto-initializes from config
        >>> knowledge = get_place_knowledge(
        ...     "Taj Mahal",
        ...     "Agra",
        ...     "monument"
        ... )
        >>> 
        >>> print(knowledge.short_summary)
        >>> print(knowledge.why_visit)
    """
    orchestrator = get_global_orchestrator(openai_client)
    return orchestrator.get_place_knowledge(
        place_name, city, category, force_regenerate
    )
