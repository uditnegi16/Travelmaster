"""
Place Knowledge System
Production-grade hybrid Wikipedia + GPT knowledge enrichment for tourist places

This package provides intelligent place knowledge generation using:
1. Wikipedia as primary source (when available and high quality)
2. GPT for summarization and enrichment
3. GPT generation from scratch (when Wikipedia is missing/poor)
4. Intelligent caching for performance and cost efficiency

Quick Start:
    >>> from backend.app.agents.place_knowledge import get_place_knowledge
    >>> 
    >>> # No client needed - auto-initializes from config
    >>> knowledge = get_place_knowledge(
    ...     "Taj Mahal",
    ...     "Agra",
    ...     "monument"
    ... )
    >>> 
    >>> print(knowledge.short_summary)
    >>> print(knowledge.why_visit)
    >>> print(knowledge.best_time_to_visit)

Components:
- PlaceKnowledge: Structured knowledge schema
- WikipediaFetcher: Fetch Wikipedia articles
- WikipediaQualityChecker: Evaluate Wikipedia quality
- GPTPlaceEnricher: Summarize or generate with GPT
- PlaceKnowledgeCache: SQLite-based caching
- PlaceKnowledgeOrchestrator: Main workflow coordinator
"""

from .schemas import (
    PlaceKnowledge,
    WikipediaPage,
    KnowledgeGenerationRequest,
    KnowledgeQualityMetrics
)

from .wikipedia_fetcher import (
    WikipediaFetcher,
    fetch_place_wikipedia
)

from .quality_checker import (
    WikipediaQualityChecker,
    is_wikipedia_good_enough
)

from .gpt_enricher import (
    GPTPlaceEnricher,
    summarize_wikipedia_to_knowledge,
    generate_knowledge_from_scratch
)

from .cache import (
    PlaceKnowledgeCache,
    get_global_cache,
    get_cached_knowledge,
    save_to_cache
)

from .orchestrator import (
    PlaceKnowledgeOrchestrator,
    get_global_orchestrator,
    get_place_knowledge
)

__all__ = [
    # Schemas
    "PlaceKnowledge",
    "WikipediaPage",
    "KnowledgeGenerationRequest",
    "KnowledgeQualityMetrics",
    
    # Wikipedia
    "WikipediaFetcher",
    "fetch_place_wikipedia",
    
    # Quality
    "WikipediaQualityChecker",
    "is_wikipedia_good_enough",
    
    # GPT
    "GPTPlaceEnricher",
    "summarize_wikipedia_to_knowledge",
    "generate_knowledge_from_scratch",
    
    # Cache
    "PlaceKnowledgeCache",
    "get_global_cache",
    "get_cached_knowledge",
    "save_to_cache",
    
    # Orchestrator (main API)
    "PlaceKnowledgeOrchestrator",
    "get_global_orchestrator",
    "get_place_knowledge",
]

__version__ = "1.0.0"
