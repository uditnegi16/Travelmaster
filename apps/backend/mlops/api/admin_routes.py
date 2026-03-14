# api/admin_routes.py
from __future__ import annotations

import logging
from typing import Any, Dict, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from utils.admin_auth import get_admin_payload, require_super_admin, log_audit
from utils.supabase_client import supabase as _supabase

supabase = cast(Any, _supabase)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Schemas ───────────────────────────────────────────────────────
class TierUpdate(BaseModel):
    tier: str  # "free" or "premium"

class BanUpdate(BaseModel):
    is_banned: bool

class ConfigUpdate(BaseModel):
    value: str


# ── User management ───────────────────────────────────────────────
@router.get("/users")
def list_users(
    request: Request,
    page: int = 1,
    limit: int = 50,
    admin_payload: Dict[str, Any] = Depends(get_admin_payload),
):
    """List all users with tier, search count, ban status."""
    offset = (page - 1) * limit
    res = (
        supabase.schema("user_db")
        .table("user_profiles")
        .select("account_id, clerk_user_id, name, email, tier, searches_this_month, is_banned, created_at")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return getattr(res, "data", None) or []


@router.patch("/users/{account_id}/tier")
def update_user_tier(
    account_id: str,
    body: TierUpdate,
    request: Request,
    admin_payload: Dict[str, Any] = Depends(get_admin_payload),
):
    """Upgrade or downgrade user tier."""
    if body.tier not in {"free", "premium"}:
        raise HTTPException(status_code=400, detail="tier must be 'free' or 'premium'")

    supabase.schema("user_db").table("user_profiles").update(
        {"tier": body.tier}
    ).eq("account_id", account_id).execute()

    log_audit(
        admin_payload["admin_id"], "update_tier",
        target_type="user", target_id=account_id,
        metadata={"tier": body.tier},
        ip_address=request.client.host if request.client else None,
    )
    return {"ok": True, "account_id": account_id, "tier": body.tier}


@router.patch("/users/{account_id}/ban")
def ban_user(
    account_id: str,
    body: BanUpdate,
    request: Request,
    admin_payload: Dict[str, Any] = Depends(get_admin_payload),
):
    """Ban or unban a user."""
    supabase.schema("user_db").table("user_profiles").update(
        {"is_banned": body.is_banned}
    ).eq("account_id", account_id).execute()

    action = "ban_user" if body.is_banned else "unban_user"
    log_audit(
        admin_payload["admin_id"], action,
        target_type="user", target_id=account_id,
        ip_address=request.client.host if request.client else None,
    )
    return {"ok": True, "account_id": account_id, "is_banned": body.is_banned}


@router.post("/users/{account_id}/reset-limit")
def reset_user_limit(
    account_id: str,
    request: Request,
    admin_payload: Dict[str, Any] = Depends(get_admin_payload),
):
    """Reset monthly search counter for a user."""
    from datetime import datetime, timezone
    supabase.schema("user_db").table("user_profiles").update({
        "searches_this_month": 0,
        "searches_reset_at": datetime.now(timezone.utc).isoformat(),
    }).eq("account_id", account_id).execute()

    log_audit(
        admin_payload["admin_id"], "reset_search_limit",
        target_type="user", target_id=account_id,
        ip_address=request.client.host if request.client else None,
    )
    return {"ok": True, "account_id": account_id}


@router.get("/users/{account_id}/sessions")
def get_user_sessions(
    account_id: str,
    admin_payload: Dict[str, Any] = Depends(get_admin_payload),
):
    """View all sessions for a specific user."""
    res = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("*")
        .eq("account_id", account_id)
        .order("last_activity_at", desc=True)
        .execute()
    )
    return getattr(res, "data", None) or []


