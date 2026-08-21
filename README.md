# SiteSync

**Construction Resource Intelligence Platform** — A full-stack application for managing construction sites, equipment, inventory, procurement, and finance — with a real-time AI multi-agent investigation system powered by LangGraph and Groq.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, PostgreSQL (via Supabase) |
| AI Engine | LangGraph, LangChain, Groq (openai/gpt-oss-120b) |
| Real-time | WebSockets (FastAPI native) |
| Auth | JWT + Supabase Auth |
| DB | PostgreSQL (Supabase hosted) |

---

## Project Structure

```
SiteSync/
├── frontend/          # Next.js 14 app
│   ├── app/           # App Router pages
│   ├── components/    # Shared UI components
│   └── .env.local     # Frontend env vars
│
├── backend/           # FastAPI server
│   ├── app/
│   │   ├── api/v1/    # REST + WebSocket endpoints
│   │   ├── events/    # Real-time EventManager (asyncio queues)
│   │   ├── models/    # SQLAlchemy ORM models
│   │   ├── schemas/   # Pydantic schemas
│   │   └── services/  # Business logic
│   ├── scripts/       # DB migration utilities
│   └── requirements.txt
│
└── ai/                # Multi-agent AI system
    ├── agent/         # LangGraph orchestrator + node config
    ├── tools/         # Agent tools (stock, budget, equipment, etc.)
    ├── core/          # Supabase client, embeddings
    ├── scripts/       # Test runner & data generation scripts
    └── requirements.txt
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Supabase project
- A Groq API key

### 1. Clone the repo
```bash
git clone https://github.com/your-username/SiteSync.git
cd SiteSync
```

### 2. Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows
# source venv/bin/activate          # macOS/Linux

pip install -r requirements.txt
```

Create `backend/.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://user:password@host:5432/db
DIRECT_URL=postgresql://user:password@host:5432/db
GROQ_API_KEY=your-groq-key
FRONTEND_URL=http://localhost:3000
```

Run migrations then start:
```bash
python scripts/migrate_db.py
uvicorn app.main:app --reload
```

### 3. AI Agent
```bash
cd ai
```

Create `ai/.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
GROQ_API_KEY=your-groq-key
```

> The AI agent shares the backend's virtual environment (`backend/venv`). All AI dependencies are included in `backend/requirements.txt`.

### 4. Frontend
```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

```bash
npm run dev
```

App runs at **http://localhost:3000**

---

## Key Features

### Core Platform
- **Sites & Projects** — Manage construction sites, projects, and milestones
- **Inventory** — Track materials with stock alerts
- **Equipment** — Monitor equipment status and maintenance
- **Procurement** — Material request → PM approval → Finance approval workflow
- **Finance** — Budget tracking and expense management
- **Alerts & Notifications** — Real-time system alerts

### Live AI Activity (LangGraph + Groq)
A multi-agent system that investigates site anomalies in real-time:

```
Webhook Event (equipment failure, stock alert, etc.)
        ↓
Anomaly Detector  →  Supervisor Agent
                            ↓
              ┌─────────────┼─────────────┐
         Equipment      Budget       Stock / Project / Procurement
              └─────────────┼─────────────┘
                            ↓
                    Master Reporter
                            ↓
                  Final Report (Markdown)
```

Events stream live to the UI via **WebSocket** — every node transition, tool call, and result appears instantly in the terminal feed as it happens.

---

## Environment Variables Summary

| File | Variable | Description |
|------|----------|-------------|
| `backend/.env` | `SUPABASE_URL` | Supabase project URL |
| `backend/.env` | `SUPABASE_ANON_KEY` | Supabase anon key |
| `backend/.env` | `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `backend/.env` | `DATABASE_URL` | PostgreSQL connection string |
| `backend/.env` | `GROQ_API_KEY` | Groq API key |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL` | Backend URL |
| `frontend/.env.local` | `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `ai/.env` | `GROQ_API_KEY` | Groq API key |
| `ai/.env` | `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |

---

## Multilingual Voice IVR (Twilio Integration)

SiteSync includes a voice-based IVR assistant allowing field staff (contractors, supervisors, PMs) to query resources or request materials over a real phone call in **English, Hindi, or Marathi**.

### Core Voice Operations
- **Stock Check**: *"How much cement is at Downtown Plaza?"* (Returns real-time inventory from Postgres).
- **Equipment Location**: *"Where is the crane?"* (Fuzzy matches type or name to check operational status).
- **Budget Tracking**: *"Check site budget"* (Restricted to PM role - returns allocated vs spent).
- **Material Placement**: *"Place an order for 860 bags of cement in Downtown Plaza"* (Prompts voice confirmation, then creates a `MaterialRequest` flagged with a `"📞 Voice IVR"` badge).

### High-Performance Architecture
To meet Twilio's strict 5-second HTTP timeout and provide a premium user experience, the voice pipeline uses a hybrid low-latency execution model:
1. **DB-Assisted Local Parsing**: Pre-matches spoken terms against site and material name tables in PostgreSQL. Typographical/STT errors (like *"is **that** Downtown Plaza"* instead of *"is **at** Downtown Plaza"*) are resolved instantly.
2. **LLM Fallback**: Only invokes the Gemini API for complex or ambiguous sentences.
3. **Zero Gemini Compression**: Localized speech response formatting runs deterministically in <5ms.
4. **Total Latency**: Dropped from **6,000ms (LLM-only)** to **under 15ms** per turn.

### Local Simulation & Testing
An interactive, browser-based voice sandbox is built directly into the Next.js frontend:
1. Navigate to the **Voice IVR** tab in the sidebar navigation.
2. Type or speak queries to the mock call simulator using the seeded phone number `+919223700700`.
3. View classified intents, extracted entities, and system audio replies, or confirm pending actions.
4. Active calls can be monitored live in the adjacent Call Monitor feed.

---

## License

MIT

