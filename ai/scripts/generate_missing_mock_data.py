import os
import sys
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.core.config import supabase

def main():
    print("Generating Projects, Tasks, and Equipment data...")

    # Fetch existing company, sites, and user
    comp_resp = supabase.table('companies').select('id').limit(1).execute()
    company_id = comp_resp.data[0]['id']

    sites_resp = supabase.table('sites').select('id').execute()
    site_ids = [s['id'] for s in sites_resp.data]

    user_resp = supabase.table('users').select('id').limit(1).execute()
    user_id = user_resp.data[0]['id']

    # Insert Projects
    projects = []
    for site_id in site_ids:
        projects.append({
            'company_id': company_id,
            'site_id': site_id,
            'pm_id': user_id,
            'name': f'Project at Site {site_id}',
            'budget_allocated': 500000.0,
            'status': 'in_progress'
        })
    p_resp = supabase.table('projects').insert(projects).execute()
    project_ids = {p['site_id']: p['id'] for p in p_resp.data}

    # Insert Tasks
    tasks = []
    base_date = datetime.now() - timedelta(days=10)
    for site_id in site_ids:
        proj_id = project_ids[site_id]
        
        # Task 1: Excavation
        tasks.append({
            'project_id': proj_id,
            'name': 'Excavation & Foundation',
            'status': 'in_progress',
            'start_date': base_date.strftime('%Y-%m-%d'),
            'end_date': (base_date + timedelta(days=5)).strftime('%Y-%m-%d'),
            'assigned_to': user_id
        })
    t_resp = supabase.table('tasks').insert(tasks).execute()
    
    # Task 2: Structural Framing (Depends on Excavation)
    tasks2 = []
    for t in t_resp.data:
        tasks2.append({
            'project_id': t['project_id'],
            'name': 'Structural Framing',
            'status': 'not_started',
            'start_date': t['end_date'],
            'end_date': (datetime.strptime(t['end_date'], '%Y-%m-%d') + timedelta(days=10)).strftime('%Y-%m-%d'),
            'depends_on_task_id': t['id'],
            'assigned_to': user_id
        })
    supabase.table('tasks').insert(tasks2).execute()

    # Insert Equipment
    equipment = []
    # Site 5 (Excavator 1)
    equipment.append({
        'site_id': site_ids[0],
        'name': 'EXC-01',
        'type': 'Excavator',
        'status': 'active',
        'allocated_to_task_id': t_resp.data[0]['id'],
        'hours_used': 120
    })
    # Site 6 (Excavator 2 - idle)
    if len(site_ids) > 1:
        equipment.append({
            'site_id': site_ids[1],
            'name': 'EXC-09',
            'type': 'Excavator',
            'status': 'idle',
            'hours_used': 45
        })
        
    supabase.table('equipment').insert(equipment).execute()

    print("Successfully populated missing mock data!")

if __name__ == '__main__':
    main()
