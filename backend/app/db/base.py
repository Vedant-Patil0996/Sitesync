from app.db.session import Base  # noqa: F401 — imports all models so Base knows them

# Import every model here so SQLAlchemy registers them with Base.metadata
from app.models.company import Company          # noqa: F401
from app.models.user import User                # noqa: F401
from app.models.site import Site, SiteAssignment  # noqa: F401
from app.models.project import Project, Task, Milestone  # noqa: F401
from app.models.inventory import Material, Inventory, InventoryTransaction  # noqa: F401
from app.models.equipment import Equipment, EquipmentLog, LaborLog  # noqa: F401
from app.models.vendor import Vendor            # noqa: F401
from app.models.procurement import (            # noqa: F401
    MaterialRequest, VendorQuote, PurchaseOrder, Delivery
)
from app.models.finance import Payment, Expense  # noqa: F401
from app.models.alert import Alert, Notification  # noqa: F401
from app.models.audit import AuditLog           # noqa: F401
