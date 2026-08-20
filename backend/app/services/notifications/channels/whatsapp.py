from sqlalchemy.orm import Session
from app.models.user import User
from app.models.alert import Notification, Alert
from app.services.notifications.base import NotificationChannel

class WhatsAppChannel(NotificationChannel):
    def send(self, db: Session, user: User, notification: Notification, alert: Alert):
        # Stub for WhatsApp delivery
        if not user.phone:
            print(f"[WhatsApp] User {user.id} has no phone number, skipping.", flush=True)
            return

        print(f"[WhatsApp] Mock dispatch -> {user.phone} | Alert: {alert.title} | {notification.message[:100]}", flush=True)
        # TODO: integrate with Meta/Twilio WhatsApp API
