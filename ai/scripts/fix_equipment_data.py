"""
fix_equipment_data.py
=====================
Fix the Supabase equipment data so that:
  1. EXC-01 is at site_id=5 with status='critical_failure'
  2. EXC-09 at site_id=5 is changed to site_id=1 with status='idle'
     so the replacement-pool query finds it when looking at sites != 5
  3. Adds a third excavator (EXC-02) at site_id=2 with status='idle'
     as an extra backup spare

This gives the equipment_agent a clear, deterministic scenario:
  - find EXC-01 → critical_failure at site 5
  - search replacement pool → EXC-09 (site 1, idle) + EXC-02 (site 2, idle)
  - reallocate one → done in 3 tool calls, no thrashing
"""
import os, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from ai.core.config import supabase

def main():
    print("=== Fixing equipment data ===\n")

    # 1. Set EXC-01 → site_id=5, status=maintenance (simulates critical failure;
    #    DB check constraint only allows: active, idle, maintenance, retired)
    r1 = supabase.table('equipment').update({
        'site_id': 5,
        'status': 'maintenance',
        'hours_used': 1240
    }).eq('name', 'EXC-01').execute()
    print(f"[1] EXC-01 updated: {r1.data}")

    # 2. Move EXC-09 to site_id=1 and set status=idle
    #    (currently at site 5 and active — wrong site for replacement search)
    r2 = supabase.table('equipment').update({
        'site_id': 1,
        'status': 'idle'
    }).eq('name', 'EXC-09').execute()
    print(f"[2] EXC-09 updated: {r2.data}")

    # 3. Add a spare excavator at site_id=2 (idle) only if it doesn't exist
    check = supabase.table('equipment').select('id').eq('name', 'EXC-02').execute()
    if not check.data:
        # Get a valid task_id to satisfy FK if needed (not required here since not allocating)
        r3 = supabase.table('equipment').insert({
            'site_id': 2,
            'name': 'EXC-02',
            'type': 'Excavator',
            'status': 'idle',
            'hours_used': 88
        }).execute()
        print(f"[3] EXC-02 inserted: {r3.data}")
    else:
        print(f"[3] EXC-02 already exists — skipping insert.")

    # Verify final state
    print("\n=== Final equipment table state ===")
    all_eq = supabase.table('equipment').select('id,name,type,status,site_id,hours_used').execute()
    for row in all_eq.data:
        print(f"  id={row['id']} name={row['name']} type={row['type']} status={row['status']} site_id={row['site_id']}")

    print("\nDone.")

if __name__ == '__main__':
    main()
