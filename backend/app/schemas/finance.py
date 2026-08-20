from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class PaymentSchema(BaseModel):
    id: int
    po_id: int
    amount: float
    status: str
    vendor_name: str
    material_name: str
    released_by_name: Optional[str]
    released_at: Optional[datetime]
    created_at: datetime

class PurchaseOrderSchema(BaseModel):
    id: int
    vendor_name: str
    material_name: str
    amount: float
    status: str
    approved_by_name: Optional[str]
    delivered_at: Optional[datetime]
    payments: List[PaymentSchema] = []

class FinanceSummarySchema(BaseModel):
    total_budget: float
    total_spent: float
    pending_payments: float
    recent_transactions: List[dict] = []
    sites_budget: List[dict] = []

