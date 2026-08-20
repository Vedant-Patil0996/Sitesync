from sqlalchemy import Column, BigInteger, Text, Numeric, DateTime, Date, ForeignKey, func
from app.db.session import Base


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(BigInteger, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    type = Column(Text)
    status = Column(Text, nullable=False, default="active")  # active | idle | maintenance
    allocated_to_task_id = Column(BigInteger, ForeignKey("tasks.id"))
    hours_used = Column(Numeric, nullable=False, default=0)
    idle_since = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EquipmentLog(Base):
    __tablename__ = "equipment_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    equipment_id = Column(BigInteger, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False)
    logged_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    hours = Column(Numeric, nullable=False)
    log_date = Column(Date, nullable=False, server_default=func.current_date())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LaborLog(Base):
    __tablename__ = "labor_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(BigInteger, ForeignKey("sites.id"), nullable=False)
    task_id = Column(BigInteger, ForeignKey("tasks.id"))
    logged_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    labor_count = Column(BigInteger, nullable=False)
    log_date = Column(Date, nullable=False, server_default=func.current_date())
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
