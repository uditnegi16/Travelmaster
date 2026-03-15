# ✈ TravelMaster — AI-Powered Travel Planning SaaS

> Plan complete trips with AI in seconds. Just describe your trip in plain English — TravelMaster finds flights, hotels, places, weather and builds a full budget breakdown automatically.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.118-green)
![React](https://img.shields.io/badge/React-18-61DAFB) 
![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E)
![LangGraph](https://img.shields.io/badge/Agent-LangGraph-orange)

---

## What It Does

TravelMaster is a full-stack AI SaaS where users type a natural language query like:

> *"Plan a 3-day trip from Delhi to Mumbai for 2 adults, budget ₹30k, March 25–27"*

And get back a complete plan with:
- ✅ Ranked flight options with booking links
- ✅ Ranked hotel options with pricing
- ✅ Places to visit with ratings
- ✅ Weather forecast for travel dates
- ✅ Full budget breakdown
- ✅ AI-generated trip narrative

---

## Architecture

```
User → React Frontend (:5173)
     → MLOps Backend (:8000)   ← Auth, Sessions, Ranking, Rate Limiting
     → Agent Service (:8001)   ← LangGraph AI Planner + Tool Execution
     → Amadeus API             ← Flights + Hotels
     → Google Places API       ← Places of Interest
     → OpenWeather API         ← Weather Forecast
     → Supabase (PostgreSQL)   ← Database
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + TypeScript + Tailwind CSS |
| Auth | Clerk (JWT-based) |
| MLOps Backend | FastAPI (Python 3.12) |
| Agent Service | LangGraph + FastAPI (Python 3.12) |
| Database | Supabase (PostgreSQL) |
| AI / LLM | OpenAI GPT-4o / Groq llama-3.3-70b |
| Flight & Hotel APIs | Amadeus |
| Places | Google Places API |
| Weather | OpenWeather API |
| PDF Export | ReportLab |
| Email | AWS SES (boto3) |

---

## Prerequisites

- Python 3.12
- Node.js 18+
- A Supabase account and project
- A Clerk account
- Amadeus API credentials (free sandbox at developers.amadeus.com)
- OpenAI API key OR Groq API key (free at console.groq.com)
- Google Maps API key
- OpenWeather API key (free at openweathermap.org)

---

## Setup — 3 Terminals Required

### Clone the repo

```bash
git clone https://github.com/uditnegi16/Travelmaster.git
cd Travelmaster
```

---

### Terminal 1 — Agent Service (port 8001)

```powershell
cd D:\Travelmaster\apps\backend\agent_in_update
```

Create `.env` file:

```env
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
AMADEUS_HOSTNAME=test
OPENAI_API_KEY=your_openai_or_groq_key
OPENAI_BASE_URL=                          # leave empty for OpenAI, set https://api.groq.com/openai/v1 for Groq
PLANNER_MODEL=gpt-4o                      # or llama-3.3-70b-versatile for Groq
COMPOSER_MODEL=gpt-4o-mini                # or llama3-8b-8192 for Groq
OPENWEATHER_API_KEY=your_openweather_key
GOOGLE_MAPS_API_KEY=your_google_maps_key
DEFAULT_CURRENCY=INR
```

Copy `.env` to backend root (required for module resolution):

```powershell
Copy-Item ".env" "D:\Travelmaster\apps\backend\.env" -Force
Copy-Item ".env" "D:\Travelmaster\.env" -Force
```

Install dependencies and run:

```powershell
cd D:\Travelmaster\apps\backend
pip install -r requirements_new.txt
$env:PYTHONPATH="D:\Travelmaster\apps\backend"
uvicorn agent_in_update.langgraph_agents.api:app --reload --port 8001
```

✅ Agent running at `http://127.0.0.1:8001`

---

### Terminal 2 — MLOps Backend (port 8000)

```powershell
cd D:\Travelmaster\apps\backend\mlops
```

Create `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...your_service_role_key
SUPABASE_ANON_KEY=eyJ...your_anon_key
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
CLERK_JWKS_URL=https://your-clerk-domain.clerk.accounts.dev/.well-known/jwks.json
AGENT_URL=http://127.0.0.1:8001
AWS_REGION=ap-south-1
SES_FROM_EMAIL=noreply@yourdomain.com
SES_ENABLED=false
APP_URL=http://localhost:5173
```

Run:

```powershell
uvicorn api.main:app --reload --port 8000
```

✅ MLOps running at `http://127.0.0.1:8000`

---

### Terminal 3 — Frontend (port 5173)

```powershell
cd D:\Travelmaster\apps\frontend\travelguru-frontend
```

Create `.env` file:

```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key
```

Install and run:

```powershell
npm install
npm run dev
```

✅ Frontend running at `http://localhost:5173`

---

## Database Setup

Run these migrations in your Supabase SQL editor before first use:

```sql
-- Add tier and rate limiting to user profiles
ALTER TABLE user_db.user_profiles
  ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'free',
  ADD COLUMN IF NOT EXISTS searches_this_month INT DEFAULT 0,
  ADD COLUMN IF NOT EXISTS searches_reset_at TIMESTAMPTZ DEFAULT date_trunc('month', now()),
  ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT false;

ALTER TABLE user_db.user_profiles ALTER COLUMN email DROP NOT NULL;

-- Shared trips table
CREATE TABLE IF NOT EXISTS hud.shared_trips (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  search_id UUID NOT NULL REFERENCES duosi.search_sessions(search_id) ON DELETE CASCADE,
  account_id UUID NOT NULL,
  share_token TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Admin tables
CREATE TABLE IF NOT EXISTS user_db.admin_users (
  admin_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  role TEXT DEFAULT 'analyst',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  last_login TIMESTAMPTZ,
  CONSTRAINT admin_users_role_check CHECK (role IN ('super_admin', 'support', 'analyst'))
);

CREATE TABLE IF NOT EXISTS user_db.app_config (
  key TEXT PRIMARY KEY, value TEXT NOT NULL, description TEXT,
  updated_by UUID REFERENCES user_db.admin_users(admin_id) ON DELETE SET NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO user_db.app_config (key, value, description) VALUES
  ('free_tier_monthly_limit', '5', 'Max searches/month free users'),
  ('premium_tier_monthly_limit', '100', 'Max searches/month premium users'),
  ('agent_timeout_seconds', '60', 'Agent timeout'),
  ('maintenance_mode', 'false', 'Block all new searches'),
  ('fallback_model_enabled', 'true', 'Fall back to Groq if OpenAI fails'),
  ('pdf_export_enabled', 'true', 'Feature flag PDF export'),
  ('trip_sharing_enabled', 'true', 'Feature flag shareable links')
ON CONFLICT (key) DO NOTHING;

CREATE TABLE IF NOT EXISTS user_db.admin_audit_log (
  log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id UUID REFERENCES user_db.admin_users(admin_id) ON DELETE SET NULL,
  action TEXT NOT NULL, target_type TEXT, target_id TEXT,
  metadata JSONB DEFAULT '{}'::jsonb, ip_address TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_db.health_logs (
  log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  service TEXT NOT NULL, status TEXT NOT NULL,
  response_time_ms INT, error_message TEXT,
  metadata JSONB DEFAULT '{}'::jsonb,
  checked_at TIMESTAMPTZ DEFAULT now()
);

-- Grants
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA user_db TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA hud TO anon, authenticated, service_role;
```

---

## Admin Setup

Add yourself as admin in Supabase SQL editor (replace with your Clerk user ID from Clerk dashboard):

```sql
INSERT INTO user_db.admin_users (clerk_user_id, email, role, is_active)
VALUES ('user_your_clerk_id_here', 'your@email.com', 'super_admin', true);
```

Then visit `http://localhost:5173` → sign in → you'll be auto-redirected to `/admin/dashboard`.

---

## User Tiers

| Feature | Free | Premium |
|---------|------|---------|
| AI trip searches / month | **5** | **100** |
| Flights + Hotels + Places | ✅ | ✅ |
| Weather + Budget breakdown | ✅ | ✅ |
| Session history | ✅ | ✅ |
| Save trips | ✅ | ✅ |
| PDF export | ✅ | ✅ |
| Shareable trip links | ✅ | ✅ |

> Free tier limit resets at the start of every month. Admins can manually reset any user's limit from the Admin panel.

---

## Admin Panel

Visit `/admin/dashboard` after signing in with an admin account.

| Page | URL | What it does |
|------|-----|-------------|
| Dashboard | `/admin/dashboard` | Business metrics — users, searches, success rate |
| Users | `/admin/users` | Manage users — upgrade tier, ban, reset limit |
| Health | `/admin/health` | Live service status |
| Config | `/admin/config` | Edit rate limits and feature flags without redeploy |
| Audit Log | `/admin/audit` | All admin actions with timestamp |

---

## Key Features

- **Natural language trip planning** — no forms, no filters, just describe your trip
- **AI agent with fallback** — primary LLM with automatic fallback on timeout
- **ML ranking pipeline** — flights and hotels scored and ranked by price, rating, stars
- **Rate limiting** — configurable per tier, stored in database
- **PDF export** — download full trip plan as PDF
- **Trip sharing** — share a read-only link with anyone, no login required
- **Admin panel** — full operations dashboard
- **Email notifications** — trip ready, welcome, limit reached (AWS SES)

---

## Package Versions (Critical)

These versions are tested and working together:

```
supabase==2.28.0
httpx==0.28.1
fastapi==0.118.0
uvicorn==0.37.0
postgrest==2.28.0
```

> ⚠️ Do not downgrade `supabase` below 2.28.0 — it breaks the `.insert().select()` chain used throughout the codebase.

---

## Common Issues

**`OPENAI_API_KEY is not set`** — Copy `.env` from `agent_in_update/` to both `apps/backend/` and the repo root. The `core/config.py` looks 3 levels up from its location.

**`Invalid API key` (Supabase)** — Ensure `SUPABASE_SERVICE_ROLE_KEY` starts with `eyJ` and has no spaces or quotes around it.

**Hotels not showing** — Check `hotel_scoring.yaml` — `city_required` must be `false`. The agent returns hotels with IATA city codes (e.g. `BOM`) which don't match city names (e.g. `Mumbai`).

**`monthly_limit_reached`** — Go to Admin → Users → Reset, or run: `UPDATE user_db.user_profiles SET searches_this_month = 0 WHERE email = 'your@email.com';`

**`SyncQueryRequestBuilder has no attribute select`** — Run `pip install supabase==2.28.0 httpx==0.28.1`

---

## Project Structure

```
Travelmaster/
├── apps/
│   ├── backend/
│   │   ├── agent_in_update/          ← LangGraph AI agent service (:8001)
│   │   │   ├── langgraph_agents/     ← Planner, Composer, Orchestrator
│   │   │   ├── tools/                ← Flight, Hotel, Places, Weather, Budget
│   │   │   ├── postprocessing/       ← Enrichment pipeline
│   │   │   └── .env                  ← Agent environment variables
│   │   ├── mlops/                    ← FastAPI MLOps backend (:8000)
│   │   │   ├── api/                  ← Routes: sessions, users, admin, pdf, share
│   │   │   ├── pipelines/            ← ML ranking: flights + hotels
│   │   │   ├── utils/                ← Auth, rate limiter, email, health logger
│   │   │   └── .env                  ← MLOps environment variables
│   │   └── core/                     ← Shared config and Amadeus client
│   └── frontend/
│       └── travelguru-frontend/      ← React app (:5173)
│           ├── src/app/routes/       ← All pages including admin/
│           └── .env                  ← Clerk publishable key
└── requirements_new.txt              ← Full Python dependencies
```

---

## License

MIT — built for portfolio demonstration purposes.