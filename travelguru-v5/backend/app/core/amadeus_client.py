"""
Production-grade Amadeus API client for TravelGuru agentic AI system.

This module provides a thread-safe singleton client with:
- Lazy initialization
- Auto token refresh (handled by SDK)
- Exponential backoff retry logic
- Circuit breaker pattern
- Comprehensive error handling
- Structured logging
"""

from __future__ import annotations

import time
import threading
from typing import Callable, Any, Optional
from functools import wraps

from amadeus import Client, ResponseError

from backend.app.core.config import (
    AMADEUS_CLIENT_ID,
    AMADEUS_CLIENT_SECRET,
    AMADEUS_ENV,
    AMADEUS_TIMEOUT,
    AMADEUS_MAX_RETRIES,
)
from backend.app.core.logging import get_logger

logger = get_logger("backend.app.core.amadeus_client")


# ========================================
# Custom Exceptions
# ========================================

class AmadeusConfigError(RuntimeError):
    """Raised when Amadeus configuration is invalid or missing."""
    pass


class AmadeusAPIError(RuntimeError):
    """Raised when Amadeus API call fails after all retries."""
    pass


# ========================================
# Configuration Validation
# ========================================

def _validate_config() -> None:
    """
    Validate all required Amadeus configuration at import time.
    
    Raises:
        AmadeusConfigError: If any required config is missing or invalid.
    """
    missing = []
    
    if not AMADEUS_CLIENT_ID:
        missing.append("AMADEUS_CLIENT_ID")
    if not AMADEUS_CLIENT_SECRET:
        missing.append("AMADEUS_CLIENT_SECRET")
    if not AMADEUS_ENV:
        missing.append("AMADEUS_ENV")
    
    if missing:
        msg = f"Missing required Amadeus configuration: {', '.join(missing)}"
        logger.error(msg)
        raise AmadeusConfigError(msg)
    
    if AMADEUS_ENV not in ("test", "production"):
        msg = f"Invalid AMADEUS_ENV: {AMADEUS_ENV}. Must be 'test' or 'production'."
        logger.error(msg)
        raise AmadeusConfigError(msg)
    
    if AMADEUS_TIMEOUT <= 0:
        msg = f"Invalid AMADEUS_TIMEOUT: {AMADEUS_TIMEOUT}. Must be > 0."
        logger.error(msg)
        raise AmadeusConfigError(msg)
    
    if AMADEUS_MAX_RETRIES < 0:
        msg = f"Invalid AMADEUS_MAX_RETRIES: {AMADEUS_MAX_RETRIES}. Must be >= 0."
        logger.error(msg)
        raise AmadeusConfigError(msg)


# Validate at import time
_validate_config()


# ========================================
# Singleton Client Manager
# ========================================

