import os
import sys
import json

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
        print("No inventory data found. Run seed_embeddings.py first.")
        return
        
    site_id = inv_resp.data[0]['site_id']
    material_id = inv_resp.data[0]['material_id']
    
    alert = {
        "id": "alert_mock_123",
        "type": "stock_low",
        "site_id": str(site_id),
        "material_id": str(material_id),
        "current_stock": 50,
        "reorder_level": 100,
        "message": "Stock has fallen below reorder level."
    }
    
    print(f"\nTriggering AI Agent with Alert:\n{json.dumps(alert, indent=2)}\n", flush=True)
    print("=" * 60, flush=True)
    print("AGENT INVESTIGATION STARTED (Calling Groq API...)", flush=True)
    print("=" * 60, flush=True)
    
    try:
        result = handle_alert(alert)
        print("HANDLE_ALERT returned!", flush=True)
    except Exception as e:
        print(f"Error in handle_alert: {e}", flush=True)
        return
    
    print("\n" + "=" * 60)
    print("AGENT INVESTIGATION COMPLETE")
    print("=" * 60)
    
    print("\nFinal Agent Findings & Recommendations:")
    if 'stock' in result['results']:
        with open('agent_output.md', 'w', encoding='utf-8') as f:
            f.write(result['results']['stock'])
        print("Wrote output to agent_output.md")
    else:
        with open('agent_output.md', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print("Wrote output to agent_output.md")

if __name__ == '__main__':
    main()
