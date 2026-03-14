# api/session_routes.py
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, cast
from fastapi import Request
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from utils.clerk_auth import get_clerk_payload
from utils.supabase_client import supabase as _supabase


from pipelines.flight_ranking import score_and_rank_flights
from pipelines.hotel_ranking import score_and_rank_hotels
    
# Agent adapter (calls your agent server)
from adapters.agent_adapter import AgentAdapter

import json
supabase = cast(Any, _supabase)

router = APIRouter(prefix="/me", tags=["sessions"])

AGENT_URL = os.getenv("AGENT_URL", "http://127.0.0.1:8001")


# -------------------------
# Auth dependency (matches api/user_routes.py style)

# -------------------------
async def current_user_payload(request: Request) -> Dict[str, Any]:
    auth = request.headers.get("authorization") or ""
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth.split(" ", 1)[1].strip()
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
    data = getattr(prof, "data", None) or []
    if not data:
        return None
    return data[0].get("account_id")


def _account_id(payload: Dict[str, Any]) -> str:
    clerk_id = payload.get("sub")
    if not clerk_id or not isinstance(clerk_id, str):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _get_account_id_from_clerk(clerk_id)
    if not account_id:
        raise HTTPException(status_code=404, detail="Profile not found")

    return account_id


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
    if not getattr(created, "data", None):
        raise HTTPException(status_code=500, detail="Failed to create profile")
    return created.data[0]["account_id"]
# def _assert_session_owner(search_id: str, account_id: str) -> Dict[str, Any]:
#     res = (
#         supabase.table("duosi.chat_messages")
#         .select("*")
#         .eq("search_id", search_id)
#         .eq("account_id", account_id)
#         .limit(1)
#         .execute()
#     )
#     rows = getattr(res, "data", None) or []
#     if not rows:
#         raise HTTPException(status_code=404, detail="Session not found")
#     return cast(Dict[str, Any], rows[0])
def _assert_session_owner(search_id: str, account_id: str) -> None:
    res = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("search_id")
        .eq("search_id", search_id)
        .eq("account_id", account_id)
        .limit(1)
        .execute()
    )
    if not getattr(res, "data", None):
        raise HTTPException(status_code=404, detail="Session not found")

# -------------------------
# Schemas
# -------------------------
class MessageIn(BaseModel):
    role: str = Field(..., description="user|assistant|system")
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RunIn(BaseModel):
    # Optional override; if not provided we'll use latest user message
    user_query: Optional[str] = None


class RankIn(BaseModel):
    # Placeholder for future controls (top_k, weights, etc.)
    top_k: Optional[int] = None


