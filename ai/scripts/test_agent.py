import os
import sys
import json
from datetime import datetime, timezone

# Ensure stdout uses UTF-8 to prevent UnicodeEncodeError in Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

# Ensure ai package is importable from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# IMPORT SENTENCE_TRANSFORMERS FIRST TO PREVENT WINDOWS DLL CRASH WITH SUPABASE
os.environ['HF_HUB_DISABLE_PROGRESS_BAR'] = '1'
import sentence_transformers  # noqa: F401

from ai.core.config import supabase
from ai.agent.orchestrator import handle_alert
from ai.agent.scenarios import SCENARIOS


def _build_payload(scenario: dict, site_id: str, material_id: str, equipment_id: str, task_id: str) -> str:
    """Fill in {site_id}, {material_id}, {equipment_id}, {task_id}, {timestamp} placeholders in the template."""
    template = scenario["payload_template"]
    raw = json.dumps(template)
    raw = raw.replace('"{site_id}"', f'"{site_id}"')
    raw = raw.replace('"{material_id}"', f'"{material_id}"')
    raw = raw.replace('"{equipment_id}"', f'"{equipment_id}"')
    raw = raw.replace('"{task_id}"', f'"{task_id}"')
    raw = raw.replace('"{timestamp}"', f'"{datetime.now(timezone.utc).isoformat()}"')
    return raw


def main():
    run_id = os.environ.get("AI_RUN_ID", "")
    scenario_id = os.environ.get("AI_SCENARIO_ID", "equipment_critical_failure")
    env_site_id = os.environ.get("AI_SITE_ID", "")
    env_material_id = os.environ.get("AI_MATERIAL_ID", "")

    # Find requested scenario (fall back to first if unknown)
    scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), SCENARIOS[0])

    print(f"Starting AI agent (run_id={run_id}, scenario={scenario_id})...", flush=True)

    # Always fetch fresh site/material from DB for realistic data
    inv_resp = supabase.table('inventory').select('site_id, material_id').limit(1).execute()

    if not inv_resp.data:
        print("No inventory records found. Run generate_mock_data.py first.", flush=True)
        return

    site_id = env_site_id or str(inv_resp.data[0]['site_id'])
    material_id = env_material_id or str(inv_resp.data[0]['material_id'])

    # Dynamically fetch an equipment and task for the site so queries succeed
    eq_resp = supabase.table('equipment').select('id').eq('site_id', int(site_id)).limit(1).execute()
    equipment_id = str(eq_resp.data[0]['id']) if eq_resp.data else "1"

    proj_resp = supabase.table('projects').select('id').eq('site_id', int(site_id)).limit(1).execute()
    if proj_resp.data:
        task_resp = supabase.table('tasks').select('id').eq('project_id', int(proj_resp.data[0]['id'])).limit(1).execute()
        task_id = str(task_resp.data[0]['id']) if task_resp.data else "123"
    else:
        task_id = "123"

    payload = _build_payload(scenario, site_id, material_id, equipment_id, task_id)

    print(f"\n[Scenario] {scenario['icon']} {scenario['label']}", flush=True)
    print(f"[Payload] {payload}\n", flush=True)

    handle_alert(payload, run_id=run_id)


if __name__ == '__main__':
    main()
