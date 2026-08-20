from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.site import Site
from app.models.project import Project, Task, Milestone
from app.schemas.project import ProjectSchema
from app.schemas.common import PaginatedResponse

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

@router.get("/{project_id}")
async def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pass

@router.get("/{project_id}/tasks")
async def get_project_tasks(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@router.get("/{project_id}/milestones")
async def get_project_milestones(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []
