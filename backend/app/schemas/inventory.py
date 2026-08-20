from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class InventorySchema(BaseModel):
    id: int
    site_id: int
    site_name: Optional[str]
    material_id: int
    material_name: str
    unit: str
    quantity: float
    reorder_level: float
    updated_at: Optional[datetime]

class InventoryTransactionSchema(BaseModel):
    id: int
    type: str
    material_name: str
    unit: str
    quantity: float
    performed_by_name: str
    note: Optional[str]
    created_at: datetime

class TransactionCreateSchema(BaseModel):
    site_id: int
    material_id: int
    type: str
    quantity: float
    reference: Optional[str] = None

class TransferCreateSchema(BaseModel):
    source_site_id: int
    destination_site_id: int
    material_id: int
    quantity: float
    reference: Optional[str] = None
