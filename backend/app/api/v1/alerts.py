from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
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
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.status = "resolved"
        alert.resolved_by = current_user.id
        alert.resolved_at = func.now()
        db.commit()
    return {"status": "success"}

@router.patch("/{alert_id}/snooze")
async def snooze_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "finance"))):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.status = "snoozed"
        db.commit()
    return {"status": "success"}

@router.patch("/{alert_id}/dismiss")
async def dismiss_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "finance"))):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.status = "dismissed"
        db.commit()
    return {"status": "success"}
