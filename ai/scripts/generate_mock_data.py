import os
import sys
import random
import uuid
from datetime import datetime, timedelta

# Ensure ai package is importable from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.core.config import supabase

def clear_table(table_name):
    # Supabase Python client doesn't support truncate easily, so we just try to delete all.
    # Note: RLS might block this or foreign keys might fail, but since DB is empty it's fine.
    try:
        supabase.table(table_name).delete().neq('id', -1).execute()
        print(f"Cleared {table_name}")
    except Exception as e:
        print(f"Failed to clear {table_name} (likely already empty or FK constraint): {e}")

def main():
    print("Generating mock data...")

    # Insert Company
    comp_resp = supabase.table('companies').insert([
        {'name': 'BuildRight Construction'}
    ]).execute()
    company_id = comp_resp.data[0]['id']

    # Insert User
    random_email = f"arjun_{uuid.uuid4().hex[:6]}@buildright.com"
    user_resp = supabase.table('users').insert([
        {'company_id': company_id, 'name': 'Arjun Mehta', 'email': random_email, 'role': 'pm', 'password_hash': 'mock_hash_123'}
    ]).execute()
    user_id = user_resp.data[0]['id']

    # Insert Sites
    sites_resp = supabase.table('sites').insert([
        {'company_id': company_id, 'name': 'Downtown Plaza'},
        {'company_id': company_id, 'name': 'Riverside Complex'}
    ]).execute()
    site_ids = [s['id'] for s in sites_resp.data]

    # Insert Materials
    mat_resp = supabase.table('materials').insert([
        {'company_id': company_id, 'name': 'Cement (50kg Bag)', 'unit': 'bags'},
        {'company_id': company_id, 'name': 'Steel Rebar (Ton)', 'unit': 'tons'},
        {'company_id': company_id, 'name': 'Bricks (Pallet)', 'unit': 'pallets'}
    ]).execute()
    mat_ids = [m['id'] for m in mat_resp.data]

    # Initialize Inventory for each site and material
    inventory = []
    for s_id in site_ids:
        for m_id in mat_ids:
            inventory.append({
                'site_id': s_id,
                'material_id': m_id,
                'quantity': random.randint(100, 1000),
                'reorder_level': random.randint(50, 200)
            })
    supabase.table('inventory').insert(inventory).execute()

    # Insert Vendors
    ven_resp = supabase.table('vendors').insert([
        {'company_id': company_id, 'name': 'UltraTech Supplies'},
        {'company_id': company_id, 'name': 'SteelCo India'},
        {'company_id': company_id, 'name': 'Metro Building Materials'}
    ]).execute()
    ven_ids = [v['id'] for v in ven_resp.data]

    # Insert Inventory Transactions
    transactions = []
    base_date = datetime.now() - timedelta(days=30)
    for _ in range(20):
        t_date = base_date + timedelta(days=random.randint(1, 29))
        transactions.append({
            'site_id': random.choice(site_ids),
            'material_id': random.choice(mat_ids),
            'user_id': user_id,
            'type': random.choice(['IN', 'OUT']),
            'quantity': random.randint(10, 100),
            'date': t_date.strftime('%Y-%m-%d'),
            'reference': f"REF-{random.randint(1000, 9999)}"
        })
    supabase.table('inventory_transactions').insert(transactions).execute()

    # Insert Material Requests
    reqs = []
    for _ in range(5):
        t_date = base_date + timedelta(days=random.randint(1, 29))
        reqs.append({
            'site_id': random.choice(site_ids),
            'material_id': random.choice(mat_ids),
            'requested_by': user_id,
            'quantity': random.randint(20, 200),
            'pm_status': random.choice(['pending', 'approved']),
            'finance_status': random.choice(['not_applicable', 'pending', 'approved']),
            'justification': 'Required for upcoming phase'
        })
    req_resp = supabase.table('material_requests').insert(reqs).execute()
    req_ids = [r['id'] for r in req_resp.data]

    # Insert Vendor Quotes
    quotes = []
    for r_id in req_ids:
        quotes.append({
            'request_id': r_id,
            'vendor_id': random.choice(ven_ids),
            'unit_price': random.randint(100, 1000),
            'total_price': random.randint(1000, 50000)
        })
    quote_resp = supabase.table('vendor_quotes').insert(quotes).execute()
    quote_ids = [q['id'] for q in quote_resp.data]

    # Insert Purchase Orders
    pos = []
    for i in range(5):
        qty = random.randint(50, 500)
        price = random.randint(100, 1000)
        t_date = base_date + timedelta(days=random.randint(1, 29))
        pos.append({
            'vendor_id': random.choice(ven_ids),
            'request_id': req_ids[i],
            'vendor_quote_id': quote_ids[i],
            'quantity': qty,
            'unit_price': price,
            'amount': qty * price,
            'status': random.choice(['pending_finance', 'approved', 'delivered']),
            'order_date': t_date.strftime('%Y-%m-%d')
        })
    supabase.table('purchase_orders').insert(pos).execute()

    # Insert Expenses
    expenses = []
    for _ in range(10):
        t_date = base_date + timedelta(days=random.randint(1, 29))
        expenses.append({
            'site_id': random.choice(site_ids),
            'recorded_by': user_id,
            'category': random.choice(['material', 'labor', 'equipment']),
            'amount': random.randint(1000, 50000),
            'date': t_date.strftime('%Y-%m-%d')
        })
    supabase.table('expenses').insert(expenses).execute()

    print("Successfully populated mock data into Supabase!")

if __name__ == '__main__':
    main()
