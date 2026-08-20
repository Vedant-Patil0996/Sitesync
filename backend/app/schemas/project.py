from typing import Optional
from pydantic import BaseModel
from datetime import date

class ProjectSchema(BaseModel):
    id: int
    name: str
    site_name: Optional[str]
    status: str
    progress_percent: float
    end_date: Optional[date]
    budget_allocated: float
    task_count: int
    completed_task_count: int
    milestone_count: int
