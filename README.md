<p align="center">
  <!-- ============================================================ -->
  <!-- REPLACE: Upload your banner to GitHub and paste the URL here -->
  <!-- ============================================================ -->
  <img width="100%" alt="TravelMaster Banner" src="docs/banner.png"/>
</p>

<p align="center">
  <a href="https://main.d1dssl0hm1ugfp.amplifyapp.com"><img src="https://img.shields.io/badge/Live_Demo-Visit_App-7c3aed?style=flat-square" alt="Live Demo" /></a>
  <a href="https://github.com/uditnegi16/Travelmaster"><img src="https://img.shields.io/badge/GitHub-TravelMaster-181717?style=flat-square&logo=github" alt="GitHub" /></a>
  <a href="#"><img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="MIT License" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.12" /></a>
  <a href="#"><img src="https://img.shields.io/badge/AWS-Deployed-FF9900?style=flat-square&logo=amazonaws&logoColor=white" alt="AWS" /></a>
  <a href="#"><img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Multi--Agent-LangGraph-orange?style=flat-square" alt="Multi-Agent" />
  <img src="https://img.shields.io/badge/Serverless-AWS_Lambda-FF9900?style=flat-square" alt="Serverless" />
  <img src="https://img.shields.io/badge/ML_Ranking-scikit--learn-F7931E?style=flat-square" alt="ML Ranking" />
  <img src="https://img.shields.io/badge/Auth-Clerk_JWT-6C47FF?style=flat-square" alt="Clerk Auth" />
  <img src="https://img.shields.io/badge/Production-Ready-brightgreen?style=flat-square" alt="Production Ready" />
  <img src="https://img.shields.io/badge/Admin-Panel-blue?style=flat-square" alt="Admin Panel" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Groq-llama--3.3--70b-red?style=flat-square" alt="Groq" />
  <img src="https://img.shields.io/badge/Amadeus-Flights_%26_Hotels-00539B?style=flat-square" alt="Amadeus" />
  <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat-square&logo=supabase" alt="Supabase" />
</p>

---

## Overview

TravelMaster is a full-stack AI SaaS that plans complete trips from a single sentence. Type a natural language query — TravelMaster orchestrates a **LangGraph multi-agent system** that searches flights, hotels, places and weather **in parallel**, ranks results using an **ML scoring pipeline**, and generates an AI travel narrative. Deployed serverless on **AWS Lambda** with a production admin panel, tier-based rate limiting, PDF export via S3, and shareable trip links.

> *"Plan a 3-day trip from Delhi to Mumbai for 2 adults, budget ₹30k, March 25–27"*
>
> → Ranked flights · Ranked hotels · Places to visit · Weather forecast · Budget breakdown · AI narrative — in seconds.

---

## Demo

<!-- ================================================================ -->
<!-- HOW TO EMBED YOUR VIDEO (GitHub renders MP4 natively):           -->
<!-- 1. Go to your repo → Issues → New Issue                          -->
<!-- 2. Drag and drop your .mp4 file into the comment box             -->
<!-- 3. GitHub generates a URL like:                                  -->
<!--    https://github.com/user/repo/assets/USERID/FILEID.mp4        -->
<!-- 4. Paste that URL below on its own line — no markdown needed     -->
<!-- 5. Delete these instructions after replacing the URL             -->
<!-- ================================================================ -->

YOUR_GITHUB_VIDEO_ASSET_URL_HERE

---

## 🌐 Live Demo

| Service | URL |
|---------|-----|
| Frontend | https://main.d1dssl0hm1ugfp.amplifyapp.com |
| MLOps API | https://g2d019moz2.execute-api.ap-south-1.amazonaws.com/prod/health |
| Agent API | https://napum590vf.execute-api.ap-south-1.amazonaws.com/prod/health |

---

## Screenshots

