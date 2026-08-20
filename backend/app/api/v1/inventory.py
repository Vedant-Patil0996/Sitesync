from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User

router = APIRouter()

@router.get("/")
async def get_inventory(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "finance"))):
    return []

@router.get("/by-site/{site_id}")
async def get_site_inventory(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@router.post("/transactions")
async def log_transaction(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "contractor"))):
    pass

@router.get("/transactions")
async def get_transactions(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    return []
