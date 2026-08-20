from sqlalchemy import (
    Column, BigInteger, Text, Numeric, DateTime, Date, ForeignKey, func, UniqueConstraint
)
from app.db.session import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    unit = Column(Text, nullable=False)
    default_reorder_level = Column(Numeric, nullable=False, default=0)
    barcode_code = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(BigInteger, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(BigInteger, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric, nullable=False, default=0)
    reorder_level = Column(Numeric, nullable=False, default=0)
    max_capacity = Column(Numeric)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("site_id", "material_id"),)


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(BigInteger, ForeignKey("sites.id"), nullable=False)
    material_id = Column(BigInteger, ForeignKey("materials.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    type = Column(Text, nullable=False)  # IN | OUT | TRANSFER_IN | TRANSFER_OUT
    quantity = Column(Numeric, nullable=False)
    related_site_id = Column(BigInteger, ForeignKey("sites.id"))
    scanned_barcode = Column(Text)
    reference = Column(Text)
    date = Column(DateTime(timezone=True), server_default=func.now())
