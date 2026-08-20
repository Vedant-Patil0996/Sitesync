from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.schemas.project import ProjectSchema
from app.schemas.inventory import InventorySchema
from app.schemas.equipment import EquipmentSchema
from app.schemas.alert import AlertSchema

class SiteSchema(BaseModel):
    id: int
    name: str
    location: Optional[str]
    status: str
    project_count: int
    alert_count: int
    budget: float
    spent: float
    budget_pct: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class SiteContractorSchema(BaseModel):
    id: int
    name: str
    specialty: str
    phone: Optional[str]

class SiteDetailSchema(SiteSchema):
    location_text: Optional[str]
    projects: List[ProjectSchema]
    inventory: List[InventorySchema]
    equipment: List[EquipmentSchema]
    alerts: List[AlertSchema]
    contractors: List[SiteContractorSchema]
