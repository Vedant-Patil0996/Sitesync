"""
Material QR lifecycle service.
All business logic lives here — API routes are thin.
"""
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.inventory import (
    Material, Inventory, InventoryTransaction,
    MaterialBatch, DeliveryDiscrepancy, generate_batch_code
)
from app.models.site import Site
from app.models.user import User
from app.core.deps import require_site_access, audit
from fastapi import HTTPException


# ─── helpers ───────────────────────────────────────────────────────────────────

def _get_batch(db: Session, batch_code: str, user: User) -> MaterialBatch:
    """Fetch batch and verify company ownership."""
    batch = db.query(MaterialBatch).filter(MaterialBatch.batch_code == batch_code).first()
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch {batch_code!r} not found")
    # Verify the batch's site belongs to the same company
    site = db.query(Site).filter(Site.id == batch.site_id).first()
    if not site or site.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Access denied to this batch")
    return batch


def _get_or_create_inv(db: Session, site_id: int, material_id: int, unit: str = "") -> Inventory:
    inv = db.query(Inventory).filter(
        Inventory.site_id == site_id, Inventory.material_id == material_id
    ).with_for_update().first()
    if not inv:
        mat = db.query(Material).filter(Material.id == material_id).first()
        inv = Inventory(
            site_id=site_id,
            material_id=material_id,
            quantity=0,
            reorder_level=mat.default_reorder_level if mat else 0
        )
        db.add(inv)
        db.flush()
    return inv


def _log_tx(db: Session, *, site_id, material_id, user_id, tx_type, action,
             quantity, batch_id=None, related_site_id=None, reason=None, reference=None):
    tx = InventoryTransaction(
        site_id=site_id, material_id=material_id, user_id=user_id,
        type=tx_type, action=action, quantity=quantity,
        batch_id=batch_id, related_site_id=related_site_id,
        reason=reason, reference=reference,
    )
    db.add(tx)
    db.flush()
    return tx


# ─── batch creation ────────────────────────────────────────────────────────────

def create_batch(db: Session, *, material_id: int, site_id: int, qty: float,
                 user: User, supplier_id: Optional[int] = None, notes: Optional[str] = None) -> MaterialBatch:
    """Create a new material batch (digital passport)."""
    material = db.query(Material).filter(
        Material.id == material_id, Material.company_id == user.company_id
    ).first()
    if not material:
        raise HTTPException(404, "Material not found")

    require_site_access(db, user, site_id)

    batch = MaterialBatch(
        batch_code=generate_batch_code(),
        material_id=material_id,
        site_id=site_id,
        supplier_id=supplier_id,
        original_qty=Decimal(str(qty)),
        current_qty=Decimal(str(qty)),
        unit=material.unit,
        status="RECEIVED",
        received_by=user.id,
        received_at=datetime.now(timezone.utc),
        notes=notes,
    )
    db.add(batch)
    db.flush()

    # Also update live inventory
    inv = _get_or_create_inv(db, site_id, material_id)
    inv.quantity += Decimal(str(qty))

    tx = _log_tx(db, site_id=site_id, material_id=material_id, user_id=user.id,
                 tx_type="IN", action="RECEIVE", quantity=qty, batch_id=batch.id)
    audit(db, user, "batch.created", "material_batch", batch.id,
          {"batch_code": batch.batch_code, "qty": qty})
    db.commit()
    return batch


# ─── receive (with discrepancy check) ─────────────────────────────────────────

