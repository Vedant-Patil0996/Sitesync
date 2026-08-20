from sqlalchemy import Column, BigInteger, Text, Boolean, DateTime, ForeignKey, func
from app.db.session import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(BigInteger, ForeignKey("sites.id"), nullable=False)
    project_id = Column(BigInteger, ForeignKey("projects.id"))
    type = Column(Text, nullable=False)       # stock | equipment | budget | task | fraud | weather
    severity = Column(Text, nullable=False)   # info | warning | critical
    title = Column(Text, nullable=False)
    description = Column(Text)
    source_table = Column(Text)               # links back to the record that caused this
    source_id = Column(BigInteger)
    status = Column(Text, nullable=False, default="open")  # open | approved | dismissed | snoozed
    resolved_by = Column(BigInteger, ForeignKey("users.id"))
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    alert_id = Column(BigInteger, ForeignKey("alerts.id"))
    related_entity_type = Column(Text)
    related_entity_id = Column(BigInteger)
    title = Column(Text, nullable=False)
    message = Column(Text)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
