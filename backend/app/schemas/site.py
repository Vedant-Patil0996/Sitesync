from typing import Optional
from pydantic import BaseModel
from datetime import datetime

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