<!-- ================================================================ -->
<!-- HOW TO ADD SCREENSHOTS:                                          -->
<!-- 1. Take screenshots using Windows Snipping Tool (Win+Shift+S)   -->
<!-- 2. Create a /screenshots folder in your repo                     -->
<!-- 3. Upload the 6 images listed below                              -->
<!-- 4. The paths below will auto-resolve once images are uploaded    -->
<!-- ================================================================ -->
<!-- Screenshots to capture:                                          -->
<!-- 1. landing.png    — Landing page hero before login               -->
<!-- 2. dashboard.png  — Dashboard with trip history cards            -->
<!-- 3. trip.png       — Chat with AI results (flights/hotels visible) -->
<!-- 4. pdf.png        — Downloaded PDF opened in browser             -->
<!-- 5. admin.png      — Admin dashboard with metrics                 -->
<!-- 6. dark.png       — Any page in dark mode                        -->
<!-- ================================================================ -->

<p align="center">
  <img src="screenshots/landing.png" width="48%" alt="Landing Page" />
  <img src="screenshots/dashboard.png" width="48%" alt="Dashboard" />
</p>
<p align="center">
  <img src="screenshots/trip.png" width="48%" alt="Trip Results" />
  <img src="screenshots/pdf.png" width="48%" alt="PDF Export" />
</p>
<p align="center">
  <img src="screenshots/admin.png" width="48%" alt="Admin Panel" />
  <img src="screenshots/dark.png" width="48%" alt="Dark Mode" />
</p>

---

## System Architecture

<!-- ================================================================ -->
<!-- REPLACE: Upload your architecture diagram to /docs/ in the repo  -->
<!-- and replace the src URL below                                     -->
<!-- ================================================================ -->

<p align="center">
  <img width="90%" alt="TravelMaster System Architecture" src="docs/architecture.png" />
</p>

---

## Agent Flow

