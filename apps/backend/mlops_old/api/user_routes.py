from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Any, cast
from datetime import date,datetime

from utils.supabase_client import supabase as _supabase
from utils.clerk_auth import get_clerk_payload
from pydantic import BaseModel, Field
from typing import Optional, Literal
import os
import requests
AGENT_URL = os.getenv("AGENT_URL", "http://127.0.0.1:8001/agent/plan-trip")

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
class CreateSessionFromChatIn(BaseModel):
    user_query: str = Field(..., min_length=2)

class CreateMessageIn(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content: str = Field(..., min_length=1)
    metadata: Optional[dict] = None
class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content: str
    metadata: Optional[dict] = None
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
        "data_source": "LIVE",
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
@router.post("/sessions/from-chat")
def create_session_from_chat(body: CreateSessionFromChatIn, payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _ensure_account_id_from_clerk(clerk_id)

    # NOTE: This is placeholder session metadata (chat-first UX).
    # Real structured fields will be filled/updated later by agent + mlops pipeline.
    insert_row = {
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
        # last_activity_at uses DB default now()
    }

    supabase.schema("duosi").table("search_sessions").insert(insert_row).execute()

    # Fetch latest for this user (MVP-safe)
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

    return {"search_id": fetch.data[0]["search_id"]}

@router.get("/analytics")
def my_analytics(payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _get_account_id_from_clerk(clerk_id)
    if not account_id:
        return {
            "total_trips": 0,
            "average_budget": 0,
            "most_visited_destination": None,
            "most_visited_count": 0,
            "upcoming_trips": 0,
        }

    res = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("search_id,to_location,budget,start_date,created_at")
        .eq("account_id", account_id)
        .execute()
    )

    rows = res.data or []
    total_trips = len(rows)

    budgets = [r.get("budget") for r in rows if r.get("budget") is not None]
    avg_budget = round(sum(budgets) / len(budgets), 2) if budgets else 0

    dest_counts: dict[str, int] = {}
    for r in rows:
        d = (r.get("to_location") or "").strip()
        if d:
            dest_counts[d] = dest_counts.get(d, 0) + 1

    most_dest = None
    most_dest_count = 0
    if dest_counts:
        most_dest = max(dest_counts.keys(), key=lambda k: dest_counts[k])
        most_dest_count = dest_counts.get(most_dest, 0)


    today = date.today().isoformat()
    upcoming_trips = sum(1 for r in rows if (r.get("start_date") or "") >= today)

    return {
        "total_trips": total_trips,
        "average_budget": avg_budget,
        "most_visited_destination": most_dest,
        "most_visited_count": most_dest_count,
        "upcoming_trips": upcoming_trips,
    }



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
def post_session_message(session_id: str, body: CreateMessageIn, payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _get_account_id_from_clerk(clerk_id)
    if not account_id:
        raise HTTPException(status_code=404, detail="Profile not found")

    # ownership check
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

    # insert message
    supabase.schema("duosi").table("chat_messages").insert(
        {
            "search_id": session_id,
            "role": body.role,
            "content": body.content,
            "metadata": body.metadata or {},
        }
    ).execute()

    # update last activity
    supabase.schema("duosi").table("search_sessions").update(
        {"last_activity_at": "now()"}
    ).eq("search_id", session_id).eq("account_id", account_id).execute()

    # fetch newest message (return shape matches frontend)
    fetch = (
        supabase.schema("duosi")
        .table("chat_messages")
        .select("message_id, role, content, created_at")
        .eq("search_id", session_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not fetch.data:
        raise HTTPException(status_code=500, detail="Message inserted but could not be fetched")

    return fetch.data[0]


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
# @router.post("/sessions/{session_id}/messages")
# def add_message(session_id: str, payload: ChatMessageIn, auth=Depends(current_user_payload)):
#     clerk_id = auth.get("sub")
#     if not clerk_id:
#         raise HTTPException(status_code=401, detail="Invalid token payload")

#     account_id = _get_account_id_from_clerk(clerk_id)
#     if not account_id:
#         raise HTTPException(status_code=404, detail="Profile not found")

#     # verify session belongs to user
#     sess = (
#         supabase.schema("duosi")
#         .table("search_sessions")
#         .select("search_id")
#         .eq("search_id", session_id)
#         .eq("account_id", account_id)
#         .limit(1)
#         .execute()
#     )
#     if not sess.data:
#         raise HTTPException(status_code=404, detail="Session not found")

#     # ins = (
#     #     supabase.schema("duosi")
#     #     .table("chat_messages")
#     #     .insert({
#     #         "search_id": session_id,
#     #         "role": payload.role,
#     #         "content": payload.content,
#     #         "metadata": payload.metadata or {},
#     #     })
#     #     .select("message_id, role, content, created_at")
#     #     .limit(1)
#     #     .execute()
#     # )
#     ins = (
#         supabase.schema("duosi")
#         .table("chat_messages")
#         .insert({
#             "search_id": session_id,      # session_id is the search_id
#             "role": payload.role,
#             "content": payload.content,
#             "metadata": payload.metadata or {},
#         })
#         .execute()
#     )

#     row = ins.data[0] if getattr(ins, "data", None) else None
#     return row if row else {"ok": True}

# 

from typing import List, Dict, Any, Tuple
import math

# ----------------------------
# Helpers: safe ranking logic
# ----------------------------

def _safe_float(x: Any) -> float:
    try:
        if x is None:
            return math.inf
        return float(x)
    except Exception:
        return math.inf

def _duration_to_minutes(val: Any) -> int:
    """
    Accepts:
      - int minutes
      - "8h 30m"
      - "PT8H30M"
      - "510" (string)
    Returns minutes (int). Unknown -> large number.
    """
    if val is None:
        return 10**9
    if isinstance(val, (int, float)):
        return int(val)

    s = str(val).strip().upper()

    # plain numeric
    if s.isdigit():
        return int(s)

    # "8H 30M"
    h = 0
    m = 0
    try:
        # ISO-8601 duration: PT8H30M
        if s.startswith("PT"):
            s2 = s[2:]
            # crude parse
            if "H" in s2:
                h = int(s2.split("H")[0])
                s2 = s2.split("H")[1]
            if "M" in s2:
                m = int(s2.split("M")[0])
            return h * 60 + m

        # human "8H 30M"
        parts = s.replace(" ", "")
        if "H" in parts:
            h = int(parts.split("H")[0])
            parts = parts.split("H")[1]
        if "M" in parts:
            m = int(parts.split("M")[0])
        total = h * 60 + m
        return total if total > 0 else 10**9
    except Exception:
        return 10**9

def _rank_flights_simple(flights: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Minimal ranking (works today even if ML models aren’t wired yet):
      score = cheaper + shorter + fewer stops
    Keeps all original keys (including booking links).
    """
    ranked = []
    for f in flights or []:
        price = _safe_float(f.get("price"))
        dur = _duration_to_minutes(f.get("duration") or f.get("duration_minutes"))
        stops = _safe_float(f.get("stops", 0))
        score = (1.0 / (1.0 + price)) + (1.0 / (1.0 + dur)) + (1.0 / (1.0 + stops))
        ff = dict(f)
        ff["_score"] = score
        ranked.append(ff)

    ranked.sort(key=lambda x: x.get("_score", -1), reverse=True)

    meta = {
        "ranking_method": "simple_v1",
        "features": ["price", "duration_minutes", "stops"],
        "note": "Replace later with trained flight ranker output.",
    }
    return ranked, meta

def _rank_hotels_simple(hotels: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Minimal ranking:
      score = higher rating + cheaper price_per_night
    Keeps all original keys (including booking links).
    """
    ranked = []
    for h in hotels or []:
        rating = _safe_float(h.get("rating") or h.get("stars") or h.get("star_rating"))
        price = _safe_float(h.get("price_per_night") or h.get("price"))
        # if rating missing treat as 0
        rating_val = 0.0 if math.isinf(rating) else rating
        score = (rating_val) + (1.0 / (1.0 + price))
        hh = dict(h)
        hh["_score"] = score
        ranked.append(hh)

    ranked.sort(key=lambda x: x.get("_score", -1), reverse=True)

    meta = {
        "ranking_method": "simple_v1",
        "features": ["rating/stars", "price_per_night"],
        "note": "Replace later with trained hotel ranker output.",
    }
    return ranked, meta


# ----------------------------
# Rank + fetch ranked endpoints
# ----------------------------

# @router.post("/sessions/{session_id}/rank")
# def rank_session(session_id: str, auth=Depends(current_user_payload)):
#     clerk_id = auth.get("sub")
#     if not clerk_id:
#         raise HTTPException(status_code=401, detail="Invalid token payload")

#     account_id = _get_account_id_from_clerk(clerk_id)
#     if not account_id:
#         raise HTTPException(status_code=404, detail="Profile not found")

#     # verify session belongs to user
#     sess = (
#         supabase.schema("duosi").table("search_sessions")
#         .select("search_id")
#         .eq("search_id", session_id)
#         .eq("account_id", account_id)
#         .limit(1)
#         .execute()
#     )
#     if not sess.data:
#         raise HTTPException(status_code=404, detail="Session not found")

#     # fetch raw agent output snapshot
#     raw = (
#         supabase.schema("duosi").table("search_results")
#         .select("flights, hotels, places, weather, budget, narrative, agent_status, updated_at")
#         .eq("search_id", session_id)
#         .limit(1)
#         .execute()
#     )
#     if not raw.data:
#         raise HTTPException(status_code=400, detail="No search_results found. Run agent first.")

#     raw_row = raw.data[0]
#     flights = raw_row.get("flights") or []
#     hotels = raw_row.get("hotels") or []

#     ranked_flights, flight_meta = _rank_flights_simple(flights)
#     ranked_hotels, hotel_meta = _rank_hotels_simple(hotels)

#     # recommended vs others (tune counts later)
#     rec_flights = ranked_flights[:3]
#     other_flights = ranked_flights[3:]
#     rec_hotels = ranked_hotels[:3]
#     other_hotels = ranked_hotels[3:]

#     ranking_metadata = {
#         "generated_at": datetime.utcnow().isoformat(),
#         "flight": flight_meta,
#         "hotel": hotel_meta,
#         "raw_status": raw_row.get("agent_status"),
#     }

#     # upsert into ranked_results
#     supabase.schema("duosi").table("ranked_results").upsert({
#         "search_id": session_id,
#         "recommended_flights": rec_flights,
#         "other_flights": other_flights,
#         "recommended_hotels": rec_hotels,
#         "other_hotels": other_hotels,
#         "ranking_metadata": ranking_metadata,
#     }).execute()

#     # bump last activity
#     supabase.schema("duosi").table("search_sessions").update({
#         "last_activity_at": datetime.utcnow().isoformat()
#     }).eq("search_id", session_id).execute()

#     return {
#         "ok": True,
#         "search_id": session_id,
#         "counts": {
#             "flights_total": len(ranked_flights),
#             "hotels_total": len(ranked_hotels),
#             "recommended_flights": len(rec_flights),
#             "recommended_hotels": len(rec_hotels),
#         },
#     }


# @router.get("/sessions/{session_id}/ranked")
# def get_ranked(session_id: str, auth=Depends(current_user_payload)):
#     clerk_id = auth.get("sub")
#     if not clerk_id:
#         raise HTTPException(status_code=401, detail="Invalid token payload")

#     account_id = _get_account_id_from_clerk(clerk_id)
#     if not account_id:
#         raise HTTPException(status_code=404, detail="Profile not found")

#     # verify ownership
#     sess = (
#         supabase.schema("duosi").table("search_sessions")
#         .select("search_id")
#         .eq("search_id", session_id)
#         .eq("account_id", account_id)
#         .limit(1)
#         .execute()
#     )
#     if not sess.data:
#         raise HTTPException(status_code=404, detail="Session not found")

#     ranked = (
#         supabase.schema("duosi").table("ranked_results")
#         .select("*")
#         .eq("search_id", session_id)
#         .limit(1)
#         .execute()
#     )
#     if not ranked.data:
#         return {
#             "search_id": session_id,
#             "recommended_flights": [],
#             "other_flights": [],
#             "recommended_hotels": [],
#             "other_hotels": [],
#             "ranking_metadata": {},
#             "ready": False,
#         }

#     row = ranked.data[0]
#     row["ready"] = True
#     return row


@router.get("/sessions/{session_id}/results")
def get_raw_results(session_id: str, auth=Depends(current_user_payload)):
    clerk_id = auth.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _get_account_id_from_clerk(clerk_id)
    if not account_id:
        raise HTTPException(status_code=404, detail="Profile not found")

    # verify ownership
    sess = (
        supabase.schema("duosi").table("search_sessions")
        .select("search_id")
        .eq("search_id", session_id)
        .eq("account_id", account_id)
        .limit(1)
        .execute()
    )
    if not sess.data:
        raise HTTPException(status_code=404, detail="Session not found")

    raw = (
        supabase.schema("duosi").table("search_results")
        .select("*")
        .eq("search_id", session_id)
        .limit(1)
        .execute()
    )

    return raw.data[0] if raw.data else {}
