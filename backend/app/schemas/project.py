from typing import Optional, List
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

class TaskSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    start_date: Optional[date]
    end_date: Optional[date]
    depends_on_task_id: Optional[int]
    
class MilestoneSchema(BaseModel):
    id: int
    name: str
    due_date: Optional[date]
    status: str

class ProjectDetailSchema(ProjectSchema):
    budget_total: float
    start_date: Optional[date]
    site_id: int
    tasks: List[TaskSchema]
    milestones: List[MilestoneSchema]
