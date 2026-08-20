# SiteSync — AI Multi-Agent System

Real-time multi-agent investigation engine built with **LangGraph**, **LangChain**, and **Groq**.

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
  (Decides which specialist agent to call next)
         │
    ┌────┴────────────────────────┐
    ▼         ▼         ▼         ▼         ▼
Equipment   Stock    Budget   Project  Procurement
 Agent      Agent    Agent    Agent     Agent
    │         │         │         │         │
    └────┬────────────────────────┘
         │   (each agent has tools to query Supabase)
         ▼
  Supervisor (loops until all relevant agents done)
         │
         ▼
  Master Reporter Node
  (Compiles final Markdown report)
```

All agents run via **LangGraph `app.invoke()`**. Each node emits a **JSON event to stdout** immediately when it starts/completes. The FastAPI parent process reads these lines and broadcasts them via WebSocket to the frontend.

## Structure

```
ai/
├── agent/
│   ├── orchestrator.py    # LangGraph graph definition + event emission
│   └── config.py          # WORKER_CONFIG — tools + prompts per agent
├── tools/
│   ├── stock.py           # Inventory/stock query tools
│   ├── budget.py          # Budget & expense tools
│   ├── equipment.py       # Equipment status & reallocation tools
│   ├── project.py         # Task & project schedule tools
│   ├── procurement.py     # Vendor quotes & procurement tools
│   └── rag.py             # Semantic search (vector embeddings)
├── core/
│   ├── config.py          # Supabase + Groq client init
│   ├── embeddings.py      # SentenceTransformer embed()
│   └── index_chunk.py     # Vector indexing helper
├── authenticity/          # Anomaly detection utilities
├── scripts/
│   ├── test_agent.py      # Main entrypoint (called by FastAPI subprocess)
│   ├── generate_mock_data.py
│   └── diagnose_agents.py
└── requirements.txt
```

## Event Schema

Every event emitted to stdout is a JSON line:

```json
{
  "id": "evt_a1b2c3d4",
  "run_id": "run_abc123def",
  "timestamp": "2026-08-21T00:30:00Z",
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
| `FINAL_REPORT` | The master reporter's finished Markdown report |
| `MESSAGE` | Plain log line |
| `RUN_COMPLETED` | Full graph execution finished |
| `RUN_FAILED` | Unrecoverable error |

## Setup

> The AI engine shares the `backend/venv` virtual environment. All dependencies are in `backend/requirements.txt`.

Create `ai/.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
GROQ_API_KEY=your-groq-api-key
```

Run directly (for testing):
```bash
cd SiteSync   # must be run from project root
backend/venv/Scripts/python.exe ai/scripts/test_agent.py
```

Or trigger via the FastAPI endpoint:
```
POST http://localhost:8000/api/v1/ai/trigger
```

## Adding New Agents

1. Add tools to `ai/tools/your_agent.py`
2. Add the agent config to `WORKER_CONFIG` in `ai/agent/config.py`
3. Add a node function in `orchestrator.py` calling `_worker_node("your_key", "YOUR_AGENT", state)`
4. Wire it into the LangGraph edges
5. Add the agent name to the Supervisor's valid nodes list
