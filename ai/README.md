# SiteSync — AI Multi-Agent System

Real-time multi-agent investigation engine built with **LangGraph**, **LangChain**, and **Groq**.

> **Note:** The AI engine runs inside the `backend/venv` virtual environment. All AI dependencies are included in `backend/requirements.txt`. There is no separate venv for `ai/`.

---

## Architecture

```
Webhook / Alert Payload (JSON)
         │
         ▼
  Anomaly Detector Node
  (Translates raw log → natural language alert)
         │
         ▼
  Supervisor Node
  (Decides which specialist agents to invoke)
         │
    ┌────┴──────────────────────────────┐
    ▼         ▼         ▼         ▼     ▼
Equipment   Stock    Budget   Project  Procurement
 Agent      Agent    Agent    Agent     Agent
    │         │         │         │         │
    └────┬──────────────────────────────┘
         │   (each agent queries Supabase via tools)
         ▼
  Supervisor (loops until all relevant agents done)
         │
         ▼
  Master Reporter Node
  (Compiles final Markdown report)
         │
         ▼
  notification_service.create_alert_and_notify()
  (Inserts Alert + role-based Notifications → SSE push)
```

All agents run via **LangGraph `app.invoke()`**. Each node emits a **JSON event to stdout** when it starts/completes. The FastAPI parent process reads these events line-by-line and broadcasts them via the EventManager to the frontend WebSocket.

---

## Directory Structure

```
ai/
├── agent/
│   ├── orchestrator.py    # LangGraph graph + event emission + notification hook
│   ├── config.py          # WORKER_CONFIG — tools + prompts per agent
│   ├── scenarios.py       # 8 simulation scenario definitions
│   └── chat_agent.py      # Conversational AI chat agent (separate from investigation)
├── tools/
│   ├── stock.py           # Inventory/stock query tools
│   ├── budget.py          # Budget & expense tools
│   ├── equipment.py       # Equipment status & reallocation tools
│   ├── project.py         # Task, milestone & schedule tools (CPM/Gantt aware)
│   ├── procurement.py     # Vendor quotes & procurement tools
│   └── rag.py             # Semantic search (SentenceTransformer embeddings)
├── core/
│   ├── config.py          # Supabase + Groq client init
│   ├── embeddings.py      # SentenceTransformer embed()
│   └── index_chunk.py     # Vector indexing helper
├── authenticity/          # Anomaly detection utilities
├── scripts/
│   ├── test_agent.py      # Main entrypoint (called as FastAPI subprocess)
│   ├── generate_mock_data.py
│   └── diagnose_agents.py
├── .env                   # AI-specific env vars (see Setup below)
├── .env.example
└── requirements.txt       # Reference only — use backend/requirements.txt
```

---

## Simulation Scenarios

The AI engine supports 8 pre-built simulation scenarios, selectable from the UI or via the API:

| ID | Label | Severity | Agents Triggered |
|----|-------|----------|-----------------|
| `equipment_critical_failure` | Equipment Critical Failure | 🔴 Critical | Equipment + Procurement |
| `stock_critically_low` | Critical Stock Shortage | 🔴 Critical | Stock + Procurement |
| `budget_overrun` | Budget Overrun Detected | 🟡 Warning | Budget + Procurement |
| `task_delay_cascade` | Task Delay Cascade | 🟡 Warning | Project + Budget |
| `vendor_price_spike` | Vendor Price Spike | 🟡 Warning | Procurement + Budget |
| `multi_site_cascade` | Multi-Site Emergency Cascade | 🔴 Critical | Equipment + Stock + Budget + Procurement |
| `safety_violation` | Safety Compliance Violation | 🔴 Critical | Project + Equipment |
| `schedule_risk_scan` | Proactive Schedule Risk Scan | 🔵 Info | Project |

---

## Event Schema

Every event emitted to stdout is a newline-delimited JSON object:

```json
{
  "id": "evt_a1b2c3d4",
  "run_id": "run_abc123def",
  "timestamp": "2026-08-31T06:00:00Z",
  "type": "AGENT_STARTED",
  "agent": "EQUIPMENT_AGENT",
  "content": "Starting investigation...",
  "tool_name": null,
  "data": {}
}
```

### Event Types

| Type | Description |
|------|-------------|
| `RUN_STARTED` | Investigation kicked off |
| `AGENT_STARTED` | A LangGraph node began executing |
| `AGENT_COMPLETED` | A node returned its result |
| `TOOL_STARTED` | An agent called a Supabase tool |
| `TOOL_COMPLETED` | Tool returned data |
| `FINAL_REPORT` | Master reporter's completed Markdown investigation report |
| `MESSAGE` | Plain log line |
| `RUN_COMPLETED` | Full graph execution finished |
| `RUN_FAILED` | Unrecoverable error |

---

## Setup

The AI engine uses the **same virtual environment as the backend**.

```bash
# Use backend venv
cd backend
.\venv\Scripts\Activate.ps1     # Windows
# source venv/bin/activate       # Mac/Linux

# All dependencies already installed via:
pip install -r requirements.txt
```

Create `ai/.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
GROQ_API_KEY=your-groq-api-key
```

### Trigger via API (recommended)
```bash
curl -X POST http://localhost:8000/api/v1/ai/trigger \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scenario_id": "equipment_critical_failure"}'
```

### Run Directly (for debugging)
```bash
# Must be run from the project root
backend/venv/Scripts/python.exe ai/scripts/test_agent.py
```

---

## Auto-Simulation (Cron)

The backend automatically triggers a rotating scenario every **15 minutes** via APScheduler. The scenario rotates through all 8 defined scenarios in sequence.

This can also be triggered manually:
```bash
python backend/swap_senario.py
```

---

## Adding New Agents

1. Add tools to `ai/tools/your_agent.py`
2. Add the agent config entry to `WORKER_CONFIG` in `ai/agent/config.py`
3. Add a node function in `orchestrator.py` calling `_worker_node("your_key", "YOUR_AGENT", state)`
4. Wire the node into the LangGraph edges
5. Add the agent name to the Supervisor's valid routing options
6. Add the scenario to `ai/agent/scenarios.py` if creating a new simulation scenario