# -------------------------
# DB helpers
# -------------------------
# 
def _insert_message(
    search_id: str,
    role: str,
    content: str,
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    ins = (
        supabase.schema("duosi")
        .table("chat_messages")
        .insert(
            {
                "search_id": search_id,
                "role": role,
                "content": content,
                "metadata": metadata or {},
            }
        )
        .execute()
    )
    data = getattr(ins, "data", None) or []
    if not data:
        raise HTTPException(status_code=500, detail="Failed to write message")
    return cast(Dict[str, Any], data[0])


def _latest_user_message(search_id: str) -> Optional[str]:
    res = (
        supabase.schema("duosi").table("chat_messages")
        .select("content,created_at")
        .eq("search_id", search_id)
        .eq("role", "user")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = getattr(res, "data", None) or []
    if not rows:
        return None
    return cast(Dict[str, Any], rows[0]).get("content")
def _normalize_agent_status(raw: Any) -> str:
    s = (str(raw or "")).strip().upper()

    # map common agent outputs -> allowed values
    if s in {"OK", "DONE", "COMPLETED"}:
        return "SUCCESS"
    if s in {"FAIL", "FAILED", "ERROR"}:
        return "PARTIAL"  # safer: don’t violate constraint

    # already valid?
    if s in {"SUCCESS", "PARTIAL"}:
        return s

    # default
    return "PARTIAL"
def _upsert_search_results(search_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    up = supabase.schema("duosi").table("search_results").upsert({"search_id": search_id, **payload}).execute()
    data = getattr(up, "data", None) or []
    # upsert can return empty depending on supabase config
    return cast(Dict[str, Any], data[0]) if data else {"search_id": search_id, **payload}


def _get_search_results(search_id: str) -> Optional[Dict[str, Any]]:
    res = supabase.schema("duosi").table("search_results").select("*").eq("search_id", search_id).limit(1).execute()
    rows = getattr(res, "data", None) or []
    return cast(Dict[str, Any], rows[0]) if rows else None


# def _upsert_ranked_results(search_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
#     payload["agent_status"] = _normalize_agent_status(payload.get("agent_status"))
#     payload["narrative"] = payload.get("narrative") or ""   # ensure non-null if your column expects text
#     up = supabase.schema("duosi").table("ranked_results").upsert({"search_id": search_id, **payload}).execute()
#     data = getattr(up, "data", None) or []
#     return cast(Dict[str, Any], data[0]) if data else {"search_id": search_id, **payload}
def _upsert_ranked_results(search_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # ranked_results table (in your DB) does NOT have agent_status/narrative.
    # Don't inject columns that don't exist, otherwise PostgREST throws PGRST204.
    up = (
        supabase.schema("duosi")
        .table("ranked_results")
        .upsert({"search_id": search_id, **payload})
        .execute()
    )
    data = getattr(up, "data", None) or []
    return cast(Dict[str, Any], data[0]) if data else {"search_id": search_id, **payload}

def _get_ranked_results(search_id: str) -> Optional[Dict[str, Any]]:
    res = supabase.schema("duosi").table("ranked_results").select("*").eq("search_id", search_id).limit(1).execute()
    rows = getattr(res, "data", None) or []
    return cast(Dict[str, Any], rows[0]) if rows else None


# -------------------------
# Minimal ranking (Phase-3)
# Replace this later with your real models/feature scoring.
# -------------------------
def _minimal_rank(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    if not items:
        return {"recommended": [], "others": []}
    return {"recommended": [items[0]], "others": items[1:]}


# -------------------------
# Routes
# -------------------------
@router.post("/sessions/{session_id}/messages")
def post_message(
    session_id: str,
    body: MessageIn,
    payload: Dict[str, Any] = Depends(current_user_payload),
):
    account_id = _account_id(payload)
    _assert_session_owner(session_id, account_id)

    role = body.role.strip().lower()
    if role not in {"user", "assistant", "system"}:
        raise HTTPException(status_code=400, detail="Invalid role")

    return _insert_message(session_id, role, body.content, body.metadata)


@router.post("/sessions/{session_id}/run")
def run_agent(
    session_id: str,
    body: RunIn = RunIn(),
    payload: Dict[str, Any] = Depends(current_user_payload),
):
    """
    Calls your agent server and stores raw output into duosi.search_results.
    """
    account_id = _account_id(payload)
    _assert_session_owner(session_id, account_id)

    user_query = (body.user_query or "").strip() or (_latest_user_message(session_id) or "").strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Missing user query")

    adapter = AgentAdapter(agent_url=AGENT_URL)

    t0 = time.time()
    try:
        agent_out = adapter.call_agent({"user_query": user_query}) or {}
        ok = True
    except Exception as e:
        agent_out = {
            "flights": [],
            "hotels": [],
            "places": [],
            "weather": [],
            "budget": {},
            "narrative": f"Agent failed: {e}",
            "agent_status": "PARTIAL",
        }
        ok = False

    elapsed = round(time.time() - t0, 4)

    payload_row = {
        "flights": agent_out.get("flights") or [],
        "hotels": agent_out.get("hotels") or [],
        "places": agent_out.get("places") or [],
        "weather": agent_out.get("weather") or [],
        "budget": agent_out.get("budget") or {},
        "narrative": agent_out.get("narrative") or "",
        "agent_status": _normalize_agent_status(agent_out.get("agent_status")),
        "execution_time": float(agent_out.get("execution_time") or elapsed),
    }

    _upsert_search_results(session_id, payload_row)

    supabase.schema("duosi").table("search_sessions").update(
        {"agent_status": payload_row["agent_status"], "data_source": "LIVE"}
    ).eq("search_id", session_id).eq("account_id", account_id).execute()

    return {"search_id": session_id, **payload_row}


# @router.post("/sessions/{session_id}/rank")
# def rank_results(
#     session_id: str,
#     body: RankIn = RankIn(),
#     payload: Dict[str, Any] = Depends(current_user_payload),
# ):
@router.post("/sessions/{session_id}/rank")
def rank_results(
    request: Request,
    session_id: str,
    body: RankIn = RankIn(),
    payload: Dict[str, Any] = Depends(current_user_payload),
):
    print("RANK AUTH HEADER:", request.headers.get("authorization"))   
    """
    Reads duosi.search_results, runs ranking, stores into duosi.ranked_results.
    Also writes an assistant message (narrative) that the UI will display.
    """
    account_id = _account_id(payload)
    print("AUTH HEADER CHECK - RANK ENDPOINT HIT")
    _assert_session_owner(session_id, account_id)

    sr = _get_search_results(session_id)
    if not sr:
        raise HTTPException(status_code=400, detail="Run agent first (no search_results)")

    flights = cast(List[Dict[str, Any]], sr.get("flights") or [])
    hotels = cast(List[Dict[str, Any]], sr.get("hotels") or [])

    # prefs (simple + safe)
    user_pref_f = {
        "origin": (sr.get("from_location") or sr.get("origin") or "").strip(),
        "destination": (sr.get("to_location") or sr.get("destination") or "").strip(),
        "preferred_airlines": sr.get("preferred_airlines") or [],
    }
    user_pref_h = {
        "preferred_city": (sr.get("to_location") or sr.get("preferred_city") or "").strip(),
    }

    rec_f, other_f, meta_f = score_and_rank_flights(flights, user_pref=user_pref_f)
    rec_h, other_h, meta_h = score_and_rank_hotels(hotels, user_pref=user_pref_h)

    ranked_payload = {
        "recommended_flights": rec_f,
        "other_flights": other_f,
        "recommended_hotels": rec_h,
        "other_hotels": other_h,
        "ranking_metadata": {
            "flight": meta_f,
            "hotel": meta_h,
            "flight_count": len(flights),
            "hotel_count": len(hotels),
        },
    }
    _upsert_ranked_results(session_id, ranked_payload)

    supabase.schema("duosi").table("search_sessions").update(
        {"data_source": "LIVE","last_activity_at": "now()"}
    ).eq("search_id", session_id).eq("account_id", account_id).execute()

    narrative = (sr.get("narrative") or "").strip()
    if narrative:
        _insert_message(
        session_id,
        "assistant",
        json.dumps(ranked_payload),
        {"type": "ranked_result", "search_id": session_id},
    )

    return {"search_id": session_id, **ranked_payload}


# @router.get("/sessions/{session_id}/ranked")
# def get_ranked(
#     session_id: str,
#     payload: Dict[str, Any] = Depends(current_user_payload),
# ):
#     account_id = _account_id(payload)
#     _assert_session_owner(session_id, account_id)

#     rr = _get_ranked_results(session_id)
#     if not rr:
#         return {
#             "search_id": session_id,
#             "recommended_flights": [],
#             "other_flights": [],
#             "recommended_hotels": [],
#             "other_hotels": [],
#             "ranking_metadata": {"status": "empty"},
#         }

#     return {
#         "search_id": session_id,
#         "recommended_flights": rr.get("recommended_flights") or [],
#         "other_flights": rr.get("other_flights") or [],
#         "recommended_hotels": rr.get("recommended_hotels") or [],
#         "other_hotels": rr.get("other_hotels") or [],
#         "ranking_metadata": rr.get("ranking_metadata") or {},
#     }
@router.get("/sessions/{session_id}/ranked")
def get_ranked(
    session_id: str,
    payload: Dict[str, Any] = Depends(current_user_payload),
):
    account_id = _account_id(payload)
    _assert_session_owner(session_id, account_id)

    rr = _get_ranked_results(session_id) or {}
    sr = _get_search_results(session_id) or {}

    return {
        "search_id": session_id,

        # ranking output (may be empty if Amadeus returned nothing)
        "recommended_flights": rr.get("recommended_flights") or [],
        "other_flights": rr.get("other_flights") or [],
        "recommended_hotels": rr.get("recommended_hotels") or [],
        "other_hotels": rr.get("other_hotels") or [],
        "ranking_metadata": rr.get("ranking_metadata") or {},

        # raw agent output (what your UI calls “Narrative (places + budget + daily plan)”)
        "narrative": (sr.get("narrative") or "").strip(),
        "places": sr.get("places") or [],
        "weather": sr.get("weather") or [],
        "budget": sr.get("budget") or {},
        "agent_status": sr.get("agent_status") or "ok",
        "execution_time": sr.get("execution_time"),
    }