"""
ai/mcp/server.py
----------------
MCP-compatible server for SiteSync.

Exposes all SiteSync database tools as MCP tools so any MCP-compatible
AI client (Claude Desktop, Cursor, custom bots, etc.) can discover and
call them using the standard Model Context Protocol.

Runs on port 8001 (separate from the main FastAPI backend on 8000).

Locally:   http://localhost:8001
Deployed:  https://your-domain.com/mcp   (just change the URL)

Endpoints:
  GET  /mcp/info          - server info
  GET  /mcp/tools         - list all available tools
  POST /mcp/call          - call a specific tool
  POST /mcp/query         - natural language query (uses chat_agent)

Usage:
  python -m ai.mcp.server
  # or
  python ai/mcp/run.py
"""

import json
import sys
import os
from typing import Optional, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Add project root to path ──────────────────────────────────────────────────

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ── Import all SiteSync tools ─────────────────────────────────────────────────

from ai.agent.config import (
    get_transaction_history,
    compare_across_sites,
    get_consumption_rate_history,
    get_pending_requests_and_pos,
    get_budget_actuals,
    get_expense_breakdown_by_category,
    get_po_history,
    get_vendor_price_trend,
    compare_vendor_quotes,
    get_equipment_status,
    find_replacement_equipment,
    reallocate_equipment,
    get_task_dependencies,
    calculate_delay_impact,
    evaluate_vendor_reliability,
    get_market_price_benchmark,
    search_historical_records,
)
from ai.agent.chat_agent import run_chat

# ── Tool registry ─────────────────────────────────────────────────────────────

