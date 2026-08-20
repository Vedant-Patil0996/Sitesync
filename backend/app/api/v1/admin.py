from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User

router = APIRouter()

@router.get("/users")
async def get_users(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    return []

@router.post("/users/invite")
async def invite_user(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    pass

@router.patch("/users/{user_id}/role")
async def update_user_role(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    pass

@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    pass

@router.get("/audit-log")
async def get_audit_log(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    return []
