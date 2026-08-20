import json
from typing import Dict, Any, List
from ai.core.config import supabase

def get_task_dependencies(task_id: str) -> List[Dict[str, Any]]:
    """Get the downstream project tasks that depend on the given task."""
    try:
        # Assuming task_id is passed as a string but is an int in DB
        task_id_int = int(task_id) if str(task_id).isdigit() else None
        if not task_id_int:
            # Fallback if the agent tries to use the name or a fake ID
            resp = supabase.table('tasks').select('*').eq('name', task_id).limit(1).execute()
            if not resp.data:
                 return []
            task_id_int = resp.data[0]['id']

        resp = supabase.table('tasks').select('*').eq('depends_on_task_id', task_id_int).execute()
        results = []
        for t in resp.data:
            results.append({
                "id": t['id'],
                "task_id": t['id'],
                "name": t['name'],
                "original_start_date": t['start_date'],
                "slack_days": 1 # Hardcoded slack for demo logic
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]

def calculate_delay_impact(task_id: str, delayed_days: int) -> Dict[str, Any]:
    """Calculate the operational and financial impact of delaying a task."""
    try:
        task_id_int = int(task_id) if str(task_id).isdigit() else None
        if not task_id_int:
            resp = supabase.table('tasks').select('*').eq('name', task_id).limit(1).execute()
            if not resp.data:
                 return {"error": "Task not found"}
            task_id_int = resp.data[0]['id']

        deps = get_task_dependencies(str(task_id_int))
        
        slack = 1
        net_delay = max(0, delayed_days - slack)
        
        return {
            "task_id": task_id_int,
            "days_delayed": delayed_days,
            "critical_path_impact": net_delay > 0,
            "downstream_tasks_affected": [d['name'] for d in deps] if net_delay > 0 else [],
            "estimated_cost_of_delay": net_delay * 5000  # $5k per day penalty
        }
    except Exception as e:
        return {"error": str(e)}
