-- Migration to alter vector dimensions from 1536 (OpenAI) to 384 (Local SentenceTransformers)

-- 1. Alter the column in document_chunks
ALTER TABLE document_chunks
ALTER COLUMN embedding TYPE vector(384);

-- 2. Drop and recreate the match_document_chunks function with the new signature
DROP FUNCTION IF EXISTS match_document_chunks(vector(1536), integer, bigint, bigint, text, bigint);

create or replace function match_document_chunks(
  query_embedding vector(384),
  match_count int default 8,
  filter_company_id bigint default null,
  filter_site_id bigint default null,
  filter_source_table text default null,
  filter_vendor_id bigint default null
)
returns table (
  id bigint, content text, source_table text, record_id bigint,
  site_id bigint, material_id bigint, vendor_id bigint, date date, similarity float
)
language sql stable as $$
  select id, content, source_table, record_id, site_id, material_id, vendor_id, date,
         1 - (embedding <=> query_embedding) as similarity
  from document_chunks
  where (filter_company_id is null or company_id = filter_company_id)
    and (filter_site_id is null or site_id = filter_site_id)
    and (filter_source_table is null or source_table = filter_source_table)
    and (filter_vendor_id is null or vendor_id = filter_vendor_id)
  order by embedding <=> query_embedding
  limit match_count;
$$;
