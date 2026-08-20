from sqlalchemy import Column, BigInteger, Text, Numeric, DateTime, ForeignKey, func
from app.db.session import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    contact_phone = Column(Text)
    contact_email = Column(Text)
    category = Column(Text)
    rating = Column(Numeric)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
