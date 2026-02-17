from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Any, cast

from utils.supabase_client import supabase as _supabase
from utils.clerk_auth import get_clerk_payload
from pydantic import BaseModel, Field
from typing import Optional, Literal

class CreateSessionIn(BaseModel):
    from_location: str = Field(..., min_length=2)
    to_location: str = Field(..., min_length=2)
    start_date: str  # "YYYY-MM-DD"
    end_date: str    # "YYYY-MM-DD"
    num_adults: int = 1
    num_children: int = 0
    budget: Optional[float] = None
    trip_type: Optional[str] = "leisure"
    session_title: Optional[str] = None

supabase = cast(Any, _supabase)

router = APIRouter(prefix="/me", tags=["user"])


def current_user_payload(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth_header.split(" ", 1)[1].strip()
    return get_clerk_payload(token)


def _get_account_id_from_clerk(clerk_id: str) -> str | None:
    prof = (
        supabase.schema("user_db")
        .table("user_profiles")
        .select("account_id")
        .eq("clerk_user_id", clerk_id)
        .limit(1)
        .execute()
    )
    if not prof.data:
        return None
    return prof.data[0].get("account_id")

def _ensure_account_id_from_clerk(clerk_id: str) -> str:
    account_id = _get_account_id_from_clerk(clerk_id)
    if account_id:
        return account_id

    created = (
        supabase.schema("user_db")
        .table("user_profiles")
        .insert({"clerk_user_id": clerk_id})
        .select("account_id")
        .execute()
    )
    if not created.data:
        raise HTTPException(status_code=500, detail="Failed to create profile")

    return created.data[0]["account_id"]

@router.get("")
def me(payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    res = (
        supabase.schema("user_db")
        .table("user_profiles")
        .select("*")
        .eq("clerk_user_id", clerk_id)
        .limit(1)
        .execute()
    )

    if res.data:
        return res.data[0]

    created = (
        supabase.schema("user_db")
        .table("user_profiles")
        .insert({"clerk_user_id": clerk_id})
        .select("*")
        .execute()
    )

    if not created.data:
        raise HTTPException(status_code=500, detail="Failed to create profile")

    return created.data[0]


@router.get("/sessions")
def my_sessions(payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _get_account_id_from_clerk(clerk_id)
    if not account_id:
        return []

    sessions = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("*")
        .eq("account_id", account_id)
        .order("last_activity_at", desc=True)
        .execute()
    )
    return sessions.data or []

@router.post("/sessions")
def create_session(body: CreateSessionIn, payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _ensure_account_id_from_clerk(clerk_id)

    title = body.session_title or f"{body.from_location} → {body.to_location}"

    insert_row = {
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
        "data_source": "DUMMY",
        # last_activity_at has DB default now()
    }

    res = (
        supabase.schema("duosi")
        .table("search_sessions")
        .insert(insert_row)
        .execute()
    )
    if not res.data:
        # Some Supabase clients return the inserted row(s) in data; if not, we fetch it.
        pass

    # Fetch latest session created for this user (safe enough for MVP)
    fetch = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("*")
        .eq("account_id", account_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not fetch.data:
        raise HTTPException(status_code=500, detail="Session created but could not be fetched")

    created = fetch.data[0]
    return created




# ✅ SINGLE truth: session detail
@router.get("/sessions/{session_id}")
def session_detail(session_id: str, payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _get_account_id_from_clerk(clerk_id)
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

    if not res.data:
        raise HTTPException(status_code=404, detail="Session not found")

    return res.data[0]


@router.get("/sessions/{session_id}/messages")
def session_messages(session_id: str, payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _get_account_id_from_clerk(clerk_id)
    if not account_id:
        raise HTTPException(status_code=404, detail="Profile not found")

    # verify session belongs to user
    sess = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("search_id")
        .eq("search_id", session_id)
        .eq("account_id", account_id)
        .limit(1)
        .execute()
    )
    if not sess.data:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs = (
        supabase.schema("duosi")
        .table("chat_messages")
        .select("message_id, role, content, created_at")
        .eq("search_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )
    return msgs.data or []


@router.get("/history")
def my_history(payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _get_account_id_from_clerk(clerk_id)
    if not account_id:
        return []

    hist = (
        supabase.schema("hud")
        .table("user_history")
        .select("*")
        .eq("account_id", account_id)
        .order("created_at", desc=True)
        .execute()
    )
    return hist.data or []


# ✅ SINGLE truth: saved
@router.get("/saved")
def my_saved(payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _get_account_id_from_clerk(clerk_id)
    if not account_id:
        return []

    saved = (
        supabase.schema("hud")
        .table("user_history")
        .select("*")
        .eq("account_id", account_id)
        .in_("action_type", ["SAVED", "SHORTLISTED"])
        .order("created_at", desc=True)
        .execute()
    )
    return saved.data or []


@router.patch("")
async def update_me(request: Request, payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

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
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None
@router.get("/saved-sessions")
def list_saved_sessions(payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _ensure_account_id_from_clerk(clerk_id)

    res = (
        supabase.schema("hud")
        .table("saved_sessions")
        .select("search_id, created_at")
        .eq("account_id", account_id)
        .order("created_at", desc=True)
        .execute()
    )

    saved_ids = [r["search_id"] for r in (res.data or [])]
    if not saved_ids:
        return []

    # Fetch sessions by ids
    sess = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("*")
        .in_("search_id", saved_ids)
        .eq("account_id", account_id)
        .execute()
    )

    # Preserve order of saved_ids
    lookup = {s["search_id"]: s for s in (sess.data or [])}
    return [lookup[sid] for sid in saved_ids if sid in lookup]
@router.post("/sessions/{session_id}/save")
def save_session(session_id: str, payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _ensure_account_id_from_clerk(clerk_id)

    # Ownership check
    own = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("search_id")
        .eq("search_id", session_id)
        .eq("account_id", account_id)
        .limit(1)
        .execute()
    )
    if not own.data:
        raise HTTPException(status_code=404, detail="Session not found")

    supabase.schema("hud").table("saved_sessions").upsert(
        {"account_id": account_id, "search_id": session_id},
        on_conflict="account_id,search_id",
    ).execute()

    return {"ok": True}
@router.delete("/sessions/{session_id}/save")
def unsave_session(session_id: str, payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _ensure_account_id_from_clerk(clerk_id)

    supabase.schema("hud").table("saved_sessions") \
        .delete() \
        .eq("account_id", account_id) \
        .eq("search_id", session_id) \
        .execute()

    return {"ok": True}
@router.get("/sessions/{session_id}/saved")
def is_session_saved(session_id: str, payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _ensure_account_id_from_clerk(clerk_id)

    res = (
        supabase.schema("hud")
        .table("saved_sessions")
        .select("id")
        .eq("account_id", account_id)
        .eq("search_id", session_id)
        .limit(1)
        .execute()
    )

    return {"saved": bool(res.data)}
