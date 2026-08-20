import abc
from app.models.user import User
from app.models.alert import Notification, Alert
from sqlalchemy.orm import Session

class NotificationChannel(abc.ABC):
    @abc.abstractmethod
    def send(self, db: Session, user: User, notification: Notification, alert: Alert):
        """Send the notification to the user."""
        pass