# ── Analytics ─────────────────────────────────────────────────────
@router.get("/analytics")
def admin_analytics(
    admin_payload: Dict[str, Any] = Depends(get_admin_payload),
):
    """Platform-wide analytics."""
    # Total users
    users_res = (
        supabase.schema("user_db").table("user_profiles")
        .select("account_id, tier, created_at")
        .execute()
    )
    users = getattr(users_res, "data", None) or []
    total_users = len(users)
    free_users = sum(1 for u in users if u.get("tier") == "free")
    premium_users = sum(1 for u in users if u.get("tier") == "premium")

    # Total searches
    sessions_res = (
        supabase.schema("duosi").table("search_sessions")
        .select("search_id, to_location, agent_status, last_activity_at")
        .execute()
    )
    sessions = getattr(sessions_res, "data", None) or []
    total_searches = len(sessions)
    success = sum(1 for s in sessions if s.get("agent_status") == "SUCCESS")
    agent_success_rate = round((success / total_searches * 100), 1) if total_searches else 0

    # Top destinations
    dest_counts: Dict[str, int] = {}
    for s in sessions:
        d = (s.get("to_location") or "").strip()
        if d and d != "—":
            dest_counts[d] = dest_counts.get(d, 0) + 1
    top_destinations = sorted(dest_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Searches today
    from datetime import date
    today = date.today().isoformat()
    searches_today = sum(
        1 for s in sessions
        if (s.get("last_activity_at") or "").startswith(today)
    )

    return {
        "total_users": total_users,
        "free_users": free_users,
        "premium_users": premium_users,
        "total_searches": total_searches,
        "searches_today": searches_today,
        "agent_success_rate": agent_success_rate,
        "top_destinations": [{"destination": d, "count": c} for d, c in top_destinations],
    }


# ── Health ────────────────────────────────────────────────────────
@router.get("/health")
def admin_health(
    admin_payload: Dict[str, Any] = Depends(get_admin_payload),
):
    """Latest health status per service from health_logs."""
    res = (
        supabase.schema("user_db").table("health_logs")
        .select("service, status, response_time_ms, error_message, checked_at")
        .order("checked_at", desc=True)
        .limit(50)
        .execute()
    )
    rows = getattr(res, "data", None) or []

    # Keep only latest per service
    seen: set = set()
    latest: list = []
    for row in rows:
        svc = row.get("service")
        if svc not in seen:
            seen.add(svc)
            latest.append(row)

    return latest


# ── Config ────────────────────────────────────────────────────────
@router.get("/config")
def get_config(
    admin_payload: Dict[str, Any] = Depends(get_admin_payload),
):
    """Read all app_config keys."""
    res = (
        supabase.schema("user_db").table("app_config")
        .select("*")
        .order("key")
        .execute()
    )
    return getattr(res, "data", None) or []


@router.patch("/config/{key}")
def update_config(
    key: str,
    body: ConfigUpdate,
    request: Request,
    admin_payload: Dict[str, Any] = Depends(get_admin_payload),
):
    """Update a config value. Logged to audit log."""
    supabase.schema("user_db").table("app_config").update({
        "value": body.value,
        "updated_by": admin_payload["admin_id"],
        "updated_at": __import__("datetime").datetime.utcnow().isoformat(),
    }).eq("key", key).execute()

    log_audit(
        admin_payload["admin_id"], "update_config",
        target_type="config", target_id=key,
        metadata={"value": body.value},
        ip_address=request.client.host if request.client else None,
    )
    return {"ok": True, "key": key, "value": body.value}


# ── Audit log ─────────────────────────────────────────────────────
@router.get("/audit-log")
def get_audit_log(
    page: int = 1,
    limit: int = 50,
    admin_payload: Dict[str, Any] = Depends(get_admin_payload),
):
    """Paginated audit log."""
    offset = (page - 1) * limit
    res = (
        supabase.schema("user_db").table("admin_audit_log")
        .select("*")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return getattr(res, "data", None) or []


# ── Admin management (super_admin only) ───────────────────────────
@router.post("/admins")
def add_admin(
    request: Request,
    admin_payload: Dict[str, Any] = Depends(get_admin_payload),
):
    """Add a new admin user. Super admin only."""
    require_super_admin(admin_payload)
    # body handled manually to keep it flexible
    import asyncio
    body = {}
    try:
        import json
        body = json.loads(request._body if hasattr(request, "_body") else b"{}") # type: ignore
    except Exception:
        pass

    clerk_id = body.get("clerk_user_id")
    email = body.get("email")
    role = body.get("role", "analyst")

    if not clerk_id or not email:
        raise HTTPException(status_code=400, detail="clerk_user_id and email required")
    if role not in {"super_admin", "support", "analyst"}:
        raise HTTPException(status_code=400, detail="Invalid role")

    supabase.schema("user_db").table("admin_users").insert({
        "clerk_user_id": clerk_id,
        "email": email,
        "role": role,
        "is_active": True,
    }).execute()

    log_audit(
        admin_payload["admin_id"], "add_admin",
        target_type="admin", target_id=clerk_id,
        metadata={"email": email, "role": role},
        ip_address=request.client.host if request.client else None,
    )
    return {"ok": True}
