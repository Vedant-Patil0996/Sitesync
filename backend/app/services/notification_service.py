"""
Notification service: after an AI run completes, parse the FINAL_REPORT
and insert Alerts + role-based Notifications into the database.
"""
import re
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.alert import Alert, Notification
from app.models.user import User
from app.services.notifications.dispatcher import dispatcher


# Role → which severity alerts they receive
ROLE_NOTIFICATION_RULES = {
    "admin":      ["critical", "warning", "info"],
    "pm":         ["critical", "warning"],
    "finance":    ["critical", "warning"],
    "contractor": ["critical"],
}

# Scenario type → alert type tag
SCENARIO_ALERT_TYPE = {
    "equipment_critical_failure": "equipment",
    "stock_critically_low":       "stock",
    "budget_overrun":             "budget",
    "task_delay_cascade":         "task",
    "vendor_price_spike":         "budget",
    "multi_site_cascade":         "equipment",
    "safety_violation":           "safety",
}


def _infer_severity(report: str, scenario_id: Optional[str]) -> str:
    """Heuristically determine severity from report text."""
    report_lower = report.lower()
    if any(w in report_lower for w in ["critical", "safety hazard", "immediate", "emergency", "halt operations"]):
        return "critical"
    if any(w in report_lower for w in ["warning", "overrun", "delay", "spike", "exceeded", "threshold"]):
        return "warning"
    return "info"


def _extract_title(report: str, scenario_id: Optional[str]) -> str:
    """Extract a short title from the report's first heading or line."""
    for line in report.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()[:120]
        if line.startswith("## "):
            return line[3:].strip()[:120]
    # Fallback: use scenario id
    return (scenario_id or "AI Investigation").replace("_", " ").title()


def _extract_summary(report: str) -> str:
    """Get a 2-3 sentence summary from the beginning of the report body."""
    lines = [l.strip() for l in report.splitlines() if l.strip() and not l.startswith("#")]
    summary_lines = []
    for line in lines[:10]:
        # Skip table separators
        if line.startswith("|") or line.startswith("-"):
            continue
        summary_lines.append(line)
        if len(summary_lines) >= 3:
            break
    return " ".join(summary_lines)[:500]


def create_alert_and_notify(
    db: Session,
    site_id: int,
    report: str,
    scenario_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Alert:
    """
    1. Insert an Alert row for this AI finding.
    2. Insert a Notification row for every user at the site whose role
       matches the alert severity.
    Returns the created Alert.
    """
    severity = _infer_severity(report, scenario_id)
    title = _extract_title(report, scenario_id)
    summary = _extract_summary(report)
    alert_type = SCENARIO_ALERT_TYPE.get(scenario_id or "", "equipment")

    # Create Alert
    alert = Alert(
        site_id=site_id,
        type=alert_type,
        severity=severity,
        title=f"AI Investigation: {title}",
        description=summary,
        source_table="ai_runs",
        status="open",
    )
    db.add(alert)
    db.flush()  # get alert.id without full commit

    # Find all users at this site's company (all users for now — scoped by company via site)
    # We join through site → company to get all company users
    from app.models.site import Site  # avoid circular import at module level
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        db.commit()
        return alert

    users = db.query(User).filter(
        User.company_id == site.company_id,
        User.is_active == True
    ).all()

    allowed_severities = ROLE_NOTIFICATION_RULES
    notif_count = 0

    notifications_created = []

    for user in users:
        role_rules = allowed_severities.get(user.role, [])
        if severity in role_rules:
            notif = Notification(
                user_id=user.id,
                alert_id=alert.id,
                related_entity_type="ai_run",
                title=f"🤖 AI Alert [{severity.upper()}]: {title[:80]}",
                message=summary[:300],
                status="created",
            )
            db.add(notif)
            notifications_created.append((user, notif))
            notif_count += 1

    db.commit()
    
    # After commit, dispatch them to channels
    for user, notif in notifications_created:
        dispatcher.dispatch(db, user, notif, alert)

    print(f"[NotificationService] Created alert #{alert.id} ({severity}) → {notif_count} notifications sent", flush=True)
    return alert
