-- =====================================================================
-- SITESYNC — FINAL DATABASE SCHEMA (PostgreSQL / Supabase)
-- =====================================================================

create extension if not exists vector;
create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------
-- 1. TENANT / IDENTITY
-- ---------------------------------------------------------------------

create table companies (
  id bigserial primary key,
  name text not null,
  created_at timestamptz default now()
);

create table users (
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

comment on table users is
  'Every login account. role is the account TYPE. Which site(s) a pm/contractor
   actually has access to is determined separately by site_assignments — role
   alone does not scope data access.';

-- ---------------------------------------------------------------------
-- 2. SITES & ASSIGNMENTS
-- ---------------------------------------------------------------------

create table sites (
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

create table site_assignments (
  id bigserial primary key,
  site_id bigint references sites(id) on delete cascade not null,
  user_id bigint references users(id) on delete cascade not null,
  assigned_role text not null,
  created_at timestamptz default now(),
  unique (site_id, user_id)
);

comment on table site_assignments is
  'The real RBAC boundary. A pm or contractor only sees data for sites
   present here. Admin creates the PM assignment; PM may add a
   contractor to their own site if Admin has not already.';

-- ---------------------------------------------------------------------
-- 3. PROJECTS, TASKS, MILESTONES
-- ---------------------------------------------------------------------

create table projects (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  site_id bigint references sites(id) on delete cascade not null,
  pm_id bigint references users(id) not null,
  name text not null,
  description text,
  budget_allocated numeric not null default 0,
  start_date date,
  end_date date,
  status text not null default 'planning' check (status in ('planning', 'in_progress', 'on_hold', 'completed', 'archived')),
  progress_percent numeric not null default 0,
  created_by bigint references users(id),
  created_at timestamptz default now()
);

alter table projects
  add constraint projects_budget_nonnegative check (budget_allocated >= 0),
  add constraint projects_progress_range check (progress_percent >= 0 and progress_percent <= 100);

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

comment on table projects is
  'budget_allocated is the source of truth for a project budget — set by
   Admin at project creation. Site-level budget vs actual is a rollup SUM()
   over this tables projects — see the site_budget_summary view.';

create table tasks (
  id bigserial primary key,
  project_id bigint references projects(id) on delete cascade not null,
  name text not null,
  description text,
  status text not null default 'not_started' check (status in ('not_started', 'in_progress', 'delayed', 'completed')),
  priority text not null default 'medium' check (priority in ('low', 'medium', 'high', 'critical')),
  progress_percent numeric not null default 0 check (progress_percent >= 0 and progress_percent <= 100),
  start_date date,
  end_date date,
  depends_on_task_id bigint references tasks(id),
  assigned_to bigint references users(id),
  created_at timestamptz default now()
);

create table milestones (
  id bigserial primary key,
  project_id bigint references projects(id) on delete cascade not null,
  name text not null,
  due_date date,
  status text not null default 'upcoming' check (status in ('upcoming', 'achieved', 'missed')),
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------------
-- 4. MATERIALS & INVENTORY
-- ---------------------------------------------------------------------

create table materials (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  name text not null,
  unit text not null,
  default_reorder_level numeric not null default 0,
  barcode_code text,
  created_at timestamptz default now()
);

create table inventory (
  id bigserial primary key,
  site_id bigint references sites(id) on delete cascade not null,
  material_id bigint references materials(id) on delete cascade not null,
  quantity numeric not null default 0,
  reorder_level numeric not null default 0,
  max_capacity numeric,
  updated_at timestamptz default now(),
  unique (site_id, material_id)
);

create table inventory_transactions (
  id bigserial primary key,
  site_id bigint references sites(id) not null,
  material_id bigint references materials(id) not null,
  user_id bigint references users(id) not null,
  type text not null check (type in ('IN', 'OUT', 'TRANSFER_IN', 'TRANSFER_OUT')),
  quantity numeric not null,
  related_site_id bigint references sites(id),
  scanned_barcode text,
  reference text,
  date timestamptz default now()
);

comment on table inventory_transactions is
  'A cross-site transfer is written as a matched pair: TRANSFER_OUT at the
   source site and TRANSFER_IN at the destination site, each rows
   related_site_id pointing at the other site.';

-- ---------------------------------------------------------------------
-- 5. EQUIPMENT & LABOR
-- ---------------------------------------------------------------------

create table equipment (
  id bigserial primary key,
  site_id bigint references sites(id) on delete cascade not null,
  name text not null,
  type text,
  status text not null default 'active' check (status in ('active', 'idle', 'maintenance')),
  allocated_to_task_id bigint references tasks(id),
  hours_used numeric not null default 0,
  idle_since timestamptz,
  created_at timestamptz default now()
);

comment on table equipment is
  'site_id is mutable — a PM reassigning equipment between their sites is
   simply an UPDATE of this column. idle_since drives the background
   workers idle > 48h alert check.';

create table equipment_logs (
  id bigserial primary key,
  equipment_id bigint references equipment(id) on delete cascade not null,
  logged_by bigint references users(id) not null,
  hours numeric not null,
  log_date date not null default current_date,
  created_at timestamptz default now()
);

create table labor_logs (
  id bigserial primary key,
  site_id bigint references sites(id) not null,
  task_id bigint references tasks(id),
  logged_by bigint references users(id) not null,
  labor_count integer not null,
  log_date date not null default current_date,
  notes text,
  created_at timestamptz default now()
);

comment on table labor_logs is
  'Covers PS-01s contractor/labor tracking requirement at the headcount
   level, separate from individual login accounts.';

-- ---------------------------------------------------------------------
-- 6. VENDORS
-- ---------------------------------------------------------------------

create table vendors (
  id bigserial primary key,
  company_id bigint references companies(id) on delete cascade not null,
  name text not null,
  contact_phone text,
  contact_email text,
  category text,
  rating numeric check (rating between 0 and 5),
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------------
-- 7. PROCUREMENT — TWO-STEP APPROVAL WORKFLOW
-- ---------------------------------------------------------------------

create table material_requests (
  id bigserial primary key,
  site_id bigint references sites(id) not null,
  project_id bigint references projects(id),
  material_id bigint references materials(id) not null,
  quantity numeric not null,
  requested_by bigint references users(id) not null,
  justification text,

  pm_status text not null default 'pending' check (pm_status in ('pending', 'approved', 'rejected')),
  pm_reviewed_by bigint references users(id),
  pm_reviewed_at timestamptz,

  finance_status text not null default 'not_applicable' check (finance_status in ('not_applicable', 'pending', 'approved', 'rejected')),
  finance_reviewed_by bigint references users(id),
  finance_reviewed_at timestamptz,

  created_at timestamptz default now()
);

comment on table material_requests is
  'Two independent status fields. PM answers is this needed (pm_status).
   Finance answers can we pay for it (finance_status), only starts at
   pending once pm_status = approved.';

create table vendor_quotes (
  id bigserial primary key,
  request_id bigint references material_requests(id) not null,
  vendor_id bigint references vendors(id) not null,
  unit_price numeric not null,
  delivery_days integer,
  total_price numeric not null,
  is_selected boolean not null default false,
  created_at timestamptz default now()
);

create table purchase_orders (
  id bigserial primary key,
  request_id bigint references material_requests(id) not null,
  vendor_quote_id bigint references vendor_quotes(id) not null,
  vendor_id bigint references vendors(id) not null,
  quantity numeric not null,
  unit_price numeric not null,
  amount numeric not null,
  status text not null default 'pending_finance' check (status in ('pending_finance', 'approved', 'rejected', 'delivered', 'completed', 'cancelled')),
  approved_by bigint references users(id),
  approved_at timestamptz,
  order_date timestamptz default now()
);

create table deliveries (
  id bigserial primary key,
  po_id bigint references purchase_orders(id) not null,
  quantity numeric not null,
  delivery_date timestamptz,
  status text not null default 'pending' check (status in ('pending', 'delivered', 'delayed')),
  confirmed_by bigint references users(id)
);

create table payments (
  id bigserial primary key,
  po_id bigint references purchase_orders(id) not null,
  amount numeric not null,
  status text not null default 'scheduled' check (status in ('scheduled', 'released')),
  released_by bigint references users(id),
  released_at timestamptz,
  created_at timestamptz default now()
);

comment on table payments is
  'Finances release payment once delivery is confirmed step.';

-- ---------------------------------------------------------------------
-- 8. FINANCE — EXPENSES
-- ---------------------------------------------------------------------

create table expenses (
  id bigserial primary key,
  site_id bigint references sites(id) not null,
  project_id bigint references projects(id),
  category text not null check (category in ('material', 'labor', 'equipment', 'misc')),
  amount numeric not null,
  description text,
  recorded_by bigint references users(id) not null,
  date date default current_date,
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------------
-- 9. AGENTIC AI — ALERTS & NOTIFICATIONS
-- ---------------------------------------------------------------------

create table alerts (
  id bigserial primary key,
  site_id bigint references sites(id) not null,
  project_id bigint references projects(id),
  type text not null check (type in ('stock', 'equipment', 'budget', 'task', 'fraud')),
  severity text not null check (severity in ('info', 'warning', 'critical')),
  title text not null,
  description text,
  source_table text,
  source_id bigint,
  status text not null default 'open' check (status in ('open', 'approved', 'resolved', 'dismissed', 'snoozed')),
  resolved_by bigint references users(id),
  resolved_at timestamptz,
  created_at timestamptz default now()
);

comment on table alerts is
  'The table the Agentic AI Core requirement in PS-01 hangs off of.
   source_table + source_id give every alert a real link back to the record
   that caused it, satisfying the Human Control requirement.';

create table notifications (
  id bigserial primary key,
  user_id bigint references users(id) not null,
  alert_id bigint references alerts(id),
  related_entity_type text,
  related_entity_id bigint,
  title text not null,
  message text,
  is_read boolean not null default false,
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------------
-- 10. AUDIT LOG
-- ---------------------------------------------------------------------

create table audit_log (
  id bigserial primary key,
  user_id bigint references users(id),
  action text not null,
  entity_type text,
  entity_id bigint,
  metadata jsonb,
  created_at timestamptz default now()
);

comment on table audit_log is
  'What Admins audit-log page reads from — who approved or rejected
   what, across the whole company.';

-- ---------------------------------------------------------------------
-- 11. RAG — DOCUMENT CHUNKS
-- ---------------------------------------------------------------------

create table document_chunks (
  id bigserial primary key,
  company_id bigint references companies(id),
  content text not null,
  embedding vector(1536),
  source_table text not null,
  record_id bigint not null,
  site_id bigint references sites(id),
  material_id bigint references materials(id),
  vendor_id bigint references vendors(id),
  date date,
  created_at timestamptz default now()
);

create index on document_chunks using ivfflat (embedding vector_cosine_ops);

create or replace function match_document_chunks(
  query_embedding vector(1536),
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

-- ---------------------------------------------------------------------
-- 12. STATIC CHATBOT — MESSAGE HISTORY
-- ---------------------------------------------------------------------

create table chat_messages (
  id bigserial primary key,
  user_id bigint references users(id) not null,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------------
-- 13. CONVENIENCE VIEW — SITE-LEVEL BUDGET ROLLUP
-- ---------------------------------------------------------------------

create or replace view site_budget_summary as
select
  s.id as site_id,
  s.name as site_name,
  coalesce(sum(p.budget_allocated), 0) as allocated,
  coalesce((
    select sum(e.amount) from expenses e where e.site_id = s.id
  ), 0) as spent
from sites s
left join projects p on p.site_id = s.id
group by s.id, s.name;
