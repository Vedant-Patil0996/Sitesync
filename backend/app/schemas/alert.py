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
    source_table: Optional[str] = None
    source_id: Optional[int] = None
    status: str
    resolved_by_name: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime

class NotificationSchema(BaseModel):
    id: int
    user_id: int
    alert_id: Optional[int]
    related_entity_type: Optional[str]
    related_entity_id: Optional[int]
    title: str
    message: Optional[str]
    status: str
    read_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    created_at: datetime
