"""
procurement.py
==============
Procurement agent tools backed by real Supabase data.
Previously these were hardcoded mocks - now they query live tables.

- evaluate_vendor_reliability: queries vendors + purchase_orders tables
- get_market_price_benchmark:  queries vendor_quotes + materials tables
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from ai.core.config import supabase


def evaluate_vendor_reliability(vendor_id: str) -> Dict[str, Any]:
    """Evaluate a vendor's historical performance from real PO and delivery data."""
    # Guard: vendor_id must be numeric
    if not vendor_id or not str(vendor_id).strip().lstrip('-').isdigit():
        return {
            "error": f"No data available: vendor_id must be a numeric ID (got '{vendor_id}'). "
                     "Use the vendors table to look up a valid numeric vendor ID first.",
            "source": "vendors table"
        }

    try:
        # Fetch vendor name
        vendor_resp = supabase.table('vendors').select('id, name').eq('id', vendor_id).limit(1).execute()
        if not vendor_resp.data:
            return {"error": f"Vendor ID {vendor_id} not found in database.", "source": "vendors table"}

        vendor = vendor_resp.data[0]

        # Fetch purchase orders for this vendor in the last 180 days
        since = (datetime.utcnow() - timedelta(days=180)).isoformat()
        po_resp = supabase.table('purchase_orders').select(
            'id, status, order_date, amount'
        ).eq('vendor_id', vendor_id).gte('order_date', since).execute()

        po_data = po_resp.data
        total_pos = len(po_data)

        if total_pos == 0:
            return {
                "vendor_id": vendor_id,
                "vendor_name": vendor['name'],
                "result": "no_purchase_history",
                "note": "No POs found for this vendor in the last 180 days. Cannot assess reliability.",
                "source": f"[vendors: {vendor_id}]"
            }

        completed = [po for po in po_data if po.get('status') == 'delivered']
        pending = [po for po in po_data if po.get('status') in ('pending', 'approved')]
        cancelled = [po for po in po_data if po.get('status') == 'cancelled']
        on_time_rate = round((len(completed) / total_pos) * 100, 1) if total_pos > 0 else 0

        return {
            "vendor_id": vendor_id,
            "vendor_name": vendor['name'],
            "total_pos_last_180d": total_pos,
            "delivered": len(completed),
            "pending": len(pending),
            "cancelled": len(cancelled),
            "delivery_completion_rate_pct": on_time_rate,
            "source": f"[vendors: {vendor_id}] [purchase_orders: {', '.join(str(p['id']) for p in po_data[:5])}]"
        }
    except Exception as e:
        return {"error": str(e)}


def get_market_price_benchmark(material_id: str) -> Dict[str, Any]:
    """Get the current regional benchmark price for a material from real vendor quotes."""
    # Guard: material_id must be numeric (materials.id is bigint)
    if not material_id or not str(material_id).strip().lstrip('-').isdigit():
        return {
            "error": f"No data available: material_id must be a numeric ID (got '{material_id}'). "
                     "This tool works with material IDs from the materials table, not equipment names.",
            "note": "For equipment procurement, there is no pre-existing market price data in the database. "
                    "State 'no benchmark data available' in your report.",
            "source": "materials + vendor_quotes tables"
        }

    try:
        # Fetch material name
        mat_resp = supabase.table('materials').select('id, name, unit').eq('id', material_id).limit(1).execute()
        if not mat_resp.data:
            return {
                "error": f"Material ID {material_id} not found in database.",
                "source": "materials table"
            }

        mat = mat_resp.data[0]

        # Fetch recent vendor quotes for this material
        since = (datetime.utcnow() - timedelta(days=90)).isoformat()
        quotes_resp = supabase.table('vendor_quotes').select(
            'unit_price, created_at, vendor_id, material_requests!inner(material_id)'
        ).eq('material_requests.material_id', material_id).gte('created_at', since).order('created_at').execute()

        quotes = quotes_resp.data

        if not quotes:
            return {
                "material_id": material_id,
                "material_name": mat['name'],
                "result": "no_quote_data",
                "note": "No vendor quotes found for this material in the last 90 days. Cannot compute benchmark.",
                "source": f"[materials: {material_id}]"
            }

        prices = [float(q['unit_price']) for q in quotes]
        avg_price = round(sum(prices) / len(prices), 2)
        min_price = round(min(prices), 2)
        max_price = round(max(prices), 2)

        # Trend: compare first half vs second half
        mid = len(prices) // 2
        if mid > 0:
            first_avg = sum(prices[:mid]) / mid
            second_avg = sum(prices[mid:]) / (len(prices) - mid)
            pct_change = round(((second_avg - first_avg) / first_avg) * 100, 1) if first_avg > 0 else 0
            trend = f"{'+' if pct_change >= 0 else ''}{pct_change}% over 90d"
        else:
            trend = "insufficient data for trend"

        return {
            "material_id": material_id,
            "material_name": mat['name'],
            "unit": mat.get('unit'),
            "quote_count": len(quotes),
            "avg_unit_price": avg_price,
            "min_unit_price": min_price,
            "max_unit_price": max_price,
            "price_trend_90d": trend,
            "source": f"[materials: {material_id}] [vendor_quotes: {len(quotes)} records]"
        }
    except Exception as e:
        return {"error": str(e)}
