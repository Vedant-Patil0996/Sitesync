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

class SiteContractorSchema(BaseModel):
    id: int
    name: str
    specialty: str
    phone: Optional[str]

class SiteDetailSchema(SiteSchema):
    latitude: Optional[float]
    longitude: Optional[float]
    location_text: Optional[str]
    projects: List[ProjectSchema]
    inventory: List[InventorySchema]
    equipment: List[EquipmentSchema]
    alerts: List[AlertSchema]
    contractors: List[SiteContractorSchema]
