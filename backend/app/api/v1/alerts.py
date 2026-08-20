from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.deps import get_current_user, require_role, audit
from app.models.user import User
from app.models.alert import Alert
from app.models.site import Site
from app.schemas.common import PaginatedResponse
from app.schemas.alert import AlertSchema

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[AlertSchema])
async def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role("admin", "pm", "finance"))
):
    query = db.query(Alert, Site, User)\
        .join(Site, Alert.site_id == Site.id)\
        .outerjoin(User, Alert.resolved_by == User.id)\
        .filter(Site.company_id == current_user.company_id)\
        .order_by(Alert.created_at.desc())
        
    total = query.count()
    alerts_db = query.offset(skip).limit(limit).all()
    
    items = []
    for alert, site, resolver in alerts_db:
        items.append(AlertSchema(
            id=alert.id,
            site_id=alert.site_id,
            site_name=site.name,
            type=alert.type,
            severity=alert.severity,
            title=alert.title,
            description=alert.description,
            source_table=alert.source_table,
            source_id=alert.source_id,
            status=alert.status,
            resolved_by_name=resolver.name if resolver else None,
            resolved_at=alert.resolved_at,
            created_at=alert.created_at
        ))
        
    return PaginatedResponse[AlertSchema](
        items=items,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.patch("/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "finance"))):
    alert = db.query(Alert).join(Site, Alert.site_id == Site.id).filter(Alert.id == alert_id, Site.company_id == current_user.company_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "resolved"
    alert.resolved_by = current_user.id
    alert.resolved_at = func.now()
    audit(db, current_user, "alert.resolved", "alert", alert.id)
    db.commit()
    return {"status": "resolved"}

@router.patch("/{alert_id}/snooze")
async def snooze_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "finance"))):
    alert = db.query(Alert).join(Site, Alert.site_id == Site.id).filter(Alert.id == alert_id, Site.company_id == current_user.company_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "snoozed"
    audit(db, current_user, "alert.snoozed", "alert", alert.id)
    db.commit()
    return {"status": "snoozed"}

@router.patch("/{alert_id}/dismiss")
async def dismiss_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "finance"))):
    alert = db.query(Alert).join(Site, Alert.site_id == Site.id).filter(Alert.id == alert_id, Site.company_id == current_user.company_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "dismissed"
    audit(db, current_user, "alert.dismissed", "alert", alert.id)
    db.commit()
    return {"status": "dismissed"}
