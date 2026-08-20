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


def _build_payload(scenario: dict, site_id: str, material_id: str) -> str:
    """Fill in {site_id}, {material_id}, {timestamp} placeholders in the template."""
    template = scenario["payload_template"]
    raw = json.dumps(template)
    raw = raw.replace('"{site_id}"', f'"{site_id}"')
    raw = raw.replace('"{material_id}"', f'"{material_id}"')
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

    payload = _build_payload(scenario, site_id, material_id)

    print(f"\n[Scenario] {scenario['icon']} {scenario['label']}", flush=True)
    print(f"[Payload] {payload}\n", flush=True)

    handle_alert(payload, run_id=run_id)


if __name__ == '__main__':
    main()
