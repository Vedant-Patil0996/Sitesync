from typing import Optional
from pydantic import BaseModel

class EquipmentSchema(BaseModel):
    id: int
    name: str
    type: Optional[str]
    site_id: int
    site_name: Optional[str]
    allocated_to_task_id: Optional[int]
    task_name: Optional[str]
    hours_used: float
    status: str

class EquipmentStatusSchema(BaseModel):
    status: str

class EquipmentLogSchema(BaseModel):
    hours: float

class EquipmentAllocationSchema(BaseModel):
    task_id: Optional[int] = None
