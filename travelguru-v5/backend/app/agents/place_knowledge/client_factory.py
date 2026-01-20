"""
OpenAI Client Factory for Place Knowledge System
Auto-initializes OpenAI client from core.config
"""

from typing import Optional
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


def get_openai_client(client: Optional[OpenAI] = None) -> Optional[OpenAI]:
    """
    Get or create OpenAI client for place knowledge system.
    
    Args:
        client: Optional pre-initialized OpenAI client
        
    Returns:
        OpenAI client (provided or auto-created from config)
        
    Note:
        If client is None, attempts to auto-initialize from core.config.OPENAI_API_KEY
    """
    if client is not None:
        return client
    
    try:
        from app.core.config import OPENAI_API_KEY
        
        if not OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not found in config - OpenAI features disabled")
            return None
            
        client = OpenAI(api_key=OPENAI_API_KEY)
        logger.debug("Auto-initialized OpenAI client from config")
        return client
        
    except Exception as e:
        logger.error(f"Failed to auto-initialize OpenAI client: {e}")
        return None
