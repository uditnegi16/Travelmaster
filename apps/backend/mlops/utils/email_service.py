# utils/email_service.py
from __future__ import annotations
import logging
import os
from typing import Any
import boto3
logger = logging.getLogger(__name__)

# These come from .env — add them when deploying to AWS
AWS_REGION        = os.getenv("AWS_REGION", "ap-south-1")
SES_FROM_EMAIL    = os.getenv("SES_FROM_EMAIL", "noreply@travelguru.app")
SES_ENABLED       = os.getenv("SES_ENABLED", "false").lower() == "true"


def _get_ses_client():
    try:
        return boto3.client("ses", region_name=AWS_REGION)
    except ImportError:
        raise RuntimeError("boto3 not installed. Run: pip install boto3")


def send_email(to: str, subject: str, html: str, text: str = "") -> bool:
    """
    Send an email via AWS SES.
    Returns True on success, False on failure (never raises — safe to call anywhere).
    If SES_ENABLED=false, logs the email instead (dev mode).
    """
    if not SES_ENABLED:
        logger.info(f"[EMAIL DEV MODE] To: {to} | Subject: {subject}")
        logger.info(f"[EMAIL DEV MODE] Body preview: {text[:200] if text else html[:200]}")
        return True

    try:
        client = _get_ses_client()
        client.send_email(
            Source=SES_FROM_EMAIL,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html, "Charset": "UTF-8"},
                    "Text": {"Data": text or html, "Charset": "UTF-8"},
                },
            },
        )
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}", exc_info=True)
        return False


# ── Email templates ────────────────────────────────────────────────────────────

def _base_html(content: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <!-- Header -->
        <tr><td style="background:#1F4E79;padding:24px 32px;">
          <span style="color:#ffffff;font-size:22px;font-weight:bold;">✈ TravelGuru</span>
        </td></tr>
        <!-- Body -->
        <tr><td style="padding:32px;">
          {content}
        </td></tr>
        <!-- Footer -->
        <tr><td style="background:#f9f9f9;padding:16px 32px;text-align:center;">
          <p style="color:#999;font-size:12px;margin:0;">TravelGuru · AI-powered travel planning</p>
          <p style="color:#bbb;font-size:11px;margin:4px 0 0;">You're receiving this because you have an account on TravelGuru.</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_trip_ready_email(
    to: str,
    user_name: str,
    from_location: str,
    to_location: str,
    start_date: str,
    session_id: str,
    app_url: str = "http://localhost:5173",
) -> bool:
    """Send email when a trip plan is ready."""
    subject = f"✈ Your trip to {to_location} is ready — TravelGuru"
    trip_url = f"{app_url}/app/trips/new/{session_id}"
    content = f"""
      <h2 style="color:#1F4E79;margin:0 0 8px;">Your trip plan is ready!</h2>
      <p style="color:#555;font-size:15px;margin:0 0 24px;">
        Hey {user_name or 'Traveler'}, your AI-powered trip plan has been generated.
      </p>
      <table width="100%" style="background:#f0f7ff;border-radius:8px;padding:16px;margin-bottom:24px;" cellpadding="8">
        <tr><td style="color:#666;font-size:13px;">From</td><td style="font-weight:bold;color:#1F4E79;">{from_location}</td></tr>
        <tr><td style="color:#666;font-size:13px;">To</td><td style="font-weight:bold;color:#1F4E79;">{to_location}</td></tr>
        <tr><td style="color:#666;font-size:13px;">Travel Date</td><td style="font-weight:bold;color:#1F4E79;">{start_date}</td></tr>
      </table>
      <a href="{trip_url}" style="display:inline-block;background:#0D6E6E;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:bold;font-size:15px;">
        View My Trip Plan →
      </a>
      <p style="color:#999;font-size:12px;margin-top:24px;">
        Your plan includes ranked flights, hotels, places to visit, weather forecast and budget breakdown.
      </p>"""
    return send_email(to, subject, _base_html(content), f"Your trip to {to_location} is ready. View it at: {trip_url}")


def send_welcome_email(to: str, user_name: str, app_url: str = "http://localhost:5173") -> bool:
    """Send welcome email when a new user signs up."""
    subject = "Welcome to TravelGuru ✈"
    content = f"""
      <h2 style="color:#1F4E79;margin:0 0 8px;">Welcome to TravelGuru!</h2>
      <p style="color:#555;font-size:15px;margin:0 0 16px;">
        Hey {user_name or 'Traveler'}! You're all set to start planning amazing trips with AI.
      </p>
      <p style="color:#555;font-size:14px;margin:0 0 24px;">
        Just describe your trip in plain English — TravelGuru will find flights, hotels, 
        places and give you a full plan in seconds.
      </p>
      <a href="{app_url}/app/trips/new" style="display:inline-block;background:#0D6E6E;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:bold;font-size:15px;">
        Plan My First Trip →
      </a>
      <p style="color:#999;font-size:13px;margin-top:24px;">
        Free plan: 5 AI searches per month. Upgrade to Premium for 100 searches/month.
      </p>"""
    return send_email(to, subject, _base_html(content), f"Welcome to TravelGuru! Start planning at {app_url}")


def send_limit_reached_email(
    to: str,
    user_name: str,
    limit: int,
    app_url: str = "http://localhost:5173",
) -> bool:
    """Send email when user hits monthly search limit."""
    subject = "You've used all your free searches — TravelGuru"
    content = f"""
      <h2 style="color:#1F4E79;margin:0 0 8px;">Monthly limit reached</h2>
      <p style="color:#555;font-size:15px;margin:0 0 16px;">
        Hey {user_name or 'Traveler'}, you've used all {limit} free AI searches for this month.
      </p>
      <p style="color:#555;font-size:14px;margin:0 0 24px;">
        Upgrade to <strong>TravelGuru Premium</strong> for 100 searches/month, 
        PDF exports, and shareable trip links.
      </p>
      <a href="{app_url}/app/account" style="display:inline-block;background:#7C3AED;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:bold;font-size:15px;">
        Upgrade to Premium →
      </a>
      <p style="color:#999;font-size:12px;margin-top:24px;">
        Your free searches reset at the start of next month.
      </p>"""
    return send_email(to, subject, _base_html(content), f"You've used all {limit} free searches. Upgrade at {app_url}/app/account")