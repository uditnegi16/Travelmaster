# api/stripe_routes.py
from __future__ import annotations
import os
from typing import Any, cast, Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from utils.clerk_auth import get_clerk_payload
from utils.supabase_client import supabase as _supabase

supabase = cast(Any, _supabase)
router = APIRouter(prefix="/me", tags=["stripe"])

STRIPE_SECRET_KEY    = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID      = os.getenv("STRIPE_PRICE_ID", "")       # your recurring price ID
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
APP_URL              = os.getenv("APP_URL", "http://localhost:5173")


async def current_user_payload(request: Request) -> Dict[str, Any]:
    auth = request.headers.get("authorization") or ""
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth.split(" ", 1)[1].strip()
    return get_clerk_payload(token)


def _get_account(payload: Dict[str, Any]) -> Dict[str, Any]:
    clerk_id = payload.get("sub")
    res = supabase.schema("user_db").table("user_profiles").select(
        "account_id, email, name, tier"
    ).eq("clerk_user_id", clerk_id).limit(1).execute()
    rows = getattr(res, "data", None) or []
    if not rows:
        raise HTTPException(status_code=404, detail="Profile not found")
    return rows[0]


@router.post("/create-checkout-session")
def create_checkout_session(
    payload: Dict[str, Any] = Depends(current_user_payload),
):
    """
    Creates a Stripe Checkout session and returns the URL.
    Frontend redirects user to this URL to complete payment.
    """
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        # Stripe not configured — return demo response
        return {
            "url": f"{APP_URL}/app/premium?demo=true",
            "demo": True,
            "message": "Stripe not configured. Set STRIPE_SECRET_KEY and STRIPE_PRICE_ID in .env to enable real payments."
        }

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
    except ImportError:
        raise HTTPException(status_code=500, detail="Stripe not installed. Run: pip install stripe")

    user = _get_account(payload)

    # Create Stripe customer if needed (idempotent)
    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        customer_email=user.get("email") or "",
        success_url=f"{APP_URL}/app/premium?success=true",
        cancel_url=f"{APP_URL}/app/premium?cancelled=true",
        metadata={"account_id": user["account_id"]},
    )

    return {"url": session.url}


@router.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    """
    Stripe calls this after successful payment.
    Upgrades user tier to premium automatically.
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Webhook secret not configured")

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
    except ImportError:
        raise HTTPException(status_code=500, detail="Stripe not installed")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")

    # Handle successful subscription
    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]
        account_id = session_data.get("metadata", {}).get("account_id")
        if account_id:
            supabase.schema("user_db").table("user_profiles").update(
                {"tier": "premium", "searches_this_month": 0}
            ).eq("account_id", account_id).execute()

    # Handle subscription cancelled
    if event["type"] in ("customer.subscription.deleted", "customer.subscription.paused"):
        customer_email = event["data"]["object"].get("customer_email")
        if customer_email:
            supabase.schema("user_db").table("user_profiles").update(
                {"tier": "free"}
            ).eq("email", customer_email).execute()

    return {"received": True}