```mermaid
flowchart TD
    A["🗣️ User Query\nPlain English — no forms"] --> B["MLOps Lambda\nFastAPI · Auth · Rate Limiting · Sessions"]
    B --> C["Agent Lambda\nLangGraph Orchestrator"]
    C --> D["🧠 Planner Agent\nDecides which tools to call"]
    D --> E["⚡ Tool Router\nParallel Execution"]
    E --> F["✈️ Amadeus\nFlights"]
    E --> G["🏨 Amadeus\nHotels"]
    E --> H["📍 Google Places"]
    E --> I["🌤️ OpenWeather"]
    E --> J["💰 Budget Calculator"]
    F & G & H & I & J --> K["📊 ML Ranking Pipeline\nscikit-learn weighted scoring"]
    K --> L["✍️ Composer Agent\nAI Narrative Generation"]
    L --> M["💾 Supabase\nResults stored in PostgreSQL"]
    M --> N["🖥️ React Frontend\nFlights · Hotels · Places · Weather · PDF · Share"]

    style A fill:#7c3aed,color:#fff,stroke:#5b21b6
    style B fill:#1e40af,color:#fff,stroke:#1e3a8a
    style C fill:#1e40af,color:#fff,stroke:#1e3a8a
    style D fill:#0369a1,color:#fff,stroke:#075985
    style E fill:#0369a1,color:#fff,stroke:#075985
    style K fill:#065f46,color:#fff,stroke:#064e3b
    style L fill:#0369a1,color:#fff,stroke:#075985
    style M fill:#1e40af,color:#fff,stroke:#1e3a8a
    style N fill:#7c3aed,color:#fff,stroke:#5b21b6
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, TypeScript, Tailwind CSS |
| Auth | Clerk (JWT-based, protected routes) |
| MLOps Backend | FastAPI 0.118, Python 3.12, Mangum |
| AI Agent | LangGraph, FastAPI, Python 3.12, Mangum |
| LLM | Groq llama-3.3-70b-versatile |
| Flight + Hotel Data | Amadeus API |
| Places | Google Places API |
| Weather | OpenWeather API |
| ML Ranking | scikit-learn weighted scoring pipeline |
| Database | Supabase (PostgreSQL) |
| PDF Export | ReportLab + AWS S3 presigned URLs |
| Email | AWS SES (boto3) |
| Frontend Hosting | AWS Amplify (CI/CD from GitHub) |
| Backend Hosting | AWS Lambda + API Gateway |
| Infrastructure as Code | AWS SAM |
| File Storage | AWS S3 |
| Monitoring | AWS CloudWatch |

---

## Features

- **Natural Language Planning** — no forms, no dropdowns, just describe your trip in plain English
- **LangGraph Multi-Agent** — planner agent → tool router → composer agent in sequence
- **Parallel Tool Execution** — flights, hotels, places, weather and budget fetched simultaneously
- **ML Ranking Pipeline** — scikit-learn weighted scoring, not just raw LLM output
- **Tier-Based Rate Limiting** — free (5/month) vs premium (100/month), configurable from admin panel without redeploy
- **Session History** — all past trips saved, searchable, re-openable like ChatGPT history
- **PDF Export** — full trip plan downloaded via AWS S3 presigned URL
- **Trip Sharing** — public read-only link with no login required
- **Admin Panel** — user management, config flags, audit log, health monitoring
- **Dark / Light Mode** — system preference detection with manual toggle and persistence
- **Serverless Architecture** — AWS Lambda + API Gateway, zero server management
- **Email Notifications** — welcome, limit reached, trip ready via AWS SES

---

## Why TravelMaster

| Traditional Travel Apps | TravelMaster |
|------------------------|-------------|
| Search forms with dropdowns | Plain English natural language |
| Manual comparison across tabs | AI-ranked results in one view |
| Static results, no scoring | ML pipeline scores by price, rating, convenience |
| No narrative or context | Full budget breakdown + AI trip narrative |
| No admin control | Full ops dashboard with real-time config flags |
| Fixed rate limits in code | Configurable per tier from database, zero redeploy |

---

## AWS Infrastructure

| Service | Purpose |
|---------|---------|
| AWS Amplify | Frontend hosting + auto CI/CD from GitHub push |
| AWS Lambda | MLOps backend + Agent backend (serverless) |
| Amazon API Gateway | Public HTTPS endpoints for both Lambdas |
| Amazon S3 (`travelmaster-pdfs`) | PDF storage + presigned URL delivery |
| AWS SAM | Infrastructure as code — Lambda + API Gateway |
| Amazon CloudWatch | Lambda logs and error monitoring |
| AWS SES | Transactional emails |

---

## Local Development — 3 Terminals

### Prerequisites

- Python 3.12
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) — `pip install uv`
- Supabase account + project
- Clerk account
- Amadeus API credentials — free sandbox at [developers.amadeus.com](https://developers.amadeus.com)
- Groq API key — free at [console.groq.com](https://console.groq.com)
- Google Maps API key
- OpenWeather API key — free at [openweathermap.org](https://openweathermap.org)

### Clone

```bash
git clone https://github.com/uditnegi16/Travelmaster.git
cd Travelmaster
```

### Terminal 1 — Agent Service (port 8001)

```powershell
cd apps/backend/agent_in_update
```

Create `.env`:

```env
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
AMADEUS_HOSTNAME=test
OPENAI_API_KEY=your_groq_key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
PLANNER_MODEL=llama-3.3-70b-versatile
COMPOSER_MODEL=llama-3.3-70b-versatile
OPENWEATHER_API_KEY=your_openweather_key
GOOGLE_MAPS_API_KEY=your_google_maps_key
DEFAULT_CURRENCY=INR
```

Copy `.env` to backend root (required for module resolution):

```powershell
Copy-Item ".env" "../../.env" -Force
Copy-Item ".env" "../../../.env" -Force
```

Install and run:

```powershell
cd ../../..
uv venv
.venv\Scripts\activate
cd apps/backend
uv pip install -r requirements_new.txt
$env:PYTHONPATH="$PWD"
uvicorn agent_in_update.langgraph_agents.api:app --reload --port 8001
```

✅ Agent running at `http://127.0.0.1:8001`

### Terminal 2 — MLOps Backend (port 8000)

```powershell
cd apps/backend/mlops
```

Create `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_ANON_KEY=your_anon_key
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

### Terminal 3 — Frontend (port 5173)

```powershell
cd apps/frontend
```

Create `.env`:

```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key
VITE_API_BASE=http://127.0.0.1:8000
```

Run:

```powershell
npm install
npm run dev
```

✅ Frontend running at `http://localhost:5173`

---

## AWS Deployment

### Prerequisites

