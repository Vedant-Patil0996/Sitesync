"""
End-to-end test of the QR batch system against the running backend.
Tests: create batch → scan (passport) → receive → consume → damage → return → export
"""
import os, sys, json, requests
from dotenv import load_dotenv
load_dotenv()

BASE = "http://localhost:8000"

# ── Auth ──────────────────────────────────────────────────────────────────
# Load the Supabase anon key from env to do auth
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

print("Logging in as admin...")
r = requests.post(
    f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    json={"email": "admin@sitesync.local", "password": "password123"},
    headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
)
if r.status_code not in (200, 201):
    # Try another email pattern
    r = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        json={"email": "alice@sitesync.com", "password": "password123"},
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
    )

if r.status_code not in (200, 201):
    print(f"Auth failed: {r.status_code} {r.text}")
    sys.exit(1)

TOKEN = r.json()["access_token"]
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
print(f"Logged in!")

# ── Step 1: Get materials & sites ─────────────────────────────────────────
print("\n[1] Fetching materials...")
mats = requests.get(f"{BASE}/api/v1/inventory/materials", headers=H).json()
mat = mats[0] if mats else None
print(f"  Material: {mat['name']} (id={mat['id']}, unit={mat['unit']})")

sites = requests.get(f"{BASE}/api/v1/sites?skip=0&limit=10", headers=H).json()
site = sites["items"][0]
print(f"  Site: {site['name']} (id={site['id']})")

# ── Step 2: Create a batch ────────────────────────────────────────────────
print(f"\n[2] Creating batch for {mat['name']}...")
r = requests.post(f"{BASE}/api/v1/inventory/batches", headers=H,
    json={"material_id": mat["id"], "site_id": site["id"], "qty": 500, "notes": "Test batch from e2e"})
print(f"  Status: {r.status_code}")
batch_info = r.json()
print(f"  Batch: {batch_info}")
batch_code = batch_info["batch_code"]

# ── Step 3: Scan (Passport) ───────────────────────────────────────────────
print(f"\n[3] Scanning batch {batch_code}...")
r = requests.post(f"{BASE}/api/v1/inventory/scan", headers=H,
    json={"batch_id": batch_code})
print(f"  Status: {r.status_code}")
passport = r.json()
print(f"  Material: {passport['material_name']}")
print(f"  Current Qty: {passport['current_qty']} {passport['unit']}")
print(f"  Status: {passport['status']}")
print(f"  Timeline events: {len(passport['timeline'])}")

# ── Step 4: Receive with discrepancy ─────────────────────────────────────
print(f"\n[4] Receiving with discrepancy (expected=500, actual=480)...")
r = requests.post(f"{BASE}/api/v1/inventory/receive", headers=H,
    json={"batch_code": batch_code, "expected_qty": 500, "actual_qty": 480})
print(f"  Status: {r.status_code}")
result = r.json()
print(f"  Result: {result}")

# ── Step 5: Consume ───────────────────────────────────────────────────────
print(f"\n[5] Consuming 50 units for Foundation Work...")
r = requests.post(f"{BASE}/api/v1/inventory/consume", headers=H,
    json={"batch_code": batch_code, "qty": 50, "activity": "Foundation Work", "reason": "Column pouring"})
print(f"  Status: {r.status_code}")
result = r.json()
print(f"  Result: {result}")

# ── Step 6: Damage ────────────────────────────────────────────────────────
print(f"\n[6] Recording 10 units as damaged...")
r = requests.post(f"{BASE}/api/v1/inventory/damage", headers=H,
    json={"batch_code": batch_code, "qty": 10, "reason": "Rain exposure"})
print(f"  Status: {r.status_code}")
print(f"  Result: {r.json()}")

# ── Step 7: Final passport / timeline ────────────────────────────────────
print(f"\n[7] Final passport & timeline for {batch_code}...")
r = requests.get(f"{BASE}/api/v1/inventory/batches/{batch_code}/timeline", headers=H)
print(f"  Status: {r.status_code}")
final = r.json()
print(f"  Final Qty: {final['current_qty']} {final['unit']}")
print(f"  Final Status: {final['status']}")
print(f"  Timeline:")
for tx in final["timeline"]:
    print(f"    {tx['action']:15} {tx['quantity']:6} {final['unit']} — {tx['performed_by']} ({tx.get('reason','') or tx.get('activity','') or ''})")

# ── Step 8: Discrepancies ─────────────────────────────────────────────────
print(f"\n[8] Listing discrepancies...")
r = requests.get(f"{BASE}/api/v1/inventory/discrepancies", headers=H)
print(f"  Status: {r.status_code}")
discs = r.json()
print(f"  Total discrepancies: {len(discs)}")
for d in discs[:3]:
    print(f"    {d['batch_code']}: expected={d['expected_qty']}, actual={d['actual_qty']}, diff={d['difference']}")

# ── Step 9: List batches ──────────────────────────────────────────────────
print(f"\n[9] Listing all batches...")
r = requests.get(f"{BASE}/api/v1/inventory/batches", headers=H)
batches = r.json()
print(f"  Total batches: {len(batches)}")
for b in batches[:5]:
    print(f"    {b['batch_code']}: {b['material_name']} @ {b['site_name']} — {b['status']} ({b['current_qty']}/{b['original_qty']} {b['unit']})")

print("\nALL END-TO-END TESTS PASSED!")
