import asyncio
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.alert import Notification, Alert
from app.services.notifications.base import NotificationChannel
from app.events.manager import event_manager
from datetime import datetime, timezone

class InAppChannel(NotificationChannel):
    def send(self, db: Session, user: User, notification: Notification, alert: Alert):
        # The DB record is already created by NotificationService before dispatcher is called.
        # This channel's job is simply to trigger the real-time WebSocket push.
        
        # Publish event for online users
        payload = {
            "type": "NEW_NOTIFICATION",
            "notification": {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "severity": alert.severity if alert else "info",
                "created_at": notification.created_at.isoformat() if notification.created_at else datetime.now(timezone.utc).isoformat(),
            }
        }
        
        # Publish to user-specific topic, e.g. "user_{user.id}"
        topic = f"user_{user.id}"
        
        # Safely find active main event loop for cross-thread publish
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                loop = asyncio.get_event_loop_policy().get_event_loop()
            except Exception:
                loop = None

        if loop and loop.is_running():
            event_manager.publish_sync(topic, payload, loop)
