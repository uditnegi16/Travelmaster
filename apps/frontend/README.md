# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
# TravelGuru — AI Travel Planning Platform

## 🚀 Project Overview

TravelGuru is a production-oriented AI Travel Planning system.

Architecture:

User (React Frontend)
        ↓
Clerk Authentication
        ↓
FastAPI Backend (MLOps Layer)
        ↓
Supabase Database
        ↓
(Phase 2) Agent + ML Recommendation Engine

This document covers everything completed so far (Phase 1: Auth + Frontend + Database Setup).

---

# ✅ Phase 0 — Existing Backend Architecture (Before Frontend Upgrade)

Previously built system:

Streamlit UI
    ↓
MLOps FastAPI (/plan-trip)
    ↓
Agent Adapter
    ↓
LangGraph Agent API
    ↓
Agent Orchestration
    ↓
Response Adapter
    ↓
MLOps Ranking
    ↓
Streamlit Display

Key principle:
- Agent = data source
- MLOps = intelligence scorer
- Streamlit = renderer

Later replaced Streamlit with production React frontend.

---

# ✅ Phase 1 — Frontend Migration (Streamlit → React + Vite)

## 1️⃣ Remove Streamlit Frontend

Old location:
app/frontend/app.py

Renamed:
mv frontend/app.py frontend/app_streamlit_old.py

Reason:
We are moving to production-grade React frontend.

---

## 2️⃣ Create React + Vite App (TypeScript)

Inside:
backend/app/frontend

Commands used:

npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm run dev

---

## 3️⃣ Downgrade Vite (Node Compatibility)

Because Node v22.11.0 was installed, Vite 7+ caused issues.

Fixed with:

npm install vite@5 @vitejs/plugin-react@4 --save-dev

---

## 4️⃣ Install Tailwind CSS

Commands:

npm i -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

Updated:

tailwind.config.js
src/index.css

Restarted:
npm run dev

---

# ✅ Phase 2 — Database Architecture (Supabase)

We designed a production-level schema.

## Schemas

### 1️⃣ user_db
- user_profiles
- clerk_user_id (TEXT UNIQUE)

### 2️⃣ duosi
- search_sessions
- chat_messages
- search_results
- ranked_results

### 3️⃣ hud
- user_history

Added:

- agent_status
- data_source
- retry_count
- metadata JSONB
- ranking metadata
- chat history table
- snapshot tables

Used SQL:
(create extension pgcrypto, alter table add columns, create new tables, triggers, indexes)

Design principle:
One search_session = one chat thread.

---

# ✅ Phase 3 — Seed Data (Dummy Data for UI Development)

Inserted:
- 2 demo users
- Multiple search sessions
- Chat messages
- Raw agent results (JSONB)
- Ranked results
- User history actions

Purpose:
Build UI without agent dependency.

---

# ✅ Phase 4 — Clerk Authentication (React + Vite)

## 1️⃣ Installed Clerk

npm i @clerk/clerk-react@latest

---

## 2️⃣ Added Environment Variable

Created:

frontend/.env.local

VITE_CLERK_PUBLISHABLE_KEY=YOUR_PUBLISHABLE_KEY

Restarted dev server.

---

## 3️⃣ Wrapped App with ClerkProvider

File:
src/main.tsx

Wrapped entire app:

<ClerkProvider publishableKey={...}>
  <App />
</ClerkProvider>

---

## 4️⃣ Added Auth Components

Used:

<SignedIn>
<SignedOut>
<SignInButton>
<SignUpButton>
<UserButton>

---

## 5️⃣ Configured Clerk Dashboard

Set:
Fallback development host:
http://localhost:5173

Set redirects:
After sign-in → /app
After sign-up → /app

---

## 6️⃣ Created Protected App Area

Created:

src/app/layout/ProtectedRoute.tsx

Protected:
Route "/app"

---

## 7️⃣ Verified Clerk User ID

Dashboard shows:

Clerk user id:
user_xxxxxxxxx

---

## 8️⃣ Linked Clerk User to Supabase

Inserted profile:

insert into user_db.user_profiles (...)
values (..., 'user_xxxxx', ...)

Updated dummy sessions:

update duosi.search_sessions
set account_id = 'UUID_HERE';

Important:
UUID must be wrapped in quotes.

---

# 🧠 Current State

✔ React + Vite frontend running  
✔ Tailwind configured  
✔ Clerk authentication working  
✔ Supabase schema production-ready  
✔ Dummy data seeded  
✔ Clerk user mapped to Supabase  
✔ Protected `/app` route working  

---

# 🎯 Next Phase

Connect:

React → FastAPI Backend → Supabase

Endpoints to build:
- GET /me
- GET /me/sessions

Followed by:
- Secure Clerk token verification
- Backend-side Supabase queries
- No service key exposure in frontend

---

# 🔒 Security Principles

- Never expose Supabase service role key to frontend
- Clerk handles authentication
- Backend verifies Clerk JWT
- Backend queries Supabase
- Frontend consumes backend API only

---

# 📌 Tech Stack

Frontend:
- React (Vite + TypeScript)
- Tailwind CSS
- Clerk Authentication

Backend:
- FastAPI
- MLOps Layer
- LangGraph Agent
- Python

Database:
- Supabase (Postgres)
- JSONB-based storage for agent output

---

# 🏁 Phase 1 Complete

Authentication + database foundation complete.
Ready for backend integration.
