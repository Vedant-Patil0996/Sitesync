import os
import sys
import json

# Ensure stdout uses UTF-8 to prevent UnicodeEncodeError in Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

# Ensure ai package is importable from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# IMPORT SENTENCE_TRANSFORMERS FIRST TO PREVENT WINDOWS DLL CRASH WITH SUPABASE
import sentence_transformers

from ai.core.config import supabase
from ai.agent.orchestrator import handle_alert

def main():
    print("Starting script...", flush=True)
    print("Fetching a valid material and site from Supabase for testing...", flush=True)
    
    # Grab any inventory record
    inv_resp = supabase.table('inventory').select('site_id, material_id').limit(1).execute()
    
    if not inv_resp.data:
        print("No inventory records found in Supabase. Run generate_mock_data.py first.")
        return
        
    site_id = str(inv_resp.data[0]['site_id'])
    material_id = str(inv_resp.data[0]['material_id'])
    
    # Scenario 7: The "Cascading Emergency" (3+ Agents Triggered)
    # Simulating a webhook from Supabase: An excavator broke down.
    raw_log = {
        "log_type": "equipment_status",
        "site_id": site_id,
        "equipment_id": "EXC-01",
        "status": "critical_failure",
        "timestamp": "2026-08-20T08:00:00Z"
    }
    
    # We pass the raw JSON to the orchestrator.
    alert_payload = json.dumps(raw_log)
    
    print("\nTriggering AI Agent with Raw Webhook Log (Cascading Emergency):")
    print(f'{alert_payload}\n')
    
    result = handle_alert(alert_payload)
    
    print("\nFinal Agent Findings & Recommendations:")
    with open('agent_output.md', 'w', encoding='utf-8') as f:
        f.write(result)
    print("Wrote output to agent_output.md")

if __name__ == '__main__':
    main()
