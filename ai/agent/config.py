import json
from langchain_core.tools import tool
from typing import Optional
from ai.tools import stock, budget, rag, equipment, project, procurement
from ai.core.config import supabase

# ─────────────────────────────────────────────────────────────────────────────
# NULL-HANDLING RULE — injected into every agent system prompt.
# This prevents the model from estimating, inferring, or using world knowledge
# when tools return empty results.
# ─────────────────────────────────────────────────────────────────────────────
NULL_HANDLING_RULE = (
    "\n\nCRITICAL DATA RULES:\n"
    "- If a tool returns an empty list [], an error, or a 'no_*_found' result: "
    "state EXACTLY 'No data available for [topic]' in your report. "
    "Do NOT estimate, infer, guess, or use general knowledge to fill the gap.\n"
    "- Do NOT fabricate prices, quantities, vendor names, dates, or any numbers "
    "that did not appear in a tool response.\n"
    "- Every factual claim MUST cite the database source: [table_name: record_id] "
    "(e.g. [equipment: 1], [purchase_orders: 42]).\n"
    "- ALWAYS pass EXACT NUMERIC IDs (e.g. '69') to tools for site_id, material_id, vendor_id. NEVER pass string names (e.g. 'Electrical Cable'). Use the list_sites, list_materials, or list_vendors tools to find the numeric ID first if needed.\n"
    "- If you cannot find data after 3-4 tool calls, stop and report what you found."
)

# ─────────────────────────────────────────────────────────────────────────────
# DISCOVERY TOOLS — let the agent look up real numeric IDs from names
# ─────────────────────────────────────────────────────────────────────────────

@tool
def list_sites() -> str:
    """List all sites with their numeric IDs and names. ALWAYS call this first when the user mentions a site by name (e.g. 'Site 1', 'Northwood') so you can get the correct numeric site_id to use in other tools."""
    try:
        resp = supabase.table('sites').select('id, name, status').order('name').execute()
        return json.dumps(resp.data if resp.data else [])
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def list_materials() -> str:
    """List all materials with their numeric IDs and names. Call this when the user mentions a material by name (e.g. 'cement', 'steel') so you can get the correct numeric material_id."""
    try:
        resp = supabase.table('materials').select('id, name, unit').order('name').execute()
        return json.dumps(resp.data if resp.data else [])
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def list_vendors() -> str:
    """List all vendors with their numeric IDs and names. Call this to look up a vendor's numeric vendor_id from their name."""
    try:
        resp = supabase.table('vendors').select('id, name, category').order('name').execute()
        return json.dumps(resp.data if resp.data else [])
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def search_historical_records(query: str, company_id: Optional[str] = None, site_id: Optional[str] = None, source_table: Optional[str] = None, vendor_id: Optional[str] = None) -> list:
    """Semantic search over historical inventory transactions, material requests, purchase orders, vendor/procurement records, and expenses — including operational/site context captured in transaction references and request justifications. Use to find relevant history before explaining an issue."""
    return json.dumps(rag.search_historical_records(query, company_id, site_id, source_table, vendor_id))

@tool
def get_transaction_history(material_id: str, site_id: str, days: int = 14, type: Optional[str] = None) -> list:
    """Recent stock in/out/transfer records for a material at a site."""
    return json.dumps(stock.get_transaction_history(material_id, site_id, days, type))

@tool
def compare_across_sites(material_id: str, exclude_site_id: str) -> list:
    """Stock of a material at other sites, flagged for surplus against max_capacity."""
    return json.dumps(stock.compare_across_sites(material_id, exclude_site_id))

@tool
def get_consumption_rate_history(material_id: str, site_id: str, days: int = 90) -> dict:
    """Baseline vs recent consumption rate, anomaly flag, per-contractor breakdown."""
    return json.dumps(stock.get_consumption_rate_history(material_id, site_id, days))

@tool
def get_pending_requests_and_pos(material_id: str, site_id: str) -> dict:
    """Check for an in-progress request/PO before recommending a new one."""
    return json.dumps(stock.get_pending_requests_and_pos(material_id, site_id))

