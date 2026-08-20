from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.finance import Payment, Expense
from app.models.procurement import PurchaseOrder, MaterialRequest
from app.models.vendor import Vendor
from app.models.inventory import Material
from app.schemas.common import PaginatedResponse
from app.schemas.finance import PaymentSchema, PurchaseOrderSchema, FinanceSummarySchema

router = APIRouter()

@router.get("/summary", response_model=FinanceSummarySchema)
async def get_finance_summary(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    # Dummy logic for finance summary since we don't have budget mapped per company yet
    total_budget = 500000.0
    
    # Calculate total spent (amount of released payments + expenses)
    payments_spent = db.query(func.sum(Payment.amount)).filter(Payment.status == "released").scalar() or 0
    expenses_spent = db.query(func.sum(Expense.amount)).scalar() or 0
    total_spent = float(payments_spent) + float(expenses_spent)
    
    # Calculate pending payments
    pending_payments = db.query(func.sum(Payment.amount)).filter(Payment.status == "scheduled").scalar() or 0
    
    # Recent transactions (last 5 released payments)
    recent_payments = db.query(Payment).filter(Payment.status == "released").order_by(Payment.released_at.desc()).limit(5).all()
    transactions = []
    for p in recent_payments:
        transactions.append({
            "id": p.id,
            "type": "payment",
            "amount": float(p.amount),
            "date": p.released_at.isoformat() if p.released_at else p.created_at.isoformat()
        })
        
    # Sites budget
    from app.models.site import Site
    from app.models.project import Project
    sites_db = db.query(Site).filter(Site.company_id == current_user.company_id).all()
    sites_budget = []
    for s in sites_db:
        # Get total budget from projects
        site_budget = db.query(func.sum(Project.budget_total)).filter(Project.site_id == s.id).scalar() or 0
        
        # We can approximate site spent from payments on POs linked to MRs on this site
        # But this is complex. Let's just mock site spent as 0 for now.
        sites_budget.append({
            "site_id": s.id,
            "site_name": s.name,
            "budget": float(site_budget),
            "spent": 0.0 # Mocked spent for site
        })
        
    return FinanceSummarySchema(
        total_budget=total_budget,
        total_spent=total_spent,
        pending_payments=float(pending_payments),
        recent_transactions=transactions,
        sites_budget=sites_budget
    )

@router.get("/purchase-orders", response_model=PaginatedResponse[PurchaseOrderSchema])
async def get_purchase_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role("admin", "finance"))
):
    query = db.query(PurchaseOrder, Vendor, MaterialRequest, Material, User)\
        .join(Vendor, PurchaseOrder.vendor_id == Vendor.id)\
        .join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id)\
        .join(Material, MaterialRequest.material_id == Material.id)\
        .outerjoin(User, PurchaseOrder.approved_by == User.id)
        
    total = query.count()
    pos_db = query.offset(skip).limit(limit).all()
    
    items = []
    for po, vendor, req, mat, approver in pos_db:
        # Get payments for PO
        payments_db = db.query(Payment, User).outerjoin(User, Payment.released_by == User.id).filter(Payment.po_id == po.id).all()
        payment_schemas = []
        for p, p_user in payments_db:
            payment_schemas.append(PaymentSchema(
                id=p.id,
                po_id=p.po_id,
                amount=float(p.amount),
                status=p.status,
                vendor_name=vendor.name,
                material_name=mat.name,
                released_by_name=p_user.name if p_user else None,
                released_at=p.released_at,
                created_at=p.created_at
            ))
            
        items.append(PurchaseOrderSchema(
            id=po.id,
            vendor_name=vendor.name,
            material_name=mat.name,
            amount=float(po.amount),
            status=po.status,
            approved_by_name=approver.name if approver else None,
            delivered_at=po.order_date, # For simplicity, using order_date as delivered_at if delivered
            payments=payment_schemas
        ))
        
    return PaginatedResponse[PurchaseOrderSchema](
        items=items,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.patch("/purchase-orders/{po_id}/approve")
async def approve_purchase_order(po_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if po:
        po.status = "approved"
        po.approved_by = current_user.id
        po.approved_at = func.now()
        db.commit()
    return {"status": "success"}

@router.get("/payments", response_model=PaginatedResponse[PaymentSchema])
async def get_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role("admin", "finance"))
):
    query = db.query(Payment, PurchaseOrder, Vendor, MaterialRequest, Material, User)\
        .join(PurchaseOrder, Payment.po_id == PurchaseOrder.id)\
        .join(Vendor, PurchaseOrder.vendor_id == Vendor.id)\
        .join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id)\
        .join(Material, MaterialRequest.material_id == Material.id)\
        .outerjoin(User, Payment.released_by == User.id)
        
    total = query.count()
    payments_db = query.offset(skip).limit(limit).all()
    
    items = []
    for p, po, vendor, req, mat, releaser in payments_db:
        items.append(PaymentSchema(
            id=p.id,
            po_id=p.po_id,
            amount=float(p.amount),
            status=p.status,
            vendor_name=vendor.name,
            material_name=mat.name,
            released_by_name=releaser.name if releaser else None,
            released_at=p.released_at,
            created_at=p.created_at
        ))
        
    return PaginatedResponse[PaymentSchema](
        items=items,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.patch("/payments/{payment_id}/release")
async def release_payment(payment_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if payment:
        payment.status = "released"
        payment.released_by = current_user.id
        payment.released_at = func.now()
        db.commit()
    return {"status": "success"}
