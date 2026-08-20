from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.site import Site
from app.models.inventory import Inventory, Material, InventoryTransaction
from app.schemas.inventory import InventorySchema, TransactionCreateSchema
from app.schemas.common import PaginatedResponse

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[InventorySchema])
async def get_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role("admin", "pm", "finance"))
):
    query = db.query(Inventory, Material, Site)\
        .join(Material, Inventory.material_id == Material.id)\
        .join(Site, Inventory.site_id == Site.id)\
        .filter(Site.company_id == current_user.company_id)
        
    total = query.count()
    inventory_db = query.offset(skip).limit(limit).all()
    
    items = []
    for inv, mat, site in inventory_db:
        items.append(InventorySchema(
            id=inv.id,
            site_id=inv.site_id,
            site_name=site.name,
            material_id=inv.material_id,
            material_name=mat.name,
            unit=mat.unit,
            quantity=float(inv.quantity),
            reorder_level=float(inv.reorder_level),
            updated_at=inv.updated_at
        ))
        
    return PaginatedResponse[InventorySchema](
        items=items,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.get("/by-site/{site_id}")
async def get_site_inventory(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@router.post("/transactions")
async def log_transaction(
    tx: TransactionCreateSchema,
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role("admin", "pm", "contractor"))
):
    # check if material exists and belongs to company
    material = db.query(Material).filter(Material.id == tx.material_id, Material.company_id == current_user.company_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
        
    # check if site belongs to company
    site = db.query(Site).filter(Site.id == tx.site_id, Site.company_id == current_user.company_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # get or create inventory record
    inv = db.query(Inventory).filter(Inventory.site_id == tx.site_id, Inventory.material_id == tx.material_id).first()
    if not inv:
        inv = Inventory(
            site_id=tx.site_id,
            material_id=tx.material_id,
            quantity=0,
            reorder_level=material.default_reorder_level
        )
        db.add(inv)
        db.flush()

    # Update quantity based on type
    if tx.type in ["stock_in", "transfer_in"]:
        inv.quantity += tx.quantity
    elif tx.type in ["stock_out", "transfer_out"]:
        if inv.quantity < tx.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        inv.quantity -= tx.quantity
    else:
        raise HTTPException(status_code=400, detail="Invalid transaction type")

    # Create transaction log
    transaction = InventoryTransaction(
        site_id=tx.site_id,
        material_id=tx.material_id,
        user_id=current_user.id,
        type=tx.type.upper(),
        quantity=tx.quantity,
        reference=tx.reference
    )
    db.add(transaction)
    db.commit()
    
    return {"status": "success"}

@router.get("/transactions")
async def get_transactions(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    return []
