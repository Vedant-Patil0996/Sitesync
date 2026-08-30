from typing import List
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.alert import Notification, Alert
from app.services.notifications.channels.in_app import InAppChannel
from app.services.notifications.channels.whatsapp import WhatsAppChannel
from app.services.notifications.channels.sms import SMSChannel

class NotificationDispatcher:
    def __init__(self):
        # Instantiate available channels
        self.channels = {
            "in_app": InAppChannel(),
            "whatsapp": WhatsAppChannel(),
            "sms": SMSChannel(),
        }

    def dispatch(self, db: Session, user: User, notification: Notification, alert: Alert):
        """
        Takes a fully persisted Notification + Alert, evaluates user preferences,
        and pushes to the appropriate delivery channels.
        """
        # For now, we simulate user preferences by just using all channels.
        # In a future iteration, we would check user.notification_preferences here.
        selected_channels = ["in_app", "whatsapp", "sms"]

        for channel_name in selected_channels:
            channel = self.channels.get(channel_name)
            if channel:
                try:
                    channel.send(db, user, notification, alert)
                except Exception as e:
                    print(f"[Dispatcher] Error sending {channel_name} to {user.id}: {e}", flush=True)

# Singleton dispatcher
dispatcher = NotificationDispatcher()
