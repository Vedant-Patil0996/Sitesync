from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User

router = APIRouter()

@router.get("/")
async def get_equipment(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "finance"))):
    return []

@router.get("/by-site/{site_id}")
async def get_site_equipment(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@router.patch("/{equipment_id}/status")
async def update_equipment_status(equipment_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    pass

@router.post("/{equipment_id}/logs")
async def log_equipment_usage(equipment_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "contractor"))):
    pass