def receive_batch(db: Session, *, batch_code: str, actual_qty: float,
                  expected_qty: float, user: User) -> dict:
    """Record actual received quantity for an existing batch."""
    batch = _get_batch(db, batch_code, user)
    require_site_access(db, user, batch.site_id, write=True)

    actual = Decimal(str(actual_qty))
    expected = Decimal(str(expected_qty))

    # Update batch
    batch.current_qty = actual
    batch.original_qty = expected
    batch.status = "IN_STOCK" if actual == expected else "RECEIVED"
    batch.received_by = user.id
    batch.received_at = datetime.now(timezone.utc)

    # Update inventory
    inv = _get_or_create_inv(db, batch.site_id, batch.material_id)
    inv.quantity += actual

    tx = _log_tx(db, site_id=batch.site_id, material_id=batch.material_id, user_id=user.id,
                 tx_type="IN", action="RECEIVE", quantity=actual, batch_id=batch.id)
    audit(db, user, "batch.received", "material_batch", batch.id, {"actual": float(actual)})

    # Discrepancy detection
    discrepancy = None
    if actual != expected:
        diff = actual - expected
        disc = DeliveryDiscrepancy(
            batch_id=batch.id, expected_qty=expected, actual_qty=actual,
            difference=diff, reported_by=user.id, site_id=batch.site_id
        )
        db.add(disc)
        db.flush()
        discrepancy = {"expected": float(expected), "actual": float(actual), "diff": float(diff)}

        # Notify via existing notification service
        try:
            from app.services.notification_service import create_alert_and_notify
            from app.db.session import SessionLocal
            mat = db.query(Material).filter(Material.id == batch.material_id).first()
            report = f"# Delivery Discrepancy Detected\nBatch {batch.batch_code} for {mat.name if mat else 'material'}: expected {float(expected)} but received {float(actual)} ({float(diff):+.0f})."
            create_alert_and_notify(db=db, site_id=batch.site_id, report=report,
                                     scenario_id="vendor_price_spike", run_id=f"disc_{batch.id}")
        except Exception as e:
            print(f"[QR] Discrepancy notification error: {e}", flush=True)

    db.commit()
    return {"status": "received", "batch_code": batch.batch_code, "discrepancy": discrepancy}


# ─── consume ──────────────────────────────────────────────────────────────────

def consume_batch(db: Session, *, batch_code: str, qty: float,
                  user: User, reason: Optional[str] = None, activity: Optional[str] = None) -> dict:
    """Consume material from a batch."""
    batch = _get_batch(db, batch_code, user)
    require_site_access(db, user, batch.site_id, write=True)

    quantity = Decimal(str(qty))
    if batch.current_qty < quantity:
        raise HTTPException(400, f"Insufficient stock in batch. Available: {float(batch.current_qty)}")

    batch.current_qty -= quantity
    if batch.current_qty == 0:
        batch.status = "DEPLETED"
    elif batch.current_qty < batch.original_qty:
        batch.status = "PARTIALLY_CONSUMED"

    inv = _get_or_create_inv(db, batch.site_id, batch.material_id)
    if inv.quantity < quantity:
        raise HTTPException(400, "Insufficient site inventory")
    inv.quantity -= quantity

    note = activity or reason
    tx = _log_tx(db, site_id=batch.site_id, material_id=batch.material_id, user_id=user.id,
                 tx_type="OUT", action="CONSUME", quantity=quantity,
                 batch_id=batch.id, reason=note)
    audit(db, user, "batch.consumed", "material_batch", batch.id, {"qty": qty, "activity": activity})

    # Stockout check
    pct = float(batch.current_qty) / float(batch.original_qty) if float(batch.original_qty) > 0 else 0
    if pct < 0.2:
        try:
            from app.services.notification_service import create_alert_and_notify
            mat = db.query(Material).filter(Material.id == batch.material_id).first()
            report = f"# Critical Stock Alert\nBatch {batch.batch_code} ({mat.name if mat else 'material'}) is at {pct:.0%} remaining ({float(batch.current_qty)} {batch.unit}). Stockout imminent."
            create_alert_and_notify(db=db, site_id=batch.site_id, report=report,
                                     scenario_id="stock_critically_low", run_id=f"qr_{batch.id}")
        except Exception as e:
            print(f"[QR] Stockout notification error: {e}", flush=True)

    db.commit()
    return {"status": "consumed", "batch_code": batch.batch_code, "remaining": float(batch.current_qty)}


# ─── transfer ─────────────────────────────────────────────────────────────────

