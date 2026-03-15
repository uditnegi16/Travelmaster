"""
Knowledge Cache
Stores generated place knowledge to avoid repeated API calls
"""

import logging
import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta
from threading import Lock

from .schemas import PlaceKnowledge

logger = logging.getLogger(__name__)


class PlaceKnowledgeCache:
    """
    SQLite-based cache for place knowledge.
    
    Features:
    - Fast lookups by place name + city
    - Automatic expiration (default: 30 days)
    - Thread-safe operations
    - Efficient JSON storage
    """
    
    DEFAULT_CACHE_DIR = Path("data/cache")
    DEFAULT_DB_NAME = "place_knowledge.db"
    DEFAULT_TTL_DAYS = 30  # Knowledge expires after 30 days
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        db_name: str = DEFAULT_DB_NAME,
        ttl_days: int = DEFAULT_TTL_DAYS
    ):
        """
        Initialize cache with SQLite database.
        
        Args:
            cache_dir: Directory to store cache database
            db_name: Name of the SQLite database file
            ttl_days: Time-to-live in days (knowledge expires after this)
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.cache_dir / db_name
        self.ttl_days = ttl_days
        self._lock = Lock()  # Thread safety
        
        self._initialize_database()
        logger.info(f"✅ Place knowledge cache initialized: {self.db_path}")
    
    def _initialize_database(self):
        """Create database schema if not exists"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS place_knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    place_name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    category TEXT,
                    knowledge_json TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence_score REAL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    hits INTEGER DEFAULT 0
                )
            """)
            
            # Create index for fast lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_key 
                ON place_knowledge(cache_key)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                ON place_knowledge(expires_at)
            """)
            
            conn.commit()
    
    def get(self, place_name: str, city: str) -> Optional[PlaceKnowledge]:
        """
        Retrieve knowledge from cache if available and not expired.
        
        Args:
            place_name: Name of the place
            city: City name
        
        Returns:
            PlaceKnowledge if found and valid, None otherwise
        """
        cache_key = self._generate_cache_key(place_name, city)
        
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT knowledge_json, expires_at 
                        FROM place_knowledge 
                        WHERE cache_key = ?
                    """, (cache_key,))
                    
                    row = cursor.fetchone()
                    
                    if row is None:
                        logger.debug(f"❌ Cache miss: {cache_key}")
                        return None
                    
                    knowledge_json, expires_at = row
                    
                    # Check expiration
                    if datetime.fromisoformat(expires_at) < datetime.utcnow():
                        logger.info(f"⏰ Cache expired: {cache_key}")
                        self._delete(cache_key)
                        return None
                    
                    # Increment hit counter
                    conn.execute("""
                        UPDATE place_knowledge 
                        SET hits = hits + 1 
                        WHERE cache_key = ?
                    """, (cache_key,))
                    conn.commit()
                    
                    # Parse and return
                    knowledge_dict = json.loads(knowledge_json)
                    knowledge = PlaceKnowledge(**knowledge_dict)
                    
                    logger.info(f"✅ Cache hit: {cache_key}")
                    return knowledge
            
            except Exception as e:
                logger.error(f"Cache retrieval error: {e}")
                return None
    
    def save(self, knowledge: PlaceKnowledge) -> bool:
        """
        Save knowledge to cache.
        
        Args:
            knowledge: PlaceKnowledge object to cache
        
        Returns:
            True if saved successfully, False otherwise
        """
        cache_key = self._generate_cache_key(knowledge.name, knowledge.city)
        
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    created_at = datetime.utcnow()
                    expires_at = created_at + timedelta(days=self.ttl_days)
                    
                    knowledge_json = knowledge.model_dump_json()
                    
                    # Upsert (insert or replace)
                    conn.execute("""
                        INSERT OR REPLACE INTO place_knowledge 
                        (cache_key, place_name, city, category, knowledge_json, 
                         source, confidence_score, created_at, expires_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cache_key,
                        knowledge.name,
                        knowledge.city,
                        knowledge.category,
                        knowledge_json,
                        knowledge.source,
                        knowledge.confidence_score,
                        created_at.isoformat(),
                        expires_at.isoformat()
                    ))
                    
                    conn.commit()
                    logger.info(f"💾 Cached knowledge: {cache_key}")
                    return True
            
            except Exception as e:
                logger.error(f"Cache save error: {e}")
                return False
    
    def invalidate(self, place_name: str, city: str) -> bool:
        """
        Remove knowledge from cache.
        
        Args:
            place_name: Name of the place
            city: City name
        
        Returns:
            True if deleted, False otherwise
        """
        cache_key = self._generate_cache_key(place_name, city)
        return self._delete(cache_key)
    
    def _delete(self, cache_key: str) -> bool:
        """Internal delete method"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM place_knowledge WHERE cache_key = ?", (cache_key,))
                conn.commit()
                logger.info(f"🗑️ Deleted from cache: {cache_key}")
                return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries deleted
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        DELETE FROM place_knowledge 
                        WHERE expires_at < ?
                    """, (datetime.utcnow().isoformat(),))
                    
                    conn.commit()
                    deleted_count = cursor.rowcount
                    
                    if deleted_count > 0:
                        logger.info(f"🧹 Cleaned up {deleted_count} expired cache entries")
                    
                    return deleted_count
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                return 0
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_entries,
                        SUM(hits) as total_hits,
                        AVG(confidence_score) as avg_confidence,
                        COUNT(CASE WHEN expires_at > ? THEN 1 END) as valid_entries,
                        COUNT(CASE WHEN expires_at <= ? THEN 1 END) as expired_entries
                    FROM place_knowledge
                """, (datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
                
                row = cursor.fetchone()
                
                return {
                    "total_entries": row[0] or 0,
                    "total_hits": row[1] or 0,
                    "avg_confidence": round(row[2], 2) if row[2] else 0.0,
                    "valid_entries": row[3] or 0,
                    "expired_entries": row[4] or 0,
                    "cache_dir": str(self.cache_dir),
                    "db_path": str(self.db_path),
                    "ttl_days": self.ttl_days
                }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def clear_all(self) -> bool:
        """
        Clear entire cache (DANGER: removes all cached knowledge).
        Use for testing or reset purposes.
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM place_knowledge")
                    conn.commit()
                    logger.warning("⚠️ Cleared entire place knowledge cache")
                    return True
            except Exception as e:
                logger.error(f"Cache clear error: {e}")
                return False
    
    @staticmethod
    def _generate_cache_key(place_name: str, city: str) -> str:
        """
        Generate normalized cache key from place name and city.
        
        Example:
            "Taj Mahal" + "Agra" → "taj_mahal_agra"
        """
        normalized_place = place_name.lower().strip().replace(" ", "_")
        normalized_city = city.lower().strip().replace(" ", "_")
        return f"{normalized_place}_{normalized_city}"


# Global cache instance (singleton pattern)
_global_cache: Optional[PlaceKnowledgeCache] = None
_cache_lock = Lock()


def get_global_cache() -> PlaceKnowledgeCache:
    """
    Get or create global cache instance.
    Singleton pattern ensures only one cache instance across the application.
    """
    global _global_cache
    
    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = PlaceKnowledgeCache()
    
    return _global_cache


# Convenience functions
def get_cached_knowledge(place_name: str, city: str) -> Optional[PlaceKnowledge]:
    """Quick function to get cached knowledge using global cache"""
    cache = get_global_cache()
    return cache.get(place_name, city)


def save_to_cache(knowledge: PlaceKnowledge) -> bool:
    """Quick function to save knowledge to global cache"""
    cache = get_global_cache()
    return cache.save(knowledge)


