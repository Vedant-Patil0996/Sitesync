from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date

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
    priority: str = "normal"
    required_date: Optional[date] = None
    estimated_unit_cost: Optional[float] = None
    total_estimated_cost: Optional[float] = None
    attachment_url: Optional[str] = None
    justification: Optional[str] = None
    pm_status: str
    pm_reviewed_by_name: Optional[str]
    pm_notes: Optional[str] = None
    finance_status: str
    finance_reviewed_by_name: Optional[str]
    finance_notes: Optional[str] = None
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
    material_id: int
    quantity: float
    site_id: int
    priority: Optional[str] = "normal"
    required_date: Optional[str] = None
    estimated_unit_cost: Optional[float] = None
    attachment_url: Optional[str] = None
    justification: Optional[str] = None
