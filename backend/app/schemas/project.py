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

class ProjectCreateSchema(BaseModel):
    site_id: int
    pm_id: int
    name: str
    description: Optional[str] = None
    budget_allocated: float = 0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "planning"

class ProjectUpdateSchema(BaseModel):
    site_id: Optional[int] = None
    pm_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    budget_allocated: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None

class ProjectScheduleUpdateSchema(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None

class TaskSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    priority: str = "medium"
    start_date: Optional[date]
    end_date: Optional[date]
    depends_on_task_id: Optional[int]
    progress_percent: float = 0
    assigned_to: Optional[int] = None
    
class MilestoneSchema(BaseModel):
    id: int
    name: str
    due_date: Optional[date]
    status: str

class TaskUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    progress_percent: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    assigned_to: Optional[int] = None
    depends_on_task_id: Optional[int] = None

class TaskCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    priority: str = "medium"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    assigned_to: Optional[int] = None
    depends_on_task_id: Optional[int] = None

class DependencyUpdateSchema(BaseModel):
    depends_on_task_id: Optional[int] = None

class MilestoneCreateSchema(BaseModel):
    name: str
    due_date: Optional[date] = None
    status: str = "upcoming"

class MilestoneUpdateSchema(BaseModel):
    name: Optional[str] = None
    due_date: Optional[date] = None
    status: str

class ProjectDetailSchema(ProjectSchema):
    budget_total: float
    start_date: Optional[date]
    site_id: int
    pm_id: int
    tasks: List[TaskSchema]
    milestones: List[MilestoneSchema]
