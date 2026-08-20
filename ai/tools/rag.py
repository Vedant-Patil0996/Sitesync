from typing import Dict, Any, List
# IMPORT SENTENCE_TRANSFORMERS/EMBEDDINGS FIRST TO PREVENT WINDOWS DLL CRASH
from ai.core.embeddings import embed
from ai.core.config import supabase

def search_historical_records(
    query: str, 
    company_id: str = None, 
    site_id: str = None, 
    source_table: str = None, 
    vendor_id: str = None
) -> List[Dict[str, Any]]:
    query_embedding = embed(query)
    
    params = {
        'query_embedding': query_embedding,
        'match_count': 8
    }
    
    if company_id:
        params['filter_company_id'] = company_id
    if site_id:
        params['filter_site_id'] = site_id
    if source_table:
        params['filter_source_table'] = source_table
    if vendor_id:
        params['filter_vendor_id'] = vendor_id
        
    resp = supabase.rpc('match_document_chunks', params).execute()
    return resp.data