def transfer_batch(db: Session, *, batch_code: str, qty: float,
                   dest_site_id: int, user: User, reference: Optional[str] = None) -> dict:
    """Initiate a site-to-site transfer (creates TRANSFER_PENDING)."""
    batch = _get_batch(db, batch_code, user)
    require_site_access(db, user, batch.site_id, write=True)
    require_site_access(db, user, dest_site_id, write=True)

    quantity = Decimal(str(qty))
    if batch.current_qty < quantity:
        raise HTTPException(400, f"Insufficient stock. Available: {float(batch.current_qty)}")
    if batch.site_id == dest_site_id:
        raise HTTPException(400, "Source and destination sites must differ")

    batch.current_qty -= quantity
    batch.status = "TRANSFER_PENDING" if batch.current_qty == 0 else "PARTIALLY_CONSUMED"

    inv_src = _get_or_create_inv(db, batch.site_id, batch.material_id)
    if inv_src.quantity < quantity:
        raise HTTPException(400, "Insufficient site inventory")
    inv_src.quantity -= quantity

    src_site_id = batch.site_id

    # Create TRANSFER_OUT transaction on source
    tx_out = _log_tx(db, site_id=src_site_id, material_id=batch.material_id, user_id=user.id,
                     tx_type="TRANSFER_OUT", action="TRANSFER", quantity=quantity,
                     batch_id=batch.id, related_site_id=dest_site_id, reference=reference)

    audit(db, user, "batch.transfer_initiated", "material_batch", batch.id,
          {"qty": qty, "dest_site_id": dest_site_id})
    db.commit()
    return {
        "status": "transfer_pending",
        "batch_code": batch.batch_code,
        "source_tx_id": tx_out.id,
        "dest_site_id": dest_site_id,
        "qty": qty,
    }


def accept_transfer(db: Session, *, batch_code: str, qty: float, user: User) -> dict:
    """Accept an incoming transfer to the user's site."""
    batch = _get_batch(db, batch_code, user)
    # The transfer target site is derived from pending TRANSFER_OUT
    # For simplicity: accept_transfer is called by destination user
    # We update inventory on their site
    dest_site_id = None
    for sa in user.company_id and []:
        pass
    # Find which site this user can access that has a pending tx
    from app.models.site import SiteAssignment
    assigned = db.query(SiteAssignment).filter(SiteAssignment.user_id == user.id).all()
    site_ids = [a.site_id for a in assigned]

    quantity = Decimal(str(qty))
    batch.current_qty += quantity
    batch.status = "IN_STOCK"

    # Find the first assigned site for this user
    target_site_id = site_ids[0] if site_ids else batch.site_id

    inv_dst = _get_or_create_inv(db, target_site_id, batch.material_id)
    inv_dst.quantity += quantity

    tx_in = _log_tx(db, site_id=target_site_id, material_id=batch.material_id, user_id=user.id,
                    tx_type="TRANSFER_IN", action="TRANSFER", quantity=quantity,
                    batch_id=batch.id, related_site_id=batch.site_id)

    audit(db, user, "batch.transfer_accepted", "material_batch", batch.id, {"qty": qty})
    db.commit()
    return {"status": "transfer_accepted", "batch_code": batch.batch_code, "qty": qty}


# ─── damage ───────────────────────────────────────────────────────────────────

def damage_batch(db: Session, *, batch_code: str, qty: float,
                 user: User, reason: Optional[str] = None) -> dict:
    batch = _get_batch(db, batch_code, user)
    require_site_access(db, user, batch.site_id, write=True)

    quantity = Decimal(str(qty))
    if batch.current_qty < quantity:
        raise HTTPException(400, f"Insufficient stock for damage report. Available: {float(batch.current_qty)}")

    batch.current_qty -= quantity
    batch.status = "DAMAGED" if batch.current_qty == 0 else "PARTIALLY_CONSUMED"

    inv = _get_or_create_inv(db, batch.site_id, batch.material_id)
    if inv.quantity >= quantity:
        inv.quantity -= quantity

    tx = _log_tx(db, site_id=batch.site_id, material_id=batch.material_id, user_id=user.id,
                 tx_type="OUT", action="DAMAGE", quantity=quantity,
                 batch_id=batch.id, reason=reason)
    audit(db, user, "batch.damaged", "material_batch", batch.id, {"qty": qty, "reason": reason})
    db.commit()
    return {"status": "damage_recorded", "batch_code": batch.batch_code, "damaged_qty": qty}


