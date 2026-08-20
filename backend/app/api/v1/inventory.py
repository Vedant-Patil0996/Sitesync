from decimal import Decimal
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user, require_role, require_site_access, audit
from app.models.user import User
from app.models.site import Site, SiteAssignment
from app.models.inventory import Inventory, Material, InventoryTransaction
from app.schemas.inventory import InventorySchema, TransactionCreateSchema, MaterialSchema, TransferCreateSchema, InventoryTransactionSchema
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
    if current_user.role in ("pm", "contractor"):
        query = query.filter(Site.id.in_(db.query(SiteAssignment.site_id).filter(SiteAssignment.user_id == current_user.id)))
        
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

@router.get("/materials", response_model=list[MaterialSchema])
async def get_materials(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    materials = db.query(Material).filter(Material.company_id == current_user.company_id).all()
    return [
        MaterialSchema(
            id=m.id,
            name=m.name,
            unit=m.unit,
            default_reorder_level=float(m.default_reorder_level),
            barcode_code=m.barcode_code
        ) for m in materials
    ]
@router.get("/by-site/{site_id}")
async def get_site_inventory(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_site_access(db, current_user, site_id)
    rows = db.query(Inventory, Material).join(Material, Inventory.material_id == Material.id).filter(Inventory.site_id == site_id).all()
    site = db.query(Site).filter(Site.id == site_id).first()
    return [InventorySchema(
        id=inv.id, site_id=inv.site_id, site_name=site.name, material_id=inv.material_id,
        material_name=mat.name, unit=mat.unit, quantity=float(inv.quantity),
        reorder_level=float(inv.reorder_level), updated_at=inv.updated_at
    ) for inv, mat in rows]

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
        
    require_site_access(db, current_user, tx.site_id, write=True)

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

    tx_qty = Decimal(str(tx.quantity))
    tx_type_raw = tx.type.lower()

    # Map transaction type to DB check constraint values ('IN', 'OUT', 'TRANSFER_IN', 'TRANSFER_OUT')
    type_mapping = {
        "stock_in": "IN",
        "in": "IN",
        "stock_out": "OUT",
        "out": "OUT",
        "transfer_in": "TRANSFER_IN",
        "transfer_out": "TRANSFER_OUT"
    }

    db_tx_type = type_mapping.get(tx_type_raw)
    if not db_tx_type:
        raise HTTPException(status_code=400, detail=f"Invalid transaction type: {tx.type}")

    # Update quantity based on type
    if db_tx_type in ["IN", "TRANSFER_IN"]:
        inv.quantity += tx_qty
    elif db_tx_type in ["OUT", "TRANSFER_OUT"]:
        if inv.quantity < tx_qty:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        inv.quantity -= tx_qty

    # Create transaction log
    transaction = InventoryTransaction(
        site_id=tx.site_id,
        material_id=tx.material_id,
        user_id=current_user.id,
        type=db_tx_type,
        quantity=tx_qty,
        reference=tx.reference
    )
    db.add(transaction)
    db.flush()
    audit(db, current_user, f"inventory.{db_tx_type.lower()}", "inventory_transaction", transaction.id, {
        "site_id": tx.site_id, "material_id": tx.material_id, "quantity": float(tx.quantity)
    })
    db.commit()
    
    return {"status": "success"}

@router.post("/transfers")
async def transfer_inventory(
    transfer: TransferCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pm")),
):
    if transfer.source_site_id == transfer.destination_site_id:
        raise HTTPException(status_code=400, detail="Source and destination sites must differ")
    if transfer.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    require_site_access(db, current_user, transfer.source_site_id, write=True)
    require_site_access(db, current_user, transfer.destination_site_id, write=True)
    material = db.query(Material).filter(Material.id == transfer.material_id, Material.company_id == current_user.company_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    source = db.query(Inventory).filter(Inventory.site_id == transfer.source_site_id, Inventory.material_id == transfer.material_id).with_for_update().first()
    if not source or source.quantity < Decimal(str(transfer.quantity)):
        raise HTTPException(status_code=400, detail="Insufficient stock at source site")
    destination = db.query(Inventory).filter(Inventory.site_id == transfer.destination_site_id, Inventory.material_id == transfer.material_id).with_for_update().first()
    if not destination:
        destination = Inventory(site_id=transfer.destination_site_id, material_id=transfer.material_id, quantity=0, reorder_level=material.default_reorder_level)
        db.add(destination)
        db.flush()
    quantity = Decimal(str(transfer.quantity))
    source.quantity -= quantity
    destination.quantity += quantity
    source_tx = InventoryTransaction(site_id=transfer.source_site_id, material_id=transfer.material_id, user_id=current_user.id, type="TRANSFER_OUT", quantity=quantity, related_site_id=transfer.destination_site_id, reference=transfer.reference)
    destination_tx = InventoryTransaction(site_id=transfer.destination_site_id, material_id=transfer.material_id, user_id=current_user.id, type="TRANSFER_IN", quantity=quantity, related_site_id=transfer.source_site_id, reference=transfer.reference)
    db.add_all([source_tx, destination_tx])
    db.flush()
    audit(db, current_user, "inventory.transfer", "inventory_transaction", source_tx.id, {"destination_transaction_id": destination_tx.id, "quantity": float(quantity)})
    db.commit()
    return {"status": "success", "source_transaction_id": source_tx.id, "destination_transaction_id": destination_tx.id}

@router.get("/transactions", response_model=list[InventoryTransactionSchema])
async def get_transactions(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "contractor", "finance"))):
    query = db.query(InventoryTransaction, Material, User, Site).join(Material, InventoryTransaction.material_id == Material.id).join(User, InventoryTransaction.user_id == User.id).join(Site, InventoryTransaction.site_id == Site.id).filter(Site.company_id == current_user.company_id)
    if current_user.role in ("pm", "contractor"):
        query = query.filter(Site.id.in_(db.query(SiteAssignment.site_id).filter(SiteAssignment.user_id == current_user.id)))
    rows = query.order_by(InventoryTransaction.date.desc()).limit(200).all()
    return [InventoryTransactionSchema(id=tx.id, type=tx.type, material_name=mat.name, unit=mat.unit, quantity=float(tx.quantity), performed_by_name=user.name, note=tx.reference, created_at=tx.date) for tx, mat, user, site in rows]
