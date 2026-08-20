import json
from typing import Dict, Any, List

def get_task_dependencies(task_id: str) -> List[Dict[str, Any]]:
    """Get the downstream project tasks that depend on the given task."""
    # Mocked for hackathon demo
    if "EXC" in task_id or "FND" in task_id:
        return [
            {
                "task_id": "FRM-01",
                "name": "Steel Framing & Concrete Pour",
                "original_start_date": "2026-08-25",
                "slack_days": 1
            }
        ]
    return []

def calculate_delay_impact(task_id: str, delayed_days: int) -> Dict[str, Any]:
    """Calculate the operational and financial impact of delaying a task."""
    # Mocked for hackathon demo
    slack = 1
    net_delay = max(0, delayed_days - slack)
    
    return {
        "task_id": task_id,
        "days_delayed": delayed_days,
        "critical_path_impact": net_delay > 0,
        "downstream_tasks_affected": ["FRM-01"] if net_delay > 0 else [],
        "estimated_cost_of_delay": net_delay * 5000  # $5k per day penalty
    }
