from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class AlertSchema(BaseModel):
    id: int
    site_id: int
    site_name: str
    project_id: Optional[int]
    type: str
    severity: str
    title: str
    description: Optional[str]
    status: str
    created_at: datetime

class PendingRequestSchema(BaseModel):
    id: int
    material_name: str
    quantity: float
    unit: str
    site_name: str
    pm_status: str
    finance_status: str
    created_at: datetime

class PendingPOSchema(BaseModel):
    id: int
    vendor_name: str
    material_name: str
    amount: float
    status: str

class EquipmentStatusSchema(BaseModel):
    active: int
    idle: int
    maintenance: int

class DashboardSummary(BaseModel):
    active_sites: int
    total_sites: int
    open_alerts: int
    critical_alerts: int
    pending_requests: int
    pending_pos: int
    pending_po_amount: float
    low_stock_items: int
    total_users: int
    active_users: int
    recent_alerts: List[AlertSchema]
    total_budget: float
    total_spend: float
    scheduled_payments: float
    pending_requests_list: List[PendingRequestSchema]
    pending_pos_list: List[PendingPOSchema]
    equipment_status: EquipmentStatusSchema
