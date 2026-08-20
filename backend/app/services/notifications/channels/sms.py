from sqlalchemy.orm import Session
from app.models.user import User
from app.models.alert import Notification, Alert
from app.services.notifications.base import NotificationChannel

class SMSChannel(NotificationChannel):
    def send(self, db: Session, user: User, notification: Notification, alert: Alert):
        # Stub for SMS delivery
        if not user.phone:
            print(f"[SMS] User {user.id} has no phone number, skipping.", flush=True)
            return

        print(f"[SMS] Mock dispatch -> {user.phone} | Alert: {alert.title}", flush=True)
        # TODO: integrate with Twilio/SNS SMS API
