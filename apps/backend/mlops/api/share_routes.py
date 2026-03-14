# api/share_routes.py
from __future__ import annotations
from typing import Any, cast
from fastapi import APIRouter, HTTPException
from utils.supabase_client import supabase as _supabase

supabase = cast(Any, _supabase)
router = APIRouter(prefix="/shared", tags=["shared"])


@router.get("/{share_token}")
def get_shared_trip(share_token: str):
    """
    Public endpoint — no auth required.
    Returns ranked results for a shared trip token.
    """
    # Look up token
    res = (
        supabase.schema("hud").table("shared_trips")
        .select("search_id, account_id, created_at")
        .eq("share_token", share_token)
        .limit(1)
        .execute()
    )
    rows = getattr(res, "data", None) or []
    if not rows:
        raise HTTPException(status_code=404, detail="Shared trip not found or link has been revoked.")

    search_id = rows[0]["search_id"]

    # Get session info
    sess = (
        supabase.schema("duosi").table("search_sessions")
        .select("from_location, to_location, start_date, end_date, session_title, num_adults")
        .eq("search_id", search_id)
        .limit(1)
        .execute()
    )
    sess_row = ((getattr(sess, "data", None) or [{}])[0])

    # Get ranked results
    rr_res = supabase.schema("duosi").table("ranked_results").select("*").eq("search_id", search_id).limit(1).execute()
    rr = ((getattr(rr_res, "data", None) or [{}])[0])

    # Get search results for narrative + places + weather + budget
    sr_res = supabase.schema("duosi").table("search_results").select("*").eq("search_id", search_id).limit(1).execute()
    sr = ((getattr(sr_res, "data", None) or [{}])[0])

    return {
        "share_token": share_token,
        "session": sess_row,
        "recommended_flights": rr.get("recommended_flights") or [],
        "other_flights": rr.get("other_flights") or [],
        "recommended_hotels": rr.get("recommended_hotels") or [],
        "other_hotels": rr.get("other_hotels") or [],
        "ranking_metadata": rr.get("ranking_metadata") or {},
        "narrative": sr.get("narrative") or "",
        "places": sr.get("places") or [],
        "weather": sr.get("weather") or [],
        "budget": sr.get("budget") or {},
    }