@tool
def get_budget_actuals(site_id: str) -> dict:
    """Allocated, spent, remaining, utilization percent for a site."""
    return json.dumps(budget.get_budget_actuals(site_id))

@tool
def get_expense_breakdown_by_category(site_id: str, days: int = 30) -> list:
    """Spend by category with percentages."""
    return json.dumps(budget.get_expense_breakdown_by_category(site_id, days))

@tool
def get_po_history(site_id: str, days: int = 60) -> list:
    """PO history with unit prices, vendors, delivery status."""
    return json.dumps(budget.get_po_history(site_id, days))

@tool
def get_vendor_price_trend(material_id: str, vendor_id: str) -> list:
    """Vendor price trend for a material over time."""
    return json.dumps(budget.get_vendor_price_trend(material_id, vendor_id))

@tool
def compare_vendor_quotes(request_id: str) -> str:
    """Compare multiple vendor quotes for a specific material request (based on price and terms). request_id must be a numeric integer from the material_requests table."""
    return json.dumps(budget.compare_vendor_quotes(request_id))

@tool
def get_equipment_status(equipment_id: str) -> str:
    """Get the current operational status of a piece of equipment by its name (e.g. 'EXC-01')."""
    return json.dumps(equipment.get_equipment_status(equipment_id))

@tool
def find_replacement_equipment(equipment_type: str, exclude_site_id: str) -> str:
    """Find available idle equipment of a specific type at sites other than exclude_site_id. equipment_type examples: 'Excavator', 'Crane'."""
    return json.dumps(equipment.find_replacement_equipment(equipment_type, exclude_site_id))

@tool
def reallocate_equipment(equipment_id: str, to_site_id: str) -> str:
    """
    Stage a reallocation PROPOSAL for idle equipment. DOES NOT write to the database.
    The returned dict has two categories of fields:
      - DB-sourced fields (equipment_name, type, current_site_id, equipment_db_source) — cite as [equipment: N]
      - Provisional/estimated fields (provisional_reference, estimated_arrival_date) — cite as [provisional]
    The proposal_status will be 'pending_approval'. Report this as a PROPOSED action, NOT a completed one.
    """
    return json.dumps(equipment.reallocate_equipment(equipment_id, to_site_id))

@tool
def get_task_dependencies(task_id: str) -> str:
    """Get the downstream project tasks that depend on the given task."""
    return json.dumps(project.get_task_dependencies(task_id))

@tool
def calculate_delay_impact(task_id: str, delayed_days: int) -> str:
    """Calculate the operational and financial impact of delaying a task."""
    return json.dumps(project.calculate_delay_impact(task_id, delayed_days))

@tool
def scan_overdue_tasks(site_id: str) -> str:
    """Proactively scans all active projects at a site to find overdue or delayed tasks. Returns details about each delayed task including dependent task count."""
    return json.dumps(project.scan_overdue_tasks(site_id))

@tool
def get_project_schedule_risk(project_id: str) -> str:
    """Retrieves schedule health metrics for a specific project based on tasks, milestones, and dependencies. Returns counts of overdue tasks, missed milestones, and upcoming tasks."""
    return json.dumps(project.get_project_schedule_risk(project_id))

@tool
def evaluate_vendor_reliability(vendor_id: str) -> str:
    """Evaluate a vendor's historical performance from real PO and delivery data. vendor_id must be a numeric ID from the vendors table."""
    return json.dumps(procurement.evaluate_vendor_reliability(vendor_id))

@tool
def get_market_price_benchmark(material_id: str) -> str:
    """Get the current regional market benchmark price for a material. material_id must be a numeric ID from the materials table — NOT an equipment name."""
    return json.dumps(procurement.get_market_price_benchmark(material_id))

stock_tools = [
    get_transaction_history,
    compare_across_sites,
    get_consumption_rate_history,
    get_pending_requests_and_pos
]

budget_tools = [
    get_budget_actuals,
    get_expense_breakdown_by_category,
    get_po_history,
    get_vendor_price_trend,
    compare_vendor_quotes
]

rag_tool = [search_historical_records]
discovery_tools = [list_sites, list_materials, list_vendors]

