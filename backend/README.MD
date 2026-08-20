# SiteSync — Backend

FastAPI backend for the SiteSync platform.

## Stack
- **FastAPI** — REST + WebSocket endpoints
- **SQLAlchemy** — ORM (PostgreSQL via psycopg2)
- **Supabase** — Auth + hosted PostgreSQL
- **LangGraph / LangChain / Groq** — Multi-agent AI engine
- **asyncio** — Event bus for real-time WebSocket streaming

## Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── ai.py          # POST /ai/trigger  +  WS /ai/stream/{run_id}
│   │       ├── auth.py
│   │       ├── dashboard.py
│   │       ├── inventory.py
│   │       ├── procurement.py
│   │       └── ...
│   ├── events/
│   │   ├── manager.py         # EventManager — asyncio queue per run_id
│   │   └── models.py          # make_event() factory
│   ├── models/                # SQLAlchemy ORM models
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/              # Business logic
│   ├── db/session.py          # DB engine + session
│   └── main.py                # FastAPI app + CORS + routers
├── scripts/
│   └── migrate_db.py          # Adds missing columns to existing tables
└── requirements.txt
```

## Setup

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env`:
```env
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
DATABASE_URL=postgresql://...
DIRECT_URL=postgresql://...
GROQ_API_KEY=...
FRONTEND_URL=http://localhost:3000
```

Run migrations (adds columns if missing):
```bash
python scripts/migrate_db.py
```

Start server:
```bash
uvicorn app.main:app --reload
```

## Real-time AI WebSocket Flow

```
POST /api/v1/ai/trigger
  → creates run_id
  → spawns subprocess (ai/scripts/test_agent.py)
  → subprocess prints JSON events to stdout line-by-line
  → FastAPI reads stdout and calls EventManager.publish_sync()

WS /api/v1/ai/stream/{run_id}
  → frontend connects
  → EventManager delivers queued events instantly via asyncio.Queue
  → connection closes cleanly on RUN_COMPLETED
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/ai/trigger` | Start AI investigation, returns `run_id` |
| WS | `/api/v1/ai/stream/{run_id}` | Stream events for a run |
| POST | `/api/v1/auth/login` | JWT login |
| GET | `/api/v1/dashboard/summary` | Dashboard metrics |
| GET/POST | `/api/v1/inventory/` | Inventory management |
| GET/POST | `/api/v1/procurement/requests/` | Material requests |
| ... | | |
