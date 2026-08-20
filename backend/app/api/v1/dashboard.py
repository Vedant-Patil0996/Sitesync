from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.site import Site
from app.models.alert import Alert
from app.models.procurement import MaterialRequest, PurchaseOrder
from app.models.finance import Payment, Expense
from app.models.inventory import Inventory
from app.models.equipment import Equipment
from app.models.project import Project
from app.schemas.dashboard import DashboardSummary, AlertSchema, PendingRequestSchema, PendingPOSchema, EquipmentStatusSchema

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # This is a simplified version. In a real app, we would scope this to the user's company and site assignments.
    company_id = current_user.company_id

    # Sites
    total_sites = db.query(Site).filter(Site.company_id == company_id).count()
    active_sites = db.query(Site).filter(Site.company_id == company_id, Site.status == 'active').count()

    # Alerts (joining with Site to get site_name)
    alerts = db.query(Alert, Site.name.label('site_name')).join(Site).filter(Site.company_id == company_id, Alert.status == 'open').all()
    open_alerts = len(alerts)
    critical_alerts = sum(1 for a, _ in alerts if a.severity == 'critical')
    recent_alerts = []
    for a, s_name in sorted(alerts, key=lambda x: x[0].created_at, reverse=True)[:5]:
        recent_alerts.append(AlertSchema(
            id=a.id, site_id=a.site_id, site_name=s_name, project_id=a.project_id,
            type=a.type, severity=a.severity, title=a.title, description=a.description,
            status=a.status, created_at=a.created_at
        ))

    # Procurement
    # For simplicity we fetch all and slice in python for the list
    requests_query = db.query(MaterialRequest, Site.name.label('site_name'), User.name.label('requested_by_name'))\
                       .join(Site, MaterialRequest.site_id == Site.id)\
                       .join(User, MaterialRequest.requested_by == User.id)\
                       .filter(Site.company_id == company_id, MaterialRequest.pm_status == 'pending')
    reqs = requests_query.all()
    pending_requests = len(reqs)
    pending_requests_list = []
    for r, s_name, u_name in reqs[:4]:
        # Need to join Material to get material name properly, assuming material_id for now
        pending_requests_list.append(PendingRequestSchema(
            id=r.id, material_name=f"Material {r.material_id}", quantity=float(r.quantity), unit="unit",
            site_name=s_name, pm_status=r.pm_status, finance_status=r.finance_status, created_at=r.created_at
        ))

    pos_query = db.query(PurchaseOrder).filter(PurchaseOrder.status == 'pending_finance') # Need company filter via request/site
    pos = pos_query.all()
    pending_pos = len(pos)
    pending_po_amount = sum(float(p.amount) for p in pos)
    pending_pos_list = []
    for p in pos[:3]:
        pending_pos_list.append(PendingPOSchema(
            id=p.id, vendor_name=f"Vendor {p.vendor_id}", material_name="Material", amount=float(p.amount), status=p.status
        ))

    # Inventory
    low_stock = db.query(Inventory).filter(Inventory.quantity <= Inventory.reorder_level).count()

    # Users
    total_users = db.query(User).filter(User.company_id == company_id).count()
    active_users = db.query(User).filter(User.company_id == company_id, User.is_active == True).count()

    # Finance
    projects = db.query(Project).filter(Project.company_id == company_id).all()
    total_budget = sum(float(p.budget_allocated) for p in projects)
    
    # Total spend from Expenses
    expenses = db.query(Expense).join(Site).filter(Site.company_id == company_id).all()
    total_spend = sum(float(e.amount) for e in expenses)

    scheduled_payments = sum(float(p.amount) for p in db.query(Payment).filter(Payment.status == 'scheduled').all())

    # Equipment
    equip_active = db.query(Equipment).join(Site).filter(Site.company_id == company_id, Equipment.status == 'active').count()
    equip_idle = db.query(Equipment).join(Site).filter(Site.company_id == company_id, Equipment.status == 'idle').count()
    equip_maint = db.query(Equipment).join(Site).filter(Site.company_id == company_id, Equipment.status == 'maintenance').count()

    return DashboardSummary(
        active_sites=active_sites,
        total_sites=total_sites,
        open_alerts=open_alerts,
        critical_alerts=critical_alerts,
        pending_requests=pending_requests,
        pending_pos=pending_pos,
        pending_po_amount=pending_po_amount,
        low_stock_items=low_stock,
        total_users=total_users,
        active_users=active_users,
        recent_alerts=recent_alerts,
        total_budget=total_budget,
        total_spend=total_spend,
        scheduled_payments=scheduled_payments,
        pending_requests_list=pending_requests_list,
        pending_pos_list=pending_pos_list,
        equipment_status=EquipmentStatusSchema(active=equip_active, idle=equip_idle, maintenance=equip_maint)
    )
