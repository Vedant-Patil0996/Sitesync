"""
Schedule Monitor Service
========================
Runs as a background cron job (every 30 min via APScheduler).

Responsibilities:
  1. Auto-mark tasks as 'delayed' when end_date < today and status is not 'completed'.
  2. Auto-mark milestones as 'missed' when due_date < today and status is 'upcoming'.
  3. Recalculate project.progress_percent from task progress.
  4. Generate an Alert row for each project that has newly detected schedule risk,
     linked to the project source record (source_table='projects', source_id=project.id).
  5. Create role-based Notifications for PM/admin users at the affected site.

No hard-coded dates or calculations — everything is derived from real DB data.
"""

from datetime import date
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.project import Project, Task, Milestone
from app.models.site import Site, SiteAssignment
from app.models.alert import Alert, Notification
from app.models.user import User


def _recalculate_project_progress(db: Session, project: Project) -> float:
    tasks = db.query(Task).filter(Task.project_id == project.id).all()
    if not tasks:
        return float(project.progress_percent)
    avg = sum(float(t.progress_percent or 0) for t in tasks) / len(tasks)
    project.progress_percent = avg
    return avg


def _create_schedule_alert(
    db: Session,
    project: Project,
    site: Site,
    overdue_task_names: list[str],
    missed_milestone_names: list[str],
    at_risk_task_names: list[str],
) -> Alert | None:
    """
    Create a single alert for a project with schedule risk.
    Returns None if no actionable issues found.
    """
    if not overdue_task_names and not missed_milestone_names:
        return None

    parts = []
    if overdue_task_names:
        parts.append(f"Overdue tasks: {', '.join(overdue_task_names[:5])}")
    if missed_milestone_names:
        parts.append(f"Missed milestones: {', '.join(missed_milestone_names[:3])}")
    if at_risk_task_names:
        parts.append(f"At-risk tasks (due within 7 days): {', '.join(at_risk_task_names[:3])}")

    description = " | ".join(parts)

    severity = "critical" if overdue_task_names or missed_milestone_names else "warning"
    title = f"Schedule Risk Detected: {project.name}"

    # Avoid duplicate open alerts for same project
    existing = (
        db.query(Alert)
        .filter(
            Alert.project_id == project.id,
            Alert.type == "task",
            Alert.status == "open",
            Alert.source_table == "projects",
        )
        .first()
    )
    if existing:
        # Update description instead of creating a new alert
        existing.description = description
        existing.severity = severity
        db.flush()
        return existing

    alert = Alert(
        site_id=site.id,
        project_id=project.id,
        type="task",
        severity=severity,
        title=title,
        description=description,
        source_table="projects",
        source_id=project.id,
        status="open",
    )
    db.add(alert)
    db.flush()

    # Notify PM and admin users at this site
    users = (
        db.query(User)
        .join(SiteAssignment, SiteAssignment.user_id == User.id)
        .filter(
            SiteAssignment.site_id == site.id,
            User.is_active == True,
            User.role.in_(["admin", "pm"]),
        )
        .all()
    )

    for user in users:
        notif = Notification(
            user_id=user.id,
            alert_id=alert.id,
            related_entity_type="project",
            related_entity_id=project.id,
            title=f"⚠️ Schedule Alert: {project.name}",
            message=description[:300],
            is_read=False,
        )
        db.add(notif)

    return alert


def run_schedule_check() -> dict:
    """
    Main entry point called by the APScheduler cron.
    Scans all active projects across all companies.
    Returns a summary dict for logging.
    """
    today = date.today()
    db: Session = SessionLocal()
    summary = {
        "tasks_marked_delayed": 0,
        "milestones_marked_missed": 0,
        "projects_at_risk": 0,
        "alerts_created": 0,
    }

    try:
        # Only scan projects that are in_progress and whose start_date has arrived
        active_projects = (
            db.query(Project)
            .filter(Project.status == "in_progress")
            .all()
        )

        for project in active_projects:
            # If project start date is in the future, it hasn't started yet
            if project.start_date and project.start_date > today:
                continue

            site = db.query(Site).filter(Site.id == project.site_id).first()
            if not site:
                continue

            tasks = db.query(Task).filter(Task.project_id == project.id).all()

            overdue_task_names: list[str] = []
            missed_milestone_names: list[str] = []
            at_risk_task_names: list[str] = []

            # ── 1. Auto-mark overdue tasks ──────────────────────────────────
            for task in tasks:
                if (
                    task.end_date
                    and task.end_date < today
                    and task.status not in ("completed",)
                ):
                    if task.status != "delayed":
                        task.status = "delayed"
                        summary["tasks_marked_delayed"] += 1
                    overdue_task_names.append(task.name)

                elif (
                    task.end_date
                    and task.start_date
                    and task.start_date <= today
                    and task.status not in ("completed", "delayed")
                    and (task.end_date - today).days <= 7
                    and float(task.progress_percent or 0) < 50
                ):
                    # At risk: active, due within 7 days and under 50% complete
                    at_risk_task_names.append(task.name)

            # ── 2. Auto-mark missed milestones ──────────────────────────────
            milestones = db.query(Milestone).filter(Milestone.project_id == project.id).all()
            for ms in milestones:
                if ms.due_date and ms.due_date < today and ms.status == "upcoming":
                    ms.status = "missed"
                    summary["milestones_marked_missed"] += 1
                    missed_milestone_names.append(ms.name)

            # ── 3. Recalculate project progress ─────────────────────────────
            _recalculate_project_progress(db, project)

            # ── 4. Create alert if schedule risk detected ───────────────────
            if overdue_task_names or missed_milestone_names or at_risk_task_names:
                summary["projects_at_risk"] += 1
                alert = _create_schedule_alert(
                    db,
                    project,
                    site,
                    overdue_task_names,
                    missed_milestone_names,
                    at_risk_task_names,
                )
                if alert and not hasattr(alert, "_existing"):
                    summary["alerts_created"] += 1

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"[ScheduleMonitor] ERROR: {e}", flush=True)
        raise

    finally:
        db.close()

    print(
        f"[ScheduleMonitor] Scan complete: "
        f"{summary['tasks_marked_delayed']} tasks marked delayed, "
        f"{summary['milestones_marked_missed']} milestones missed, "
        f"{summary['projects_at_risk']} projects at risk, "
        f"{summary['alerts_created']} new alerts.",
        flush=True,
    )
    return summary
