from sqlalchemy import Column, BigInteger, Text, Numeric, DateTime, ForeignKey, func, UniqueConstraint
from app.db.session import Base


class Site(Base):
    __tablename__ = "sites"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    location = Column(Text)
    latitude = Column(Numeric)
    longitude = Column(Numeric)
    status = Column(Text, nullable=False, default="active")  # active | on_hold | completed
    created_by = Column(BigInteger, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SiteAssignment(Base):
    __tablename__ = "site_assignments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(BigInteger, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_role = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("site_id", "user_id"),)
