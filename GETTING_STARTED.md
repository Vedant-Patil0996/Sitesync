# Getting Started with SiteSync

This document covers how to set up and run the project locally.

The stack consists of a **Next.js Frontend**, a **FastAPI Backend**, an **AI Multi-Agent Engine** (LangGraph + Groq), a **PWA** (Vite + React), and a **Supabase PostgreSQL** database.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.10+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Git | any | [git-scm.com](https://git-scm.com) |

---

## 1. Environment Setup

### Backend (`backend/.env`)
```env
# Supabase
SUPABASE_URL=https://[YOUR-PROJECT].supabase.co
SUPABASE_ANON_KEY=[YOUR-ANON-KEY]
SUPABASE_SERVICE_ROLE_KEY=[YOUR-SERVICE-ROLE-KEY]

# PostgreSQL direct connection
DATABASE_URL=postgresql://postgres.[YOUR-PROJECT]:[URL_ENCODED_PASSWORD]@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres

# AI / Groq
GROQ_API_KEY=[YOUR-GROQ-API-KEY]

# Optional: Gemini (used by IVR fallback classifier)
GEMINI_API_KEY=[YOUR-GEMINI-API-KEY]

# CORS
FRONTEND_URL=http://localhost:3000
```
> **Note:** If your database password contains special characters like `@`, URL-encode them — e.g. `%40`.

### AI Engine (`ai/.env`)
```env
SUPABASE_URL=https://[YOUR-PROJECT].supabase.co
SUPABASE_SERVICE_ROLE_KEY=[YOUR-SERVICE-ROLE-KEY]
GROQ_API_KEY=[YOUR-GROQ-API-KEY]
```

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 2. Seeding the Database

Run the seed script once to populate demo company data and RBAC accounts.

```bash
# Navigate to the test directory
cd test

# Install Supabase JS client (if not already installed)
npm install @supabase/supabase-js

# Run the seed script
node seed.js
```

This creates the following demo accounts in both Supabase Auth and the PostgreSQL `users` table:

| Email | Password | Role |
|-------|----------|------|
| `admin@sitesync.local` | `password123` | Admin |
| `pm@sitesync.local` | `password123` | Project Manager |
| `contractor@sitesync.local` | `password123` | Contractor |
| `finance@sitesync.local` | `password123` | Finance |

For a richer dataset (projects, tasks, inventory, equipment), run the Python demo seeder:
```bash
cd backend
.\venv\Scripts\Activate.ps1     # Windows
# source venv/bin/activate       # Mac/Linux
python seed_demo.py
```

---

## 3. Starting the Backend (FastAPI)

The backend serves the REST API, WebSocket streams, SSE notification stream, and the IVR webhook.

```bash
cd backend

# Create virtual environment (first time only)
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1     # Windows
# source venv/bin/activate       # Mac/Linux

# Install all dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn app.main:app --reload
```

The backend runs at **http://localhost:8000**.
Interactive API docs are at **http://localhost:8000/docs**.

On startup, the server automatically starts:
- **Background Cron Scheduler** — triggers an AI simulation scenario every 15 minutes.
- **Schedule Monitor** — scans all active projects for at-risk tasks and milestones.

---

## 4. Starting the Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend runs at **http://localhost:3000**.

### Login & Testing
1. Open **http://localhost:3000**
2. Click **Log In** and use any seeded demo account.
3. The dashboard adapts to your role — admins see full system health, contractors only see their assigned tasks.

---

## 5. Starting the PWA (Mobile Companion)

The PWA is a lightweight Vite + React app for on-site workers (contractors, supervisors).

```bash
cd pwa

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The PWA runs at **http://localhost:5173** by default.

---

## 6. AI Agent (Running Directly)

The AI multi-agent engine runs as a subprocess of the FastAPI backend. To trigger it manually:

```bash
# Trigger via API (recommended)
curl -X POST http://localhost:8000/api/v1/ai/trigger \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"scenario_id": "equipment_critical_failure"}'
```

Or run directly for debugging:
```bash
# Must be run from the project root
backend/venv/Scripts/python.exe ai/scripts/test_agent.py
```

Available simulation scenarios:
| ID | Description |
|----|-------------|
| `equipment_critical_failure` | Excavator critical failure |
| `stock_critically_low` | Cement stock below 10% threshold |
| `budget_overrun` | Site expenses at 95% of monthly budget |
| `task_delay_cascade` | Foundation delay cascades to 3 tasks |
| `vendor_price_spike` | Cable price spike 35% above benchmark |
| `multi_site_cascade` | Simultaneous equipment + stock emergency |
| `safety_violation` | Safety inspection flagged 3 violations |
| `schedule_risk_scan` | Proactive task/milestone risk scan |

---

## 7. Real-Time Architecture Overview

```
Frontend (Next.js)
    │
    ├── SSE stream   GET /api/v1/notifications/stream   (in-app alerts)
    │
    ├── WebSocket    WS /api/v1/ai/stream/{run_id}      (live AI events)
    │
    └── REST         GET/POST /api/v1/...               (data operations)

Backend (FastAPI)
    │
    ├── EventManager (asyncio pub/sub)
    │   ├── Publishes AI run events → WS stream
    │   └── Publishes notifications → SSE stream per user
    │
    ├── AI Subprocess (LangGraph + Groq)
    │   └── Emits JSON events to stdout → EventManager
    │
    ├── APScheduler (background)
    │   ├── Auto-simulation cron every 15 minutes
    │   └── Schedule health monitor
    │
    └── IVR (Twilio voice webhook at /ivr/incoming)
        └── Keyword classifier → Gemini fallback (google-genai)
```

---

## 8. Key Env Variables Reference

| Variable | Where | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | `backend/.env` | PostgreSQL connection string |
| `SUPABASE_URL` | `backend/.env`, `ai/.env` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | `backend/.env`, `ai/.env` | Full DB access (server-side only) |
| `GROQ_API_KEY` | `backend/.env`, `ai/.env` | AI inference via Groq (LLaMA / Gemma) |
| `GEMINI_API_KEY` | `backend/.env` | Gemini fallback for IVR voice intent |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` | Backend URL for the frontend |
| `FRONTEND_URL` | `backend/.env` | CORS origin allowlist |
