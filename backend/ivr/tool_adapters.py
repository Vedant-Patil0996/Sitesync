import sys
import os
import json

# Add project root to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from app.db.session import SessionLocal
from app.models.inventory import Inventory, Material

def query_stock(material_id: str, site_id: str) -> str:
    """
    Queries the current stock quantity for a given material and site.
    """
    db = SessionLocal()
    try:
        inv = db.query(Inventory).filter(Inventory.material_id == material_id, Inventory.site_id == site_id).first()
        mat = db.query(Material).filter(Material.id == material_id).first()
        if inv and mat:
            data = {
                "material_name": mat.name,
                "current_stock": float(inv.quantity),
                "unit": mat.unit,
                "site_id": site_id
            }
            return json.dumps(data)
        return json.dumps({"error": "Stock not found for this material at this site."})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()

def query_equipment(equipment_name: str) -> str:
    """
    Queries equipment status using fuzzy matching in SQLAlchemy, skipping question modifiers.
    """
    db = SessionLocal()
    try:
        from app.models.equipment import Equipment
        from app.models.site import Site
        from sqlalchemy import or_

        # Split words to find the actual equipment keyword (e.g. "crane" or "excavator")
        search_words = [w.strip() for w in equipment_name.lower().split() if len(w.strip()) > 2]
        
        eq = None
        for word in search_words:
            # Skip common question/retrieval modifiers
            if word in ("where", "status", "check", "find", "locate", "info", "query", "is", "the"):
                continue
            eq = db.query(Equipment, Site).join(Site, Equipment.site_id == Site.id).filter(
                or_(
                    Equipment.name.ilike(f"%{word}%"),
                    Equipment.type.ilike(f"%{word}%")
                )
            ).first()
            if eq:
                break
                
        # Fallback to whole string match
        if not eq:
            eq = db.query(Equipment, Site).join(Site, Equipment.site_id == Site.id).filter(
                or_(
                    Equipment.name.ilike(f"%{equipment_name}%"),
                    Equipment.type.ilike(f"%{equipment_name}%")
                )
            ).first()

        if eq:
            eq_obj, site_obj = eq
            data = {
                "equipment_name": eq_obj.name,
                "type": eq_obj.type,
                "status": eq_obj.status,
                "site_name": site_obj.name,
                "hours_used": float(eq_obj.hours_used)
            }
            return json.dumps(data)
        return json.dumps({"error": f"Equipment matching '{equipment_name}' not found."})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()

def query_budget(site_id: str) -> str:
    """
    Queries budget actuals for a site using SQLAlchemy.
    """
    db = SessionLocal()
    try:
        from app.models.site import Site
        from app.models.project import Project
        from app.models.finance import Expense, Payment
        from app.models.procurement import PurchaseOrder, MaterialRequest
        from sqlalchemy import func

        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            return json.dumps({"error": "Site not found."})

        # Get total budget from projects assigned to the site
        site_budget = db.query(func.sum(Project.budget_allocated)).filter(Project.site_id == site_id).scalar() or 0

        # Get expenses on the site
        site_expenses = db.query(func.sum(Expense.amount)).filter(Expense.site_id == site_id).scalar() or 0

        # Get released payments on the site
        site_payments = db.query(func.sum(Payment.amount))\
            .join(PurchaseOrder, Payment.po_id == PurchaseOrder.id)\
            .join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id)\
            .filter(MaterialRequest.site_id == site_id, Payment.status == "released")\
            .scalar() or 0

        total_spent = float(site_expenses) + float(site_payments)
        allocated = float(site_budget)

        data = {
            "site_name": site.name,
            "allocated": allocated,
            "spent": total_spent,
            "remaining": allocated - total_spent,
            "utilization_percent": round((total_spent / allocated) * 100) if allocated > 0 else 0
        }
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()
