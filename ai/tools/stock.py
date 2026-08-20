from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from ai.core.config import supabase

def get_transaction_history(material_id: str, site_id: str, days: int = 14, type: str = None) -> List[Dict[str, Any]]:
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    q = supabase.table('inventory_transactions').select(
        'id, type, quantity, date, reference, materials(name, unit), sites!inventory_transactions_site_id_fkey(name)'
    ).eq('material_id', material_id).eq('site_id', site_id).gte('date', since).order('date', desc=True)
    
    if type:
        q = q.eq('type', type)
        
    response = q.execute()
    return response.data

def compare_across_sites(material_id: str, exclude_site_id: str) -> List[Dict[str, Any]]:
    response = supabase.table('inventory').select(
        'site_id, quantity, max_capacity, sites(name)'
    ).eq('material_id', material_id).neq('site_id', exclude_site_id).execute()
    
    results = []
    for row in response.data:
        max_capacity = row.get('max_capacity')
        quantity = row.get('quantity', 0)
        surplus = quantity - round(max_capacity * 0.5) if max_capacity else None
        has_surplus = quantity > max_capacity * 0.7 if max_capacity else None
        
        results.append({
            'site_id': row['site_id'],
            'site_name': row.get('sites', {}).get('name'),
            'quantity': quantity,
            'max_capacity': max_capacity,
            'surplus': surplus,
            'has_surplus': has_surplus
        })
    return results

def get_consumption_rate_history(material_id: str, site_id: str, days: int = 90) -> Dict[str, Any]:
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    recent_since = (datetime.utcnow() - timedelta(days=3)).isoformat()

    own_history_resp = supabase.table('inventory_transactions').select(
        'quantity, date, user_id, users(name)'
    ).eq('material_id', material_id).eq('site_id', site_id).eq('type', 'OUT').gte('date', since).order('date').execute()
    own_history = own_history_resp.data

    other_sites_resp = supabase.table('inventory_transactions').select(
        'quantity, date'
    ).eq('material_id', material_id).neq('site_id', site_id).eq('type', 'OUT').gte('date', since).execute()
    other_sites = other_sites_resp.data

    def sum_qty(rows):
        return sum([float(r.get('quantity', 0)) for r in rows])

    baseline_avg_per_day = sum_qty(own_history) / days if days > 0 else 0
    recent_rows = [r for r in own_history if r.get('date', '') >= recent_since]
    recent_avg_per_day = sum_qty(recent_rows) / 3
    other_sites_avg_per_day = sum_qty(other_sites) / days if other_sites and days > 0 else 0
    
    increase_percent = None
    if baseline_avg_per_day > 0:
        increase_percent = round(((recent_avg_per_day - baseline_avg_per_day) / baseline_avg_per_day) * 100)

    by_contractor = {}
    for r in recent_rows:
        name = r.get('users', {}).get('name') if r.get('users') else f"user_{r.get('user_id')}"
        by_contractor[name] = by_contractor.get(name, 0) + float(r.get('quantity', 0))

    return {
        'baseline_avg_per_day': round(baseline_avg_per_day, 2),
        'recent_avg_per_day': round(recent_avg_per_day, 2),
        'increase_percent': increase_percent,
        'other_sites_avg_per_day': round(other_sites_avg_per_day, 2),
        'anomaly': increase_percent is not None and increase_percent > 75,
        'recent_consumption_by_contractor': by_contractor
    }

def get_pending_requests_and_pos(material_id: str, site_id: str) -> Dict[str, Any]:
    requests_resp = supabase.table('material_requests').select(
        'id, pm_status, finance_status, quantity, created_at'
    ).eq('material_id', material_id).eq('site_id', site_id).or_(
        'pm_status.eq.pending,finance_status.eq.pending'
    ).execute()
    requests = requests_resp.data
    
    if not requests:
        return {'request_exists': False, 'po_exists': False}

    created_at_str = requests[0]['created_at']
    if created_at_str.endswith('Z'):
        created_at_str = created_at_str[:-1] + '+00:00'
    created_at = datetime.fromisoformat(created_at_str)
    
    pending_days = (datetime.now(timezone.utc) - created_at).days
    
    request_ids = [r['id'] for r in requests]
    pos_resp = supabase.table('purchase_orders').select(
        'id, status, amount, order_date, deliveries(delivery_date, status)'
    ).in_('request_id', request_ids).neq('status', 'completed').neq('status', 'cancelled').execute()
    
    pos = pos_resp.data
    po = pos[0] if pos else None
    
    deliveries = po.get('deliveries', []) if po else []
    expected_delivery = deliveries[0].get('delivery_date') if deliveries else None

    return {
        'request_exists': True,
        'pm_status': requests[0].get('pm_status'),
        'finance_status': requests[0].get('finance_status'),
        'requested_quantity': requests[0].get('quantity'),
        'pending_days': pending_days,
        'po_exists': po is not None,
        'po_status': po.get('status') if po else None,
        'po_order_date': po.get('order_date') if po else None,
        'expected_delivery': expected_delivery
    }
