# SiteSync — Backend

FastAPI backend for the SiteSync construction management platform.

## Stack

| Layer | Technology |
|-------|-----------|
| API | **FastAPI** — REST + WebSocket + SSE endpoints |
| ORM | **SQLAlchemy 2.0** (PostgreSQL via psycopg2-binary) |
| Auth | **Supabase Auth** + JWT (python-jose) |
| AI Engine | **LangGraph + LangChain + Groq** (multi-agent) |
| IVR | **Twilio** + **google-genai** (voice intent classification) |
| Notifications | **APScheduler** + asyncio event bus (in-app SSE + WhatsApp) |
| DB | **Supabase** hosted PostgreSQL |

---

## Directory Structure

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── ai.py              # POST /ai/trigger + WS /ai/stream/{run_id}
│   │   ├── auth.py            # POST /auth/login, GET /auth/me
│   │   ├── alerts.py          # GET /alerts (role-filtered)
│   │   ├── notifications.py   # GET /notifications + SSE /notifications/stream
│   │   ├── projects.py        # Projects + Tasks + Milestones + Gantt + Schedule Health
│   │   ├── sites.py
│   │   ├── inventory.py
│   │   ├── equipment.py
│   │   ├── procurement.py
│   │   ├── finance.py
│   │   ├── dashboard.py
│   │   ├── admin.py
│   │   └── chat.py
│   ├── events/
│   │   └── manager.py         # EventManager — asyncio queue pub/sub
│   ├── models/                # SQLAlchemy ORM models
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/
│   │   ├── notification_service.py   # AI-run → Alert + role-based Notifications
│   │   ├── notifications/
│   │   │   ├── dispatcher.py         # Multi-channel delivery
│   │   │   ├── channels/in_app.py    # SSE WebSocket push
│   │   │   ├── channels/whatsapp.py  # WhatsApp (whapi.co)
│   │   │   └── channels/sms.py       # SMS (Twilio, stub)
│   │   └── schedule_monitor.py       # Background project risk scanner
│   ├── core/
│   │   ├── deps.py            # get_current_user, require_role, require_site_access
│   │   └── supabase.py        # Supabase client init
│   ├── db/session.py          # DB engine + SessionLocal
│   └── main.py                # FastAPI app + CORS + routers + APScheduler startup
├── ivr/
│   ├── webhook.py             # Twilio inbound call handler (/ivr/*)
│   ├── intent_classifier.py   # Keyword → Gemini fallback classifier
│   ├── request_extractor.py   # Material/quantity/site extractor
│   ├── caller_lookup.py       # DB-assisted caller identity resolution
│   └── tool_adapters.py       # IVR → backend API adapters
├── scripts/
│   └── benchmark_ivr_latency.py
├── seed_demo.py               # Demo data seeder (projects, inventory, equipment)
├── swap_senario.py            # CLI tool to rotate AI scenario
└── requirements.txt
```

---

## Setup

```bash
cd backend

# Create virtual environment (first time only)
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1     # Windows
# source venv/bin/activate       # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### `.env` file
```env
# Supabase
SUPABASE_URL=https://[YOUR-PROJECT].supabase.co
SUPABASE_ANON_KEY=[YOUR-ANON-KEY]
SUPABASE_SERVICE_ROLE_KEY=[YOUR-SERVICE-ROLE-KEY]

# PostgreSQL
DATABASE_URL=postgresql://postgres.[PROJECT]:[PASSWORD]@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres

# AI / Groq (for multi-agent AI engine)
GROQ_API_KEY=[YOUR-GROQ-API-KEY]

# Gemini (optional — IVR fallback classifier only)
GEMINI_API_KEY=[YOUR-GEMINI-API-KEY]

# CORS
FRONTEND_URL=http://localhost:3000
```

### Start Server
```bash
python -m uvicorn app.main:app --reload
```

API runs at **http://localhost:8000** | Docs at **http://localhost:8000/docs**

On startup, two background schedulers are started automatically:
- **AI Auto-Simulation** — triggers a random simulation scenario every 15 minutes
- **Schedule Monitor** — scans active projects for overdue tasks / at-risk milestones

