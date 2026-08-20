from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class AlertSchema(BaseModel):
    id: int
    site_id: int
    site_name: str
    type: str
    severity: str
    title: str
    description: Optional[str]
    status: str
    resolved_by_name: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime
