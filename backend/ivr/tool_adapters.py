import sys
import os
import json

# Add project root to sys.path so we can import the 'ai' package
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from ai.tools import stock, equipment, budget
from app.db.session import SessionLocal
from app.models.inventory import Inventory, Material

def query_stock(material_id: str, site_id: str) -> str:
    """
    Queries the current stock quantity for a given matcderial and site.
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
def query_equipment(equipment_id: str) -> str:
    """
    Queries equipment status.
    """
    try:
        status = equipment.get_equipment_status(equipment_id=equipment_id)
        return json.dumps({"equipment_id": equipment_id, "status": status})
    except Exception as e:
        return json.dumps({"error": str(e)})

def query_budget(site_id: str) -> str:
    """
    Queries budget actuals for a site.
    """
    try:
        actuals = budget.get_budget_actuals(site_id=site_id)
        return json.dumps({"site_id": site_id, "budget_actuals": actuals})
    except Exception as e:
        return json.dumps({"error": str(e)})
