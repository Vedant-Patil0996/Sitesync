import os
import sys
import json

# Ensure stdout uses UTF-8 to prevent UnicodeEncodeError in Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

# Ensure ai package is importable from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# IMPORT SENTENCE_TRANSFORMERS FIRST TO PREVENT WINDOWS DLL CRASH WITH SUPABASE
os.environ['HF_HUB_DISABLE_PROGRESS_BAR'] = '1'
import sentence_transformers  # noqa: F401

from ai.core.config import supabase
from ai.agent.orchestrator import handle_alert

def main():
    # run_id is injected by FastAPI via environment variable
    run_id = os.environ.get("AI_RUN_ID", "")

    print(f"Starting AI agent (run_id={run_id})...", flush=True)

    # Grab any inventory record to get valid site/material ids
    inv_resp = supabase.table('inventory').select('site_id, material_id').limit(1).execute()

    if not inv_resp.data:
        print("No inventory records found in Supabase. Run generate_mock_data.py first.", flush=True)
        return

    site_id = str(inv_resp.data[0]['site_id'])

    # Scenario: Equipment critical failure
    raw_log = {
        "log_type": "equipment_status",
        "site_id": site_id,
        "equipment_id": "EXC-01",
        "status": "critical_failure",
        "timestamp": "2026-08-20T08:00:00Z"
    }

    alert_payload = json.dumps(raw_log)

    result = handle_alert(alert_payload, run_id=run_id)

    print(f"Wrote output to agent_output.md", flush=True)


if __name__ == '__main__':
    main()
