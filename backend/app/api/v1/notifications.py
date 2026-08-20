from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.alert import Notification
from app.schemas.alert import NotificationSchema
from typing import List

router = APIRouter()

@router.get("/", response_model=List[NotificationSchema])
async def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notifs = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).all()
    return [NotificationSchema(
        id=n.id, user_id=n.user_id, alert_id=n.alert_id, related_entity_type=n.related_entity_type,
        related_entity_id=n.related_entity_id, title=n.title, message=n.message,
        is_read=n.is_read, created_at=n.created_at
    ) for n in notifs]

@router.patch("/{notification_id}/read")
async def mark_read(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notif = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"status": "success"}

@router.patch("/mark-all-read")
async def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"status": "success"}
