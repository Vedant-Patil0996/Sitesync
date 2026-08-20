from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User

router = APIRouter()

@router.get("/")
async def get_sites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Return all sites for admin/finance, or assigned sites for PM/contractor
    return []

@router.post("/")
async def create_site(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    pass

@router.get("/{site_id}")
async def get_site(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pass

@router.get("/{site_id}/assignments")
async def get_site_assignments(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    pass
