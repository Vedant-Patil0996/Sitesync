"""
diagnose_agents.py
==================
Four-point diagnosis:
  1. Direct Supabase queries for site_id=5 / EXC-01 (no agent involved).
  2. Verbose per-call trace of equipment_agent and procurement_agent tools.
  3. Reproduce the procurement input error with exact args.
  4. Audit system prompts for null/empty-data handling instructions.
"""
import os, sys, json, time, traceback
os.environ['HF_HUB_DISABLE_PROGRESS_BAR'] = '1'
os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = '1'

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── 1. Direct Supabase Queries ──────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 1 --- DIRECT SUPABASE QUERIES (no agent)")
print("="*60)

from ai.core.config import supabase

# 1a. equipment table -- look for EXC-01 by name
print("\n[equipment] Rows where name = 'EXC-01':")
r = supabase.table('equipment').select('*').eq('name', 'EXC-01').execute()
print(f"  Count: {len(r.data)}")
for row in r.data:
    print(f"  {json.dumps(row, indent=4)}")
if not r.data:
    print("  ZERO ROWS found for name='EXC-01'")

# 1b. equipment table -- look for any rows at site_id=5
print("\n[equipment] Rows where site_id = 5:")
r2 = supabase.table('equipment').select('*').eq('site_id', 5).execute()
print(f"  Count: {len(r2.data)}")
for row in r2.data:
    print(f"  id={row['id']} name={row.get('name')} type={row.get('type')} status={row.get('status')} site_id={row.get('site_id')}")
if not r2.data:
    print("  ZERO ROWS at site_id=5")

# 1c. equipment table -- all rows (cap at 20)
print("\n[equipment] ALL rows (first 20):")
r3 = supabase.table('equipment').select('id,name,type,status,site_id,hours_used').limit(20).execute()
print(f"  Total fetched: {len(r3.data)}")
for row in r3.data:
    print(f"  id={row['id']} name={row.get('name')} type={row.get('type')} status={row.get('status')} site_id={row.get('site_id')}")

# 1d. idle equipment at other sites (what find_replacement_equipment would see)
print("\n[equipment] Idle excavators at any site != 5 (replacement pool):")
r4 = supabase.table('equipment').select('id,name,type,status,site_id').eq('type', 'excavator').eq('status', 'idle').neq('site_id', 5).execute()
print(f"  Count: {len(r4.data)}")
for row in r4.data:
    print(f"  {row}")
if not r4.data:
    print("  ZERO idle excavators at other sites")

# 1e. vendors table (if exists)
print("\n[vendors] First 10 rows (procurement reference):")
try:
    rv = supabase.table('vendors').select('id,name,category').limit(10).execute()
    print(f"  Count: {len(rv.data)}")
    for row in rv.data:
        print(f"  {row}")
    if not rv.data:
        print("  ZERO vendor rows")
except Exception as e:
    print(f"  Table query failed: {e}")

# 1f. purchase_orders table
print("\n[purchase_orders] Recent POs (first 10):")
try:
    rp = supabase.table('purchase_orders').select('id,vendor_id,status,total_amount').limit(10).execute()
    print(f"  Count: {len(rp.data)}")
    for row in rp.data:
        print(f"  {row}")
    if not rp.data:
        print("  ZERO purchase orders")
except Exception as e:
    print(f"  Table query failed: {e}")

# ── 2. Verbose tool-call wrappers ────────────────────────────────────────────
print("\n" + "="*60)
print("STEP 2 --- VERBOSE TOOL CALL TRACE (equipment + procurement)")
print("="*60)

from ai.tools import equipment as eq_tools, procurement as proc_tools

def traced_call(label, fn, *args, **kwargs):
    sig = f"args={args} kwargs={kwargs}"
    print(f"\n  CALL  [{label}] {sig}")
    try:
        result = fn(*args, **kwargs)
        print(f"  RETURN [{label}] {json.dumps(result, default=str)[:600]}")
        return result
    except Exception as exc:
        print(f"  EXCEPTION [{label}]: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return {"error": str(exc)}

print("\n-- Equipment agent calls --")
traced_call("get_equipment_status", eq_tools.get_equipment_status, "EXC-01")
traced_call("find_replacement_equipment", eq_tools.find_replacement_equipment, "excavator", "5")
traced_call("reallocate_equipment", eq_tools.reallocate_equipment, "EXC-01", "5")

print("\n-- Procurement agent calls --")
traced_call("evaluate_vendor_reliability", proc_tools.evaluate_vendor_reliability, "vendor_001")
traced_call("get_market_price_benchmark", proc_tools.get_market_price_benchmark, "EXC-01")

# ── 3. Procurement "input error" -- exact exception ────────────────────────
print("\n" + "="*60)
print("STEP 3 --- PROCUREMENT compare_vendor_quotes INPUT ERROR")
print("="*60)
from ai.tools import budget as budget_tools

test_request_ids = ["EXC-01", "", "1", None]
for rid in test_request_ids:
    print(f"\n  compare_vendor_quotes(request_id={rid!r})")
    try:
        result = budget_tools.compare_vendor_quotes(rid)
        print(f"  <- {json.dumps(result, default=str)[:300]}")
    except Exception as e:
        print(f"  EXCEPTION: {type(e).__name__}: {e}")

# ── 4. System prompt audit for null-data instructions ────────────────────────
print("\n" + "="*60)
print("STEP 4 --- SYSTEM PROMPT AUDIT (null/empty-data handling)")
print("="*60)

from ai.agent.config import WORKER_CONFIG

null_keywords = ["null", "no data", "not available", "empty", "estimate", "fabricat", "hallucin", "do not guess", "if no data"]

for agent_name, cfg in WORKER_CONFIG.items():
    sp = cfg.get("system_prompt", "")
    print(f"\n  [{agent_name}] prompt length={len(sp)} chars")
    found = []
    for kw in null_keywords:
        if kw.lower() in sp.lower():
            found.append(kw)
    if found:
        print(f"    CONTAINS null-handling keywords: {found}")
    else:
        print(f"    MISSING null-handling instruction -- model may hallucinate when tools return empty")
    print(f"    Prompt snippet: {sp[:200]!r}")

print("\n" + "="*60)
print("DIAGNOSIS COMPLETE")
print("="*60)
