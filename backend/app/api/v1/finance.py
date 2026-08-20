from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User

router = APIRouter()

@router.get("/summary")
async def get_finance_summary(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    return []

@router.get("/purchase-orders")
async def get_purchase_orders(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    return []

@router.patch("/purchase-orders/{po_id}/approve")
async def approve_purchase_order(po_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    pass

@router.get("/payments")
async def get_payments(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    return []

@router.patch("/payments/{payment_id}/release")
async def release_payment(payment_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    pass
