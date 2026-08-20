from sqlalchemy import Column, BigInteger, Text, Numeric, Boolean, DateTime, Date, Integer, ForeignKey, func
from app.db.session import Base


class MaterialRequest(Base):
    __tablename__ = "material_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(BigInteger, ForeignKey("sites.id"), nullable=False)
    project_id = Column(BigInteger, ForeignKey("projects.id"))
    material_id = Column(BigInteger, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Numeric, nullable=False)
    requested_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    justification = Column(Text)

    priority = Column(Text, nullable=False, default="normal")  # low | normal | high | urgent
    required_date = Column(Date)
    estimated_unit_cost = Column(Numeric)
    total_estimated_cost = Column(Numeric)
    attachment_url = Column(Text)

    pm_status = Column(Text, nullable=False, default="pending")  # pending | approved | rejected
    pm_reviewed_by = Column(BigInteger, ForeignKey("users.id"))
    pm_reviewed_at = Column(DateTime(timezone=True))
    pm_notes = Column(Text)

    finance_status = Column(Text, nullable=False, default="not_applicable")  # not_applicable | pending | approved | rejected
    finance_reviewed_by = Column(BigInteger, ForeignKey("users.id"))
    finance_reviewed_at = Column(DateTime(timezone=True))
    finance_notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VendorQuote(Base):
    __tablename__ = "vendor_quotes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(BigInteger, ForeignKey("material_requests.id"), nullable=False)
    vendor_id = Column(BigInteger, ForeignKey("vendors.id"), nullable=False)
    unit_price = Column(Numeric, nullable=False)
    delivery_days = Column(Integer)
    total_price = Column(Numeric, nullable=False)
    is_selected = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(BigInteger, ForeignKey("material_requests.id"), nullable=False)
    vendor_quote_id = Column(BigInteger, ForeignKey("vendor_quotes.id"), nullable=False)
    vendor_id = Column(BigInteger, ForeignKey("vendors.id"), nullable=False)
    quantity = Column(Numeric, nullable=False)
    unit_price = Column(Numeric, nullable=False)
    amount = Column(Numeric, nullable=False)
    status = Column(Text, nullable=False, default="pending_finance")
    # pending_finance | approved | rejected | delivered | completed | cancelled
    approved_by = Column(BigInteger, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    order_date = Column(DateTime(timezone=True), server_default=func.now())


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    po_id = Column(BigInteger, ForeignKey("purchase_orders.id"), nullable=False)
    quantity = Column(Numeric, nullable=False)
    delivery_date = Column(DateTime(timezone=True))
    status = Column(Text, nullable=False, default="pending")  # pending | delivered | delayed
    confirmed_by = Column(BigInteger, ForeignKey("users.id"))
