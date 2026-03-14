# utils/rate_limiter.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, cast
from fastapi import HTTPException
from utils.supabase_client import supabase as _supabase

supabase = cast(Any, _supabase)


def _get_config(key: str, default: int) -> int:
    try:
        res = (
            supabase.schema("user_db")
            .table("app_config")
            .select("value")
            .eq("key", key)
            .limit(1)
            .execute()
        )
        rows = getattr(res, "data", None) or []
        if rows:
            return int(rows[0]["value"])
    except Exception:
        pass
    return default


def check_and_increment_rate_limit(account_id: str) -> Dict[str, Any]:
    """
    Check if user has exceeded their monthly search limit.
    Increments counter if within limit.
    Raises HTTP 429 if limit exceeded.
    Raises HTTP 403 if user is banned.
    Returns user tier info.
    """
    try:
        res = (
            supabase.schema("user_db")
            .table("user_profiles")
            .select("tier, searches_this_month, searches_reset_at, is_banned")
            .eq("account_id", account_id)
            .limit(1)
            .execute()
        )
        rows = getattr(res, "data", None) or []
        if not rows:
            raise HTTPException(status_code=404, detail="User profile not found")

        user = rows[0]

        # Check ban
        if user.get("is_banned"):
            raise HTTPException(status_code=403, detail="Account suspended. Contact support.")

        # Check maintenance mode
        maintenance = _get_config_str("maintenance_mode", "false")
        if maintenance.lower() == "true":
            raise HTTPException(status_code=503, detail="TravelGuru is under maintenance. Please try again later.")

        # Check if monthly counter needs reset
        tier = user.get("tier") or "free"
        searches = user.get("searches_this_month") or 0
        reset_at_raw = user.get("searches_reset_at")

        now = datetime.now(timezone.utc)
        needs_reset = False
        if reset_at_raw:
            try:
                reset_at = datetime.fromisoformat(str(reset_at_raw).replace("Z", "+00:00"))
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if reset_at < month_start:
                    needs_reset = True
            except Exception:
                needs_reset = True

        if needs_reset:
            searches = 0
            supabase.schema("user_db").table("user_profiles").update({
                "searches_this_month": 0,
                "searches_reset_at": now.isoformat(),
            }).eq("account_id", account_id).execute()

        # Get limit for tier
        if tier == "premium":
            limit = _get_config("premium_tier_monthly_limit", 100)
        else:
            limit = _get_config("free_tier_monthly_limit", 5)

        if searches >= limit:
            # Send limit reached email (non-blocking)
            try:
                from utils.email_service import send_limit_reached_email
                import os
                profile = supabase.schema("user_db").table("user_profiles").select(
                    "email, name"
                ).eq("account_id", account_id).limit(1).execute()
                p = (getattr(profile, "data", None) or [{}])[0]
                if p.get("email"):
                    send_limit_reached_email(
                        to=p["email"],
                        user_name=p.get("name") or "",
                        limit=limit,
                        app_url=os.getenv("APP_URL", "http://localhost:5173"),
                    )
            except Exception:
                pass
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "monthly_limit_reached",
                    "tier": tier,
                    "used": searches,
                    "limit": limit,
                    "message": (
                        f"You've used all {limit} free searches this month. "
                        "Upgrade to Premium for more searches."
                        if tier == "free"
                        else f"Monthly limit of {limit} searches reached."
                    ),
                },
            )

        # Increment counter
        supabase.schema("user_db").table("user_profiles").update({
            "searches_this_month": searches + 1,
        }).eq("account_id", account_id).execute()

        return {"tier": tier, "searches_used": searches + 1, "limit": limit}

    except HTTPException:
        raise
    except Exception as e:
        # Don't block the user if rate limit check itself fails
        import logging
        logging.getLogger(__name__).error(f"Rate limit check failed: {e}", exc_info=True)
        return {"tier": "free", "searches_used": 0, "limit": 5}


def _get_config_str(key: str, default: str) -> str:
    try:
        res = (
            supabase.schema("user_db")
            .table("app_config")
            .select("value")
            .eq("key", key)
            .limit(1)
            .execute()
        )
        rows = getattr(res, "data", None) or []
        if rows:
            return str(rows[0]["value"])
    except Exception:
        pass
    return default