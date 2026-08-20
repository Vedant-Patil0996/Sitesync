from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict

class UserSchema(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

class AuditLogSchema(BaseModel):
    id: int
    user_name: Optional[str]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
