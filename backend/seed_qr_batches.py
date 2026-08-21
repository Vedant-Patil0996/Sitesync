"""
Seed 4 demo material batches for the QR system demo.
Run after migrate_qr_batches.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app.db import base  # register all models
from app.db.session import SessionLocal
from app.models.inventory import Material, Inventory, MaterialBatch, InventoryTransaction, generate_batch_code
from app.models.site import Site
from app.models.user import User
from decimal import Decimal
from datetime import datetime, timezone

def main():
    db = SessionLocal()
    try:
        # Get company's first admin user
        admin = db.query(User).filter(User.role == "admin", User.is_active == True).first()
        if not admin:
            print("No admin user found!"); return
        print(f"Using admin: {admin.name} (company {admin.company_id})")

        # Get company's sites
        sites = db.query(Site).filter(Site.company_id == admin.company_id).limit(3).all()
        if not sites:
            print("No sites found!"); return
        site1 = sites[0]
        site2 = sites[1] if len(sites) > 1 else sites[0]
        print(f"Site1: {site1.name}, Site2: {site2.name}")

        # Get some materials
        materials = db.query(Material).filter(Material.company_id == admin.company_id).limit(4).all()
        if not materials:
            print("No materials found!"); return
        print(f"Materials: {[m.name for m in materials]}")

        demo_batches = [
            {
                "material": materials[0],
                "site": site1,
                "original_qty": 500,
                "current_qty": 100,
                "status": "PARTIALLY_CONSUMED",
                "notes": "Delivered by ABC Supplies, 21 Aug 2026",
            },
            {
                "material": materials[1] if len(materials) > 1 else materials[0],
                "site": site1,
                "original_qty": 200,
                "current_qty": 200,
                "status": "IN_STOCK",
                "notes": "Fresh delivery, quality certified",
            },
            {
                "material": materials[2] if len(materials) > 2 else materials[0],
                "site": site2,
                "original_qty": 800,
                "current_qty": 0,
                "status": "DEPLETED",
                "notes": "Used for Phase 1 foundation",
            },
            {
                "material": materials[3] if len(materials) > 3 else materials[0],
                "site": site1,
                "original_qty": 300,
                "current_qty": 300,
                "status": "TRANSFER_PENDING",
                "notes": "Pending transfer to Site B",
            },
        ]

        for b in demo_batches:
            # Check if a batch for this material+site already exists
            existing = db.query(MaterialBatch).filter(
                MaterialBatch.material_id == b["material"].id,
                MaterialBatch.status == b["status"],
            ).first()
            if existing:
                print(f"  Skipping (already exists): {b['material'].name} / {b['status']}")
                continue

            batch = MaterialBatch(
                batch_code=generate_batch_code(),
                material_id=b["material"].id,
                site_id=b["site"].id,
                original_qty=Decimal(str(b["original_qty"])),
                current_qty=Decimal(str(b["current_qty"])),
                unit=b["material"].unit,
                status=b["status"],
                received_by=admin.id,
                received_at=datetime.now(timezone.utc),
                notes=b["notes"],
            )
            db.add(batch)
            db.flush()

            # Add a sample transaction for each
            db.add(InventoryTransaction(
                site_id=b["site"].id,
                material_id=b["material"].id,
                user_id=admin.id,
                type="IN",
                action="RECEIVE",
                quantity=Decimal(str(b["original_qty"])),
                batch_id=batch.id,
                reference="Demo seed",
            ))

            if b["current_qty"] < b["original_qty"] and b["current_qty"] >= 0:
                consumed = b["original_qty"] - b["current_qty"]
                db.add(InventoryTransaction(
                    site_id=b["site"].id,
                    material_id=b["material"].id,
                    user_id=admin.id,
                    type="OUT",
                    action="CONSUME",
                    quantity=Decimal(str(consumed)),
                    batch_id=batch.id,
                    reason="Foundation work — demo",
                ))

            print(f"  Created batch {batch.batch_code}: {b['material'].name} ({b['status']})")

        db.commit()
        print("\nSeeding complete!")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