WORKER_CONFIG = {
    "stock": {
        "system_prompt": (
            "You are the Stock Agent. Investigate before answering. "
            "Check consumption anomalies and cross-site surplus before recommending a purchase. "
            "Never recommend a PO if one is already pending."
            + NULL_HANDLING_RULE
        ),
        "tools": stock_tools + rag_tool + discovery_tools
    },
    "budget": {
        "system_prompt": (
            "You are the Budget Agent. Find the root cause of budget drift — "
            "vendor price creep, category overspend, or quantity change. "
            "Cite specific numbers from tool responses only."
            + NULL_HANDLING_RULE
        ),
        "tools": budget_tools + rag_tool + discovery_tools
    },
    "equipment": {
        "tools": [
            get_equipment_status,
            find_replacement_equipment,
            reallocate_equipment,
            search_historical_records
        ] + discovery_tools,
        "system_prompt": (
            "You are the Equipment Intelligence Agent. Resolve equipment failures by following this strict sequence:\n"
            "STEP 1: Call get_equipment_status to confirm the equipment's real status and location.\n"
            "STEP 2: Call find_replacement_equipment with the equipment TYPE (e.g. 'Excavator') and the SITE ID to exclude.\n"
            "STEP 3: If replacements are available, call reallocate_equipment for ONE of them to stage a proposal.\n"
            "STEP 4: Write your final report immediately — do NOT loop back to step 1.\n"
            "MAX TOOL CALLS: 4. Stop and report after 4 calls regardless of outcome.\n"
            "\nREPORT FORMAT RULES:\n"
            "- Cite DB-sourced facts as [equipment: N] (e.g. status, site, equipment type).\n"
            "- Cite provisional/estimated values as [provisional] (e.g. the reference number, arrival date).\n"
            "- If a reallocation was proposed, write 'PROPOSED ACTION — awaiting human approval:' before describing it.\n"
            "  Do NOT write 'submitted', 'completed', 'executed', or any past-tense that implies the action already happened.\n"
            "- If no replacement is available, say exactly: 'No idle replacement equipment found — no data available for this.'"
            + NULL_HANDLING_RULE
        )
    },
    "project": {
        "tools": [
            get_task_dependencies,
            calculate_delay_impact,
            scan_overdue_tasks,
            get_project_schedule_risk,
            search_historical_records
        ] + discovery_tools,
        "system_prompt": (
            "You are the Project Intelligence Agent. Your job is to handle task delays, milestones, and schedule risk.\n"
            "When performing a schedule scan or investigating a task delay:\n"
            "STEP 1: Run scan_overdue_tasks for the site, or run get_project_schedule_risk for the project if one is given.\n"
            "STEP 2: For any delayed task, call get_task_dependencies and calculate_delay_impact to assess cascading effects.\n"
            "STEP 3: Gather necessary info with 2-3 tool calls maximum, then generate your explainable report and recommendations.\n"
            "Cite downstream tasks/milestones affected, estimate financial/time impact, and recommend next steps.\n"
            "CRITICAL: Every claim you make MUST cite the source database record using this format: [source_table: record_id] "
            "(e.g. [tasks: 5] or [projects: 2]). You must extract these IDs from the tool responses."
            + NULL_HANDLING_RULE
        )
    },
    "procurement": {
        "tools": [
            compare_vendor_quotes,
            evaluate_vendor_reliability,
            get_market_price_benchmark,
            search_historical_records
        ] + discovery_tools,
        "system_prompt": (
            "You are the Procurement Intelligence Agent. Your job is to optimize purchasing decisions.\n"
            "Compare quotes, evaluate vendor reliability from real delivery history, and check market benchmarks.\n"
            "IMPORTANT: evaluate_vendor_reliability requires a NUMERIC vendor ID (not a name). "
            "get_market_price_benchmark requires a NUMERIC material ID (not an equipment name like 'EXC-01'). "
            "compare_vendor_quotes requires a NUMERIC material request ID.\n"
            "When you have finished, output a final procurement recommendation."
            + NULL_HANDLING_RULE
        )
    }
}