- AWS CLI configured (`aws configure`)
- SAM CLI installed — [install guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- S3 bucket: `aws s3 mb s3://travelmaster-pdfs --region ap-south-1`

### Deploy Agent Lambda

```powershell
cd apps/backend/agent_in_update
sam build
sam deploy --guided
```

Stack name: `travelmaster-agent` · Region: `ap-south-1`

### Deploy MLOps Lambda

```powershell
cd apps/backend/mlops
sam build
sam deploy --guided
```

Stack name: `travelmaster-mlops` · Region: `ap-south-1`

### Deploy Frontend

Push to `main` — Amplify auto-deploys on every push.

**Required Amplify environment variables:**

```
VITE_CLERK_PUBLISHABLE_KEY = pk_live_your_key
VITE_API_BASE = https://g2d019moz2.execute-api.ap-south-1.amazonaws.com/prod
```

---

## Database Setup

All SQL queries to build the complete database schema are in a separate file:

📄 **[database_setup.sql](database_setup.sql)**

Run the queries in your Supabase SQL editor in order.

---

## Admin Setup

Get your Clerk user ID from Clerk Dashboard → Users → click your account → copy `user_xxx` ID.

```sql
INSERT INTO user_db.admin_users (clerk_user_id, email, role, is_active)
VALUES ('user_your_clerk_id_here', 'your@email.com', 'super_admin', true);
```

Sign in on the live app → auto-redirected to `/admin/dashboard`.

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

> Limits reset at the start of every month. Admins can manually reset any user from the Admin panel.

---

## Admin Panel

| Page | URL | Purpose |
|------|-----|---------|
| Dashboard | `/admin/dashboard` | Business metrics — users, searches, success rate |
| Users | `/admin/users` | Upgrade tier, ban users, reset monthly limit |
| Health | `/admin/health` | Live Lambda + Supabase service status |
| Config | `/admin/config` | Edit rate limits + feature flags — no redeploy needed |
| Audit Log | `/admin/audit` | All admin actions with timestamp |

---

## Common Issues

**`OPENAI_API_KEY is not set`** — Copy `.env` from `agent_in_update/` to `apps/backend/` and repo root. `core/config.py` looks 3 levels up.

**`Invalid API key` (Supabase)** — Ensure `SUPABASE_SERVICE_ROLE_KEY` starts with `eyJ` with no spaces.

**Hotels not showing** — Check `hotel_scoring.yaml` — `city_required` must be `false`. Agent returns IATA city codes (e.g. `BOM`) not city names.

**`monthly_limit_reached`** — Go to Admin → Users → Reset, or run:
```sql
UPDATE user_db.user_profiles SET searches_this_month = 0 WHERE email = 'your@email.com';
```

**PDF corrupted** — Ensure S3 presigned URL delivery is used, not direct binary response through API Gateway.

---

## Package Versions (Critical)

```
supabase==2.28.0
httpx==0.28.1
fastapi==0.118.0
uvicorn==0.37.0
postgrest==2.28.0
```

> ⚠️ Do not downgrade `supabase` below 2.28.0 — breaks the `.insert().select()` chain.

---

## Project Structure

```
Travelmaster/
├── apps/
│   ├── backend/
│   │   ├── agent_in_update/          ← LangGraph AI agent (Lambda :8001)
│   │   │   ├── langgraph_agents/     ← Planner, Composer, Tool Router
│   │   │   ├── shared/               ← Schemas + constants
│   │   │   ├── postprocessing/       ← ML enrichment pipeline
│   │   │   ├── core/                 ← Amadeus client + config
│   │   │   ├── lambda_handler.py     ← AWS Lambda entry point
│   │   │   └── template.yaml         ← SAM deployment config
│   │   └── mlops/                    ← FastAPI MLOps backend (Lambda :8000)
│   │       ├── api/                  ← Routes: sessions, users, admin, pdf, share
│   │       ├── utils/                ← Auth, rate limiter, email, health logger
│   │       ├── lambda_handler.py     ← AWS Lambda entry point
│   │       └── template.yaml         ← SAM deployment config
│   └── frontend/                     ← React app (AWS Amplify)
│       ├── src/app/routes/           ← All pages including admin/
│       ├── src/components/           ← Shared UI + OnboardingTour
│       └── src/lib/api.ts            ← All API calls
└── README.md
```

---

## License

MIT — built for portfolio demonstration purposes.

---

<p align="center">
  Built with ☕ and frustration in India 🇮🇳
</p>
