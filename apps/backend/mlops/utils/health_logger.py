# utils/health_logger.py
from __future__ import annotations
import time
import logging
from typing import Any, cast
from utils.supabase_client import supabase as _supabase

supabase = cast(Any, _supabase)
logger = logging.getLogger(__name__)


def log_health(
    service: str,
    status: str,
    response_time_ms: int | None = None,
    error_message: str | None = None,
    metadata: dict | None = None,
) -> None:
    """Write a health check result to user_db.health_logs."""
    try:
        supabase.schema("user_db").table("health_logs").insert({
            "service": service,
            "status": status,
            "response_time_ms": response_time_ms,
            "error_message": error_message,
            "metadata": metadata or {},
        }).execute()
    except Exception as e:
        logger.error(f"Failed to write health log: {e}")


def ping_service(url: str, service_name: str, timeout: int = 5) -> dict:
    """Ping a service URL and log the result."""
    import httpx
    start = time.time()
    try:
        r = httpx.get(url, timeout=timeout)
        ms = int((time.time() - start) * 1000)
        status = "healthy" if r.status_code == 200 else "degraded"
        log_health(service_name, status, ms)
        return {"service": service_name, "status": status, "response_time_ms": ms}
    except Exception as e:
        ms = int((time.time() - start) * 1000)
        log_health(service_name, "down", ms, str(e))
        return {"service": service_name, "status": "down", "response_time_ms": ms, "error": str(e)}