class _AmadeusClientManager:
    """
    Thread-safe singleton manager for Amadeus API client.
    
    Implements lazy initialization with double-checked locking pattern.
    
    Circuit Breaker States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests blocked for timeout period
    
    Future enhancement (v2):
    - HALF-OPEN: Allow limited test requests after timeout to check recovery
    
    Current implementation uses binary CLOSED/OPEN states, which is sufficient
    for v1 production deployment.
    """
    
    _instance: Optional[Client] = None
    _lock = threading.Lock()
    _failure_count = 0
    _circuit_open = False
    _circuit_open_until: float = 0.0
    _circuit_breaker_lock = threading.Lock()
    
    # Circuit breaker thresholds
    _CIRCUIT_BREAKER_THRESHOLD = 5
    _CIRCUIT_BREAKER_TIMEOUT = 60.0  # seconds
    
    # TODO (v2): Add HALF-OPEN state with limited test requests
    # TODO (v2): Track successful requests in HALF-OPEN before full CLOSED transition
    
    @classmethod
    def get_client(cls) -> Client:
        """
        Get or create the singleton Amadeus client.
        
        Returns:
            Client: Configured Amadeus SDK client.
            
        Raises:
            AmadeusConfigError: If client creation fails.
        """
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking
                if cls._instance is None:
                    cls._instance = cls._create_client()
        return cls._instance
    
    @classmethod
    def _create_client(cls) -> Client:
        """
        Create and configure Amadeus client.
        
        Returns:
            Client: Configured Amadeus SDK client.
            
        Raises:
            AmadeusConfigError: If client creation fails.
        """
        try:
            logger.info(
                "Creating Amadeus API client",
                extra={
                    "environment": AMADEUS_ENV,
                    "timeout": AMADEUS_TIMEOUT,
                    "max_retries": AMADEUS_MAX_RETRIES,
                }
            )
            
            # Create client (SDK handles token management)
            client = Client(
                client_id=AMADEUS_CLIENT_ID,
                client_secret=AMADEUS_CLIENT_SECRET,
                hostname=AMADEUS_ENV,  # 'test' or 'production'
            )
            
            logger.info(
                "Amadeus API client created successfully",
                extra={"environment": AMADEUS_ENV}
            )
            
            # TODO: Initialize Prometheus metrics counter
            # TODO: Initialize OpenTelemetry tracer
            
            return client
            
        except Exception as e:
            msg = f"Failed to create Amadeus client: {e}"
            logger.error(msg, exc_info=True)
            raise AmadeusConfigError(msg) from e
    
    @classmethod
    def check_circuit_breaker(cls) -> None:
        """
        Check if circuit breaker is open.
        
        Raises:
            AmadeusAPIError: If circuit breaker is open.
        """
        with cls._circuit_breaker_lock:
            if cls._circuit_open:
                if time.time() < cls._circuit_open_until:
                    raise AmadeusAPIError(
                        f"Circuit breaker is OPEN. Too many failures. "
                        f"Retry after {int(cls._circuit_open_until - time.time())}s"
                    )
                else:
                    # Reset circuit breaker
                    logger.info("Circuit breaker reset - attempting recovery")
                    cls._circuit_open = False
                    cls._failure_count = 0
    
    @classmethod
    def record_failure(cls) -> None:
        """Record API failure and potentially open circuit breaker."""
        with cls._circuit_breaker_lock:
            cls._failure_count += 1
            if cls._failure_count >= cls._CIRCUIT_BREAKER_THRESHOLD:
                cls._circuit_open = True
                cls._circuit_open_until = time.time() + cls._CIRCUIT_BREAKER_TIMEOUT
                logger.error(
                    "Circuit breaker OPENED due to repeated failures",
                    extra={
                        "failure_count": cls._failure_count,
                        "reset_in_seconds": cls._CIRCUIT_BREAKER_TIMEOUT,
                    }
                )
    
    @classmethod
    def record_success(cls) -> None:
        """Record successful API call."""
        with cls._circuit_breaker_lock:
            if cls._failure_count > 0:
                cls._failure_count = 0
                logger.info("Failure count reset after successful call")


# ========================================
# Public API
# ========================================

def get_amadeus_client() -> Client:
    """
    Get the singleton Amadeus API client.
    
    Thread-safe lazy initialization. The SDK handles token refresh automatically.
    
    Returns:
        Client: Configured Amadeus SDK client.
        
    Raises:
        AmadeusConfigError: If configuration is invalid or client creation fails.
    """
    return _AmadeusClientManager.get_client()


