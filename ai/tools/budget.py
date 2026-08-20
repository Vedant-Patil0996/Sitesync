from datetime import datetime, timedelta
from typing import Dict, Any, List
from ai.core.config import supabase

def get_budget_actuals(site_id: str) -> Dict[str, Any]:
    summary_resp = supabase.table('site_budget_summary').select(
        'allocated, spent'
    ).eq('site_id', site_id).execute()
    
    if not summary_resp.data:
        return {
            'allocated': 0,
            'spent': 0,
            'remaining': 0,
            'utilization_percent': 0,
            'recent_expenses': []
        }
        
    summary = summary_resp.data[0]
    
    expenses_resp = supabase.table('expenses').select(
        'category, amount, date'
    ).eq('site_id', site_id).order('date', desc=True).limit(20).execute()
    expenses = expenses_resp.data
    
    allocated = summary.get('allocated', 0)
    spent = summary.get('spent', 0)
    
    utilization_percent = round((spent / allocated) * 100) if allocated > 0 else 0
    
    return {
        'allocated': allocated,
        'spent': spent,
        'remaining': allocated - spent,
        'utilization_percent': utilization_percent,
        'recent_expenses': expenses
    }

def get_expense_breakdown_by_category(site_id: str, days: int = 30) -> List[Dict[str, Any]]:
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    resp = supabase.table('expenses').select(
        'category, amount'
    ).eq('site_id', site_id).gte('date', since).execute()
    
    data = resp.data
    total = sum([float(e.get('amount', 0)) for e in data])
    
    by_category = {}
    for e in data:
        cat = e.get('category')
        by_category[cat] = by_category.get(cat, 0) + float(e.get('amount', 0))
        
    result = []
    for category, amount in by_category.items():
        percentage = round((amount / total) * 100) if total > 0 else 0
        result.append({
            'category': category,
            'amount': amount,
            'percentage': percentage
        })
        
    result.sort(key=lambda x: x['amount'], reverse=True)
    return result

def get_po_history(site_id: str, days: int = 60) -> List[Dict[str, Any]]:
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    resp = supabase.table('purchase_orders').select(
        'id, amount, status, order_date, quantity, unit_price, '
        'material_requests!inner(site_id, materials(name)), vendors(name), deliveries(delivery_date, status)'
    ).eq('material_requests.site_id', site_id).gte('order_date', since).execute()
    
    data = resp.data
    result = []
    for po in data:
        mat_req = po.get('material_requests', {})
        material_name = mat_req.get('materials', {}).get('name') if isinstance(mat_req, dict) else None
        
        vendor_name = po.get('vendors', {}).get('name') if po.get('vendors') else None
        
        deliveries = po.get('deliveries', [])
        delivery_date = deliveries[0].get('delivery_date') if deliveries else None
        
        result.append({
            'po_id': po['id'],
            'material': material_name,
            'quantity': po.get('quantity'),
            'unit_price': po.get('unit_price'),
            'total_amount': po.get('amount'),
            'vendor': vendor_name,
            'status': po.get('status'),
            'order_date': po.get('order_date'),
            'delivery_date': delivery_date
        })
    return result

def get_vendor_price_trend(material_id: str, vendor_id: str) -> Dict[str, Any]:
    resp = supabase.table('vendor_quotes').select(
        'unit_price, created_at, material_requests!inner(material_id)'
    ).eq('vendor_id', vendor_id).eq('material_requests.material_id', material_id).order('created_at').execute()
    
    data = resp.data
    if len(data) < 2:
        return {'insufficient_data': True, 'quotes': data}
        
    starting_price = float(data[0]['unit_price'])
    latest_price = float(data[-1]['unit_price'])
    
    increase_percent = 0
    if starting_price > 0:
        increase_percent = round(((latest_price - starting_price) / starting_price) * 100)
        
    trend = 'stable'
    if increase_percent > 5:
        trend = 'increasing'
    elif increase_percent < -5:
        trend = 'decreasing'
        
    return {
        'starting_price': starting_price,
        'latest_price': latest_price,
        'absolute_change': latest_price - starting_price,
        'increase_percent': increase_percent,
        'trend': trend,
        'quote_history': data
    }

def compare_vendor_quotes(request_id: str) -> List[Dict[str, Any]]:
    # Guard: request_id must be a numeric integer (postgres bigint FK)
    if not request_id or not str(request_id).strip().lstrip('-').isdigit():
        return [{"error": f"No data available: 'request_id' must be a numeric material-request ID (got '{request_id}'). Query pending_requests first to get a valid ID."}]
    
    try:
        resp = supabase.table('vendor_quotes').select(
            'unit_price, delivery_days, total_price, vendors(name, rating)'
        ).eq('request_id', request_id).order('total_price').execute()
        
        if not resp.data:
            return [{"result": "no_quotes_found", "request_id": request_id, "note": "No vendor quotes on file for this request ID."}]
        return resp.data
    except Exception as e:
        return [{"error": str(e)}]