# Map tool name -> (callable, description, parameter schema)
_TOOL_REGISTRY: dict[str, dict] = {
    # ---- Stock ----------------------------------------------------------------
    "get_transaction_history": {
        "callable": get_transaction_history,
        "description": "Recent stock IN/OUT/TRANSFER records for a material at a site.",
        "parameters": {
            "material_id": {"type": "string", "description": "Numeric material ID"},
            "site_id":     {"type": "string", "description": "Numeric site ID"},
            "days":        {"type": "integer", "description": "Look-back window in days (default 14)", "default": 14},
            "type":        {"type": "string",  "description": "Filter: 'IN', 'OUT', or 'TRANSFER'", "optional": True},
        },
    },
    "compare_across_sites": {
        "callable": compare_across_sites,
        "description": "Stock levels of a material at all sites except the specified one, flagged for surplus.",
        "parameters": {
            "material_id":     {"type": "string", "description": "Numeric material ID"},
            "exclude_site_id": {"type": "string", "description": "Numeric site ID to exclude"},
        },
    },
    "get_consumption_rate_history": {
        "callable": get_consumption_rate_history,
        "description": "Baseline vs recent consumption rate, anomaly flag, per-contractor breakdown.",
        "parameters": {
            "material_id": {"type": "string",  "description": "Numeric material ID"},
            "site_id":     {"type": "string",  "description": "Numeric site ID"},
            "days":        {"type": "integer", "description": "History window in days (default 90)", "default": 90},
        },
    },
    "get_pending_requests_and_pos": {
        "callable": get_pending_requests_and_pos,
        "description": "Check for in-progress material request or purchase order for a material at a site.",
        "parameters": {
            "material_id": {"type": "string", "description": "Numeric material ID"},
            "site_id":     {"type": "string", "description": "Numeric site ID"},
        },
    },
    # ---- Budget ---------------------------------------------------------------
    "get_budget_actuals": {
        "callable": get_budget_actuals,
        "description": "Allocated, spent, remaining budget and utilization % for a site.",
        "parameters": {
            "site_id": {"type": "string", "description": "Numeric site ID"},
        },
    },
    "get_expense_breakdown_by_category": {
        "callable": get_expense_breakdown_by_category,
        "description": "Spend by category with percentages for a site.",
        "parameters": {
            "site_id": {"type": "string",  "description": "Numeric site ID"},
            "days":    {"type": "integer", "description": "Look-back window (default 30)", "default": 30},
        },
    },
    "get_po_history": {
        "callable": get_po_history,
        "description": "Purchase order history with unit prices, vendors, and delivery status.",
        "parameters": {
            "site_id": {"type": "string",  "description": "Numeric site ID"},
            "days":    {"type": "integer", "description": "Look-back window (default 60)", "default": 60},
        },
    },
    "get_vendor_price_trend": {
        "callable": get_vendor_price_trend,
        "description": "Vendor price trend for a specific material over time.",
        "parameters": {
            "material_id": {"type": "string", "description": "Numeric material ID"},
            "vendor_id":   {"type": "string", "description": "Numeric vendor ID"},
        },
    },
    "compare_vendor_quotes": {
        "callable": compare_vendor_quotes,
        "description": "Compare multiple vendor quotes for a specific material request.",
        "parameters": {
            "request_id": {"type": "string", "description": "Numeric material request ID"},
        },
    },
    # ---- Equipment ------------------------------------------------------------
    "get_equipment_status": {
        "callable": get_equipment_status,
        "description": "Current operational status of a piece of equipment by name (e.g. 'EXC-01').",
        "parameters": {
            "equipment_id": {"type": "string", "description": "Equipment name/code"},
        },
    },
    "find_replacement_equipment": {
        "callable": find_replacement_equipment,
        "description": "Find available idle equipment of a specific type at sites other than the given one.",
        "parameters": {
            "equipment_type":  {"type": "string", "description": "Type e.g. 'Excavator', 'Crane'"},
            "exclude_site_id": {"type": "string", "description": "Numeric site ID to exclude"},
        },
    },
    "reallocate_equipment": {
        "callable": reallocate_equipment,
        "description": "Stage a reallocation PROPOSAL for idle equipment (does NOT write to DB).",
        "parameters": {
            "equipment_id": {"type": "string", "description": "Equipment name/code"},
            "to_site_id":   {"type": "string", "description": "Numeric destination site ID"},
        },
    },
    # ---- Project --------------------------------------------------------------
    "get_task_dependencies": {
        "callable": get_task_dependencies,
        "description": "Get the downstream project tasks that depend on a given task.",
        "parameters": {
            "task_id": {"type": "string", "description": "Numeric task ID"},
        },
    },
    "calculate_delay_impact": {
        "callable": calculate_delay_impact,
        "description": "Calculate the operational and financial impact of delaying a task.",
        "parameters": {
            "task_id":      {"type": "string",  "description": "Numeric task ID"},
            "delayed_days": {"type": "integer", "description": "Number of days delayed"},
        },
    },
    # ---- Procurement ---------------------------------------------------------
    "evaluate_vendor_reliability": {
        "callable": evaluate_vendor_reliability,
        "description": "Evaluate a vendor's historical performance from real PO and delivery data.",
        "parameters": {
            "vendor_id": {"type": "string", "description": "Numeric vendor ID"},
        },
    },
    "get_market_price_benchmark": {
        "callable": get_market_price_benchmark,
        "description": "Current regional market benchmark price for a material.",
        "parameters": {
            "material_id": {"type": "string", "description": "Numeric material ID"},
        },
    },
    # ---- RAG / Semantic search -----------------------------------------------
    "search_historical_records": {
        "callable": search_historical_records,
        "description": (
            "Semantic search over historical inventory transactions, material requests, "
            "purchase orders, vendor/procurement records. Use to find relevant history."
        ),
        "parameters": {
            "query":        {"type": "string", "description": "Natural language search query"},
            "company_id":   {"type": "string", "description": "Optional company ID filter", "optional": True},
            "site_id":      {"type": "string", "description": "Optional site ID filter",    "optional": True},
            "source_table": {"type": "string", "description": "Optional table filter",      "optional": True},
            "vendor_id":    {"type": "string", "description": "Optional vendor ID filter",  "optional": True},
        },
    },
    # ---- Natural language query (high-level) ---------------------------------
    "query_sitesync": {
        "callable": None,  # handled separately — calls run_chat()
        "description": (
            "Ask SiteSync any natural-language operational question. "
            "The AI agent will automatically pick the right tools and return a grounded answer. "
            "Use this for complex questions instead of calling individual tools."
        ),
        "parameters": {
            "question":   {"type": "string", "description": "Plain-English question"},
            "site_id":    {"type": "string", "description": "Optional site context", "optional": True},
            "company_id": {"type": "string", "description": "Optional company context", "optional": True},
        },
    },
}

