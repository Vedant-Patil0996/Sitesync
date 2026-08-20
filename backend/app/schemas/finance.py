from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date

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
    quantity: Optional[float] = None
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
    committed_costs: float = 0

class ExpenseCreateSchema(BaseModel):
    site_id: int
    project_id: Optional[int] = None
    category: str
    amount: float
    description: Optional[str] = None

class PaymentCreateSchema(BaseModel):
    po_id: int
    amount: float

class ExpenseSchema(BaseModel):
    id: int
    site_id: int
    project_id: Optional[int]
    category: str
    amount: float
    description: Optional[str]
    recorded_by: int
    date: Optional[date]
    created_at: datetime

class DeliveryConfirmSchema(BaseModel):
    quantity: float

