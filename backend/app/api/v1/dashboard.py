from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, select, case
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.site import Site, SiteAssignment
from app.models.alert import Alert
from app.models.procurement import MaterialRequest, PurchaseOrder
from app.models.finance import Payment, Expense
from app.models.inventory import Inventory, Material
from app.models.equipment import Equipment
from app.models.project import Project
from app.schemas.dashboard import DashboardSummary, AlertSchema, PendingRequestSchema, PendingPOSchema, EquipmentStatusSchema

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_id = current_user.company_id

    site_query = db.query(Site.id).filter(Site.company_id == company_id)
    if current_user.role in ("pm", "contractor"):
        site_query = site_query.join(SiteAssignment, SiteAssignment.site_id == Site.id).filter(SiteAssignment.user_id == current_user.id)
    site_ids = select(site_query.subquery().c.id)

    # Sites
    site_counts = db.query(
        func.count(Site.id),
        func.coalesce(func.sum(case((Site.status == 'active', 1), else_=0)), 0),
    ).filter(Site.id.in_(site_ids)).one()
    total_sites = int(site_counts[0] or 0)
    active_sites = int(site_counts[1] or 0)

    # Alerts (joining with Site to get site_name)
    alerts_query = db.query(Alert, Site.name.label('site_name')).join(Site).filter(Site.id.in_(site_ids), Alert.status == 'open')
    alert_counts = db.query(
        func.count(Alert.id),
        func.coalesce(func.sum(case((Alert.severity == 'critical', 1), else_=0)), 0),
    ).join(Site).filter(Site.id.in_(site_ids), Alert.status == 'open').one()
    open_alerts = int(alert_counts[0] or 0)
    critical_alerts = int(alert_counts[1] or 0)
    recent_alerts = []
    for a, s_name in alerts_query.order_by(Alert.created_at.desc()).limit(5).all():
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
    pending_requests = requests_query.count()
    reqs = requests_query.order_by(MaterialRequest.created_at.desc()).limit(4).all()
    pending_requests_list = []
    for r, s_name, u_name in reqs[:4]:
        # Need to join Material to get material name properly, assuming material_id for now
        pending_requests_list.append(PendingRequestSchema(
            id=r.id, material_name=f"Material {r.material_id}", quantity=float(r.quantity), unit="unit",
            site_name=s_name, pm_status=r.pm_status, finance_status=r.finance_status, created_at=r.created_at
        ))

    pos_query = db.query(PurchaseOrder).join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id).filter(MaterialRequest.site_id.in_(site_ids), PurchaseOrder.status == 'pending_finance')
    if current_user.role in ("finance", "admin"):
        pending_pos = pos_query.count()
        pending_po_amount = float(pos_query.with_entities(func.coalesce(func.sum(PurchaseOrder.amount), 0)).scalar() or 0)
        pos = pos_query.order_by(PurchaseOrder.order_date.desc()).limit(3).all()
    else:
        pending_pos = 0
        pending_po_amount = 0
        pos = []
    pending_pos_list = []
    for p in pos[:3]:
        pending_pos_list.append(PendingPOSchema(
            id=p.id, vendor_name=f"Vendor {p.vendor_id}", material_name="Material", amount=float(p.amount), status=p.status
        ))

    # Inventory
    low_stock = 0
    if current_user.role in ("pm", "admin"):
        low_stock = db.query(func.count(Inventory.id)).filter(Inventory.site_id.in_(site_ids), Inventory.quantity <= Inventory.reorder_level).scalar() or 0

    # Users
    if current_user.role == "admin":
        user_counts = db.query(
            func.count(User.id),
            func.coalesce(func.sum(case((User.is_active == True, 1), else_=0)), 0),
        ).filter(User.company_id == company_id).one()
        total_users = int(user_counts[0] or 0)
        active_users = int(user_counts[1] or 0)
    else:
        total_users = 0
        active_users = 0

    # Finance
    total_budget = float(db.query(func.coalesce(func.sum(Project.budget_allocated), 0)).filter(Project.site_id.in_(site_ids)).scalar() or 0)
    
    # Total spend from Expenses
    total_spend = float(db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(Expense.site_id.in_(site_ids)).scalar() or 0)

    scheduled_payments = 0
    if current_user.role in ("finance", "admin", "pm"):
        scheduled_payments = float(db.query(func.coalesce(func.sum(Payment.amount), 0)).join(PurchaseOrder, Payment.po_id == PurchaseOrder.id).join(MaterialRequest, PurchaseOrder.request_id == MaterialRequest.id).filter(MaterialRequest.site_id.in_(site_ids), Payment.status == 'scheduled').scalar() or 0)

    # Equipment
    if current_user.role in ("pm", "admin"):
        equipment_counts = db.query(
            func.coalesce(func.sum(case((Equipment.status == 'active', 1), else_=0)), 0),
            func.coalesce(func.sum(case((Equipment.status == 'idle', 1), else_=0)), 0),
            func.coalesce(func.sum(case((Equipment.status == 'maintenance', 1), else_=0)), 0),
        ).filter(Equipment.site_id.in_(site_ids)).one()
        equip_active = int(equipment_counts[0] or 0)
        equip_idle = int(equipment_counts[1] or 0)
        equip_maint = int(equipment_counts[2] or 0)
    else:
        equip_active = 0
        equip_idle = 0
        equip_maint = 0

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
