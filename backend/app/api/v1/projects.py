from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.deps import get_current_user, require_role, require_site_access, audit
from app.models.user import User
from app.models.site import Site, SiteAssignment
from app.models.project import Project, Task, Milestone
from app.models.equipment import Equipment
from app.schemas.project import ProjectSchema, ProjectDetailSchema, TaskSchema, MilestoneSchema, TaskUpdateSchema, TaskCreateSchema, MilestoneUpdateSchema, MilestoneCreateSchema, ProjectCreateSchema, ProjectUpdateSchema, ProjectScheduleUpdateSchema
from app.schemas.common import PaginatedResponse
from fastapi import HTTPException

router = APIRouter()

TASK_STATUSES = ("not_started", "in_progress", "delayed", "completed")
TASK_PRIORITIES = ("low", "medium", "high", "critical")
MILESTONE_STATUSES = ("upcoming", "achieved", "missed")

def _project_for_user(db: Session, project_id: int, user: User, write: bool = False) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.company_id == user.company_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    require_site_access(db, user, project.site_id, write=write)
    return project

def _validate_task_dependency(db: Session, project_id: int, task_id: int | None, depends_on_task_id: int | None):
    if depends_on_task_id is None:
        return
    if task_id is not None and depends_on_task_id == task_id:
        raise HTTPException(status_code=400, detail="A task cannot depend on itself")
    dependency = db.query(Task).filter(Task.id == depends_on_task_id, Task.project_id == project_id).first()
    if not dependency:
        raise HTTPException(status_code=400, detail="Dependency must be another task in this project")
    seen = {task_id} if task_id is not None else set()
    current = dependency
    while current and current.depends_on_task_id:
        if current.id in seen:
            raise HTTPException(status_code=400, detail="Task dependency cycle detected")
        seen.add(current.id)
        current = db.query(Task).filter(Task.id == current.depends_on_task_id, Task.project_id == project_id).first()

def _validate_assignee(db: Session, project: Project, user: User | None):
    if not user:
        return
    if user.role != "contractor" or user.company_id != project.company_id or not user.is_active:
        raise HTTPException(status_code=400, detail="Task assignee must be an active contractor in this company")
    if not db.query(SiteAssignment).filter(SiteAssignment.site_id == project.site_id, SiteAssignment.user_id == user.id).first():
        raise HTTPException(status_code=400, detail="Contractor is not assigned to this project site")

