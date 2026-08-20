"""
Simulation scenarios for the AI multi-agent system.
Each scenario is a JSON webhook payload that the agent interprets.
"""

SCENARIOS = [
    {
        "id": "equipment_critical_failure",
        "label": "Equipment Critical Failure",
        "description": "An excavator reports critical failure mid-operation. Triggers Equipment Agent + Procurement Agent.",
        "severity": "critical",
        "icon": "🔴",
        "tags": ["equipment", "safety"],
        "payload_template": {
            "log_type": "equipment_status",
            "site_id": "{site_id}",
            "equipment_id": "EXC-01",
            "status": "critical_failure",
            "timestamp": "{timestamp}"
        }
    },
    {
        "id": "stock_critically_low",
        "label": "Critical Stock Shortage",
        "description": "Cement stock drops below 10% of minimum threshold at an active site. Triggers Stock Agent + Procurement Agent.",
        "severity": "critical",
        "icon": "📦",
        "tags": ["inventory", "procurement"],
        "payload_template": {
            "log_type": "inventory_alert",
            "site_id": "{site_id}",
            "material_id": "{material_id}",
            "current_quantity": 12,
            "min_threshold": 150,
            "unit": "bags",
            "timestamp": "{timestamp}"
        }
    },
    {
        "id": "budget_overrun",
        "label": "Budget Overrun Detected",
        "description": "Site expenses exceed 95% of monthly budget with 12 days remaining. Triggers Budget Agent + Procurement Agent.",
        "severity": "warning",
        "icon": "💸",
        "tags": ["finance", "budget"],
        "payload_template": {
            "log_type": "budget_alert",
            "site_id": "{site_id}",
            "allocated_budget": 500000,
            "spent_to_date": 478000,
            "days_remaining_in_period": 12,
            "timestamp": "{timestamp}"
        }
    },
    {
        "id": "task_delay_cascade",
        "label": "Task Delay Cascade",
        "description": "Foundation work delayed by 5 days due to weather, cascading to 3 dependent tasks. Triggers Project Agent + Budget Agent.",
        "severity": "warning",
        "icon": "📅",
        "tags": ["project", "schedule"],
        "payload_template": {
            "log_type": "task_delay",
            "site_id": "{site_id}",
            "task_id": "1",
            "delay_days": 5,
            "cause": "adverse_weather",
            "timestamp": "{timestamp}"
        }
    },
    {
        "id": "vendor_price_spike",
        "label": "Vendor Price Spike",
        "description": "Steel reinforcement price spiked 35% above market benchmark from primary vendor. Triggers Procurement Agent + Budget Agent.",
        "severity": "warning",
        "icon": "📈",
        "tags": ["procurement", "vendor"],
        "payload_template": {
            "log_type": "price_anomaly",
            "site_id": "{site_id}",
            "material_id": "{material_id}",
            "vendor_price": 8500,
            "market_benchmark": 6300,
            "deviation_percent": 34.9,
            "timestamp": "{timestamp}"
        }
    },
    {
        "id": "multi_site_cascade",
        "label": "Multi-Site Emergency Cascade",
        "description": "Simultaneous equipment failure + stock shortage at same site. Triggers Equipment + Stock + Budget + Procurement agents.",
        "severity": "critical",
        "icon": "🚨",
        "tags": ["equipment", "inventory", "finance", "multi-agent"],
        "payload_template": {
            "log_type": "cascading_emergency",
            "site_id": "{site_id}",
            "events": [
                {"type": "equipment_failure", "equipment_id": "CRN-01", "status": "critical_failure"},
                {"type": "stock_critical", "material_id": "{material_id}", "quantity_remaining": 5}
            ],
            "timestamp": "{timestamp}"
        }
    },
    {
        "id": "safety_violation",
        "label": "Safety Compliance Violation",
        "description": "Safety inspection flagged 3 violations at active site. Equipment without valid inspection certificates operating. Triggers Project + Equipment agents.",
        "severity": "critical",
        "icon": "⚠️",
        "tags": ["safety", "compliance"],
        "payload_template": {
            "log_type": "safety_violation",
            "site_id": "{site_id}",
            "violation_count": 3,
            "equipment_ids": ["EXC-02", "CRN-01"],
            "violation_types": ["missing_inspection_cert", "operator_license_expired"],
            "timestamp": "{timestamp}"
        }
    },
]
