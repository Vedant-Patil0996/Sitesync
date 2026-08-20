from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/")
async def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@router.patch("/{notification_id}/read")
async def mark_read(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pass

@router.patch("/mark-all-read")
async def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pass
