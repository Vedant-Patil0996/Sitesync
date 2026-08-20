import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from ai.core.config import supabase

# DB check constraint only allows: active, idle, maintenance, retired
# 'maintenance' is what we set when equipment has a critical failure.
CRITICAL_STATUSES = {'maintenance'}

def get_equipment_status(equipment_id: str) -> Dict[str, Any]:
    """Get the current operational status of a piece of equipment."""
    try:
        resp = supabase.table('equipment').select('*').eq('name', equipment_id).limit(1).execute()
        if not resp.data:
            return {"error": f"Equipment '{equipment_id}' not found in database. Cannot confirm status.", "source": "equipment table"}
        
        eq = resp.data[0]
        is_critical = eq['status'] in CRITICAL_STATUSES
        return {
            "id": eq['id'],
            "equipment_id": eq['name'],
            "type": eq['type'],
            "status": eq['status'],
            "is_critical_failure": is_critical,
            "site_id": eq['site_id'],
            "hours_used": eq['hours_used'],
            "estimated_repair_time_days": 5 if is_critical else 0,
            "source": f"[equipment: {eq['id']}]"
        }
    except Exception as e:
        return {"error": str(e)}

def find_replacement_equipment(equipment_type: str, exclude_site_id: str) -> List[Dict[str, Any]]:
    """Find available idle equipment of a specific type at other sites."""
    try:
        # Use ilike for case-insensitive type matching (LLM may pass 'excavator' or 'Excavator')
        resp = supabase.table('equipment').select(
            'id, name, type, status, site_id, hours_used'
        ).ilike('type', equipment_type).eq('status', 'idle').neq('site_id', exclude_site_id).execute()
        
        if not resp.data:
            return [{"result": "no_idle_equipment_found", "equipment_type": equipment_type, "searched_sites": "all except site " + str(exclude_site_id)}]
        
        results = []
        for eq in resp.data:
            results.append({
                "id": eq['id'],
                "equipment_id": eq['name'],
                "site_id": eq['site_id'],
                "type": eq['type'],
                "status": eq['status'],
                "hours_used": eq['hours_used'],
                "source": f"[equipment: {eq['id']}]"
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]

def reallocate_equipment(equipment_id: str, to_site_id: str) -> Dict[str, Any]:
    """
    Stage a reallocation PROPOSAL for idle equipment — does NOT write to the database.
    Returns a structured proposal that requires explicit human approval before execution.
    DB-sourced facts are tagged [equipment: id]; computed estimates are tagged [provisional].
    """
    try:
        # Verify the equipment exists and is idle (DB read — sourced)
        check = supabase.table('equipment').select('id, name, type, status, site_id').eq('name', equipment_id).limit(1).execute()
        if not check.data:
            return {"error": f"Equipment '{equipment_id}' not found. Cannot propose reallocation.", "source": "equipment table"}

        eq = check.data[0]
        if eq['status'] not in ('idle',):
            return {
                "proposal_status": "rejected",
                "reason": f"Equipment '{equipment_id}' has status '{eq['status']}' — only idle equipment can be reallocated.",
                "equipment_db_source": f"[equipment: {eq['id']}]"  # DB-sourced
            }

        # NOTE: NO database write here. This is a proposal only.
        provisional_ref = f"PROP-{equipment_id}-SITE{to_site_id}"  # provisional, not a DB record
        provisional_arrival = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")  # estimate, not DB

        return {
            "proposal_status": "pending_approval",
            "approval_required": True,
            # ── DB-sourced facts ─────────────────────────────────────────
            "equipment_name": eq['name'],          # [equipment: eq['id']]
            "equipment_type": eq['type'],           # [equipment: eq['id']]
            "current_site_id": eq['site_id'],       # [equipment: eq['id']]
            "equipment_db_source": f"[equipment: {eq['id']}]",
            # ── Proposed action (not yet executed) ───────────────────────
            "proposed_destination_site_id": to_site_id,
            # ── System-generated estimates (NOT DB-sourced) ──────────────
            "provisional_reference": provisional_ref,          # [provisional - system generated]
            "estimated_arrival_date": provisional_arrival,     # [provisional - 1-day estimate, not logistics data]
            "note": "NO database change has been made. This proposal requires human approval before execution."
        }
    except Exception as e:
        return {"error": str(e)}
