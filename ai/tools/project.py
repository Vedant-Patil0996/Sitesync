from datetime import date
from typing import Dict, Any, List
from ai.core.config import supabase

def get_task_dependencies(task_id: str) -> List[Dict[str, Any]]:
    """Get the downstream project tasks that depend on the given task."""
    try:
        task_id_int = int(task_id) if str(task_id).isdigit() else None
        if not task_id_int:
            # Fallback if the agent tries to use the name
            resp = supabase.table('tasks').select('*').eq('name', task_id).limit(1).execute()
            if not resp.data:
                 return []
            task_id_int = resp.data[0]['id']

        resp = supabase.table('tasks').select('*').eq('depends_on_task_id', task_id_int).execute()
        results = []
        for t in resp.data:
            results.append({
                "id": t['id'],
                "task_id": t['id'],
                "name": t['name'],
                "start_date": t['start_date'],
                "end_date": t['end_date'],
                "status": t['status'],
                "progress_percent": float(t['progress_percent'] or 0)
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]

def calculate_delay_impact(task_id: str, delayed_days: int) -> Dict[str, Any]:
    """Calculate the operational and financial impact of delaying a task using real DB data."""
    try:
        task_id_int = int(task_id) if str(task_id).isdigit() else None
        task_data = None
        if not task_id_int:
            resp = supabase.table('tasks').select('*').eq('name', task_id).limit(1).execute()
            if not resp.data:
                 return {"error": "Task not found"}
            task_data = resp.data[0]
            task_id_int = task_data['id']
        else:
            resp = supabase.table('tasks').select('*').eq('id', task_id_int).limit(1).execute()
            if resp.data:
                task_data = resp.data[0]

        if not task_data:
            return {"error": "Task not found"}

        deps = get_task_dependencies(str(task_id_int))
        
        # Calculate real slack if possible, or fallback to 1 if no dependent dates exist
        slack = 1
        if task_data.get('end_date') and deps:
            try:
                task_end = date.fromisoformat(task_data['end_date'])
                # Find the earliest start date among dependent tasks
                dep_starts = []
                for d in deps:
                    if d.get('start_date'):
                        dep_starts.append(date.fromisoformat(d['start_date']))
                if dep_starts:
                    min_dep_start = min(dep_starts)
                    gap = (min_dep_start - task_end).days
                    slack = max(0, gap)
            except Exception:
                pass

        net_delay = max(0, delayed_days - slack)
        
        return {
            "task_id": task_id_int,
            "task_name": task_data['name'],
            "days_delayed": delayed_days,
            "calculated_slack_days": slack,
            "critical_path_impact": net_delay > 0,
            "downstream_tasks_affected": [d['name'] for d in deps] if net_delay > 0 else [],
            "estimated_cost_of_delay": net_delay * 5000  # $5k per day penalty
        }
    except Exception as e:
        return {"error": str(e)}

def scan_overdue_tasks(site_id: str) -> List[Dict[str, Any]]:
    """Proactively scans all active projects at a site to find overdue or delayed tasks."""
    try:
        site_id_int = int(site_id) if str(site_id).isdigit() else None
        if not site_id_int:
            return [{"error": "Invalid site_id"}]

        # 1. Fetch projects for this site
        proj_resp = supabase.table('projects').select('id, name').eq('site_id', site_id_int).execute()
        if not proj_resp.data:
            return []

        project_ids = [p['id'] for p in proj_resp.data]
        project_map = {p['id']: p['name'] for p in proj_resp.data}

        # 2. Fetch tasks for these projects
        task_resp = supabase.table('tasks').select('*').in_('project_id', project_ids).execute()
        if not task_resp.data:
            return []

        today = date.today()
        overdue_tasks = []

        for t in task_resp.data:
            days_overdue = 0
            is_overdue = False

            if t.get('end_date') and t.get('status') != 'completed':
                try:
                    end_date = date.fromisoformat(t['end_date'])
                    if end_date < today:
                        days_overdue = (today - end_date).days
                        is_overdue = True
                except Exception:
                    pass

            if is_overdue or t.get('status') == 'delayed':
                # Count children dependents
                dep_count_resp = supabase.table('tasks').select('id', count='exact').eq('depends_on_task_id', t['id']).execute()
                dep_count = dep_count_resp.count if dep_count_resp.count is not None else 0

                overdue_tasks.append({
                    "id": t['id'],
                    "name": t['name'],
                    "project_name": project_map.get(t['project_id'], "Unknown"),
                    "status": t['status'],
                    "end_date": t['end_date'],
                    "days_overdue": days_overdue,
                    "progress_percent": float(t['progress_percent'] or 0),
                    "dependent_tasks_count": dep_count
                })

        return overdue_tasks
    except Exception as e:
        return [{"error": str(e)}]

def get_project_schedule_risk(project_id: str) -> Dict[str, Any]:
    """Retrieves schedule health metrics for a specific project based on tasks, milestones, and dependencies."""
    try:
        project_id_int = int(project_id) if str(project_id).isdigit() else None
        if not project_id_int:
            return {"error": "Invalid project_id"}

        # Fetch project
        proj_resp = supabase.table('projects').select('*').eq('id', project_id_int).limit(1).execute()
        if not proj_resp.data:
            return {"error": "Project not found"}
        project = proj_resp.data[0]

        # Fetch tasks
        tasks_resp = supabase.table('tasks').select('*').eq('project_id', project_id_int).execute()
        tasks = tasks_resp.data or []

        # Fetch milestones
        milestones_resp = supabase.table('milestones').select('*').eq('project_id', project_id_int).execute()
        milestones = milestones_resp.data or []

        today = date.today()
        overdue_task_count = 0
        delayed_task_count = 0
        upcoming_deadline_count = 0
        completed_task_count = 0
        missed_milestone_count = 0

        for t in tasks:
            if t.get('status') == 'completed':
                completed_task_count += 1
                continue

            if t.get('status') == 'delayed':
                delayed_task_count += 1

            if t.get('end_date'):
                try:
                    end_date = date.fromisoformat(t['end_date'])
                    if end_date < today:
                        overdue_task_count += 1
                    elif (end_date - today).days <= 7:
                        upcoming_deadline_count += 1
                except Exception:
                    pass

        for m in milestones:
            if m.get('status') == 'missed':
                missed_milestone_count += 1
            elif m.get('status') == 'upcoming' and m.get('due_date'):
                try:
                    due_date = date.fromisoformat(m['due_date'])
                    if due_date < today:
                        missed_milestone_count += 1
                    elif (due_date - today).days <= 7:
                        upcoming_deadline_count += 1
                except Exception:
                    pass

        # Compute risk level
        if overdue_task_count > 0 or missed_milestone_count > 0:
            risk_level = "critical"
        elif delayed_task_count > 0 or upcoming_deadline_count > 0:
            risk_level = "at_risk"
        else:
            risk_level = "on_track"

        return {
            "project_id": project_id_int,
            "project_name": project['name'],
            "risk_level": risk_level,
            "overdue_tasks": overdue_task_count,
            "delayed_tasks": delayed_task_count,
            "missed_milestones": missed_milestone_count,
            "upcoming_deadlines_7_days": upcoming_deadline_count,
            "total_tasks": len(tasks),
            "completed_tasks": completed_task_count,
            "progress_percent": float(project.get('progress_percent') or 0)
        }
    except Exception as e:
        return {"error": str(e)}