# ── FastAPI app ───────────────────────────────────────────────────────────────

mcp_app = FastAPI(
    title="SiteSync MCP Server",
    version="1.0.0",
    description=(
        "Model Context Protocol server for SiteSync construction operations. "
        "Exposes live database tools so any MCP-compatible AI client can query "
        "stock, budget, equipment, projects, and procurement data in natural language."
    ),
)

mcp_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # MCP clients may come from anywhere — restrict in prod if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response schemas ──────────────────────────────────────────────────

class ToolCallRequest(BaseModel):
    tool: str
    arguments: dict[str, Any] = {}


class NLQueryRequest(BaseModel):
    question: str
    site_id: Optional[str] = None
    company_id: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@mcp_app.get("/mcp/info")
def mcp_info():
    """MCP server metadata — used by clients to identify this server."""
    return {
        "name": "sitesync-mcp",
        "version": "1.0.0",
        "description": "SiteSync construction operations MCP server",
        "protocol": "mcp/1.0",
        "capabilities": ["tools"],
        "tools_count": len(_TOOL_REGISTRY),
        "base_url": "http://localhost:8001",
    }


@mcp_app.get("/mcp/tools")
def list_tools():
    """
    List all available MCP tools.
    MCP clients call this on connect to discover what tools are available.
    """
    tools = []
    for name, meta in _TOOL_REGISTRY.items():
        tools.append({
            "name": name,
            "description": meta["description"],
            "parameters": meta["parameters"],
        })
    return {"tools": tools}


@mcp_app.post("/mcp/call")
def call_tool(req: ToolCallRequest):
    """
    Call a specific MCP tool by name with arguments.

    This is the standard MCP tool-call endpoint.
    Any MCP-compatible client (Claude Desktop, Cursor, custom bots) sends requests here.

    Example:
        POST /mcp/call
        {
          "tool": "get_budget_actuals",
          "arguments": { "site_id": "2" }
        }
    """
    if req.tool not in _TOOL_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{req.tool}' not found. Call GET /mcp/tools to see available tools."
        )

    meta = _TOOL_REGISTRY[req.tool]

    # Special case: query_sitesync calls the chat agent
    if req.tool == "query_sitesync":
        question = req.arguments.get("question")
        if not question:
            raise HTTPException(status_code=400, detail="'question' argument is required for query_sitesync.")
        try:
            result = run_chat(
                question=question,
                site_id=req.arguments.get("site_id"),
                company_id=req.arguments.get("company_id"),
            )
            return {"tool": req.tool, "result": result, "type": "text/markdown"}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    # All other tools: call the underlying function directly
    fn = meta["callable"]
    try:
        raw_result = fn.invoke(req.arguments)
        # LangChain tools return JSON strings — parse for cleaner response
        try:
            parsed = json.loads(raw_result)
        except (json.JSONDecodeError, TypeError):
            parsed = raw_result
        return {"tool": req.tool, "result": parsed, "type": "application/json"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@mcp_app.post("/mcp/query")
def natural_language_query(req: NLQueryRequest):
    """
    High-level natural language query endpoint.
    Equivalent to calling the 'query_sitesync' tool directly.

    Example:
        POST /mcp/query
        { "question": "What is the budget status for Site 2?" }
    """
    try:
        result = run_chat(
            question=req.question,
            site_id=req.site_id,
            company_id=req.company_id,
        )
        return {
            "question": req.question,
            "answer": result,
            "type": "text/markdown",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@mcp_app.get("/health")
def health():
    return {"status": "ok", "service": "sitesync-mcp"}


# ── Run directly ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("MCP_PORT", 8001))
    print(f"[MCP] SiteSync MCP Server starting on http://localhost:{port}")
    print(f"[MCP] Tools available: {len(_TOOL_REGISTRY)}")
    print(f"[MCP] Tools list: GET http://localhost:{port}/mcp/tools")
    print(f"[MCP] Tool call: POST http://localhost:{port}/mcp/call")
    print(f"[MCP] NL query:  POST http://localhost:{port}/mcp/query")
    uvicorn.run("ai.mcp.server:mcp_app", host="0.0.0.0", port=port, reload=False)
