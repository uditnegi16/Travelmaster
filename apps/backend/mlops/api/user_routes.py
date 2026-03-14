# api/user_routes.py

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from utils.clerk_auth import get_clerk_payload
from utils.supabase_client import supabase as _supabase

logger = logging.getLogger(__name__)
supabase = cast(Any, _supabase)

router = APIRouter(prefix="/me", tags=["user"])


# ── Auth dependency ───────────────────────────────────────────────
def current_user_payload(request: Request) -> Dict[str, Any]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth.split(" ", 1)[1].strip()
    return get_clerk_payload(token)


# ── Supabase helpers ──────────────────────────────────────────────
def _get_account_id(clerk_id: str) -> Optional[str]:
    res = (
        supabase.schema("user_db")
        .table("user_profiles")
        .select("account_id")
        .eq("clerk_user_id", clerk_id)
        .limit(1)
        .execute()
    )
    data = getattr(res, "data", None) or []
    return data[0].get("account_id") if data else None


def _ensure_account_id(clerk_id: str) -> str:
    """Get or auto-create a user_profile row, return account_id."""
    account_id = _get_account_id(clerk_id)
    if account_id:
        return account_id

    created = (
        supabase.schema("user_db")
        .table("user_profiles")
        .insert({"clerk_user_id": clerk_id})
        .select("account_id")
        .execute()
    )
    data = getattr(created, "data", None) or []
    if not data:
        raise HTTPException(status_code=500, detail="Failed to auto-create user profile")
    return data[0]["account_id"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Pydantic schemas ──────────────────────────────────────────────
class CreateSessionIn(BaseModel):
    from_location: str = Field(..., min_length=1)
    to_location: str = Field(..., min_length=1)
    start_date: str
    end_date: str
    num_adults: int = 1
    num_children: int = 0
    budget: Optional[float] = None
    trip_type: Optional[str] = "leisure"
    session_title: Optional[str] = None


class CreateSessionFromChatIn(BaseModel):
    user_query: str = Field(..., min_length=1)


class CreateMessageIn(BaseModel):
    role: str = "user"
    content: str = Field(..., min_length=1)
    metadata: Optional[dict] = None


# ── Routes ────────────────────────────────────────────────────────

@router.get("")
def me(payload: Dict[str, Any] = Depends(current_user_payload)):
    """Return or auto-create the current user's profile."""
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing sub")

    res = (
        supabase.schema("user_db")
        .table("user_profiles")
        .select("*")
        .eq("clerk_user_id", clerk_id)
        .limit(1)
        .execute()
    )
    data = getattr(res, "data", None) or []
    if data:
        return data[0]

    # Auto-create on first sign-in
    created = (
        supabase.schema("user_db")
        .table("user_profiles")
        .insert({"clerk_user_id": clerk_id})
        .select("*")
        .execute()
    )
    created_data = getattr(created, "data", None) or []
    if not created_data:
        raise HTTPException(status_code=500, detail="Failed to create user profile")

    # Send welcome email (non-blocking — never fails the request)
    try:
        import os
        from utils.email_service import send_welcome_email
        new_profile = created_data[0]
        if new_profile.get("email"):
            send_welcome_email(
                to=new_profile["email"],
                user_name=new_profile.get("name") or "",
                app_url=os.getenv("APP_URL", "http://localhost:5173"),
            )
    except Exception as _e:
        logger.warning(f"Welcome email failed (non-fatal): {_e}")

    return created_data[0]


@router.patch("")
async def update_me(request: Request, payload: Dict[str, Any] = Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    body = await request.json()
    allowed = {"name", "email", "address", "age", "company", "gender"}
    patch = {k: v for k, v in (body or {}).items() if k in allowed}
    if not patch:
        return {"ok": True, "updated": False}

    res = (
        supabase.schema("user_db")
        .table("user_profiles")
        .update(patch)
        .eq("clerk_user_id", clerk_id)
        .select("*")
        .execute()
    )
    data = getattr(res, "data", None) or []
    return data[0] if data else {"ok": True}


@router.get("/analytics")
def my_analytics(payload: Dict[str, Any] = Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    account_id = _get_account_id(clerk_id)
    empty = {"total_trips": 0, "average_budget": 0, "most_visited_destination": None,
             "most_visited_count": 0, "upcoming_trips": 0}
    if not account_id:
        return empty

    res = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("search_id,to_location,budget,start_date")
        .eq("account_id", account_id)
        .execute()
    )
    rows = getattr(res, "data", None) or []
    if not rows:
        return empty

    total = len(rows)
    budgets = [r["budget"] for r in rows if r.get("budget") is not None]
    avg_budget = round(sum(budgets) / len(budgets), 2) if budgets else 0

    dest_counts: Dict[str, int] = {}
    for r in rows:
        d = (r.get("to_location") or "").strip()
        if d and d != "—":
            dest_counts[d] = dest_counts.get(d, 0) + 1

    most_dest = None
    most_dest_count = 0
    if dest_counts:
        most_dest = max(dest_counts, key=lambda k: dest_counts[k])
        most_dest_count = dest_counts[most_dest]

    today = date.today().isoformat()
    upcoming = sum(1 for r in rows if (r.get("start_date") or "") >= today)

    return {
        "total_trips": total,
        "average_budget": avg_budget,
        "most_visited_destination": most_dest,
        "most_visited_count": most_dest_count,
        "upcoming_trips": upcoming,
    }


@router.get("/sessions")
def my_sessions(payload: Dict[str, Any] = Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    account_id = _get_account_id(clerk_id)
    if not account_id:
        return []

    res = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("*")
        .eq("account_id", account_id)
        .order("last_activity_at", desc=True)
        .execute()
    )
    return getattr(res, "data", None) or []


@router.post("/sessions")
def create_session(body: CreateSessionIn, payload: Dict[str, Any] = Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    account_id = _ensure_account_id(clerk_id)
    title = body.session_title or f"{body.from_location} → {body.to_location}"
    now = _now_iso()

    row = {
        "account_id": account_id,
        "from_location": body.from_location,
        "to_location": body.to_location,
        "start_date": body.start_date,
        "end_date": body.end_date,
        "num_adults": body.num_adults,
        "num_children": body.num_children,
        "budget": body.budget,
        "trip_type": body.trip_type,
        "session_title": title,
        "agent_status": "ACTIVE",
        "data_source": "LIVE",
        "last_activity_at": now,
    }

    supabase.schema("duosi").table("search_sessions").insert(row).execute()

    fetch = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("*")
        .eq("account_id", account_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    data = getattr(fetch, "data", None) or []
    if not data:
        raise HTTPException(status_code=500, detail="Session created but could not be fetched")
    return data[0]


@router.post("/sessions/from-chat")
def create_session_from_chat(
    body: CreateSessionFromChatIn,
    payload: Dict[str, Any] = Depends(current_user_payload),
):
    """
    Chat-first session creation. Stores raw user_query in agent_request.
    The /run endpoint will parse it and fill structured fields later.
    """
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    account_id = _ensure_account_id(clerk_id)
    now = _now_iso()

    row = {
        "account_id": account_id,
        "from_location": "—",
        "to_location": "—",
        "start_date": str(date.today()),
        "end_date": str(date.today()),
        "num_adults": 1,
        "num_children": 0,
        "budget": None,
        "trip_type": "leisure",
        "session_title": "New Trip",
        "agent_status": "ACTIVE",
        "data_source": "LIVE",
        "agent_request": {"user_query": body.user_query},
        "last_activity_at": now,
    }

    supabase.schema("duosi").table("search_sessions").insert(row).execute()

    fetch = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("search_id")
        .eq("account_id", account_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    data = getattr(fetch, "data", None) or []
    if not data:
        raise HTTPException(status_code=500, detail="Session created but could not be fetched")

    return {"search_id": data[0]["search_id"]}


@router.get("/sessions/{session_id}")
def session_detail(session_id: str, payload: Dict[str, Any] = Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    account_id = _get_account_id(clerk_id)
    if not account_id:
        raise HTTPException(status_code=404, detail="Profile not found")

    res = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("*")
        .eq("search_id", session_id)
        .eq("account_id", account_id)
        .limit(1)
        .execute()
    )
    data = getattr(res, "data", None) or []
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data[0]


@router.get("/sessions/{session_id}/messages")
def session_messages(session_id: str, payload: Dict[str, Any] = Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    account_id = _get_account_id(clerk_id)
    if not account_id:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Verify ownership
    sess = (
        supabase.schema("duosi").table("search_sessions")
        .select("search_id")
        .eq("search_id", session_id)
        .eq("account_id", account_id)
        .limit(1)
        .execute()
    )
    if not getattr(sess, "data", None):
        raise HTTPException(status_code=404, detail="Session not found")

    msgs = (
        supabase.schema("duosi").table("chat_messages")
        .select("message_id, role, content, created_at, metadata")
        .eq("search_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )
    return getattr(msgs, "data", None) or []


@router.get("/sessions/{session_id}/saved")
def is_session_saved(session_id: str, payload: Dict[str, Any] = Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    account_id = _ensure_account_id(clerk_id)
    res = (
        supabase.schema("hud").table("saved_sessions")
        .select("id")
        .eq("account_id", account_id)
        .eq("search_id", session_id)
        .limit(1)
        .execute()
    )
    return {"saved": bool(getattr(res, "data", None))}


@router.post("/sessions/{session_id}/save")
def save_session(session_id: str, payload: Dict[str, Any] = Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    account_id = _ensure_account_id(clerk_id)

    # Ownership check
    own = (
        supabase.schema("duosi").table("search_sessions")
        .select("search_id")
        .eq("search_id", session_id)
        .eq("account_id", account_id)
        .limit(1)
        .execute()
    )
    if not getattr(own, "data", None):
        raise HTTPException(status_code=404, detail="Session not found")

    supabase.schema("hud").table("saved_sessions").upsert(
        {"account_id": account_id, "search_id": session_id},
        on_conflict="account_id,search_id",
    ).execute()
    return {"ok": True}


@router.delete("/sessions/{session_id}/save")
def unsave_session(session_id: str, payload: Dict[str, Any] = Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    account_id = _ensure_account_id(clerk_id)
    supabase.schema("hud").table("saved_sessions") \
        .delete() \
        .eq("account_id", account_id) \
        .eq("search_id", session_id) \
        .execute()
    return {"ok": True}


@router.get("/saved-sessions")
def list_saved_sessions(payload: Dict[str, Any] = Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    account_id = _ensure_account_id(clerk_id)

    res = (
        supabase.schema("hud").table("saved_sessions")
        .select("search_id, created_at")
        .eq("account_id", account_id)
        .order("created_at", desc=True)
        .execute()
    )
    saved_ids = [r["search_id"] for r in (getattr(res, "data", None) or [])]
    if not saved_ids:
        return []

    sess = (
        supabase.schema("duosi").table("search_sessions")
        .select("*")
        .in_("search_id", saved_ids)
        .eq("account_id", account_id)
        .execute()
    )
    lookup = {s["search_id"]: s for s in (getattr(sess, "data", None) or [])}
    return [lookup[sid] for sid in saved_ids if sid in lookup]


@router.get("/sessions/{session_id}/results")
def get_raw_results(session_id: str, payload: Dict[str, Any] = Depends(current_user_payload)):
    """Return raw agent output from search_results table."""
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    account_id = _get_account_id(clerk_id)
    if not account_id:
        raise HTTPException(status_code=404, detail="Profile not found")

    sess = (
        supabase.schema("duosi").table("search_sessions")
        .select("search_id")
        .eq("search_id", session_id)
        .eq("account_id", account_id)
        .limit(1)
        .execute()
    )
    if not getattr(sess, "data", None):
        raise HTTPException(status_code=404, detail="Session not found")

    raw = (
        supabase.schema("duosi").table("search_results")
        .select("*")
        .eq("search_id", session_id)
        .limit(1)
        .execute()
    )
    data = getattr(raw, "data", None) or []
    return data[0] if data else {}


@router.get("/history")
def my_history(payload: Dict[str, Any] = Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    account_id = _get_account_id(clerk_id)
    if not account_id:
        return []

    hist = (
        supabase.schema("hud").table("user_history")
        .select("*")
        .eq("account_id", account_id)
        .order("created_at", desc=True)
        .execute()
    )
    return getattr(hist, "data", None) or []
