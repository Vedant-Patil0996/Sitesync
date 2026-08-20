import os
import sys
import random
import uuid
from datetime import datetime, timedelta

# Ensure ai package is importable from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.core.config import supabase

def main():
    print("Generating rich, multi-site demo data for Hackathon Scenarios...")

    # 1. Company & User
    comp_resp = supabase.table('companies').insert([
        {'name': 'BuildRight Construction Group'}
    ]).execute()
    company_id = comp_resp.data[0]['id']

    random_email = f"demo_pm_{uuid.uuid4().hex[:6]}@buildright.com"
    user_resp = supabase.table('users').insert([
        {'company_id': company_id, 'name': 'Arjun Mehta (Demo PM)', 'email': random_email, 'role': 'pm', 'password_hash': 'mock_hash_123'}
    ]).execute()
    user_id = user_resp.data[0]['id']

    # 2. Multiple Sites
    site_names = [
        'Site 1 (Northwood Estate)',
        'Site 2 (Riverside Depot)', # Backup Site
        'Site 3 (Westend Tower)',
        'Site 4 (Airport Link Road)',
        'Site 5 (Downtown Core)'    # Trouble Site
    ]
    
    sites_data = [{'company_id': company_id, 'name': name} for name in site_names]
    sites_resp = supabase.table('sites').insert(sites_data).execute()
    
    # Store mapped IDs
    site_ids = {s['name']: s['id'] for s in sites_resp.data}
    site_5_id = site_ids['Site 5 (Downtown Core)']
    site_2_id = site_ids['Site 2 (Riverside Depot)']

    # 3. Multiple Projects & Tasks (Gantt Data)
    projects_data = []
    for s_name, s_id in site_ids.items():
        projects_data.append({'site_id': s_id, 'company_id': company_id, 'name': f'{s_name} - Main Phase', 'status': 'in_progress', 'pm_id': user_id})
    proj_resp = supabase.table('projects').insert(projects_data).execute()
    
    tasks_data = []
    for proj in proj_resp.data:
        # Create 3 tasks per project to show a timeline
        start = datetime.utcnow()
        for i in range(3):
            tasks_data.append({
                'project_id': proj['id'],
                'name': f'Phase {i+1} Work',
                'status': 'in_progress' if i == 0 else 'not_started',
                'start_date': (start + timedelta(days=i*15)).strftime('%Y-%m-%d'),
                'end_date': (start + timedelta(days=(i*15)+14)).strftime('%Y-%m-%d'),
                'assigned_to': user_id
            })
            
    # Explicit Critical Path Task for Site 5
    site_5_proj_id = next(p['id'] for p in proj_resp.data if p['site_id'] == site_5_id)
    tasks_data.append({
        'project_id': site_5_proj_id,
        'name': 'Deep Foundation Digging (Critical Path)',
        'status': 'in_progress',
        'start_date': datetime.utcnow().strftime('%Y-%m-%d'),
        'end_date': (datetime.utcnow() + timedelta(days=10)).strftime('%Y-%m-%d'),
        'assigned_to': user_id
    })
    tasks_resp = supabase.table('tasks').insert(tasks_data).execute()
    critical_task_id = next(t['id'] for t in tasks_resp.data if 'Critical Path' in t['name'])

    # 4. Equipment Spread
    equip_data = [
        {'site_id': site_5_id, 'name': 'EXC-01', 'type': 'Excavator', 'status': 'maintenance', 'hours_used': 1240, 'allocated_to_task_id': critical_task_id},
        {'site_id': site_2_id, 'name': 'EXC-02', 'type': 'Excavator', 'status': 'idle', 'hours_used': 88},
        {'site_id': site_ids['Site 1 (Northwood Estate)'], 'name': 'CRN-01', 'type': 'Crane', 'status': 'active', 'hours_used': 500},
        {'site_id': site_ids['Site 3 (Westend Tower)'], 'name': 'BULL-04', 'type': 'Bulldozer', 'status': 'active', 'hours_used': 300},
        {'site_id': site_ids['Site 4 (Airport Link Road)'], 'name': 'EXC-05', 'type': 'Excavator', 'status': 'active', 'hours_used': 900}
    ]
    supabase.table('equipment').insert(equip_data).execute()

    # 5. Materials & Inventory (Multiple items)
    mat_data = [
        {'company_id': company_id, 'name': 'MAT-CONC-01 (Ready Mix Concrete)', 'unit': 'tons'},
        {'company_id': company_id, 'name': 'MAT-STEEL-02 (TMT Rebar)', 'unit': 'tons'},
        {'company_id': company_id, 'name': 'MAT-BRICK-03 (Standard Bricks)', 'unit': 'pallets'}
    ]
    mat_resp = supabase.table('materials').insert(mat_data).execute()
    conc_id = next(m['id'] for m in mat_resp.data if 'CONC' in m['name'])

    inv_data = []
    for s_id in site_ids.values():
        for mat in mat_resp.data:
            # Force low stock on Site 5 for Concrete
            qty = 10 if (s_id == site_5_id and mat['id'] == conc_id) else random.randint(150, 500)
            inv_data.append({'site_id': s_id, 'material_id': mat['id'], 'quantity': qty, 'reorder_level': 100})
    supabase.table('inventory').insert(inv_data).execute()

    # 6. Vendors & RAG Data
    ven_data = [
        {'company_id': company_id, 'name': 'Vendor A (Fast, Premium)', 'rating': 4.8},
        {'company_id': company_id, 'name': 'Vendor B (Standard, Cheap)', 'rating': 4.1},
        {'company_id': company_id, 'name': 'Vendor C (Local Supply)', 'rating': 3.5}
    ]
    ven_resp = supabase.table('vendors').insert(ven_data).execute()
    
    # Material requests for RAG context
    req_data = []
    for i in range(10):
        req_data.append({
            'site_id': random.choice(list(site_ids.values())),
            'material_id': random.choice([m['id'] for m in mat_resp.data]),
            'requested_by': user_id,
            'quantity': random.randint(50, 200),
            'pm_status': 'approved',
            'justification': f'Phase {i} Bulk Order'
        })
    req_resp = supabase.table('material_requests').insert(req_data).execute()

    # 7. Expenses & Budgets (Force Budget Drift on Site 5)
    exp_data = []
    for s_id in site_ids.values():
        for _ in range(3):
            exp_data.append({
                'site_id': s_id, 'recorded_by': user_id, 
                'category': random.choice(['material', 'labor', 'equipment']),
                'amount': random.randint(2000, 10000), 'date': datetime.now().strftime('%Y-%m-%d')
            })
            
    # Massive blowout on Site 5 Equipment
    exp_data.append({'site_id': site_5_id, 'recorded_by': user_id, 'category': 'equipment', 'amount': 45000, 'date': datetime.now().strftime('%Y-%m-%d')})
    supabase.table('expenses').insert(exp_data).execute()

    print(f"Rich Data Seeded Successfully!")
    print(f"--- RUNTIME IDs ---")
    print(f"Site 5 (Trouble Site) ID: {site_5_id}")
    print(f"Site 2 (Backup Site) ID: {site_2_id}")

if __name__ == '__main__':
    main()
