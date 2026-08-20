print("Debug: Starting imports")
import os
import sys

# Ensure ai package is importable from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

print("Debug: Importing index_record (PyTorch/SentenceTransformers)")
from ai.core.index_chunk import index_record

print("Debug: Importing supabase")
from ai.core.config import supabase

print("Debug: Imports complete")

def seed_table(table_name: str, select_str: str):
    print(f"Fetching data from {table_name}...")
    resp = supabase.table(table_name).select(select_str).execute()
    data = resp.data
    
    for record in data:
        index_record(table_name, record)
        
    print(f"Indexed {len(data)} rows from {table_name}")

def main():
    seed_table(
        'inventory_transactions', 
        'id, site_id, material_id, type, quantity, date, reference, materials(name), sites!inventory_transactions_site_id_fkey(name, company_id)'
    )
    
    seed_table(
        'material_requests',
        'id, site_id, material_id, quantity, pm_status, finance_status, justification, materials(name), sites(name, company_id)'
    )
    
    # CRITICAL FIX applied here: added material_requests(...) join
    seed_table(
        'purchase_orders',
        'id, vendor_id, quantity, unit_price, amount, status, order_date, vendors(name), material_requests(site_id, material_id, materials(name), sites(name, company_id))'
    )
    
    seed_table(
        'expenses',
        'id, site_id, category, amount, date, sites(name, company_id)'
    )
    
    print("Seeding complete.")

if __name__ == "__main__":
    main()
