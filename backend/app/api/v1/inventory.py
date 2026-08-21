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


# ───────────────────────────── QR BATCH ENDPOINTS ──────────────────────────────

from app.models.inventory import MaterialBatch, DeliveryDiscrepancy
from app.models.vendor import Vendor
import csv, io
from fastapi.responses import StreamingResponse


@router.get("/batches/export")
async def export_batches(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pm", "finance", "contractor"))
):
    """Export all material batches as CSV."""
    query = db.query(MaterialBatch, Material, Site)\
        .join(Material, MaterialBatch.material_id == Material.id)\
        .join(Site, MaterialBatch.site_id == Site.id)\
        .filter(Site.company_id == current_user.company_id)\
        .order_by(MaterialBatch.created_at.desc())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Batch Code", "Material", "Site", "Unit", "Original Qty",
                     "Current Qty", "Status", "Received At", "Notes"])
    for batch, mat, site in query.all():
        writer.writerow([
            batch.batch_code, mat.name, site.name, batch.unit,
            float(batch.original_qty), float(batch.current_qty),
            batch.status,
            batch.received_at.isoformat() if batch.received_at else "",
            batch.notes or ""
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="batches.csv"'}
    )


@router.get("/batches")
async def list_batches(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pm", "finance", "contractor"))
):
    """List all material batches (company-scoped)."""
    query = db.query(MaterialBatch, Material, Site)\
        .join(Material, MaterialBatch.material_id == Material.id)\
        .join(Site, MaterialBatch.site_id == Site.id)\
        .filter(Site.company_id == current_user.company_id)\
        .order_by(MaterialBatch.created_at.desc())

    results = []
    for batch, mat, site in query.all():
        pct = 0.0
        if float(batch.original_qty) > 0:
            pct = round(float(batch.current_qty) / float(batch.original_qty) * 100, 1)
        results.append({
            "id": batch.id,
            "batch_code": batch.batch_code,
            "material_name": mat.name,
            "material_id": batch.material_id,
            "site_name": site.name,
            "site_id": batch.site_id,
            "unit": batch.unit,
            "original_qty": float(batch.original_qty),
            "current_qty": float(batch.current_qty),
            "pct_remaining": pct,
            "status": batch.status,
            "received_at": batch.received_at.isoformat() if batch.received_at else None,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
        })
    return results


@router.post("/batches")
async def create_batch(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pm", "contractor"))
):
    """Create a new material batch and generate its QR batch code."""
    from app.services.material_service import create_batch
    batch = create_batch(
        db, material_id=payload["material_id"], site_id=payload["site_id"],
        qty=payload["qty"], user=current_user,
        supplier_id=payload.get("supplier_id"), notes=payload.get("notes")
    )
    return {"batch_code": batch.batch_code, "id": batch.id, "status": batch.status}


@router.post("/scan")
async def scan_batch(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pm", "contractor"))
):
    """Decode a QR scan payload and return the Material Passport."""
    from app.services.material_service import get_batch_passport
    # QR payload: {"type": "SITESYNC_MATERIAL", "v": 1, "batch_id": "BAT-2026-XXXXX"}
    batch_code = payload.get("batch_id") or payload.get("batch_code")
    if not batch_code:
        raise HTTPException(status_code=400, detail="QR payload missing batch_id")
    return get_batch_passport(db, batch_code, current_user)


@router.get("/batches/{batch_code}/timeline")
async def get_batch_timeline(
    batch_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pm", "finance", "contractor"))
):
    from app.services.material_service import get_batch_passport
    return get_batch_passport(db, batch_code, current_user)


@router.post("/receive")
async def receive_batch_endpoint(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pm", "contractor"))
):
    """Record actual received quantity (triggers discrepancy if mismatch)."""
    from app.services.material_service import receive_batch
    return receive_batch(
        db, batch_code=payload["batch_code"],
        actual_qty=payload["actual_qty"],
        expected_qty=payload["expected_qty"],
        user=current_user
    )


@router.post("/consume")
async def consume_batch_endpoint(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pm", "contractor"))
):
    """Consume material from a batch."""
    from app.services.material_service import consume_batch
    return consume_batch(
        db, batch_code=payload["batch_code"],
        qty=payload["qty"],
        user=current_user,
        reason=payload.get("reason"),
        activity=payload.get("activity")
    )


@router.post("/transfer-batch")
async def transfer_batch_endpoint(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pm", "contractor"))
):
    """Initiate a batch transfer to another site."""
    from app.services.material_service import transfer_batch
    return transfer_batch(
        db, batch_code=payload["batch_code"],
        qty=payload["qty"],
        dest_site_id=payload["dest_site_id"],
        user=current_user,
        reference=payload.get("reference")
    )


@router.post("/damage")
async def damage_batch_endpoint(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pm", "contractor"))
):
    """Record damaged material from a batch."""
    from app.services.material_service import damage_batch
    return damage_batch(
        db, batch_code=payload["batch_code"],
        qty=payload["qty"],
        user=current_user,
        reason=payload.get("reason")
    )


@router.post("/return-batch")
async def return_batch_endpoint(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pm", "contractor"))
):
    """Return material from a batch."""
    from app.services.material_service import return_batch
    return return_batch(
        db, batch_code=payload["batch_code"],
        qty=payload["qty"],
        user=current_user,
        reason=payload.get("reason")
    )


@router.get("/discrepancies")
async def list_discrepancies(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pm"))
):
    """List all delivery discrepancies (admin/pm only)."""
    rows = db.query(DeliveryDiscrepancy, MaterialBatch, Material, User, Site)\
        .join(MaterialBatch, DeliveryDiscrepancy.batch_id == MaterialBatch.id)\
        .join(Material, MaterialBatch.material_id == Material.id)\
        .join(User, DeliveryDiscrepancy.reported_by == User.id)\
        .join(Site, DeliveryDiscrepancy.site_id == Site.id)\
        .filter(Site.company_id == current_user.company_id)\
        .order_by(DeliveryDiscrepancy.created_at.desc()).all()
    return [
        {
            "id": disc.id,
            "batch_code": batch.batch_code,
            "material_name": mat.name,
            "site_name": site.name,
            "expected_qty": float(disc.expected_qty),
            "actual_qty": float(disc.actual_qty),
            "difference": float(disc.difference),
            "reported_by": user.name,
            "created_at": disc.created_at.isoformat() if disc.created_at else None,
        }
        for disc, batch, mat, user, site in rows
    ]
