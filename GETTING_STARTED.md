# Getting Started with SiteSync

This document covers how to set up and run the project locally using either **Docker Compose (Recommended)** or **Manual Bare-Metal Setup**.

The stack consists of a **Next.js Frontend**, a **FastAPI Backend**, an **AI Multi-Agent Engine** (LangGraph + Groq), a **PWA** (Vite + React), and a **Supabase PostgreSQL** database.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker & Docker Compose | Latest | [docker.com](https://www.docker.com) |
| Python *(for manual setup)* | 3.10+ | [python.org](https://python.org) |
| Node.js *(for manual setup)* | 18+ | [nodejs.org](https://nodejs.org) |
| Git | any | [git-scm.com](https://git-scm.com) |

---

## 1. Environment Configuration

Create your environment files before running the application:

### Backend (`backend/.env`)
```env
# Supabase
SUPABASE_URL=https://[YOUR-PROJECT].supabase.co
SUPABASE_ANON_KEY=[YOUR-ANON-KEY]
SUPABASE_SERVICE_ROLE_KEY=[YOUR-SERVICE-ROLE-KEY]

# Database Connection (Use IPv4 pooler on port 5432 or 6543)
DATABASE_URL=postgresql://postgres.[YOUR-PROJECT]:[URL_ENCODED_PASSWORD]@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
DIRECT_URL=postgresql://postgres.[YOUR-PROJECT]:[URL_ENCODED_PASSWORD]@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres

# AI / Groq (Required for multi-agent engine)
GROQ_API_KEY=[YOUR-GROQ-API-KEY]

# Optional: Gemini (used by IVR fallback classifier)
GEMINI_API_KEY=[YOUR-GEMINI-API-KEY]

# Optional: Twilio Voice & Whapi WhatsApp
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...
WHAPI_CLOUD_API_TOKEN=...

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

## 2. Running with Docker Compose (Recommended)

Docker Compose containerizes and runs the entire stack together across 3 isolated services connected via an internal network (`sitesync-net`):

```bash
# 1. Build and start all services in detached mode
docker compose up --build -d

# 2. Check service status and health
docker compose ps
```

### Container Endpoints:

| Service | Container Name | Port Mapping | URL |
|---------|----------------|--------------|-----|
| **Frontend** | `sitesync-frontend` | `3000:3000` | [http://localhost:3000](http://localhost:3000) |
| **Backend & AI** | `sitesync-backend` | `8000:8000` | [http://localhost:8000](http://localhost:8000) / [Docs](http://localhost:8000/docs) |
| **Mobile PWA** | `sitesync-pwa` | `5173:80` | [http://localhost:5173](http://localhost:5173) |

### Useful Docker Commands:
```bash
# View backend & live AI cron logs
docker compose logs -f backend

# View frontend logs
docker compose logs -f frontend

# Execute a bash shell inside the backend container
docker compose exec -it backend bash

# Stop and remove containers
docker compose down
```

---

## 3. Manual Bare-Metal Setup (Alternative)

### A. Seeding the Database
Run the seed script once to populate demo company data and RBAC accounts:
```bash
# Navigate to the test directory
cd test
npm install @supabase/supabase-js
node seed.js
```
This creates the 4 core demo accounts (`admin@sitesync.local`, `pm@sitesync.local`, `contractor@sitesync.local`, `finance@sitesync.local` / Password: `password123`).

For a richer dataset (projects, tasks, inventory, equipment), run:
```bash
cd backend
.\venv\Scripts\Activate.ps1     # Windows
# source venv/bin/activate       # Mac/Linux
python seed_demo.py
```

### B. Starting the Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1     # Windows
# source venv/bin/activate       # Mac/Linux

pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
Runs at **http://localhost:8000** (Swagger at `/docs`).

### C. Starting the Frontend
```bash
cd frontend
npm install
npm run dev
```
Runs at **http://localhost:3000**.

### D. Starting the PWA
```bash
cd pwa
npm install
npm run dev
```
Runs at **http://localhost:5173**.

---

## 4. AI Agent System

The AI multi-agent engine runs as a subprocess of the FastAPI backend.

### Simulation Scenarios:
| ID | Description | Agents Triggered |
|----|-------------|------------------|
| `equipment_critical_failure` | Excavator critical failure | Equipment + Procurement |
| `stock_critically_low` | Cement stock below 10% threshold | Stock + Procurement |
| `budget_overrun` | Site expenses at 95% of monthly budget | Budget + Procurement |
| `task_delay_cascade` | Foundation delay cascades to 3 tasks | Project + Budget |
| `vendor_price_spike` | Cable price spike 35% above benchmark | Procurement + Budget |
| `multi_site_cascade` | Simultaneous equipment + stock emergency | Equipment + Stock + Budget + Procurement |
| `safety_violation` | Safety inspection flagged 3 violations | Project + Equipment |
| `schedule_risk_scan` | Proactive task/milestone risk scan | Project |

### Manual Trigger:
```bash
curl -X POST http://localhost:8000/api/v1/ai/trigger \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"scenario_id": "equipment_critical_failure"}'
```

---

## 5. Real-Time Architecture Overview

```
Frontend (Next.js) & PWA
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
