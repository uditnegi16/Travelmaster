# core/amadeus_client.py
"""
Centralised Amadeus SDK client.

BUG FIXES:
1. Was missing entirely — caused ImportError across all tools.
2. Hostname now read from config (test vs production) so sandbox keys work.
3. call_amadeus wraps any SDK call with retry + structured error.
4. ensure_amadeus_healthy() raises fast with a clear message if not configured.
"""

import time
import threading
from typing import Any, Callable

from core.config import AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET, AMADEUS_HOSTNAME
from core.logging import get_logger

logger = get_logger(__name__)

# ── Lazy singleton ────────────────────────────────────────────────
_client = None
_client_lock = threading.Lock()


class AmadeusAPIError(RuntimeError):
    """Raised when an Amadeus SDK call fails after retries."""
    pass


def get_amadeus_client():
    """
    Return a lazily-initialised Amadeus SDK client (singleton).

    Uses AMADEUS_HOSTNAME from config to switch between:
      - 'test'       → test.api.amadeus.com  (sandbox keys)
      - 'production' → api.amadeus.com        (live keys)
    """
    global _client
    if _client is not None:
        return _client

    with _client_lock:
        if _client is not None:
            return _client

        if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
            raise AmadeusAPIError(
                "Amadeus credentials not set. "
                "Add AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET to your .env file."
            )

        try:
            from amadeus import Client as AmadeusSDK

            hostname = AMADEUS_HOSTNAME  # 'test' or 'production'
            logger.info("Initialising Amadeus client (hostname=%s)", hostname)

            _client = AmadeusSDK(
                client_id=AMADEUS_CLIENT_ID,
                client_secret=AMADEUS_CLIENT_SECRET,
                hostname=hostname,
                log_level="silent",   # suppress SDK's own verbose logs
            )
            logger.info("Amadeus client ready (hostname=%s)", hostname)
            return _client

        except ImportError:
            raise AmadeusAPIError(
                "amadeus package not installed. Run: pip install amadeus"
            )
        except Exception as e:
            raise AmadeusAPIError(f"Failed to create Amadeus client: {e}") from e


def ensure_amadeus_healthy() -> None:
    """
    Fast pre-flight check: raises AmadeusAPIError if credentials missing.
    Called at the top of every adapter so the error message is immediate.
    """
    if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
        raise AmadeusAPIError(
            "Amadeus not configured: AMADEUS_CLIENT_ID / AMADEUS_CLIENT_SECRET missing in .env"
        )


def call_amadeus(
    fn: Callable,
    *args: Any,
    max_retries: int = 2,
    retry_delay: float = 1.0,
    **kwargs: Any,
) -> Any:
    """
    Call any Amadeus SDK function with automatic retry on transient errors.

    Args:
        fn: Any callable (SDK method or plain function).
        max_retries: Number of attempts before raising.
        retry_delay: Base delay between retries (doubles each time).
        *args / **kwargs: Forwarded to fn.

    Returns:
        Whatever fn returns.

    Raises:
        AmadeusAPIError: After all retries exhausted.
    """
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)

        except Exception as e:
            last_exc = e
            msg = str(e).upper()

            # Non-retryable: auth / bad-request errors
            if any(code in msg for code in ["[400]", "[401]", "[403]", "[404]"]):
                logger.warning("Amadeus non-retryable error (attempt %d): %s", attempt + 1, e)
                raise AmadeusAPIError(str(e)) from e

            # Retryable: server / rate-limit errors
            if attempt < max_retries - 1:
                delay = retry_delay * (2 ** attempt)
                logger.warning(
                    "Amadeus transient error (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1, max_retries, delay, e,
                )
                time.sleep(delay)
            else:
                logger.error("Amadeus call failed after %d attempts: %s", max_retries, e)

    raise AmadeusAPIError(f"Amadeus call failed after {max_retries} attempts: {last_exc}") from last_exc


