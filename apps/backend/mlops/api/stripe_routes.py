# api/stripe_routes.py  (Razorpay)
from __future__ import annotations
import os
import hmac
import hashlib
from typing import Any, cast, Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from utils.clerk_auth import get_clerk_payload
from utils.supabase_client import supabase as _supabase

supabase = cast(Any, _supabase)
router = APIRouter(prefix="/me", tags=["payments"])

RAZORPAY_KEY_ID     = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
APP_URL             = os.getenv("APP_URL", "http://localhost:5173")

# ₹399/month in paise (Razorpay uses smallest currency unit)
PREMIUM_AMOUNT_PAISE = 39900


async def current_user_payload(request: Request) -> Dict[str, Any]:
    auth = request.headers.get("authorization") or ""
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth.split(" ", 1)[1].strip()
    return get_clerk_payload(token)


def _get_account(payload: Dict[str, Any]) -> Dict[str, Any]:
    clerk_id = payload.get("sub")
    res = (
        supabase.schema("user_db").table("user_profiles")
        .select("account_id, email, name, tier")
        .eq("clerk_user_id", clerk_id)
        .limit(1)
        .execute()
    )
    rows = getattr(res, "data", None) or []
    if not rows:
        raise HTTPException(status_code=404, detail="Profile not found")
    return rows[0]


# ── Create Razorpay order ──────────────────────────────────────────────────────

@router.post("/create-order")
def create_order(
    payload: Dict[str, Any] = Depends(current_user_payload),
):
    """
    Creates a Razorpay order and returns order_id + key_id to frontend.
    Frontend uses these to open Razorpay checkout popup.
    """
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        # Demo mode — Razorpay not configured
        return {
            "demo": True,
            "order_id": "demo_order_123",
            "key_id": "demo_key",
            "amount": PREMIUM_AMOUNT_PAISE,
            "currency": "INR",
            "message": "Razorpay not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env",
        }

    try:
        import razorpay
    except ImportError:
        raise HTTPException(status_code=500, detail="razorpay not installed. Run: pip install razorpay")

    user = _get_account(payload)

    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

    order = client.order.create({
        "amount": PREMIUM_AMOUNT_PAISE,
        "currency": "INR",
        "receipt": f"tg_{user['account_id'][:8]}",
        "notes": {
            "account_id": user["account_id"],
            "email": user.get("email") or "",
        },
    })

    return {
        "demo": False,
        "order_id": order["id"],
        "key_id": RAZORPAY_KEY_ID,
        "amount": PREMIUM_AMOUNT_PAISE,
        "currency": "INR",
        "name": user.get("name") or "Traveler",
        "email": user.get("email") or "",
    }


# ── Verify payment after popup closes ─────────────────────────────────────────

class VerifyPaymentIn(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("/verify-payment")
def verify_payment(
    body: VerifyPaymentIn,
    payload: Dict[str, Any] = Depends(current_user_payload),
):
    """
    Called by frontend after Razorpay popup closes successfully.
    Verifies signature, upgrades user to premium.
    """
    user = _get_account(payload)

    # Demo mode — no real keys
    if not RAZORPAY_KEY_SECRET:
        supabase.schema("user_db").table("user_profiles").update(
            {"tier": "premium", "searches_this_month": 0}
        ).eq("account_id", user["account_id"]).execute()
        return {"success": True, "tier": "premium", "demo": True}

    # Verify Razorpay signature
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        f"{body.razorpay_order_id}|{body.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if expected != body.razorpay_signature:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # Upgrade tier
    supabase.schema("user_db").table("user_profiles").update(
        {"tier": "premium", "searches_this_month": 0}
    ).eq("account_id", user["account_id"]).execute()

    return {"success": True, "tier": "premium", "demo": False}


# ── Webhook (optional — Razorpay server-to-server events) ────────────────────

@router.post("/razorpay-webhook")
async def razorpay_webhook(request: Request):
    """
    Optional Razorpay webhook for subscription cancellations.
    """
    body = await request.body()
    sig = request.headers.get("x-razorpay-signature", "")

    if RAZORPAY_KEY_SECRET and sig:
        expected = hmac.new(
            RAZORPAY_KEY_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        if expected != sig:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    import json
    event = json.loads(body)
    event_type = event.get("event", "")

    if event_type == "subscription.cancelled":
        email = (
            event.get("payload", {})
            .get("subscription", {})
            .get("entity", {})
            .get("notes", {})
            .get("email", "")
        )
        if email:
            supabase.schema("user_db").table("user_profiles").update(
                {"tier": "free"}
            ).eq("email", email).execute()

    return {"received": True}