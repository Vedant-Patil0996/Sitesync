from sqlalchemy import Column, BigInteger, Text, Numeric, Boolean, DateTime, Date, ForeignKey, func
from app.db.session import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    po_id = Column(BigInteger, ForeignKey("purchase_orders.id"), nullable=False)
    amount = Column(Numeric, nullable=False)
    status = Column(Text, nullable=False, default="scheduled")  # scheduled | released
    released_by = Column(BigInteger, ForeignKey("users.id"))
    released_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(BigInteger, ForeignKey("sites.id"), nullable=False)
    project_id = Column(BigInteger, ForeignKey("projects.id"))
    category = Column(Text, nullable=False)  # material | labor | equipment | misc
    amount = Column(Numeric, nullable=False)
    description = Column(Text)
    recorded_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    date = Column(Date, server_default=func.current_date())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
