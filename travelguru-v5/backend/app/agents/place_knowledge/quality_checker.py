"""
Quality Checker
Evaluates Wikipedia content quality to decide whether to use it or generate knowledge via GPT
"""

import logging
import re
from typing import Optional

from .schemas import WikipediaPage, KnowledgeQualityMetrics

logger = logging.getLogger(__name__)


class WikipediaQualityChecker:
    """
    Evaluates Wikipedia page quality for tourist place information.
    Determines if the Wikipedia content is good enough to use or if GPT generation is needed.
    """
    
    # Quality thresholds
    MIN_CONTENT_LENGTH = 800  # Minimum characters for meaningful content
    MIN_SUMMARY_LENGTH = 100  # Minimum summary length
    GOOD_CONTENT_LENGTH = 2000  # Length indicating good detail
    EXCELLENT_CONTENT_LENGTH = 5000  # Length indicating excellent detail
    
    # Disambiguation/generic page indicators
    DISAMBIGUATION_INDICATORS = [
        "may refer to",
        "may also refer to",
        "can refer to",
        "disambiguation",
        "is the name of",
        "several places",
        "several entities"
    ]
    
    # Generic/meta page indicators (not specific place articles)
    GENERIC_PAGE_INDICATORS = [
        "list of",
        "category:",
        "this article is about",
        "for other uses",
        "see also:",
        "not to be confused with"
    ]
    
    # Tourist-relevant section indicators (good signs)
    TOURIST_RELEVANT_SECTIONS = [
        "history",
        "architecture",
        "tourism",
        "visitor information",
        "gallery",
        "description",
        "features",
        "significance",
        "cultural",
        "religious",
        "attractions"
    ]
    
    def is_good_enough(self, page: Optional[WikipediaPage]) -> bool:
        """
        Main quality check: Is this Wikipedia page good enough to use?
        
        Returns:
            True if page is high quality and tourist-relevant
            False if page is missing, low quality, or not tourist-focused
        """
        if page is None:
            logger.info("❌ No Wikipedia page provided")
            return False
        
        # Check 1: Disambiguation page?
        if self._is_disambiguation_page(page):
            logger.info(f"❌ Disambiguation page detected: {page.title}")
            return False
        
        # Check 2: Generic/meta page?
        if self._is_generic_page(page):
            logger.info(f"❌ Generic page detected: {page.title}")
            return False
        
        # Check 3: Sufficient content length?
        if not self._has_sufficient_content(page):
            logger.info(f"❌ Insufficient content: {len(page.content)} chars")
            return False
        
        # Check 4: Tourist-relevant sections?
        if not self._has_tourist_relevant_sections(page):
            logger.info(f"⚠️ No tourist-relevant sections found")
            # Don't fail, but note it
        
        # Check 5: Summary quality
        if not self._has_good_summary(page):
            logger.info(f"⚠️ Weak summary quality")
            # Don't fail, but note it
        
        logger.info(f"✅ Wikipedia page passes quality checks: {page.title}")
        return True
    
    def evaluate_quality(self, page: Optional[WikipediaPage]) -> KnowledgeQualityMetrics:
        """
        Comprehensive quality evaluation with detailed metrics.
        
        Returns:
            Detailed quality metrics
        """
        if page is None:
            return KnowledgeQualityMetrics(
                completeness_score=0.0,
                detail_richness_score=0.0,
                factual_confidence=0.0,
                source_reliability="low",
                overall_quality="poor"
            )
        
        # Calculate individual scores
        completeness = self._calculate_completeness_score(page)
        detail_richness = self._calculate_detail_richness_score(page)
        factual_confidence = self._calculate_factual_confidence(page)
        
        # Determine source reliability
        if self._is_disambiguation_page(page) or self._is_generic_page(page):
            reliability = "low"
        elif len(page.content) > self.EXCELLENT_CONTENT_LENGTH:
            reliability = "high"
        elif len(page.content) > self.GOOD_CONTENT_LENGTH:
            reliability = "medium"
        else:
            reliability = "low"
        
        # Overall quality
        avg_score = (completeness + detail_richness + factual_confidence) / 3
        if avg_score >= 0.8:
            overall = "excellent"
        elif avg_score >= 0.6:
            overall = "good"
        elif avg_score >= 0.4:
            overall = "fair"
        else:
            overall = "poor"
        
        return KnowledgeQualityMetrics(
            completeness_score=completeness,
            detail_richness_score=detail_richness,
            factual_confidence=factual_confidence,
            source_reliability=reliability,
            overall_quality=overall
        )
    
    # ============================================================================
    # INTERNAL QUALITY CHECKS
    # ============================================================================
    
    def _is_disambiguation_page(self, page: WikipediaPage) -> bool:
        """Check if this is a disambiguation page"""
        summary_lower = page.summary.lower()
        content_lower = page.content.lower()
        
        for indicator in self.DISAMBIGUATION_INDICATORS:
            if indicator in summary_lower or indicator in content_lower[:500]:
                return True
        
        return False
    
    def _is_generic_page(self, page: WikipediaPage) -> bool:
        """Check if this is a generic/meta page (not a specific place)"""
        summary_lower = page.summary.lower()
        title_lower = page.title.lower()
        
        for indicator in self.GENERIC_PAGE_INDICATORS:
            if indicator in summary_lower or indicator in title_lower:
                return True
        
        return False
    
    def _has_sufficient_content(self, page: WikipediaPage) -> bool:
        """Check if content length is sufficient"""
        return (
            len(page.content) >= self.MIN_CONTENT_LENGTH and
            len(page.summary) >= self.MIN_SUMMARY_LENGTH
        )
    
    def _has_tourist_relevant_sections(self, page: WikipediaPage) -> bool:
        """Check if page has tourist-relevant sections"""
        if not page.sections:
            return False
        
        sections_lower = [s.lower() for s in page.sections]
        
        for relevant_keyword in self.TOURIST_RELEVANT_SECTIONS:
            if any(relevant_keyword in section for section in sections_lower):
                return True
        
        return False
    
    def _has_good_summary(self, page: WikipediaPage) -> bool:
        """Check if summary is informative"""
        summary = page.summary.strip()
        
        # Must have reasonable length
        if len(summary) < self.MIN_SUMMARY_LENGTH:
            return False
        
        # Should not be too generic
        generic_phrases = ["is a", "was a", "refers to"]
        if all(phrase not in summary.lower() for phrase in generic_phrases):
            return False  # Might be too vague
        
        return True
    
    # ============================================================================
    # QUALITY SCORING
    # ============================================================================
    
    def _calculate_completeness_score(self, page: WikipediaPage) -> float:
        """Score: How complete is the information? (0.0 - 1.0)"""
        score = 0.0
        
        # Content length contribution (0-0.4)
        if len(page.content) >= self.EXCELLENT_CONTENT_LENGTH:
            score += 0.4
        elif len(page.content) >= self.GOOD_CONTENT_LENGTH:
            score += 0.3
        elif len(page.content) >= self.MIN_CONTENT_LENGTH:
            score += 0.2
        
        # Summary quality contribution (0-0.2)
        if self._has_good_summary(page):
            score += 0.2
        
        # Section diversity contribution (0-0.4)
        if page.sections:
            num_sections = len(page.sections)
            if num_sections >= 10:
                score += 0.4
            elif num_sections >= 5:
                score += 0.3
            elif num_sections >= 3:
                score += 0.2
            else:
                score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_detail_richness_score(self, page: WikipediaPage) -> float:
        """Score: How rich and detailed is the content? (0.0 - 1.0)"""
        score = 0.0
        
        # Content depth (0-0.5)
        content_length = len(page.content)
        if content_length >= self.EXCELLENT_CONTENT_LENGTH:
            score += 0.5
        elif content_length >= self.GOOD_CONTENT_LENGTH:
            score += 0.4
        elif content_length >= self.MIN_CONTENT_LENGTH:
            score += 0.3
        else:
            score += 0.1
        
        # Tourist-relevant sections (0-0.3)
        if self._has_tourist_relevant_sections(page):
            score += 0.3
        
        # Paragraph structure (0-0.2)
        paragraphs = [p for p in page.content.split('\n\n') if len(p.strip()) > 100]
        if len(paragraphs) >= 5:
            score += 0.2
        elif len(paragraphs) >= 3:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_factual_confidence(self, page: WikipediaPage) -> float:
        """Score: Confidence in factual accuracy (0.0 - 1.0)"""
        # Wikipedia articles are generally reliable
        # Penalize only for clear issues
        score = 0.8  # Start with high confidence
        
        # Penalize if disambiguation
        if self._is_disambiguation_page(page):
            score -= 0.5
        
        # Penalize if generic
        if self._is_generic_page(page):
            score -= 0.3
        
        # Penalize if very short (might be stub)
        if len(page.content) < self.MIN_CONTENT_LENGTH:
            score -= 0.3
        
        # Bonus for comprehensive articles
        if len(page.content) > self.EXCELLENT_CONTENT_LENGTH:
            score += 0.1
        
        return max(0.0, min(score, 1.0))


# Convenience function
def is_wikipedia_good_enough(page: Optional[WikipediaPage]) -> bool:
    """
    Quick check: Is this Wikipedia page good enough to use?
    
    Example:
        >>> page = fetch_place_wikipedia("Taj Mahal", "Agra")
        >>> if is_wikipedia_good_enough(page):
        ...     # Use Wikipedia content
        ... else:
        ...     # Generate via GPT
    """
    checker = WikipediaQualityChecker()
    return checker.is_good_enough(page)
