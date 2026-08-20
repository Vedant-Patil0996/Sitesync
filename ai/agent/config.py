import json
from langchain_core.tools import tool
from typing import Optional
from ai.tools import stock, budget, rag, equipment, project, procurement

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
    """Compare multiple vendor quotes for a specific material request (based on price and terms)."""
    return json.dumps(budget.compare_vendor_quotes(request_id))

@tool
def get_equipment_status(equipment_id: str) -> str:
    """Get the current operational status of a piece of equipment."""
    return json.dumps(equipment.get_equipment_status(equipment_id))

@tool
def find_replacement_equipment(equipment_type: str, exclude_site_id: str) -> str:
    """Find available equipment of a specific type at other sites."""
    return json.dumps(equipment.find_replacement_equipment(equipment_type, exclude_site_id))

@tool
def reallocate_equipment(equipment_id: str, to_site_id: str) -> str:
    """Submit a request to move equipment to a new site."""
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
def evaluate_vendor_reliability(vendor_id: str) -> str:
    """Evaluate a vendor's historical performance, delivery times, and quality issues."""
    return json.dumps(procurement.evaluate_vendor_reliability(vendor_id))

@tool
def get_market_price_benchmark(material_id: str) -> str:
    """Get the current regional market benchmark price for a material."""
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

WORKER_CONFIG = {
    "stock": {
        "system_prompt": "You are the Stock Agent. Investigate before answering. Check consumption anomalies and cross-site surplus before recommending a purchase. Never recommend a PO if one is already pending.",
        "tools": stock_tools + rag_tool
    },
    "budget": {
        "system_prompt": "You are the Budget Agent. Find the root cause of budget drift — vendor price creep, category overspend, or quantity change. Cite specific numbers.",
        "tools": budget_tools + rag_tool
    },
    "equipment": {
        "tools": [
            get_equipment_status,
            find_replacement_equipment,
            reallocate_equipment,
            search_historical_records
        ],
        "system_prompt": (
            "You are the Equipment Intelligence Agent. Your job is to resolve equipment failures or idleness.\n"
            "Investigate the status, find replacements across sites if necessary, and recommend reallocation.\n"
            "Always explain the operational impact. When you have finished, output a final report with recommended next steps."
        )
    },
    "project": {
        "tools": [
            get_task_dependencies,
            calculate_delay_impact,
            search_historical_records
        ],
        "system_prompt": (
            "You are the Project Intelligence Agent. Your job is to handle task delays and operational roadblocks.\n"
            "Identify downstream task dependencies, calculate the cost of delay, and recommend corrective scheduling actions.\n"
            "Always provide a comprehensive impact analysis. When you have finished, output a final report with recommended next steps."
        )
    },
    "procurement": {
        "tools": [
            compare_vendor_quotes,
            evaluate_vendor_reliability,
            get_market_price_benchmark,
            search_historical_records
        ],
        "system_prompt": (
            "You are the Procurement Intelligence Agent. Your job is to optimize purchasing.\n"
            "Compare quotes, evaluate vendor reliability, check market benchmarks, and explain why the cheapest isn't always the best.\n"
            "When you have finished, output a final report with a recommended purchase or transfer."
        )
    }
}
