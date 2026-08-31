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
    assigned_to_name: Optional[str] = None

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

# ── Gantt schemas ──────────────────────────────────────────────────────────────

class GanttTaskSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    status: str
    priority: str
    start_date: Optional[date]
    end_date: Optional[date]
    progress_percent: float
    depends_on_task_id: Optional[int] = None
    assigned_to: Optional[int] = None
    assigned_to_name: Optional[str] = None
    days_overdue: int = 0          # 0 if not overdue, else days past end_date
    is_on_critical_path: bool = False  # True if task has dependents AND is delayed/at-risk

class GanttMilestoneSchema(BaseModel):
    id: int
    name: str
    due_date: Optional[date]
    status: str

class GanttDataSchema(BaseModel):
    project_id: int
    project_name: str
    project_start: Optional[date]
    project_end: Optional[date]
    project_status: str
    tasks: List[GanttTaskSchema]
    milestones: List[GanttMilestoneSchema]

# ── Schedule health schemas ────────────────────────────────────────────────────

class ScheduleHealthSchema(BaseModel):
    project_id: int
    project_name: str
    risk_level: str                    # "on_track" | "at_risk" | "critical"
    overdue_task_count: int
    delayed_task_count: int
    missed_milestone_count: int
    upcoming_deadline_count: int       # tasks/milestones due within 7 days
    total_tasks: int
    completed_tasks: int
    progress_percent: float
    days_to_project_deadline: Optional[int]  # None if no end_date set

