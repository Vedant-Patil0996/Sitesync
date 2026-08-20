import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

def get_equipment_status(equipment_id: str) -> Dict[str, Any]:
    """Get the current operational status of a piece of equipment."""
    # Mocked for hackathon demo
    return {
        "equipment_id": equipment_id,
        "type": "Excavator",
        "status": "critical_failure",
        "last_maintenance": "2026-02-15",
        "estimated_repair_time_days": 5
    }

def find_replacement_equipment(equipment_type: str, exclude_site_id: str) -> List[Dict[str, Any]]:
    """Find available equipment of a specific type at other sites."""
    # Mocked for hackathon demo
    return [
        {
            "equipment_id": "EXC-09",
            "site_id": "6",
            "site_name": "Riverside Complex",
            "status": "idle",
            "utilization_percent": 30
        }
    ]

def reallocate_equipment(equipment_id: str, to_site_id: str) -> Dict[str, Any]:
    """Submit a request to move equipment to a new site."""
    return {
        "success": True,
        "transfer_id": f"TRF-{equipment_id}-{to_site_id}",
        "estimated_arrival": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    }
