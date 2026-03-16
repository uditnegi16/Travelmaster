# api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.stripe_routes import router as stripe_router
# ML pipelines disabled in Lambda deployment
from api.plan_trip import router as plan_trip_router
from api.user_routes import router as user_router
from api.session_routes import router as session_router
from api.admin_routes import router as admin_router
from api.share_routes import router as share_router
from api.pdf_routes import router as pdf_router
from fastapi.middleware.cors import CORSMiddleware

# in the routers section:
import os
from utils import health_logger
# ── App ──────────────────────────────────────────────────────────
app = FastAPI(
    title="TravelGuru MLOps API",
    version="1.0.0",
    description="MLOps backend: auth, sessions, agent orchestration, ranking",
)
# ── CORS ─────────────────────────────────────────────────────────
# FIX: was missing 127.0.0.1 variants — frontend on 127.0.0.1 was blocked
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://main.d1dssl0hm1ugfp.amplifyapp.com",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────
app.include_router(plan_trip_router)
app.include_router(user_router)
app.include_router(session_router)
app.include_router(admin_router)
app.include_router(share_router)
app.include_router(pdf_router)
app.include_router(stripe_router)

# ── Health ────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "service": "travelguru-mlops", "port": 8000}


@app.get("/health")
def health():
    return {"status": "ok", "service": "mlops", "port": 8000}


@app.get("/health/full")
def health_full():
    """Full health check — pings agent and logs results to DB."""
    agent_url = os.getenv("AGENT_URL", "http://127.0.0.1:8001")
    results = []

    # Ping agent
    results.append(health_logger.ping_service(f"{agent_url}/health", "agent"))
    # Check Supabase
    import time
    from utils.supabase_client import supabase as _sb
    from typing import cast, Any
    sb = cast(Any, _sb)
    start = time.time()
    try:
        sb.schema("user_db").table("app_config").select("key").limit(1).execute()
        ms = int((time.time() - start) * 1000)
        health_logger.log_health("supabase", "healthy", ms)
        results.append({"service": "supabase", "status": "healthy", "response_time_ms": ms})
    except Exception as e:
        ms = int((time.time() - start) * 1000)
        health_logger.log_health("supabase", "down", ms, str(e))
        results.append({"service": "supabase", "status": "down", "error": str(e)})

    overall = "healthy" if all(r["status"] == "healthy" for r in results) else "degraded"
    return {"overall": overall, "services": results}


