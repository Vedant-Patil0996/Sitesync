-- =====================================================================
-- SITESYNC — COMPLETE MASTER DATABASE SCHEMA (PostgreSQL / Supabase)
-- Consolidated with 384-dim Vector RAG support and triggers
-- =====================================================================

create extension if not exists vector;
create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------
-- 1. TENANT / IDENTITY
-- ---------------------------------------------------------------------

create table if not exists companies (
  id bigserial primary key,
  name text not null,
  created_at timestamptz default now()
);

create table if not exists users (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  name text not null,
  email text not null unique,
  password_hash text not null,
  phone text,
  role text not null check (role in ('admin', 'pm', 'contractor', 'finance')),
  is_active boolean not null default true,
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------------
-- 2. SITES & ASSIGNMENTS
-- ---------------------------------------------------------------------

create table if not exists sites (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  name text not null,
  location text,
  latitude numeric,
  longitude numeric,
  status text not null default 'active' check (status in ('active', 'on_hold', 'completed')),
  created_by bigint references users(id),
  created_at timestamptz default now()
);

create table if not exists site_assignments (
  id bigserial primary key,
  site_id bigint references sites(id) on delete cascade not null,
  user_id bigint references users(id) on delete cascade not null,
  assigned_role text not null,
  created_at timestamptz default now(),
  unique (site_id, user_id)
);

-- ---------------------------------------------------------------------
-- 3. PROJECTS, TASKS, MILESTONES
-- ---------------------------------------------------------------------

create table if not exists projects (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  site_id bigint references sites(id) on delete cascade not null,
  pm_id bigint references users(id) not null,
  name text not null,
  description text,
  budget_allocated numeric not null default 0 check (budget_allocated >= 0),
  start_date date,
  end_date date,
  status text not null default 'planning' check (status in ('planning', 'in_progress', 'on_hold', 'completed', 'archived')),
  progress_percent numeric not null default 0 check (progress_percent >= 0 and progress_percent <= 100),
  created_by bigint references users(id),
  created_at timestamptz default now()
);

create table if not exists tasks (
  id bigserial primary key,
  project_id bigint references projects(id) on delete cascade,
  site_id bigint references sites(id) on delete cascade,
  name text not null,
  description text,
  assigned_contractor_id bigint references users(id),
  status text not null default 'pending' check (status in ('pending', 'in_progress', 'delayed', 'completed')),
  priority text not null default 'medium' check (priority in ('low', 'medium', 'high', 'critical')),
  start_date date not null,
  end_date date not null,
  progress_percent numeric not null default 0 check (progress_percent >= 0 and progress_percent <= 100),
  depends_on_task_id bigint references tasks(id),
  created_at timestamptz default now()
);

create table if not exists milestones (
  id bigserial primary key,
  project_id bigint references projects(id) on delete cascade not null,
  name text not null,
  target_date date not null,
  achieved boolean not null default false,
  achieved_at timestamptz
);

-- PM validation trigger function
create or replace function validate_project_pm()
returns trigger
language plpgsql
as $$
declare
  project_company_id bigint;
  pm_company_id bigint;
  pm_role text;
  pm_active boolean;
begin
  select company_id into project_company_id from sites where id = new.site_id;
  select company_id, role, is_active into pm_company_id, pm_role, pm_active from users where id = new.pm_id;
  if project_company_id is null or pm_company_id is null or project_company_id <> pm_company_id or pm_role <> 'pm' or not pm_active then
    raise exception 'Project PM must be an active PM in the project site company';
  end if;
  return new;
end;
$$;

drop trigger if exists projects_validate_pm on projects;
create trigger projects_validate_pm
before insert or update of site_id, pm_id on projects
for each row execute function validate_project_pm();

-- ---------------------------------------------------------------------
-- 4. MATERIALS & INVENTORY
-- ---------------------------------------------------------------------

create table if not exists materials (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  name text not null,
  category text not null,
  unit_of_measure text not null,
  reorder_level numeric not null default 0 check (reorder_level >= 0),
  minimum_stock_threshold numeric not null default 0 check (minimum_stock_threshold >= 0),
  unit_cost numeric not null default 0 check (unit_cost >= 0),
  qr_code_prefix text,
  created_at timestamptz default now()
);

create table if not exists inventory (
  id bigserial primary key,
  site_id bigint references sites(id) on delete cascade not null,
  material_id bigint references materials(id) on delete cascade not null,
  quantity numeric not null default 0 check (quantity >= 0),
  last_updated timestamptz default now(),
  unique (site_id, material_id)
);

create table if not exists inventory_transactions (
  id bigserial primary key,
  site_id bigint references sites(id) on delete cascade not null,
  material_id bigint references materials(id) on delete cascade not null,
  type text not null check (type in ('receipt', 'dispatch', 'adjustment', 'transfer_in', 'transfer_out')),
  quantity numeric not null,
  performed_by bigint references users(id) not null,
  notes text,
  created_at timestamptz default now()
);

create table if not exists material_batches (
  id bigserial primary key,
  batch_number text not null unique,
  site_id bigint references sites(id) on delete cascade not null,
  material_id bigint references materials(id) on delete cascade not null,
  quantity numeric not null check (quantity >= 0),
  qr_code text not null unique,
  manufactured_date date,
  expiry_date date,
  created_at timestamptz default now()
);

create table if not exists delivery_discrepancies (
  id bigserial primary key,
  delivery_id bigint,
  batch_id bigint references material_batches(id) on delete set null,
  expected_quantity numeric not null,
  received_quantity numeric not null,
  discrepancy_reason text not null,
  reported_by bigint references users(id) not null,
  status text not null default 'flagged' check (status in ('flagged', 'investigating', 'resolved')),
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------------
-- 5. EQUIPMENT & LABOR LOGS
-- ---------------------------------------------------------------------

create table if not exists equipment (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  site_id bigint references sites(id) on delete set null,
  name text not null,
  type text not null,
  status text not null default 'operational' check (status in ('operational', 'idle', 'in_use', 'maintenance', 'critical_failure')),
  hourly_cost numeric not null default 0 check (hourly_cost >= 0),
  last_maintenance_date date,
  created_at timestamptz default now()
);

create table if not exists equipment_logs (
  id bigserial primary key,
  equipment_id bigint references equipment(id) on delete cascade not null,
  site_id bigint references sites(id) on delete cascade not null,
  logged_by bigint references users(id) not null,
  hours_used numeric not null check (hours_used >= 0),
  fuel_used numeric check (fuel_used >= 0),
  issue_description text,
  created_at timestamptz default now()
);

create table if not exists labor_logs (
  id bigserial primary key,
  site_id bigint references sites(id) on delete cascade not null,
  contractor_id bigint references users(id) not null,
  worker_count integer not null check (worker_count >= 0),
  hours_worked numeric not null check (hours_worked >= 0),
  trade_type text not null,
  notes text,
  date date not null default current_date,
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------------
-- 6. VENDORS & PROCUREMENT
-- ---------------------------------------------------------------------

create table if not exists vendors (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  name text not null,
  contact_person text,
  email text,
  phone text,
  category text,
  rating numeric check (rating >= 0 and rating <= 5),
  reliability_score numeric default 1.0 check (reliability_score >= 0 and reliability_score <= 1),
  created_at timestamptz default now()
);

create table if not exists material_requests (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  site_id bigint references sites(id) on delete cascade not null,
  material_id bigint references materials(id) on delete cascade not null,
  quantity numeric not null check (quantity > 0),
  requested_by bigint references users(id) not null,
  status text not null default 'pending' check (status in ('pending', 'approved', 'rejected', 'ordered', 'fulfilled')),
  required_by_date date,
  reason text,
  created_at timestamptz default now()
);

create table if not exists vendor_quotes (
  id bigserial primary key,
  request_id bigint references material_requests(id) on delete cascade not null,
  vendor_id bigint references vendors(id) on delete cascade not null,
  unit_price numeric not null check (unit_price >= 0),
  total_price numeric not null check (total_price >= 0),
  delivery_days integer check (delivery_days >= 0),
  is_selected boolean not null default false,
  created_at timestamptz default now()
);

create table if not exists purchase_orders (
  id bigserial primary key,
  request_id bigint references material_requests(id) on delete set null,
  vendor_id bigint references vendors(id) on delete cascade not null,
  vendor_quote_id bigint references vendor_quotes(id) on delete set null,
  quantity numeric not null check (quantity > 0),
  unit_price numeric not null check (unit_price >= 0),
  amount numeric not null check (amount >= 0),
  status text not null default 'draft' check (status in ('draft', 'approved', 'sent', 'received', 'cancelled')),
  approved_by bigint references users(id),
  approved_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists deliveries (
  id bigserial primary key,
  po_id bigint references purchase_orders(id) on delete cascade not null,
  site_id bigint references sites(id) on delete cascade not null,
  quantity_received numeric not null check (quantity_received >= 0),
  received_by bigint references users(id) not null,
  received_at timestamptz default now(),
  status text not null default 'accepted' check (status in ('accepted', 'rejected', 'partial')),
  notes text
);

-- Add delivery_id reference back to discrepancies
alter table delivery_discrepancies
  add constraint fk_delivery_discrepancies_delivery
  foreign key (delivery_id) references deliveries(id) on delete set null;

-- ---------------------------------------------------------------------
-- 7. FINANCE
-- ---------------------------------------------------------------------

create table if not exists payments (
  id bigserial primary key,
  po_id bigint references purchase_orders(id) on delete set null,
  vendor_id bigint references vendors(id) on delete cascade not null,
  amount numeric not null check (amount > 0),
  payment_method text not null,
  status text not null default 'pending' check (status in ('pending', 'completed', 'failed')),
  paid_by bigint references users(id),
  paid_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists expenses (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  site_id bigint references sites(id) on delete cascade not null,
  category text not null,
  amount numeric not null check (amount > 0),
  logged_by bigint references users(id) not null,
  approved_by bigint references users(id),
  status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
  description text,
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------------
-- 8. ALERTS & NOTIFICATIONS
-- ---------------------------------------------------------------------

create table if not exists alerts (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  site_id bigint references sites(id) on delete cascade,
  type text not null check (type in ('low_stock', 'delivery_delay', 'equipment_failure', 'budget_overrun', 'schedule_risk', 'discrepancy')),
  severity text not null check (severity in ('info', 'warning', 'critical')),
  message text not null,
  status text not null default 'open' check (status in ('open', 'acknowledged', 'resolved')),
  metadata jsonb,
  created_at timestamptz default now()
);

create table if not exists notifications (
  id bigserial primary key,
  alert_id bigint references alerts(id) on delete cascade,
  recipient_id bigint references users(id) on delete cascade not null,
  channel text not null check (channel in ('in_app', 'whatsapp', 'email', 'sms', 'ivr')),
  status text not null default 'pending' check (status in ('pending', 'sent', 'failed')),
  sent_at timestamptz,
  payload jsonb,
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------------
-- 9. AUDIT LOGS
-- ---------------------------------------------------------------------

create table if not exists audit_logs (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  user_id bigint references users(id) on delete set null,
  action text not null,
  entity_type text not null,
  entity_id bigint,
  details jsonb,
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------------
-- 10. AI RAG VECTOR EMBEDDINGS (SentenceTransformers 384-dim)
-- ---------------------------------------------------------------------

create table if not exists document_chunks (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  site_id bigint references sites(id) on delete cascade,
  material_id bigint references materials(id) on delete set null,
  vendor_id bigint references vendors(id) on delete set null,
  content text not null,
  source_table text not null,
  record_id bigint not null,
  date date,
  metadata jsonb,
  embedding vector(384),
  created_at timestamptz default now()
);

create index if not exists idx_document_chunks_embedding on document_chunks using ivfflat (embedding vector_cosine_ops);

-- RAG similarity match function
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
