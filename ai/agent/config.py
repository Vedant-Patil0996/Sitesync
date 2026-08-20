from ai.tools import stock, budget, rag

TOOL_FUNCTIONS = {
    'get_transaction_history': stock.get_transaction_history,
    'compare_across_sites': stock.compare_across_sites,
    'get_consumption_rate_history': stock.get_consumption_rate_history,
    'get_pending_requests_and_pos': stock.get_pending_requests_and_pos,
    'get_budget_actuals': budget.get_budget_actuals,
    'get_expense_breakdown_by_category': budget.get_expense_breakdown_by_category,
    'get_po_history': budget.get_po_history,
    'get_vendor_price_trend': budget.get_vendor_price_trend,
    'compare_vendor_quotes': budget.compare_vendor_quotes,
    'search_historical_records': rag.search_historical_records,
}

rag_tool = {
    "type": "function",
    "function": {
        "name": "search_historical_records",
        "description": "Semantic search over historical inventory transactions, material requests, purchase orders, vendor/procurement records, and expenses — including operational/site context captured in transaction references and request justifications. Use to find relevant history before explaining an issue.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "company_id": {"type": ["string", "null"], "description": "Optional, filter by company"},
                "site_id": {"type": ["string", "null"]},
                "source_table": {"type": ["string", "null"], "description": "inventory_transactions, material_requests, purchase_orders, expenses"},
                "vendor_id": {"type": ["string", "null"], "description": "Optional, filter to a specific vendor's procurement history"}
            },
            "required": ["query"]
        }
    }
}

stock_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_transaction_history",
            "description": "Recent stock in/out/transfer records for a material at a site.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_id": {"type": "string"},
                    "site_id": {"type": "string"},
                    "days": {"type": "integer", "default": 14},
                    "type": {"type": "string", "enum": ["IN", "OUT", "TRANSFER_IN", "TRANSFER_OUT"]}
                },
                "required": ["material_id", "site_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_across_sites",
            "description": "Stock of a material at other sites, flagged for surplus against max_capacity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_id": {"type": "string"},
                    "exclude_site_id": {"type": "string"}
                },
                "required": ["material_id", "exclude_site_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_consumption_rate_history",
            "description": "Baseline vs recent consumption rate, anomaly flag, per-contractor breakdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_id": {"type": "string"},
                    "site_id": {"type": "string"},
                    "days": {"type": "integer", "default": 90}
                },
                "required": ["material_id", "site_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pending_requests_and_pos",
            "description": "Check for an in-progress request/PO before recommending a new one.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_id": {"type": "string"},
                    "site_id": {"type": "string"}
                },
                "required": ["material_id", "site_id"]
            }
        }
    }
]

budget_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_budget_actuals",
            "description": "Allocated, spent, remaining, utilization percent for a site.",
            "parameters": {
                "type": "object",
                "properties": {
                    "site_id": {"type": "string"}
                },
                "required": ["site_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expense_breakdown_by_category",
            "description": "Spend by category with percentages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "site_id": {"type": "string"},
                    "days": {"type": "integer", "default": 30}
                },
                "required": ["site_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_po_history",
            "description": "PO history with unit prices, vendors, delivery status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "site_id": {"type": "string"},
                    "days": {"type": "integer", "default": 60}
                },
                "required": ["site_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_vendor_price_trend",
            "description": "Vendor price trend for a material over time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_id": {"type": "string"},
                    "vendor_id": {"type": "string"}
                },
                "required": ["material_id", "vendor_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_vendor_quotes",
            "description": "Compare quotes for a request — price, rating, delivery days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"}
                },
                "required": ["request_id"]
            }
        }
    }
]

WORKER_CONFIG = {
    "stock": {
        "system_prompt": "You are the Stock Agent. Investigate before answering. Check consumption anomalies and cross-site surplus before recommending a purchase. Never recommend a PO if one is already pending.",
        "tools": stock_tools + [rag_tool]
    },
    "budget": {
        "system_prompt": "You are the Budget Agent. Find the root cause of budget drift — vendor price creep, category overspend, or quantity change. Cite specific numbers.",
        "tools": budget_tools + [rag_tool]
    }
}