# ─── return ───────────────────────────────────────────────────────────────────

def return_batch(db: Session, *, batch_code: str, qty: float,
                 user: User, reason: Optional[str] = None) -> dict:
    batch = _get_batch(db, batch_code, user)
    require_site_access(db, user, batch.site_id, write=True)

    quantity = Decimal(str(qty))
    batch.current_qty -= quantity
    if batch.current_qty <= 0:
        batch.current_qty = Decimal("0")
        batch.status = "RETURNED"

    inv = _get_or_create_inv(db, batch.site_id, batch.material_id)
    if inv.quantity >= quantity:
        inv.quantity -= quantity

    tx = _log_tx(db, site_id=batch.site_id, material_id=batch.material_id, user_id=user.id,
                 tx_type="OUT", action="RETURN", quantity=quantity,
                 batch_id=batch.id, reason=reason)
    audit(db, user, "batch.returned", "material_batch", batch.id, {"qty": qty, "reason": reason})
    db.commit()
    return {"status": "return_recorded", "batch_code": batch.batch_code}


# ─── batch passport / timeline ────────────────────────────────────────────────

def get_batch_passport(db: Session, batch_code: str, user: User) -> dict:
    """Return the full Material Passport for a batch."""
    batch = _get_batch(db, batch_code, user)
    mat = db.query(Material).filter(Material.id == batch.material_id).first()
    site = db.query(Site).filter(Site.id == batch.site_id).first()
    receiver = db.query(User).filter(User.id == batch.received_by).first() if batch.received_by else None
    supplier = None
    if batch.supplier_id:
        from app.models.vendor import Vendor
        supplier = db.query(Vendor).filter(Vendor.id == batch.supplier_id).first()

    # Build timeline
    txs = db.query(InventoryTransaction, User).join(
        User, InventoryTransaction.user_id == User.id
    ).filter(InventoryTransaction.batch_id == batch.id).order_by(InventoryTransaction.date.asc()).all()

    timeline = []
    for tx, u in txs:
        timeline.append({
            "action": tx.action or tx.type,
            "quantity": float(tx.quantity),
            "performed_by": u.name,
            "role": u.role,
            "date": tx.date.isoformat() if tx.date else None,
            "reason": tx.reason,
        })

    # Discrepancies
    discs = db.query(DeliveryDiscrepancy).filter(DeliveryDiscrepancy.batch_id == batch.id).all()

    pct_used = 0.0
    if float(batch.original_qty) > 0:
        pct_used = (1 - float(batch.current_qty) / float(batch.original_qty)) * 100

    return {
        "batch_code": batch.batch_code,
        "material_name": mat.name if mat else "Unknown",
        "material_id": batch.material_id,
        "unit": batch.unit,
        "site_name": site.name if site else "Unknown",
        "site_id": batch.site_id,
        "supplier": supplier.name if supplier else None,
        "original_qty": float(batch.original_qty),
        "current_qty": float(batch.current_qty),
        "pct_used": round(pct_used, 1),
        "status": batch.status,
        "received_by": receiver.name if receiver else None,
        "received_at": batch.received_at.isoformat() if batch.received_at else None,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "notes": batch.notes,
        "timeline": timeline,
        "discrepancies": [
            {
                "expected": float(d.expected_qty),
                "actual": float(d.actual_qty),
                "diff": float(d.difference),
                "date": d.created_at.isoformat() if d.created_at else None,
            }
            for d in discs
        ],
    }
