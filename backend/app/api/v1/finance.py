from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.deps import get_current_user, require_role, require_site_access, audit
from app.models.user import User
from app.models.finance import Payment, Expense
from app.models.procurement import PurchaseOrder, MaterialRequest, Delivery
from app.models.vendor import Vendor
from app.models.inventory import Material
from app.models.project import Project
from app.schemas.common import PaginatedResponse
from app.schemas.finance import PaymentSchema, PurchaseOrderSchema, FinanceSummarySchema, ExpenseCreateSchema, ExpenseSchema, PaymentCreateSchema, DeliveryConfirmSchema

router = APIRouter()

@router.get("/summary", response_model=FinanceSummarySchema)
async def get_finance_summary(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    from app.models.site import Site
    site_ids = db.query(Site.id).filter(Site.company_id == current_user.company_id).subquery()
    project_ids = db.query(Project.id).filter(Project.company_id == current_user.company_id).subquery()
    total_budget = float(db.query(func.sum(Project.budget_allocated)).filter(Project.company_id == current_user.company_id).scalar() or 0)
    expenses_spent = db.query(func.sum(Expense.amount)).filter(Expense.site_id.in_(site_ids)).scalar() or 0
    released_payments = db.query(func.sum(Payment.amount)).join(PurchaseOrder, Payment.po_id == PurchaseOrder.id).join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id).filter(MaterialRequest.site_id.in_(site_ids), Payment.status == "released").scalar() or 0
    total_spent = float(expenses_spent) + float(released_payments)
    pending_payments = db.query(func.sum(Payment.amount)).join(PurchaseOrder, Payment.po_id == PurchaseOrder.id).join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id).filter(MaterialRequest.site_id.in_(site_ids), Payment.status == "scheduled").scalar() or 0
    committed_costs = db.query(func.sum(PurchaseOrder.amount)).join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id).filter(MaterialRequest.site_id.in_(site_ids), PurchaseOrder.status.in_(["pending_finance", "approved", "delivered"])).scalar() or 0
    
    # Recent transactions (last 5 released payments)
    recent_payments = db.query(Payment).join(PurchaseOrder, Payment.po_id == PurchaseOrder.id).join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id).filter(MaterialRequest.site_id.in_(site_ids), Payment.status == "released").order_by(Payment.released_at.desc()).limit(5).all()
    transactions = []
    for p in recent_payments:
        transactions.append({
            "id": p.id,
            "type": "payment",
            "amount": float(p.amount),
            "date": p.released_at.isoformat() if p.released_at else p.created_at.isoformat()
        })
        
    # Sites budget
    sites_db = db.query(Site).filter(Site.company_id == current_user.company_id).all()
    sites_budget = []
    for s in sites_db:
        # Get total budget from projects
        site_budget = db.query(func.sum(Project.budget_total)).filter(Project.site_id == s.id).scalar() or 0
        
        site_expenses = db.query(func.sum(Expense.amount)).filter(Expense.site_id == s.id).scalar() or 0
        site_payments = db.query(func.sum(Payment.amount)).join(PurchaseOrder, Payment.po_id == PurchaseOrder.id).join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id).filter(MaterialRequest.site_id == s.id, Payment.status == "released").scalar() or 0
        sites_budget.append({
            "site_id": s.id,
            "site_name": s.name,
            "budget": float(site_budget),
            "spent": float(site_expenses) + float(site_payments)
        })
        
    return FinanceSummarySchema(
        total_budget=total_budget,
        total_spent=total_spent,
        pending_payments=float(pending_payments),
        recent_transactions=transactions,
        sites_budget=sites_budget,
        committed_costs=float(committed_costs)
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
        .outerjoin(User, PurchaseOrder.approved_by == User.id)\
        .join(__import__('app.models.site', fromlist=['Site']).Site, MaterialRequest.site_id == __import__('app.models.site', fromlist=['Site']).Site.id)\
        .filter(__import__('app.models.site', fromlist=['Site']).Site.company_id == current_user.company_id)
        
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
            quantity=float(po.quantity),
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
    po = db.query(PurchaseOrder, MaterialRequest).join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id).join(__import__('app.models.site', fromlist=['Site']).Site, MaterialRequest.site_id == __import__('app.models.site', fromlist=['Site']).Site.id).filter(PurchaseOrder.id == po_id, __import__('app.models.site', fromlist=['Site']).Site.company_id == current_user.company_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    order, request = po
    if order.status != "pending_finance" or request.pm_status != "approved" or request.finance_status != "approved":
        raise HTTPException(status_code=409, detail="Purchase order is not pending valid approval")
    order.status = "approved"
    order.approved_by = current_user.id
    order.approved_at = func.now()
    audit(db, current_user, "purchase_order.approved", "purchase_order", order.id)
    db.commit()
    return {"status": "approved"}

@router.patch("/purchase-orders/{po_id}/reject")
async def reject_purchase_order(po_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    row = db.query(PurchaseOrder, MaterialRequest).join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id).join(__import__('app.models.site', fromlist=['Site']).Site, MaterialRequest.site_id == __import__('app.models.site', fromlist=['Site']).Site.id).filter(PurchaseOrder.id == po_id, __import__('app.models.site', fromlist=['Site']).Site.company_id == current_user.company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    order, request = row
    if order.status != "pending_finance":
        raise HTTPException(status_code=409, detail="Purchase order is not pending finance approval")
    order.status = "rejected"
    audit(db, current_user, "purchase_order.rejected", "purchase_order", order.id)
    db.commit()
    return {"status": "rejected"}

@router.post("/expenses", response_model=ExpenseSchema)
async def create_expense(payload: ExpenseCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    require_site_access(db, current_user, payload.site_id, write=True)
    if payload.amount <= 0 or payload.category not in ("material", "labor", "equipment", "misc"):
        raise HTTPException(status_code=400, detail="Invalid expense")
    expense = Expense(site_id=payload.site_id, project_id=payload.project_id, category=payload.category, amount=payload.amount, description=payload.description, recorded_by=current_user.id)
    db.add(expense)
    db.flush()
    audit(db, current_user, "expense.created", "expense", expense.id, {"amount": payload.amount})
    db.commit()
    db.refresh(expense)
    return expense

@router.get("/expenses", response_model=list[ExpenseSchema])
async def get_expenses(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    from app.models.site import Site
    rows = db.query(Expense).join(Site, Expense.site_id == Site.id).filter(Site.company_id == current_user.company_id).order_by(Expense.date.desc()).limit(200).all()
    return rows

@router.post("/payments", response_model=PaymentSchema)
async def schedule_payment(payload: PaymentCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    row = db.query(PurchaseOrder, Vendor, MaterialRequest, Material).join(Vendor, PurchaseOrder.vendor_id == Vendor.id).join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id).join(Material, MaterialRequest.material_id == Material.id).join(__import__('app.models.site', fromlist=['Site']).Site, MaterialRequest.site_id == __import__('app.models.site', fromlist=['Site']).Site.id).filter(PurchaseOrder.id == payload.po_id, __import__('app.models.site', fromlist=['Site']).Site.company_id == current_user.company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    po, vendor, request, material = row
    if po.status not in ("approved", "delivered") or payload.amount <= 0 or payload.amount > float(po.amount):
        raise HTTPException(status_code=409, detail="Payment cannot be scheduled for this purchase order")
    already = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.po_id == po.id).scalar() or 0
    if float(already) + payload.amount > float(po.amount):
        raise HTTPException(status_code=409, detail="Scheduled payments exceed purchase order amount")
    payment = Payment(po_id=po.id, amount=payload.amount, status="scheduled")
    db.add(payment)
    db.flush()
    audit(db, current_user, "payment.scheduled", "payment", payment.id, {"po_id": po.id, "amount": payload.amount})
    db.commit()
    db.refresh(payment)
    return PaymentSchema(id=payment.id, po_id=payment.po_id, amount=float(payment.amount), status=payment.status, vendor_name=vendor.name, material_name=material.name, released_by_name=None, released_at=None, created_at=payment.created_at)

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
    row = db.query(Payment, PurchaseOrder).join(PurchaseOrder, Payment.po_id == PurchaseOrder.id).join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id).join(__import__('app.models.site', fromlist=['Site']).Site, MaterialRequest.site_id == __import__('app.models.site', fromlist=['Site']).Site.id).filter(Payment.id == payment_id, __import__('app.models.site', fromlist=['Site']).Site.company_id == current_user.company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Payment not found")
    payment, po = row
    delivery = db.query(Delivery).filter(Delivery.po_id == po.id, Delivery.status == "delivered").first()
    if payment.status != "scheduled" or po.status not in ("approved", "delivered") or not delivery:
        raise HTTPException(status_code=409, detail="Payment requires an approved PO and confirmed delivery")
    payment.status = "released"
    payment.released_by = current_user.id
    payment.released_at = func.now()
    audit(db, current_user, "payment.released", "payment", payment.id, {"po_id": po.id})
    db.commit()
    return {"status": "released"}

@router.post("/purchase-orders/{po_id}/delivery")
async def confirm_delivery(po_id: int, payload: DeliveryConfirmSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "contractor"))):
    row = db.query(PurchaseOrder, MaterialRequest).join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id).join(__import__('app.models.site', fromlist=['Site']).Site, MaterialRequest.site_id == __import__('app.models.site', fromlist=['Site']).Site.id).filter(PurchaseOrder.id == po_id, __import__('app.models.site', fromlist=['Site']).Site.company_id == current_user.company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    po, request = row
    require_site_access(db, current_user, request.site_id, write=True)
    if po.status != "approved" or payload.quantity <= 0 or payload.quantity > float(po.quantity):
        raise HTTPException(status_code=409, detail="Invalid delivery")
    delivery = Delivery(po_id=po.id, quantity=payload.quantity, status="delivered", confirmed_by=current_user.id, delivery_date=func.now())
    po.status = "delivered"
    db.add(delivery)
    db.flush()
    audit(db, current_user, "delivery.confirmed", "delivery", delivery.id, {"po_id": po.id, "quantity": payload.quantity})
    db.commit()
    return {"status": "delivered", "delivery_id": delivery.id}
