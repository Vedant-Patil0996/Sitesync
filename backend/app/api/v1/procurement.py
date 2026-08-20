from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.site import Site
from app.models.inventory import Material
from app.models.vendor import Vendor
from app.models.procurement import MaterialRequest, VendorQuote, PurchaseOrder
from app.schemas.procurement import MaterialRequestSchema, VendorQuoteSchema, MaterialRequestCreateSchema
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
    
    items = []
    for req, mat, site, user in requests_db:
        # Get reviewers
        pm_reviewer_name = None
        if req.pm_reviewed_by:
            pm_user = db.query(User).filter(User.id == req.pm_reviewed_by).first()
            if pm_user:
                pm_reviewer_name = pm_user.name
                
        fin_reviewer_name = None
        if req.finance_reviewed_by:
            fin_user = db.query(User).filter(User.id == req.finance_reviewed_by).first()
            if fin_user:
                fin_reviewer_name = fin_user.name
                
        # Get quotes
        quotes_db = db.query(VendorQuote, Vendor).join(Vendor, VendorQuote.vendor_id == Vendor.id).filter(VendorQuote.request_id == req.id).all()
        quotes = []
        for q, v in quotes_db:
            quotes.append(VendorQuoteSchema(
                id=q.id,
                vendor_name=v.name,
                unit_price=float(q.unit_price),
                total_price=float(q.total_price),
                delivery_days=q.delivery_days,
                is_selected=q.is_selected
            ))
            
        po = db.query(PurchaseOrder).filter(PurchaseOrder.request_id == req.id).first()
        po_status = po.status if po else None

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
    # Verify site exists and belongs to company
    site = db.query(Site).filter(Site.id == request.site_id, Site.company_id == current_user.company_id).first()
    if not site:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Site not found")
        
    # Verify material exists and belongs to company
    material = db.query(Material).filter(Material.id == request.material_id, Material.company_id == current_user.company_id).first()
    if not material:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Material not found")

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
async def pm_review_request(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    pass

@router.patch("/requests/{request_id}/finance-review")
async def finance_review_request(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    pass

@router.get("/quotes", response_model=PaginatedResponse[VendorQuoteSchema])
async def get_quotes(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role("admin", "finance"))
):
    # In a real app we'd join requests to filter by company.
    # For now simply paginating VendorQuotes directly for demonstration.
    query = db.query(VendorQuote, Vendor).join(Vendor, VendorQuote.vendor_id == Vendor.id)
    
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
async def add_quote(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    pass

@router.patch("/quotes/{quote_id}/select")
async def select_quote(quote_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "finance"))):
    pass
