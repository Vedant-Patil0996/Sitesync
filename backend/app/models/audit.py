from sqlalchemy import Column, BigInteger, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    action = Column(Text, nullable=False)       # e.g. material_request.approved
    entity_type = Column(Text)                  # e.g. material_request
    entity_id = Column(BigInteger)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
