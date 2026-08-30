from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.alert import Notification
from app.schemas.alert import NotificationSchema
from typing import List
from datetime import datetime, timezone
import asyncio
from fastapi.responses import StreamingResponse
from app.events.manager import event_manager

router = APIRouter()

@router.get("/", response_model=List[NotificationSchema])
async def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notifs = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).all()
    return [NotificationSchema(
        id=n.id, user_id=n.user_id, alert_id=n.alert_id, related_entity_type=n.related_entity_type,
        related_entity_id=n.related_entity_id, title=n.title, message=n.message,
        status=n.status, read_at=n.read_at, delivered_at=n.delivered_at, failed_at=n.failed_at, created_at=n.created_at
    ) for n in notifs]

@router.patch("/{notification_id}/read")
async def mark_read(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notif = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if notif and not notif.read_at:
        notif.read_at = datetime.now(timezone.utc)
        db.commit()
    return {"status": "success"}

@router.patch("/mark-all-read")
async def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Notification).filter(Notification.user_id == current_user.id, Notification.read_at == None).update({"read_at": datetime.now(timezone.utc)})
    db.commit()
    return {"status": "success"}

@router.get("/stream")
async def notification_stream(current_user: User = Depends(get_current_user)):
    """Server-Sent Events (SSE) stream for real-time in-app notifications."""
    async def event_generator():
        q = event_manager.subscribe(f"user_{current_user.id}")
        try:
            while True:
                event = await q.get()
                import json
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_manager.unsubscribe(f"user_{current_user.id}", q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
