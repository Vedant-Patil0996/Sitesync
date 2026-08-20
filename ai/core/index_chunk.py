from typing import Any, Dict
from ai.core.embeddings import embed
from ai.core.config import supabase

TEMPLATES = {
    'inventory_transactions': lambda r: (
        f"{r.get('type')} {r.get('quantity')} {r.get('materials', {}).get('name', 'Unknown')} "
        f"at {r.get('sites', {}).get('name', 'Unknown')} on {r.get('date')}"
        f"{', ref: ' + r.get('reference') if r.get('reference') else ''}"
    ),
    'material_requests': lambda r: (
        f"Request for {r.get('quantity')} {r.get('materials', {}).get('name', 'Unknown')} "
        f"at {r.get('sites', {}).get('name', 'Unknown')}, "
        f"pm_status: {r.get('pm_status')}, finance_status: {r.get('finance_status')}"
        f"{', justification: ' + r.get('justification') if r.get('justification') else ''}"
    ),
    'purchase_orders': lambda r: (
        f"PO to {r.get('vendors', {}).get('name', 'Unknown')} for {r.get('quantity')} units "
        f"at {r.get('unit_price')}/unit, total {r.get('amount')}, status {r.get('status')}"
    ),
    'expenses': lambda r: (
        f"{r.get('category')} expense of {r.get('amount')} "
        f"at {r.get('sites', {}).get('name', 'Unknown')} on {r.get('date')}"
    )
}

def index_record(source_table: str, record: Dict[str, Any]):
    """
    Generate an embedding for a record and insert it into document_chunks.
    """
    if source_table not in TEMPLATES:
        raise ValueError(f"No template found for source_table: {source_table}")

    template_func = TEMPLATES[source_table]
    content = template_func(record)
    embedding = embed(content)

    # Determine site_id
    site_id = record.get('site_id')
    if not site_id and 'material_requests' in record and record['material_requests']:
        site_id = record['material_requests'].get('site_id')

    # Determine material_id
    material_id = record.get('material_id')
    if not material_id and 'material_requests' in record and record['material_requests']:
        material_id = record['material_requests'].get('material_id')

    # Determine company_id (from sites if available, or material_requests.sites)
    company_id = None
    if 'sites' in record and record['sites']:
        company_id = record['sites'].get('company_id')
    elif 'material_requests' in record and record['material_requests'] and 'sites' in record['material_requests']:
        company_id = record['material_requests']['sites'].get('company_id')
    elif 'company_id' in record:
        company_id = record['company_id']

    date_val = record.get('date') or record.get('order_date') or record.get('created_at')

    payload = {
        'company_id': company_id,
        'content': content,
        'embedding': embedding,
        'source_table': source_table,
        'record_id': record.get('id'),
        'site_id': site_id,
        'material_id': material_id,
        'vendor_id': record.get('vendor_id'),
        'date': date_val
    }

    response = supabase.table('document_chunks').insert(payload).execute()
    return response.data
