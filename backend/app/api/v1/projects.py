from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User

router = APIRouter()

@router.get("/")
async def get_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@router.get("/{project_id}")
async def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pass

@router.get("/{project_id}/tasks")
async def get_project_tasks(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@router.get("/{project_id}/milestones")
async def get_project_milestones(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []
