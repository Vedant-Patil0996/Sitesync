-- Apply once to an existing SiteSync database.
-- Project writes are additionally enforced by backend role/site authorization.

alter table projects drop constraint if exists projects_status_check;
alter table projects add constraint projects_status_check check (status in ('planning', 'in_progress', 'on_hold', 'completed', 'archived'));
do $$ begin
	if not exists (select 1 from pg_constraint where conname = 'projects_budget_nonnegative') then
		alter table projects add constraint projects_budget_nonnegative check (budget_allocated >= 0);
	end if;
	if not exists (select 1 from pg_constraint where conname = 'projects_progress_range') then
		alter table projects add constraint projects_progress_range check (progress_percent >= 0 and progress_percent <= 100);
	end if;
end $$;

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

alter table tasks add column if not exists progress_percent numeric not null default 0;
alter table tasks add column if not exists priority text not null default 'medium';
do $$ begin
	if not exists (select 1 from pg_constraint where conname = 'tasks_progress_range') then
		alter table tasks add constraint tasks_progress_range check (progress_percent >= 0 and progress_percent <= 100);
	end if;
	if not exists (select 1 from pg_constraint where conname = 'tasks_priority_valid') then
		alter table tasks add constraint tasks_priority_valid check (priority in ('low', 'medium', 'high', 'critical'));
	end if;
end $$;
