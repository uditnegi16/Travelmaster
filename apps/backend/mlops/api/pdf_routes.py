# api/pdf_routes.py
from __future__ import annotations
from typing import Any, cast, Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
import io

from utils.clerk_auth import get_clerk_payload
from utils.supabase_client import supabase as _supabase
from fastapi.responses import Response
import base64
import boto3

supabase = cast(Any, _supabase)
router = APIRouter(prefix="/me", tags=["pdf"])


async def current_user_payload(request: Request) -> Dict[str, Any]:
    auth = request.headers.get("authorization") or ""
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth.split(" ", 1)[1].strip()
    return get_clerk_payload(token)


def _account_id(payload: Dict[str, Any]) -> str:
    clerk_id = payload.get("sub")
    res = supabase.schema("user_db").table("user_profiles").select("account_id").eq("clerk_user_id", clerk_id).limit(1).execute()
    rows = getattr(res, "data", None) or []
    if not rows:
        raise HTTPException(status_code=404, detail="Profile not found")
    return rows[0]["account_id"]


@router.get("/sessions/{session_id}/pdf")
def export_trip_pdf(
    session_id: str,
    payload: Dict[str, Any] = Depends(current_user_payload),
):
    """Generate and stream a PDF for the trip plan."""
    # Check feature flag
    flag = supabase.schema("user_db").table("app_config").select("value").eq("key", "pdf_export_enabled").limit(1).execute()
    flag_rows = getattr(flag, "data", None) or []
    if flag_rows and flag_rows[0].get("value", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="PDF export is not enabled yet.")

    account_id = _account_id(payload)

    # Verify ownership
    sess_check = supabase.schema("duosi").table("search_sessions").select("search_id").eq("search_id", session_id).eq("account_id", account_id).limit(1).execute()
    if not getattr(sess_check, "data", None):
        raise HTTPException(status_code=404, detail="Session not found")

    # Fetch all data
    sess_res = supabase.schema("duosi").table("search_sessions").select("*").eq("search_id", session_id).limit(1).execute()
    sess = ((getattr(sess_res, "data", None) or [{}])[0])

    sr_res = supabase.schema("duosi").table("search_results").select("*").eq("search_id", session_id).limit(1).execute()
    sr = ((getattr(sr_res, "data", None) or [{}])[0])

    rr_res = supabase.schema("duosi").table("ranked_results").select("*").eq("search_id", session_id).limit(1).execute()
    rr = ((getattr(rr_res, "data", None) or [{}])[0])

    pdf_bytes = _build_pdf(sess, sr, rr)

    title = (sess.get("session_title") or "trip_plan").replace(" ", "_").lower()
    filename = f"travelguru_{title}.pdf"

    s3 = boto3.client("s3", region_name="ap-south-1")
    bucket = "travelmaster-pdfs"
    key = f"pdfs/{session_id}/{filename}"

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
        ContentDisposition=f'attachment; filename="{filename}"',
    )

    presigned_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=120,
    )

    return {"url": presigned_url, "filename": filename}


