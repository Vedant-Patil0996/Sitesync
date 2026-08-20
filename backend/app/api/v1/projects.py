from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.site import Site
from app.models.project import Project, Task, Milestone
from app.schemas.project import ProjectSchema, ProjectDetailSchema, TaskSchema, MilestoneSchema
from app.schemas.common import PaginatedResponse
from fastapi import HTTPException

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[ProjectSchema])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    query = db.query(Project).filter(Project.company_id == current_user.company_id)
    
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

@router.get("/{project_id}", response_model=ProjectDetailSchema)
async def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id, Project.company_id == current_user.company_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    site = db.query(Site).filter(Site.id == project.site_id).first()
    site_name = site.name if site else None
    
    tasks_db = db.query(Task).filter(Task.project_id == project.id).all()
    milestones_db = db.query(Milestone).filter(Milestone.project_id == project.id).all()
    
    task_count = len(tasks_db)
    completed_task_count = len([t for t in tasks_db if t.status == 'completed'])
    milestone_count = len(milestones_db)
    
    tasks_data = [TaskSchema(
        id=t.id, name=t.name, description=t.description, status=t.status,
        start_date=t.start_date, end_date=t.end_date, depends_on_task_id=t.depends_on_task_id
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
        site_id=project.site_id, tasks=tasks_data, milestones=milestones_data
    )

@router.get("/{project_id}/tasks")
async def get_project_tasks(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Simple check if project exists and user has access
    project = db.query(Project).filter(Project.id == project_id, Project.company_id == current_user.company_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    return [TaskSchema(
        id=t.id, name=t.name, description=t.description, status=t.status,
        start_date=t.start_date, end_date=t.end_date, depends_on_task_id=t.depends_on_task_id
    ) for t in tasks]

@router.get("/{project_id}/milestones")
async def get_project_milestones(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id, Project.company_id == current_user.company_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    milestones = db.query(Milestone).filter(Milestone.project_id == project_id).all()
    return [MilestoneSchema(
        id=m.id, name=m.name, due_date=m.due_date, status=m.status
    ) for m in milestones]
