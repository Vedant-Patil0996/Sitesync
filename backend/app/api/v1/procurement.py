from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.deps import get_current_user, require_role, require_site_access, audit
from app.models.user import User
from app.models.site import Site
from app.models.inventory import Material
from app.models.vendor import Vendor
from app.models.procurement import MaterialRequest, VendorQuote, PurchaseOrder
from app.models.project import Project
from app.schemas.procurement import MaterialRequestSchema, VendorQuoteSchema, MaterialRequestCreateSchema, ReviewSchema, VendorQuoteCreateSchema, PurchaseOrderCreateSchema
from app.schemas.common import PaginatedResponse

router = APIRouter()

@router.get("/requests", response_model=PaginatedResponse[MaterialRequestSchema])
async def get_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    query = db.query(MaterialRequest, Material, Site, User)\
        .join(Material, MaterialRequest.material_id == Material.id)\
        .join(Site, MaterialRequest.site_id == Site.id)\
        .join(User, MaterialRequest.requested_by == User.id)\
        .filter(Site.company_id == current_user.company_id)
        
    total = query.count()
    requests_db = query.offset(skip).limit(limit).all()
    
    if not requests_db:
        return PaginatedResponse[MaterialRequestSchema](items=[], total=0, page=1, size=limit, pages=0)

    req_ids = [r[0].id for r in requests_db]
    reviewer_ids = set()
    for r, _, _, _ in requests_db:
        if r.pm_reviewed_by: reviewer_ids.add(r.pm_reviewed_by)
        if r.finance_reviewed_by: reviewer_ids.add(r.finance_reviewed_by)

    # Batch fetch reviewer names
    user_names = {}
    if reviewer_ids:
        user_names = dict(
            db.query(User.id, User.name)
            .filter(User.id.in_(reviewer_ids)).all()
        )

    # Batch fetch quotes
    all_quotes = db.query(VendorQuote, Vendor).join(Vendor, VendorQuote.vendor_id == Vendor.id)\
        .filter(VendorQuote.request_id.in_(req_ids)).all()
    
    quotes_by_req = {}
    for q, v in all_quotes:
        if q.request_id not in quotes_by_req:
            quotes_by_req[q.request_id] = []
        quotes_by_req[q.request_id].append(VendorQuoteSchema(
            id=q.id,
            vendor_name=v.name,
            unit_price=float(q.unit_price),
            total_price=float(q.total_price),
            delivery_days=q.delivery_days,
            is_selected=q.is_selected
        ))

    # Batch fetch purchase orders
    pos = dict(
        db.query(PurchaseOrder.request_id, PurchaseOrder.status)
        .filter(PurchaseOrder.request_id.in_(req_ids)).all()
    )

    items = []
    for req, mat, site, user in requests_db:
        pm_reviewer_name = user_names.get(req.pm_reviewed_by) if req.pm_reviewed_by else None
        fin_reviewer_name = user_names.get(req.finance_reviewed_by) if req.finance_reviewed_by else None
        quotes = quotes_by_req.get(req.id, [])
        po_status = pos.get(req.id)

        items.append(MaterialRequestSchema(
            id=req.id,
            material_name=mat.name,
            quantity=float(req.quantity),
            unit=mat.unit,
            site_name=site.name,
            requested_by_name=user.name,
            created_at=req.created_at,
            priority=req.priority or "normal",
            required_date=req.required_date,
            estimated_unit_cost=float(req.estimated_unit_cost) if req.estimated_unit_cost is not None else None,
            total_estimated_cost=float(req.total_estimated_cost) if req.total_estimated_cost is not None else None,
            attachment_url=req.attachment_url,
            justification=req.justification,
            pm_status=req.pm_status,
            pm_reviewed_by_name=pm_reviewer_name,
            pm_notes=req.pm_notes,
            finance_status=req.finance_status,
            finance_reviewed_by_name=fin_reviewer_name,
            finance_notes=req.finance_notes,
            quotes=quotes,
            po_status=po_status
        ))
        
    return PaginatedResponse[MaterialRequestSchema](
        items=items,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.post("/requests", response_model=MaterialRequestSchema)
async def create_request(
    request: MaterialRequestCreateSchema,
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role("pm", "contractor"))
):
    from datetime import datetime
    require_site_access(db, current_user, request.site_id, write=True)
    
    # Verify site exists and belongs to company
    site = db.query(Site).filter(Site.id == request.site_id, Site.company_id == current_user.company_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
        
    # Verify material exists and belongs to company
    material = db.query(Material).filter(Material.id == request.material_id, Material.company_id == current_user.company_id).first()
    if not material or request.quantity <= 0:
        raise HTTPException(status_code=400, detail="Invalid material or quantity")

    if request.project_id:
        project = db.query(Project).filter_by(id=request.project_id, site_id=request.site_id, company_id=current_user.company_id).first()
        if not project:
            raise HTTPException(status_code=400, detail="Project does not belong to the selected site")

    unit_cost = request.estimated_unit_cost
    total_cost = (float(request.quantity) * float(unit_cost)) if unit_cost is not None else None

    req_date = None
    if request.required_date:
        try:
            req_date = datetime.strptime(request.required_date, "%Y-%m-%d").date()
        except Exception:
            pass

    new_request = MaterialRequest(
        site_id=request.site_id,
        project_id=request.project_id,
        material_id=request.material_id,
        quantity=request.quantity,
        requested_by=current_user.id,
        priority=request.priority or "normal",
        required_date=req_date,
        estimated_unit_cost=unit_cost,
        total_estimated_cost=total_cost,
        attachment_url=request.attachment_url,
        justification=request.justification,
        pm_status="pending",
        finance_status="not_applicable"
    )
    db.add(new_request)
    db.flush()
    audit(db, current_user, "material_request.created", "material_request", new_request.id, {"site_id": request.site_id, "quantity": request.quantity})
    db.commit()
    db.refresh(new_request)
    
    return MaterialRequestSchema(
        id=new_request.id,
        material_name=material.name,
        quantity=float(new_request.quantity),
        unit=material.unit,
        site_name=site.name,
        requested_by_name=current_user.name,
        created_at=new_request.created_at,
        priority=new_request.priority,
        required_date=new_request.required_date,
        estimated_unit_cost=float(new_request.estimated_unit_cost) if new_request.estimated_unit_cost is not None else None,
        total_estimated_cost=float(new_request.total_estimated_cost) if new_request.total_estimated_cost is not None else None,
        attachment_url=new_request.attachment_url,
        justification=new_request.justification,
        pm_status=new_request.pm_status,
        pm_reviewed_by_name=None,
        pm_notes=None,
        finance_status=new_request.finance_status,
        finance_reviewed_by_name=None,
        finance_notes=None,
        quotes=[],
        po_status=None
    )

@router.patch("/requests/{request_id}/pm-review")
async def pm_review_request(request_id: int, review: ReviewSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    req = db.query(MaterialRequest, Site).join(Site, MaterialRequest.site_id == Site.id).filter(MaterialRequest.id == request_id, Site.company_id == current_user.company_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Material request not found")
    request = req[0]
    if request.pm_status != "pending":
        raise HTTPException(status_code=409, detail="Request has already been reviewed")
    request.pm_status = "approved" if review.approved else "rejected"
    request.finance_status = "pending" if review.approved else "not_applicable"
    request.pm_reviewed_by = current_user.id
    request.pm_reviewed_at = func.now()
    audit(db, current_user, f"material_request.pm_{request.pm_status}", "material_request", request.id, {"reason": review.reason})
    db.commit()
    return {"status": request.pm_status}

@router.patch("/requests/{request_id}/finance-review")
async def finance_review_request(request_id: int, review: ReviewSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    req = db.query(MaterialRequest, Site).join(Site, MaterialRequest.site_id == Site.id).filter(MaterialRequest.id == request_id, Site.company_id == current_user.company_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Material request not found")
    request = req[0]
    if request.pm_status != "approved" or request.finance_status != "pending":
        raise HTTPException(status_code=409, detail="Request is not pending finance review")
    request.finance_status = "approved" if review.approved else "rejected"
    request.finance_reviewed_by = current_user.id
    request.finance_reviewed_at = func.now()
    audit(db, current_user, f"material_request.finance_{request.finance_status}", "material_request", request.id, {"reason": review.reason})
    db.commit()
    return {"status": request.finance_status}

@router.get("/quotes", response_model=PaginatedResponse[VendorQuoteSchema])
async def get_quotes(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role("admin", "finance"))
):
    query = db.query(VendorQuote, Vendor).join(Vendor, VendorQuote.vendor_id == Vendor.id).join(MaterialRequest, VendorQuote.request_id == MaterialRequest.id).join(Site, MaterialRequest.site_id == Site.id).filter(Site.company_id == current_user.company_id)
    
    total = query.count()
    quotes_db = query.offset(skip).limit(limit).all()
    
    items = []
    for q, v in quotes_db:
        items.append(VendorQuoteSchema(
            id=q.id,
            vendor_name=v.name,
            unit_price=float(q.unit_price),
            total_price=float(q.total_price),
            delivery_days=q.delivery_days,
            is_selected=q.is_selected
        ))
        
    return PaginatedResponse[VendorQuoteSchema](
        items=items,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.post("/quotes")
async def add_quote(payload: VendorQuoteCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    request = db.query(MaterialRequest, Site).join(Site, MaterialRequest.site_id == Site.id).filter(MaterialRequest.id == payload.request_id, Site.company_id == current_user.company_id).first()
    vendor = db.query(Vendor).filter(Vendor.id == payload.vendor_id, Vendor.company_id == current_user.company_id).first()
    if not request or not vendor or payload.unit_price < 0 or payload.total_price < 0:
        raise HTTPException(status_code=400, detail="Invalid request, vendor, or quote")
    req = request[0]
    if req.pm_status != "approved" or req.finance_status not in ("pending", "approved"):
        raise HTTPException(status_code=409, detail="Quotes require PM approval")
    quote = VendorQuote(request_id=req.id, vendor_id=payload.vendor_id, unit_price=payload.unit_price, delivery_days=payload.delivery_days, total_price=payload.total_price)
    db.add(quote)
    db.flush()
    audit(db, current_user, "vendor_quote.created", "vendor_quote", quote.id, {"request_id": req.id})
    db.commit()
    return {"id": quote.id, "status": "created"}

@router.patch("/quotes/{quote_id}/select")
async def select_quote(quote_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    row = db.query(VendorQuote, MaterialRequest, Site).join(MaterialRequest, VendorQuote.request_id == MaterialRequest.id).join(Site, MaterialRequest.site_id == Site.id).filter(VendorQuote.id == quote_id, Site.company_id == current_user.company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")
    quote, request, site = row
    if request.pm_status != "approved" or request.finance_status != "approved":
        raise HTTPException(status_code=409, detail="Request must be approved by PM and Finance")
    db.query(VendorQuote).filter(VendorQuote.request_id == request.id).update({"is_selected": False})
    quote.is_selected = True
    audit(db, current_user, "vendor_quote.selected", "vendor_quote", quote.id, {"request_id": request.id})
    db.commit()
    return {"status": "selected"}

@router.post("/purchase-orders")
async def create_purchase_order(payload: PurchaseOrderCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    row = db.query(MaterialRequest, VendorQuote, Site).join(VendorQuote, VendorQuote.request_id == MaterialRequest.id).join(Site, MaterialRequest.site_id == Site.id).filter(MaterialRequest.id == payload.request_id, VendorQuote.id == payload.quote_id, Site.company_id == current_user.company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Approved request or quote not found")
    request, quote, site = row
    if request.pm_status != "approved" or request.finance_status != "approved" or not quote.is_selected:
        raise HTTPException(status_code=409, detail="Request and selected quote must be approved")
    existing = db.query(PurchaseOrder).filter(PurchaseOrder.request_id == request.id, PurchaseOrder.status.notin_(["cancelled", "rejected"])).first()
    if existing:
        raise HTTPException(status_code=409, detail="Purchase order already exists")
    po = PurchaseOrder(request_id=request.id, vendor_quote_id=quote.id, vendor_id=quote.vendor_id, quantity=request.quantity, unit_price=quote.unit_price, amount=quote.total_price, status="approved", approved_by=current_user.id, approved_at=func.now())
    db.add(po)
    db.flush()
    audit(db, current_user, "purchase_order.created", "purchase_order", po.id, {"request_id": request.id, "quote_id": quote.id})
    db.commit()
    return {"id": po.id, "status": po.status}