def _build_pdf(sess: dict, sr: dict, rr: dict) -> bytes:
    """Build PDF bytes using reportlab."""
    import json as _json

    def _parse(val):
        if isinstance(val, str):
            try:
                return _json.loads(val)
            except Exception:
                return []
        return val or []

    # Parse all JSON string fields
    rr = dict(rr)
    rr["recommended_flights"] = _parse(rr.get("recommended_flights"))
    rr["other_flights"]       = _parse(rr.get("other_flights"))
    rr["recommended_hotels"]  = _parse(rr.get("recommended_hotels"))
    rr["other_hotels"]        = _parse(rr.get("other_hotels"))
    rr["places"]              = _parse(rr.get("places"))
    rr["weather"]             = _parse(rr.get("weather"))

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
    except ImportError:
        raise HTTPException(status_code=500, detail="PDF library not installed. Run: pip install reportlab")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)

    styles = getSampleStyleSheet()
    BLUE = colors.HexColor("#1F4E79")
    TEAL = colors.HexColor("#0D6E6E")
    GRAY = colors.HexColor("#595959")
    LGRAY = colors.HexColor("#F2F2F2")

    title_style   = ParagraphStyle("title",   fontSize=22, textColor=BLUE,  spaceAfter=4,  fontName="Helvetica-Bold", alignment=TA_LEFT)
    h2_style      = ParagraphStyle("h2",      fontSize=13, textColor=BLUE,  spaceBefore=14, spaceAfter=4, fontName="Helvetica-Bold")
    body_style    = ParagraphStyle("body",    fontSize=9,  textColor=GRAY,  spaceAfter=3,  fontName="Helvetica", leading=14)
    label_style   = ParagraphStyle("label",   fontSize=8,  textColor=TEAL,  spaceAfter=2,  fontName="Helvetica-Bold")

    story = []

    # Header
    from_loc = sess.get("from_location") or "—"
    to_loc   = sess.get("to_location") or "—"
    title    = sess.get("session_title") or f"{from_loc} → {to_loc}"
    story.append(Paragraph("TravelGuru", ParagraphStyle("brand", fontSize=10, textColor=TEAL, fontName="Helvetica-Bold")))
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"{from_loc} → {to_loc}  |  {sess.get('start_date','')} – {sess.get('end_date','')}  |  {sess.get('num_adults',1)} adult(s)", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE, spaceAfter=10))

    # Narrative
    narrative = (sr.get("narrative") or "").strip()
    if narrative:
        story.append(Paragraph("Trip Summary", h2_style))
        for line in narrative.split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), body_style))
        story.append(Spacer(1, 8))

    # Top flight
    rec_flights = rr.get("recommended_flights") or []
    if rec_flights:
        story.append(Paragraph("Recommended Flight", h2_style))
        f = rec_flights[0]
        flight_data = [
            ["Airline", "Departure", "Arrival", "Duration", "Stops", "Price"],
            [
                str(f.get("airline") or f.get("carrier") or "—"),
                str((f.get("departure_time") or "")[:16].replace("T", " ")),
                str((f.get("arrival_time") or "")[:16].replace("T", " ")),
                str(f.get("duration") or "—"),
                str(f.get("stops") or "0"),
                f"Rs.{f.get('price', 0):,}" if f.get("price") else "—",
            ]
        ]
        t = Table(flight_data, colWidths=[3.5*cm, 4*cm, 4*cm, 2.5*cm, 1.5*cm, 2.5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), BLUE),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LGRAY]),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
            ("PADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    # Top hotel
    rec_hotels = rr.get("recommended_hotels") or []
    if rec_hotels:
        story.append(Paragraph("Recommended Hotel", h2_style))
        h = rec_hotels[0]
        hotel_data = [
            ["Hotel", "City", "Stars", "Check-in", "Check-out", "Price/night"],
            [
                str(h.get("name") or h.get("hotel_name") or "—"),
                str(h.get("city") or "—"),
                str(h.get("stars") or "—"),
                str(h.get("check_in") or "—"),
                str(h.get("check_out") or "—"),
                f"Rs.{h.get('price_per_night', 0):,}" if h.get("price_per_night") else "—",
            ]
        ]
        t2 = Table(hotel_data, colWidths=[4.5*cm, 2.5*cm, 1.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), BLUE),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LGRAY]),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
            ("PADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(t2)
        story.append(Spacer(1, 8))

    # Places
    places = sr.get("places") or []
    if places:
        story.append(Paragraph("Places to Visit", h2_style))
        for pl in places[:6]:
            name = pl.get("name") or pl.get("place_name") or "—"
            cat  = pl.get("category") or pl.get("type") or ""
            desc = pl.get("description") or pl.get("summary") or ""
            story.append(Paragraph(f"<b>{name}</b>{f'  · {cat}' if cat else ''}", label_style))
            if desc:
                story.append(Paragraph(str(desc)[:200], body_style))
        story.append(Spacer(1, 8))

    # Budget
    budget = sr.get("budget") or {}
    if budget:
        story.append(Paragraph("Budget Summary", h2_style))
        brows = []
        for k, v in budget.items():
            if isinstance(v, (int, float)) and v > 0:
                brows.append([k.replace("_", " ").title(), f"Rs.{v:,.0f}"])
        if brows:
            bt = Table([["Category", "Amount"]] + brows, colWidths=[8*cm, 4*cm])
            bt.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), BLUE),
                ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
                ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",   (0,0), (-1,-1), 8),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LGRAY]),
                ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
                ("PADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(bt)

    # Footer
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    story.append(Paragraph("Generated by TravelGuru · AI-powered travel planning", ParagraphStyle("footer", fontSize=7, textColor=GRAY, alignment=TA_CENTER, spaceBefore=4)))

    doc.build(story)
    return buf.getvalue()