---

## API Endpoints

### AI
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/ai/trigger` | Start AI investigation, returns `run_id` |
| `WS` | `/api/v1/ai/stream/{run_id}` | WebSocket stream of real-time AI events |
| `GET` | `/api/v1/ai/scenarios` | List all available simulation scenarios |

### Notifications
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/notifications/` | Fetch paginated notifications for current user |
| `GET` | `/api/v1/notifications/stream` | SSE stream — real-time push to browser |
| `PATCH` | `/api/v1/notifications/{id}/read` | Mark single notification read |
| `PATCH` | `/api/v1/notifications/mark-all-read` | Mark all notifications read |

### Projects & Scheduling
| Method | Path | Description |
|--------|------|-------------|
| `GET/POST` | `/api/v1/projects/` | List / create projects |
| `GET/PATCH` | `/api/v1/projects/{id}` | Project detail / update |
| `GET` | `/api/v1/projects/{id}/gantt` | Gantt chart data with critical path |
| `GET` | `/api/v1/projects/{id}/schedule-health` | Risk banner: on_track / at_risk / critical |
| `GET/POST` | `/api/v1/projects/{id}/tasks` | Task list / create |
| `PATCH` | `/api/v1/projects/{id}/tasks/{task_id}` | Update task status / progress |
| `GET/POST` | `/api/v1/projects/{id}/milestones` | Milestone list / create |

### Core
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/login` | Login → JWT |
| `GET` | `/api/v1/auth/me` | Current user profile |
| `GET` | `/api/v1/dashboard/summary` | Dashboard metrics |
| `GET/POST` | `/api/v1/inventory/` | Inventory management |
| `GET/POST` | `/api/v1/equipment/` | Equipment tracking |
| `GET/POST` | `/api/v1/procurement/requests/` | Material requests |
| `GET` | `/api/v1/alerts/` | Role-filtered alerts |
| `GET/POST` | `/api/v1/sites/` | Site management |
| `GET` | `/api/v1/finance/` | Budget & expense tracking |

### IVR (Twilio Voice)
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ivr/incoming` | Twilio inbound call webhook |
| `POST` | `/ivr/process` | Natural language intent parsing |
| `POST` | `/ivr/confirm_request` | Voice confirmation response |
| `GET` | `/ivr/logs` | Simulated/live call logs |
| `POST` | `/ivr/simulate` | Submit mock speech for browser simulator |

---

## Real-Time Architecture

### AI WebSocket Flow
```
POST /api/v1/ai/trigger
  → creates run_id
  → spawns subprocess: ai/scripts/test_agent.py
  → subprocess prints JSON events to stdout
  → FastAPI reads stdout → EventManager.publish_sync()

WS /api/v1/ai/stream/{run_id}
  → frontend connects
  → EventManager delivers queued events via asyncio.Queue
  → connection closes on RUN_COMPLETED
```

### Notification SSE Flow
```
AI run completes
  → notification_service.create_alert_and_notify()
  → Alert row inserted in DB
  → Notification rows inserted per role-matched user
  → InAppChannel.send() → event_manager.publish_sync(f"user_{user.id}", payload)

SSE GET /api/v1/notifications/stream
  → event_generator subscribes to "user_{user.id}" queue
  → pushes notification events as text/event-stream to browser
```

---

## Multilingual Voice IVR Pipeline

SiteSync mounts a low-latency voice pipeline at `/ivr`.

To test with real calls, start an ngrok tunnel:
```bash
ngrok http 8000
```
Set your **Twilio Console** webhook to: `https://<ngrok-url>/ivr/incoming` (HTTP POST)

### Performance Design
- **Keyword classifier** runs first (zero latency, handles 90% of calls)
- **google-genai** (`Gemini`) fallback fires only for ambiguous speech, with a 5-second hard timeout to prevent Twilio gateway timeouts
- **DB-Assisted Entity Resolution**: site and material names are matched directly against the PostgreSQL database for high accuracy