def call_amadeus(fn: Callable[..., Any], **kwargs) -> Any:
    """
    Execute an Amadeus API call with retry logic and error handling.
    
    This is the STANDARD way to call Amadeus API. Always use this wrapper.
    It provides:
    - Exponential backoff retry
    - Circuit breaker protection
    - Rate limit header tracking
    - Structured logging
    - Metrics hooks (TODO)
    
    Args:
        fn: Callable that performs the Amadeus API call.
        **kwargs: Arguments to pass to the callable.
    
    Returns:
        Any: The result from the API call.
    
    Raises:
        AmadeusAPIError: If the call fails after all retries.
    
    Example:
        >>> client = get_amadeus_client()
        >>> result = call_amadeus(
        ...     client.shopping.flight_offers_search.get,
        ...     originLocationCode='NYC',
        ...     destinationLocationCode='MAD',
        ...     departureDate='2026-06-01',
        ...     adults=1
        ... )
        
    Note:
        - **Layered Retry Strategy**: Amadeus SDK may have internal retries.
          This wrapper adds application-level retry with exponential backoff,
          circuit breaker, and business logic (e.g., rate limit handling).
        - Both layers are fine and provide defense in depth.
        - If SDK retry causes issues, lower AMADEUS_MAX_RETRIES or disable SDK retry.
        - Current config (AMADEUS_MAX_RETRIES) is for this application layer only.
    """
    # Check circuit breaker
    _AmadeusClientManager.check_circuit_breaker()
    
    max_retries = AMADEUS_MAX_RETRIES
    base_delay = 1.0  # seconds
    
    for attempt in range(max_retries + 1):
        try:
            # TODO: Start OpenTelemetry span
            # TODO: Increment Prometheus request counter
            
            start_time = time.time()
            
            # Execute the API call
            result = fn(**kwargs)
            
            elapsed = time.time() - start_time
            
            # Extract rate limit headers if available
            rate_limit_info = _extract_rate_limit_headers(result)
            
            log_extra = {
                "function": fn.__name__ if hasattr(fn, '__name__') else str(fn),
                "attempt": attempt + 1,
                "elapsed_seconds": round(elapsed, 3),
            }
            
            if rate_limit_info:
                log_extra.update(rate_limit_info)
            
            logger.info(
                "Amadeus API call succeeded",
                extra=log_extra
            )
            
            # TODO: Record success metric in Prometheus
            # TODO: End OpenTelemetry span with success
            
            _AmadeusClientManager.record_success()
            return result
            
        except ResponseError as e:
            # Amadeus SDK exception
            status_code = getattr(e.response, 'status_code', None)
            error_detail = str(e)
            
            # Extract endpoint for future per-endpoint retry logic
            endpoint = fn.__name__ if hasattr(fn, '__name__') else None
            
            is_retryable = _is_retryable_error(status_code, endpoint=endpoint)
            is_final_attempt = attempt >= max_retries
            
            logger.warning(
                "Amadeus API call failed",
                extra={
                    "function": fn.__name__ if hasattr(fn, '__name__') else str(fn),
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "status_code": status_code,
                    "error": error_detail,
                    "retryable": is_retryable,
                }
            )
            
            # TODO: Increment Prometheus error counter
            
            if is_final_attempt or not is_retryable:
                _AmadeusClientManager.record_failure()
                
                msg = (
                    f"Amadeus API call failed after {attempt + 1} attempts: "
                    f"[{status_code}] {error_detail}"
                )
                logger.error(msg)
                
                # TODO: End OpenTelemetry span with error
                raise AmadeusAPIError(msg) from e
            
            # Exponential backoff
            delay = base_delay * (2 ** attempt)
            logger.info(f"Retrying in {delay}s...")
            time.sleep(delay)
            
        except Exception as e:
            # Unexpected error (network, timeout, etc.)
            is_final_attempt = attempt >= max_retries
            
            logger.warning(
                "Amadeus API call failed with unexpected error",
                extra={
                    "function": fn.__name__ if hasattr(fn, '__name__') else str(fn),
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
                exc_info=True,
            )
            
            if is_final_attempt:
                _AmadeusClientManager.record_failure()
                
                msg = f"Amadeus API call failed after {attempt + 1} attempts: {e}"
                logger.error(msg)
                
                # TODO: End OpenTelemetry span with error
                raise AmadeusAPIError(msg) from e
            
            # Exponential backoff
            delay = base_delay * (2 ** attempt)
            logger.info(f"Retrying in {delay}s...")
            time.sleep(delay)
    
    # Should never reach here
    raise AmadeusAPIError("Unexpected error in retry loop")


def health_check() -> bool:
    """
    Perform health check by pinging Amadeus API.
    
    Tests connectivity by querying /v1/reference-data/locations.
    
    Returns:
        bool: True if API is healthy, False otherwise.
    """
    try:
        logger.info("Performing Amadeus API health check")
        
        client = get_amadeus_client()
        
        # Simple query to verify connectivity
        response = client.reference_data.locations.get(
            keyword='LON',
            subType='AIRPORT'
        )
        
        is_healthy = response is not None
        
        if is_healthy:
            logger.info("Amadeus API health check: OK")
        else:
            logger.warning("Amadeus API health check: FAILED (empty response)")
        
        # TODO: Update Prometheus health gauge
        
        return is_healthy
        
    except ResponseError as e:
        logger.error(
            "Amadeus API health check failed",
            extra={
                "status_code": getattr(e.response, 'status_code', None),
                "error": str(e),
            }
        )
        return False
        
    except Exception as e:
        logger.error(
            "Amadeus API health check failed with unexpected error",
            extra={
                "error_type": type(e).__name__,
                "error": str(e),
            },
            exc_info=True,
        )
        return False


# ========================================
# Helper Functions
# ========================================

# TODO (v2): Per-endpoint retry classification
# Centralized retry rules for different Amadeus endpoints
# Example structure:
# _ENDPOINT_RETRY_RULES = {
#     'flight_offers_search': {
#         'retryable_status_codes': {429, 500, 502, 503, 504},
#         'max_retries_override': 3,
#     },
#     'flight_order': {
#         'retryable_status_codes': {429, 500, 502, 503, 504},
#         'max_retries_override': 1,  # Be careful with booking operations
#     },
#     'hotel_search': {
#         'retryable_status_codes': {429, 500, 502, 503, 504},
#         'max_retries_override': 3,
#     },
# }

def _is_retryable_error(status_code: Optional[int], endpoint: Optional[str] = None) -> bool:
    """
    Determine if an HTTP status code indicates a retryable error.
    
    Global classification for all Amadeus endpoints. Future enhancement may
    support per-endpoint classification (e.g., flights vs hotels may have
    different retry semantics).
    
    Args:
        status_code: HTTP status code from the response.
        endpoint: Optional endpoint identifier for per-endpoint logic (future use).
    
    Returns:
        bool: True if the error is retryable, False otherwise.
        
    TODO (v2): Implement per-endpoint retry classification:
        - Flight search: retry 429, 5xx
        - Booking: never retry 4xx (except 429), always retry 5xx
        - Price quotes: retry 5xx, careful with 429
    """
    # TODO: Check _ENDPOINT_RETRY_RULES[endpoint] if endpoint-specific rules exist
    # For now, use global classification
    
    if status_code is None:
        # Network errors, timeouts, etc.
        return True
    
    # 429 Rate Limit - retryable
    if status_code == 429:
        return True
    
    # 5xx Server Errors - retryable
    if 500 <= status_code < 600:
        return True
    
    # 4xx Client Errors (except 429) - not retryable
    # 401 Unauthorized - not retryable (bad credentials)
    # 400 Bad Request - not retryable
    # 404 Not Found - not retryable
    return False


def _extract_rate_limit_headers(result: Any) -> dict[str, Any]:
    """
    Extract rate limit headers from Amadeus API response.
    
    Amadeus returns:
    - X-RateLimit-Remaining: Requests remaining in current window
    - X-RateLimit-Reset: Timestamp when limit resets
    
    Args:
        result: Response object from Amadeus API call.
    
    Returns:
        dict: Rate limit information for logging, or empty dict if not available.
    """
    rate_limit_info = {}
    
    try:
        # Amadeus SDK response objects may have a response attribute
        if hasattr(result, 'response'):
            response = result.response
            headers = getattr(response, 'headers', {})
            
            remaining = headers.get('X-RateLimit-Remaining')
            reset = headers.get('X-RateLimit-Reset')
            
            if remaining is not None:
                rate_limit_info['rate_limit_remaining'] = remaining
                
                # Log warning if getting close to limit
                try:
                    remaining_int = int(remaining)
                    if remaining_int < 10:
                        logger.warning(
                            f"Approaching rate limit: {remaining_int} requests remaining",
                            extra={'rate_limit_remaining': remaining_int}
                        )
                except (ValueError, TypeError):
                    pass
            
            if reset is not None:
                rate_limit_info['rate_limit_reset'] = reset
                
            # TODO: Implement auto-throttling based on remaining quota
            # TODO: Emit Prometheus gauge for rate_limit_remaining
            
    except Exception as e:
        # Don't fail the request if we can't extract headers
        logger.debug(
            f"Could not extract rate limit headers: {e}",
            exc_info=True
        )
    
    return rate_limit_info
