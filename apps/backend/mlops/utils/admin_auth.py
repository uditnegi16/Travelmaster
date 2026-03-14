# utils/admin_auth.py
from __future__ import annotations
from typing import Any, Dict, cast
from fastapi import HTTPException, Request
from utils.clerk_auth import get_clerk_payload
from utils.supabase_client import supabase as _supabase

supabase = cast(Any, _supabase)


def get_admin_payload(request: Request) -> Dict[str, Any]:
    """
    Validates Bearer token and checks admin_users table.
    Returns dict with clerk payload + admin role.
    Raises 401 if not authenticated, 403 if not an admin.
    """
    auth = request.headers.get("authorization") or ""
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = auth.split(" ", 1)[1].strip()
    payload = get_clerk_payload(token)

    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    res = (
        supabase.schema("user_db")
        .table("admin_users")
        .select("admin_id, role, is_active")
        .eq("clerk_user_id", clerk_id)
        .limit(1)
        .execute()
    )
    rows = getattr(res, "data", None) or []
    if not rows:
        raise HTTPException(status_code=403, detail="Admin access required")

    admin = rows[0]
    if not admin.get("is_active"):
        raise HTTPException(status_code=403, detail="Admin account is inactive")

    return {
        **payload,
        "admin_id": admin["admin_id"],
        "admin_role": admin["role"],
    }


def require_super_admin(admin_payload: Dict[str, Any]) -> None:
    """Call this inside any route that needs super_admin role."""
    if admin_payload.get("admin_role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")


def log_audit(
    admin_id: str,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """Write an entry to admin_audit_log. Never raises — audit failures are silent."""
    try:
        supabase.schema("user_db").table("admin_audit_log").insert({
            "admin_id": admin_id,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "metadata": metadata or {},
            "ip_address": ip_address,
        }).execute()
    except Exception:
        pass