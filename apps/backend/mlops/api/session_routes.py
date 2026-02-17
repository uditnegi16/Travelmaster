from fastapi import APIRouter, Depends, Request, HTTPException
from utils.supabase_client import supabase
from utils.clerk_auth import get_clerk_payload

router = APIRouter(prefix="/me/sessions", tags=["sessions"])

def current_user_payload(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth_header.split(" ", 1)[1].strip()
    return get_clerk_payload(token)

def _get_account_id(clerk_id: str):
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

@router.get("/{search_id}")
def get_session(search_id: str, payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _get_account_id(clerk_id)
    if not account_id:
        raise HTTPException(status_code=404, detail="Profile not found")

    res = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("*")
        .eq("search_id", search_id)
        .eq("account_id", account_id)
        .limit(1)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Session not found")

    return res.data[0]

@router.get("/{search_id}/messages")
def get_messages(search_id: str, payload=Depends(current_user_payload)):
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    account_id = _get_account_id(clerk_id)
    if not account_id:
        raise HTTPException(status_code=404, detail="Profile not found")

    # ownership check (session must belong to this user)
    owns = (
        supabase.schema("duosi")
        .table("search_sessions")
        .select("search_id")
        .eq("search_id", search_id)
        .eq("account_id", account_id)
        .limit(1)
        .execute()
    )
    if not owns.data:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs = (
        supabase.schema("duosi")
        .table("chat_messages")
        .select("*")
        .eq("search_id", search_id)
        .order("created_at", desc=False)
        .execute()
    )
    return msgs.data or []
