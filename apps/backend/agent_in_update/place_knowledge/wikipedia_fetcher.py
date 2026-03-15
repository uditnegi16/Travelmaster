"""
Wikipedia Fetcher
Retrieves place information from Wikipedia with intelligent search strategies
"""

import logging
from typing import Optional
import requests
from urllib.parse import quote

from .schemas import WikipediaPage

logger = logging.getLogger(__name__)


class WikipediaFetcher:
    """
    Fetches Wikipedia articles about tourist places.
    Handles multiple search strategies to find the best matching article.
    """
    
    WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TravelGuru/1.0 (Educational Travel Planning Assistant)'
        })
    
    def fetch(self, place_name: str, city: str, category: Optional[str] = None) -> Optional[WikipediaPage]:
        """
        Fetch Wikipedia page for a place using intelligent search strategies.
        
        Tries multiple search patterns:
        1. Exact place name
        2. Place name + city
        3. Place name + category
        4. Place name + city + category
        
        Args:
            place_name: Name of the place
            city: City where the place is located
            category: Optional category (monument, temple, museum, etc.)
        
        Returns:
            WikipediaPage if found, None otherwise
        """
        search_queries = self._generate_search_queries(place_name, city, category)
        
        for query in search_queries:
            logger.info(f"Trying Wikipedia search: '{query}'")
            page = self._search_and_fetch(query)
            if page:
                logger.info(f"✅ Found Wikipedia page: {page.title}")
                return page
        
        logger.warning(f"❌ No Wikipedia page found for: {place_name}")
        return None
    
    def _generate_search_queries(self, place_name: str, city: str, category: Optional[str]) -> list[str]:
        """Generate search queries in order of specificity"""
        queries = [
            place_name,  # Exact name first
        ]
        
        # Add city-specific variations
        if city:
            queries.append(f"{place_name}, {city}")
            queries.append(f"{place_name} {city}")
        
        # Add category variations
        if category:
            queries.append(f"{place_name} {category}")
            if city:
                queries.append(f"{place_name} {category} {city}")
        
        # Extract core name from long temple/place names
        # Example: "Shree Saunsthan Shantadurga Chamundeshwari" -> "Shantadurga"
        simplified_name = self._extract_core_name(place_name, category)
        if simplified_name and simplified_name != place_name:
            queries.append(simplified_name)
            if city:
                queries.append(f"{simplified_name}, {city}")
                queries.append(f"{simplified_name} {city}")
            if category:
                queries.append(f"{simplified_name} {category}")
        
        return queries
    
    def _extract_core_name(self, place_name: str, category: Optional[str]) -> str:
        """Extract core name from long formal place names"""
        import re
        
        # Remove common prefixes (religious, honorific, administrative)
        prefixes_to_remove = [
            'Shree ', 'Shri ', 'Sri ', 'Sree ', 'Saint ', 'St. ', 'St ',
            'Saunsthan ', 'Sausthan ', 'Devasthan ', 'Royal ', 'The ',
            'Mahamaya ', 'Mandir ', 'Mata ', 'Maha ', 'Devi ', 'Bhagwan ',
            'National ', 'International ', 'Central ', 'Government ',
            'Archaeological ', 'Historic ', 'Ancient ', 'Old ', 'New ',
            'Shree Saunsthan ', 'Shri Mahalaxmi ', 'Shri Mahalakshmi '
        ]
        
        # Remove common suffixes (building types, descriptors)
        suffixes_to_remove = [
            ' Temple', ' Mandir', ' Devasthan', ' Church', ' Mosque', ' Shrine',
            ' Cathedral', ' Basilica', ' Chapel', ' Monastery', ' Convent',
            ' Museum', ' Gallery', ' Art Gallery', ' Museum of Art',
            ' Memorial', ' Monument', ' Statue', ' Tower', ' Fort', ' Palace',
            ' Park', ' Garden', ' Gardens', ' Botanical Garden', ' Zoo',
            ' Beach', ' Lake', ' Waterfall', ' Hill', ' Mountain',
            ' House', ' Mansion', ' Haveli', ' Complex', ' Centre', ' Center',
            ' Institute', ' Foundation', ' Trust', ' Society',
            ' Mahamaya', ' Chamundeshwari', ' Kudtari', ' Devasthanam',
            ' Building', ' Hall', ' Auditorium', ' Stadium', ' Arena',
            ' Pvt Ltd', ' Private Limited', ' Ltd', ' Inc', ' Corporation',
            ' ( NV Eco farm )', ' Eco Agro Tourism', ' Tourism'
        ]
        
        cleaned = place_name
        
        # Remove prefixes (case-insensitive but preserve original case)
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):]
        
        # Remove suffixes (case-insensitive)
        for suffix in suffixes_to_remove:
            if cleaned.lower().endswith(suffix.lower()):
                cleaned = cleaned[:-len(suffix)]
        
        # Remove parenthetical content like "(NV Eco farm)"
        cleaned = re.sub(r'\s*\([^)]*\)\s*', ' ', cleaned)
        
        # Clean up multiple spaces
        cleaned = ' '.join(cleaned.split())
        
        # Extract core name based on length
        words = cleaned.split()
        
        # If still too long (>4 words), extract core (first 2-3 significant words)
        if len(words) > 4:
            # Skip common filler words
            filler_words = {'of', 'the', 'and', 'at', 'in', 'on', 'for', 'to', 'a', 'an'}
            significant_words = [w for w in words if w.lower() not in filler_words]
            
            if len(significant_words) > 3:
                cleaned = ' '.join(significant_words[:2])
            elif significant_words:
                cleaned = ' '.join(significant_words[:3])
        
        return cleaned.strip()
    
    def _search_and_fetch(self, search_query: str) -> Optional[WikipediaPage]:
        """Search Wikipedia and fetch the best matching page"""
        try:
            # Step 1: Search for matching pages
            search_results = self._search_wikipedia(search_query)
            if not search_results:
                return None
            
            # Step 2: Get the first result's page content
            page_title = search_results[0]
            return self._fetch_page_content(page_title)
        
        except Exception as e:
            logger.error(f"Error fetching Wikipedia page for '{search_query}': {e}")
            return None
    
    def _search_wikipedia(self, query: str) -> list[str]:
        """Search Wikipedia and return list of matching page titles"""
        try:
            params = {
                'action': 'opensearch',
                'search': query,
                'limit': 5,
                'namespace': 0,
                'format': 'json'
            }
            
            response = self.session.get(self.WIKIPEDIA_API_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            # OpenSearch returns: [query, [titles], [descriptions], [urls]]
            if len(data) >= 2 and data[1]:
                return data[1]  # List of titles
            
            return []
        
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return []
    
    def _fetch_page_content(self, page_title: str) -> Optional[WikipediaPage]:
        """Fetch full content of a Wikipedia page"""
        try:
            params = {
                'action': 'query',
                'titles': page_title,
                'prop': 'extracts|info',
                'exintro': False,  # Get full content, not just intro
                'explaintext': True,  # Plain text, no HTML
                'inprop': 'url',
                'format': 'json'
            }
            
            response = self.session.get(self.WIKIPEDIA_API_URL, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            
            if not pages:
                return None
            
            # Get the first (and should be only) page
            page_data = next(iter(pages.values()))
            
            # Check if page exists (missing pages have negative IDs)
            if page_data.get('missing'):
                return None
            
            # Extract summary (first paragraph)
            full_content = page_data.get('extract', '')
            summary = self._extract_summary(full_content)
            
            return WikipediaPage(
                title=page_data.get('title', page_title),
                summary=summary,
                content=full_content,
                url=page_data.get('fullurl', f"https://en.wikipedia.org/wiki/{quote(page_title)}"),
                sections=self._extract_sections(full_content)
            )
        
        except Exception as e:
            logger.error(f"Error fetching page content for '{page_title}': {e}")
            return None
    
    def _extract_summary(self, content: str) -> str:
        """Extract first paragraph as summary"""
        if not content:
            return ""
        
        # Split by double newline (paragraph separator in Wikipedia plain text)
        paragraphs = content.split('\n\n')
        
        # Get first non-empty paragraph
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 50:  # Meaningful paragraph
                return para
        
        # Fallback: first 500 chars
        return content[:500].strip()
    
    def _extract_sections(self, content: str) -> list[str]:
        """Extract section titles from content"""
        sections = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Wikipedia plain text uses "==" for sections
            if line.startswith('==') and line.endswith('=='):
                section_title = line.replace('==', '').strip()
                if section_title:
                    sections.append(section_title)
        
        return sections
    
    def fetch_by_url(self, wikipedia_url: str) -> Optional[WikipediaPage]:
        """
        Fetch Wikipedia page by direct URL.
        Useful for testing or when exact URL is known.
        """
        try:
            # Extract page title from URL
            # https://en.wikipedia.org/wiki/Page_Title
            if '/wiki/' in wikipedia_url:
                page_title = wikipedia_url.split('/wiki/')[-1]
                page_title = requests.utils.unquote(page_title)
                return self._fetch_page_content(page_title)
        except Exception as e:
            logger.error(f"Error fetching by URL '{wikipedia_url}': {e}")
        
        return None


# Convenience function for simple usage
def fetch_place_wikipedia(place_name: str, city: str, category: Optional[str] = None) -> Optional[WikipediaPage]:
    """
    Convenience function to fetch Wikipedia page for a place.
    
    Example:
        >>> page = fetch_place_wikipedia("India Gate", "Delhi", "monument")
        >>> if page:
        ...     print(page.summary)
    """
    fetcher = WikipediaFetcher()
    return fetcher.fetch(place_name, city, category)


