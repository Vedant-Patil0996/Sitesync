from sqlalchemy import (
    Column, BigInteger, Text, Numeric, DateTime, Date, ForeignKey, func, UniqueConstraint
)
from app.db.session import Base
import uuid
from datetime import datetime, timezone


def generate_batch_code():
    """Generate a human-readable batch code like BAT-2026-00182."""
    import random
    return f"BAT-{datetime.now(timezone.utc).year}-{random.randint(10000,99999)}"


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


class MaterialBatch(Base):
    """Digital passport for a physical material batch."""
    __tablename__ = "material_batches"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    batch_code = Column(Text, nullable=False, unique=True)  # e.g. BAT-2026-00182
    material_id = Column(BigInteger, ForeignKey("materials.id"), nullable=False)
    site_id = Column(BigInteger, ForeignKey("sites.id"), nullable=False)  # current owning site
    supplier_id = Column(BigInteger, ForeignKey("vendors.id"))  # nullable
    original_qty = Column(Numeric, nullable=False)
    current_qty = Column(Numeric, nullable=False)
    unit = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="RECEIVED")
    # RECEIVED | IN_STOCK | PARTIALLY_CONSUMED | TRANSFER_PENDING | TRANSFERRED | DEPLETED | DAMAGED | RETURNED
    received_by = Column(BigInteger, ForeignKey("users.id"))
    received_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DeliveryDiscrepancy(Base):
    """Recorded when actual received qty differs from expected."""
    __tablename__ = "delivery_discrepancies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    batch_id = Column(BigInteger, ForeignKey("material_batches.id"), nullable=False)
    expected_qty = Column(Numeric, nullable=False)
    actual_qty = Column(Numeric, nullable=False)
    difference = Column(Numeric, nullable=False)
    reported_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    site_id = Column(BigInteger, ForeignKey("sites.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(BigInteger, ForeignKey("sites.id"), nullable=False)
    material_id = Column(BigInteger, ForeignKey("materials.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    type = Column(Text, nullable=False)  # IN | OUT | TRANSFER_IN | TRANSFER_OUT
    action = Column(Text)  # RECEIVE | CONSUME | TRANSFER | DAMAGE | RETURN | ADJUSTMENT
    quantity = Column(Numeric, nullable=False)
    related_site_id = Column(BigInteger, ForeignKey("sites.id"))
    batch_id = Column(BigInteger, ForeignKey("material_batches.id"))
    scanned_barcode = Column(Text)
    reference = Column(Text)
    reason = Column(Text)
    date = Column(DateTime(timezone=True), server_default=func.now())