@router.get("/", response_model=PaginatedResponse[ProjectSchema])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    query = db.query(Project).join(Site, Project.site_id == Site.id).filter(Project.company_id == current_user.company_id)
    if current_user.role in ("pm", "contractor"):
        query = query.filter(Site.id.in_(db.query(SiteAssignment.site_id).filter(SiteAssignment.user_id == current_user.id)))
    
    total = query.count()
    projects_db = query.offset(skip).limit(limit).all()
    
    items = []
    for project in projects_db:
        site = db.query(Site).filter(Site.id == project.site_id).first()
        site_name = site.name if site else None
        
        task_count = db.query(Task).filter(Task.project_id == project.id).count()
        completed_task_count = db.query(Task).filter(Task.project_id == project.id, Task.status == 'completed').count()
        milestone_count = db.query(Milestone).filter(Milestone.project_id == project.id).count()
        
        items.append(ProjectSchema(
            id=project.id,
            name=project.name,
            site_name=site_name,
            status=project.status,
            progress_percent=float(project.progress_percent),
            end_date=project.end_date,
            budget_allocated=float(project.budget_allocated),
            task_count=task_count,
            completed_task_count=completed_task_count,
            milestone_count=milestone_count
        ))
        
    return PaginatedResponse[ProjectSchema](
        items=items,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.post("/", response_model=dict)
async def create_project(payload: ProjectCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    site = db.query(Site).filter(Site.id == payload.site_id, Site.company_id == current_user.company_id).first()
    pm = db.query(User).filter(User.id == payload.pm_id, User.company_id == current_user.company_id, User.role == "pm", User.is_active == True).first()
    if not site or not pm:
        raise HTTPException(status_code=400, detail="Site or active PM is invalid")
    if payload.budget_allocated < 0 or payload.status not in ("planning", "in_progress", "on_hold"):
        raise HTTPException(status_code=400, detail="Budget cannot be negative")
    if not db.query(SiteAssignment).filter(SiteAssignment.site_id == site.id, SiteAssignment.user_id == pm.id).first():
        db.add(SiteAssignment(site_id=site.id, user_id=pm.id, assigned_role="pm"))
    project = Project(site_id=site.id, company_id=current_user.company_id, pm_id=pm.id, name=payload.name, description=payload.description, budget_allocated=payload.budget_allocated, start_date=payload.start_date, end_date=payload.end_date, status=payload.status, created_by=current_user.id)
    db.add(project)
    db.flush()
    audit(db, current_user, "project.created", "project", project.id, {"site_id": site.id, "pm_id": pm.id, "budget": payload.budget_allocated})
    db.commit()
    return {"id": project.id, "status": "created"}

@router.get("/{project_id}", response_model=ProjectDetailSchema)
async def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id, Project.company_id == current_user.company_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    require_site_access(db, current_user, project.site_id)
        
    site = db.query(Site).filter(Site.id == project.site_id).first()
    site_name = site.name if site else None
    
    tasks_query = db.query(Task).filter(Task.project_id == project.id)
    if current_user.role == "contractor":
        tasks_query = tasks_query.filter(Task.assigned_to == current_user.id)
    tasks_db = tasks_query.all()
    milestones_db = db.query(Milestone).filter(Milestone.project_id == project.id).all()
    
    task_count = len(tasks_db)
    completed_task_count = len([t for t in tasks_db if t.status == 'completed'])
    milestone_count = len(milestones_db)
    
    tasks_data = [TaskSchema(
        id=t.id, name=t.name, description=t.description, status=t.status,
        priority=t.priority,
        start_date=t.start_date, end_date=t.end_date, depends_on_task_id=t.depends_on_task_id,
        progress_percent=float(t.progress_percent), assigned_to=t.assigned_to
    ) for t in tasks_db]
    
    milestones_data = [MilestoneSchema(
        id=m.id, name=m.name, due_date=m.due_date, status=m.status
    ) for m in milestones_db]
    
    return ProjectDetailSchema(
        id=project.id, name=project.name, site_name=site_name, status=project.status,
        progress_percent=float(project.progress_percent), end_date=project.end_date,
        budget_allocated=float(project.budget_allocated), task_count=task_count,
        completed_task_count=completed_task_count, milestone_count=milestone_count,
        budget_total=float(project.budget_allocated), start_date=project.start_date,
        site_id=project.site_id, pm_id=project.pm_id, tasks=tasks_data, milestones=milestones_data
    )

@router.patch("/{project_id}")
async def update_project(project_id: int, payload: ProjectUpdateSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    project = db.query(Project).filter(Project.id == project_id, Project.company_id == current_user.company_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if payload.budget_allocated is not None and payload.budget_allocated < 0:
        raise HTTPException(status_code=400, detail="Budget cannot be negative")
    target_site_id = payload.site_id if payload.site_id is not None else project.site_id
    target_pm_id = payload.pm_id if payload.pm_id is not None else project.pm_id
    site = db.query(Site).filter(Site.id == target_site_id, Site.company_id == current_user.company_id).first()
    pm = db.query(User).filter(User.id == target_pm_id, User.company_id == current_user.company_id, User.role == "pm", User.is_active == True).first()
    if not site or not pm:
        raise HTTPException(status_code=400, detail="Site or active PM is invalid")
    if not db.query(SiteAssignment).filter(SiteAssignment.site_id == site.id, SiteAssignment.user_id == pm.id).first():
        db.add(SiteAssignment(site_id=site.id, user_id=pm.id, assigned_role="pm"))
    if payload.status is not None and payload.status not in ("planning", "in_progress", "on_hold", "completed", "archived"):
        raise HTTPException(status_code=400, detail="Invalid project status")
    for field in ("site_id", "pm_id", "name", "description", "budget_allocated", "start_date", "end_date", "status"):
        value = getattr(payload, field)
        if value is not None:
            setattr(project, field, value)
    audit(db, current_user, "project.updated", "project", project.id, {"status": project.status})
    db.commit()
    return {"status": "updated"}

@router.patch("/{project_id}/archive")
async def archive_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    project = db.query(Project).filter(Project.id == project_id, Project.company_id == current_user.company_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status == "archived":
        raise HTTPException(status_code=409, detail="Project is already archived")
    project.status = "archived"
    audit(db, current_user, "project.archived", "project", project.id)
    db.commit()
    return {"status": "archived"}

@router.patch("/{project_id}/schedule")
async def update_project_schedule(project_id: int, payload: ProjectScheduleUpdateSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    project = _project_for_user(db, project_id, current_user, write=True)
    if payload.start_date and payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="Project end date cannot be before start date")
    if payload.status and payload.status not in ("planning", "in_progress", "on_hold", "completed"):
        raise HTTPException(status_code=400, detail="Invalid project schedule status")
    values = payload.model_dump(exclude_unset=True)
    for field in ("start_date", "end_date", "status"):
        if field in values and values[field] is not None:
            setattr(project, field, values[field])
    audit(db, current_user, "project.schedule_updated", "project", project.id, {"status": project.status})
    db.commit()
    return {"status": "updated"}

@router.post("/{project_id}/tasks", response_model=TaskSchema)
async def create_task(project_id: int, payload: TaskCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    project = _project_for_user(db, project_id, current_user, write=True)
    if not payload.name.strip() or payload.priority not in TASK_PRIORITIES:
        raise HTTPException(status_code=400, detail="Task name and priority are invalid")
    if payload.start_date and payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="Task end date cannot be before start date")
    assignee = db.query(User).filter(User.id == payload.assigned_to).first() if payload.assigned_to else None
    _validate_assignee(db, project, assignee)
    _validate_task_dependency(db, project.id, None, payload.depends_on_task_id)
    task = Task(project_id=project.id, name=payload.name.strip(), description=payload.description, priority=payload.priority, start_date=payload.start_date, end_date=payload.end_date, assigned_to=payload.assigned_to)
    db.add(task)
    db.flush()
    audit(db, current_user, "task.created", "task", task.id, {"project_id": project.id, "assigned_to": payload.assigned_to})
    db.commit()
    return TaskSchema(id=task.id, name=task.name, description=task.description, status=task.status, priority=task.priority, start_date=task.start_date, end_date=task.end_date, depends_on_task_id=task.depends_on_task_id, progress_percent=float(task.progress_percent), assigned_to=task.assigned_to)

@router.get("/{project_id}/tasks")
async def get_project_tasks(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Simple check if project exists and user has access
    project = _project_for_user(db, project_id, current_user)
        
    tasks_query = db.query(Task).filter(Task.project_id == project_id)
    if current_user.role == "contractor":
        tasks_query = tasks_query.filter(Task.assigned_to == current_user.id)
    tasks = tasks_query.all()
    return [TaskSchema(
        id=t.id, name=t.name, description=t.description, status=t.status,
        priority=t.priority,
        start_date=t.start_date, end_date=t.end_date, depends_on_task_id=t.depends_on_task_id,
        progress_percent=float(t.progress_percent), assigned_to=t.assigned_to
    ) for t in tasks]

@router.patch("/{project_id}/tasks/{task_id}")
async def update_project_task(project_id: int, task_id: int, payload: TaskUpdateSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "contractor"))):
    project = _project_for_user(db, project_id, current_user, write=True)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role == "contractor" and task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Contractors can only update assigned tasks")
    if payload.status and payload.status not in TASK_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid task status")
    if payload.priority and payload.priority not in TASK_PRIORITIES:
        raise HTTPException(status_code=400, detail="Invalid task priority")
    if payload.start_date and payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="Task end date cannot be before start date")
    values = payload.model_dump(exclude_unset=True)
    assignee = db.query(User).filter(User.id == values["assigned_to"]).first() if "assigned_to" in values and values["assigned_to"] else None
    if "assigned_to" in values:
        _validate_assignee(db, project, assignee)
    if "depends_on_task_id" in values:
        _validate_task_dependency(db, project.id, task.id, values["depends_on_task_id"])
    for field in ("name", "description", "status", "priority", "progress_percent", "start_date", "end_date", "assigned_to", "depends_on_task_id"):
        if field in values:
            setattr(task, field, values[field])
    if payload.progress_percent is not None:
        if payload.progress_percent < 0 or payload.progress_percent > 100:
            raise HTTPException(status_code=400, detail="Progress must be between 0 and 100")
        task.progress_percent = payload.progress_percent
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    project.progress_percent = (sum(float(item.progress_percent or 0) for item in tasks) / len(tasks)) if tasks else 0
    audit(db, current_user, "task.updated", "task", task.id, {"status": task.status, "project_id": project_id})
    db.commit()
    return {"status": "success", "progress_percent": float(project.progress_percent)}

@router.post("/{project_id}/milestones", response_model=MilestoneSchema)
async def create_milestone(project_id: int, payload: MilestoneCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    project = _project_for_user(db, project_id, current_user, write=True)
    if not payload.name.strip() or payload.status not in MILESTONE_STATUSES:
        raise HTTPException(status_code=400, detail="Milestone name or status is invalid")
    milestone = Milestone(project_id=project.id, name=payload.name.strip(), due_date=payload.due_date, status=payload.status)
    db.add(milestone)
    db.flush()
    audit(db, current_user, "milestone.created", "milestone", milestone.id, {"project_id": project.id})
    db.commit()
    return MilestoneSchema(id=milestone.id, name=milestone.name, due_date=milestone.due_date, status=milestone.status)

@router.get("/{project_id}/milestones")
async def get_project_milestones(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _project_for_user(db, project_id, current_user)
        
    milestones = db.query(Milestone).filter(Milestone.project_id == project_id).all()
    return [MilestoneSchema(
        id=m.id, name=m.name, due_date=m.due_date, status=m.status
    ) for m in milestones]

@router.patch("/{project_id}/milestones/{milestone_id}")
async def update_project_milestone(project_id: int, milestone_id: int, payload: MilestoneUpdateSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    project = _project_for_user(db, project_id, current_user, write=True)
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id, Milestone.project_id == project_id).first()
    if not milestone or payload.status not in MILESTONE_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid milestone or status")
    values = payload.model_dump(exclude_unset=True)
    for field in ("name", "due_date", "status"):
        if field in values and values[field] is not None:
            setattr(milestone, field, values[field])
    milestone.status = payload.status
    audit(db, current_user, "milestone.updated", "milestone", milestone.id, {"status": payload.status})
    db.commit()
    return {"status": "success"}
