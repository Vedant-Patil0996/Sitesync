from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User

router = APIRouter()

@router.get("/requests")
async def get_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@router.post("/requests")
async def create_request(db: Session = Depends(get_db), current_user: User = Depends(require_role("pm", "contractor"))):
    pass

@router.patch("/requests/{request_id}/pm-review")
async def pm_review_request(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    pass

@router.patch("/requests/{request_id}/finance-review")
async def finance_review_request(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    pass

@router.get("/quotes")
async def get_quotes(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    return []

@router.post("/quotes")
async def add_quote(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    pass

@router.patch("/quotes/{quote_id}/select")
async def select_quote(quote_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    pass
