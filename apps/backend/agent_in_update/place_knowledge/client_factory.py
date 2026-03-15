"""
OpenAI Client Factory for Place Knowledge System
Auto-initializes OpenAI client from core.config
Supports Groq and other OpenAI-compatible providers via OPENAI_BASE_URL
"""

from typing import Optional
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


def get_openai_client(client: Optional[OpenAI] = None) -> Optional[OpenAI]:
    """
    Get or create OpenAI client for place knowledge system.
    Reads OPENAI_BASE_URL from env so Groq routing works automatically.
    """
    if client is not None:
        return client

    try:
        from core.config import OPENAI_API_KEY, OPENAI_BASE_URL

        if not OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not found in config - OpenAI features disabled")
            return None

        base_url = OPENAI_BASE_URL if OPENAI_BASE_URL else None
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=base_url)
        logger.debug(f"Auto-initialized OpenAI client (base_url={base_url or 'default'})")
        return client

    except Exception as e:
        logger.error(f"Failed to auto-initialize OpenAI client: {e}")
        return None

