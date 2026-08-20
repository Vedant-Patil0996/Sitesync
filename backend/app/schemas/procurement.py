from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class VendorQuoteSchema(BaseModel):
    id: int
    vendor_name: str
    unit_price: float
    total_price: float
    delivery_days: Optional[int]
    is_selected: bool

class MaterialRequestSchema(BaseModel):
    id: int
    material_name: str
    quantity: float
    unit: str
    site_name: str
    requested_by_name: str
    created_at: datetime
    pm_status: str
    pm_reviewed_by_name: Optional[str]
    finance_status: str
    finance_reviewed_by_name: Optional[str]
    quotes: List[VendorQuoteSchema] = []
    po_status: Optional[str] = None

class ProcurementQuoteViewSchema(BaseModel):
    request_id: int
    material_name: str
    quantity: float
    unit: str
    site_name: str
    requested_by_name: str
    quotes: List[VendorQuoteSchema]

class MaterialRequestCreateSchema(BaseModel):
    site_id: int
    project_id: Optional[int] = None
    material_id: int
    quantity: float
    justification: Optional[str] = None

class ReviewSchema(BaseModel):
    approved: bool
    reason: Optional[str] = None

class VendorQuoteCreateSchema(BaseModel):
    request_id: int
    vendor_id: int
    unit_price: float
    delivery_days: Optional[int] = None
    total_price: float

class PurchaseOrderCreateSchema(BaseModel):
    request_id: int
    quote_id: int
