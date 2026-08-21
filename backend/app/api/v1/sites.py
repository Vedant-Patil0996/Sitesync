from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.site import Site
from app.models.project import Project
from app.models.alert import Alert
from app.models.finance import Expense
from app.models.inventory import Inventory, Material
from app.models.equipment import Equipment
from app.models.site import SiteAssignment
from app.schemas.site import SiteSchema, SiteDetailSchema, SiteContractorSchema
from app.schemas.project import ProjectSchema
from app.schemas.inventory import InventorySchema
from app.schemas.equipment import EquipmentSchema
from app.schemas.alert import AlertSchema
from app.schemas.common import PaginatedResponse
from fastapi import HTTPException

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[SiteSchema])
async def get_sites(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    query = db.query(Site).filter(Site.company_id == current_user.company_id)
    
    total = query.count()
    sites_db = query.offset(skip).limit(limit).all()
    
    if not sites_db:
        return PaginatedResponse[SiteSchema](items=[], total=0, page=1, size=limit, pages=0)

    site_ids = [s.id for s in sites_db]

    # Batch counts & sums across all sites in 1 roundtrip per table
    project_counts = dict(
        db.query(Project.site_id, func.count(Project.id))
        .filter(Project.site_id.in_(site_ids))
        .group_by(Project.site_id).all()
    )
    alert_counts = dict(
        db.query(Alert.site_id, func.count(Alert.id))
        .filter(Alert.site_id.in_(site_ids), Alert.status == 'open')
        .group_by(Alert.site_id).all()
    )
    budgets = dict(
        db.query(Project.site_id, func.coalesce(func.sum(Project.budget_allocated), 0))
        .filter(Project.site_id.in_(site_ids))
        .group_by(Project.site_id).all()
    )
    spents = dict(
        db.query(Expense.site_id, func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.site_id.in_(site_ids))
        .group_by(Expense.site_id).all()
    )

    items = []
    for site in sites_db:
        project_count = project_counts.get(site.id, 0)
        alert_count = alert_counts.get(site.id, 0)
        budget = float(budgets.get(site.id, 0))
        spent = float(spents.get(site.id, 0))
        budget_pct = int((spent / budget * 100)) if budget > 0 else 0
        
        items.append(SiteSchema(
            id=site.id,
            name=site.name,
            location=site.location,
            status=site.status,
            project_count=project_count,
            alert_count=alert_count,
            budget=budget,
            spent=spent,
            budget_pct=budget_pct,
            latitude=float(site.latitude) if site.latitude else None,
            longitude=float(site.longitude) if site.longitude else None
        ))
        
    return PaginatedResponse[SiteSchema](
        items=items,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.get("/my-site", response_model=SiteDetailSchema)
async def get_my_site(db: Session = Depends(get_db), current_user: User = Depends(require_role("contractor"))):
    assignment = db.query(SiteAssignment).filter(SiteAssignment.user_id == current_user.id).first()
    
    if assignment:
        site_id = assignment.site_id
    else:
        # Fallback to the first active site of the user's company if no explicit assignment exists
        first_site = db.query(Site).filter(Site.company_id == current_user.company_id).first()
        if not first_site:
            raise HTTPException(status_code=404, detail="No site found for your company")
        site_id = first_site.id
        
    return await get_site(site_id=site_id, db=db, current_user=current_user)

@router.get("/{site_id}", response_model=SiteDetailSchema)
async def get_site(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id, Site.company_id == current_user.company_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
        
    projects_db = db.query(Project).filter(Project.site_id == site.id).all()
    project_count = len(projects_db)
    budget = sum(float(p.budget_allocated) for p in projects_db)
    
    expenses = db.query(Expense).filter(Expense.site_id == site.id).all()
    spent = sum(float(e.amount) for e in expenses)
    budget_pct = int((spent / budget * 100)) if budget > 0 else 0
    
    alert_count = db.query(Alert).filter(Alert.site_id == site.id, Alert.status == 'open').count()
    
    projects_data = []
    for p in projects_db:
        # task / milestone counts are needed for ProjectSchema
        from app.models.project import Task, Milestone
        t_count = db.query(Task).filter(Task.project_id == p.id).count()
        c_count = db.query(Task).filter(Task.project_id == p.id, Task.status == 'completed').count()
        m_count = db.query(Milestone).filter(Milestone.project_id == p.id).count()
        projects_data.append(ProjectSchema(
            id=p.id, name=p.name, site_name=site.name, status=p.status,
            progress_percent=float(p.progress_percent), end_date=p.end_date,
            budget_allocated=float(p.budget_allocated), task_count=t_count,
            completed_task_count=c_count, milestone_count=m_count
        ))
        
    inventory_data = []
    invs = db.query(Inventory, Material).join(Material, Inventory.material_id == Material.id).filter(Inventory.site_id == site.id).all()
    for inv, mat in invs:
        inventory_data.append(InventorySchema(
            id=inv.id, site_id=site.id, site_name=site.name, material_id=mat.id,
            material_name=mat.name, unit=mat.unit, quantity=float(inv.quantity),
            reorder_level=float(inv.reorder_level), updated_at=inv.updated_at
        ))
        
    equipment_data = []
    eqs = db.query(Equipment).filter(Equipment.site_id == site.id).all()
    for eq in eqs:
        equipment_data.append(EquipmentSchema(
            id=eq.id, name=eq.name, type=eq.type, site_id=site.id, site_name=site.name,
            allocated_to_task_id=eq.allocated_to_task_id, task_name=None,
            hours_used=float(eq.hours_used), status=eq.status
        ))
        
    alerts_data = []
    alts = db.query(Alert).filter(Alert.site_id == site.id, Alert.status == 'open').all()
    for al in alts:
        alerts_data.append(AlertSchema(
            id=al.id, site_id=site.id, site_name=site.name, type=al.type,
            severity=al.severity, title=al.title, description=al.description,
            status=al.status, resolved_by_name=None, resolved_at=al.resolved_at, created_at=al.created_at
        ))
        
    contractors_data = []
    assigns = db.query(SiteAssignment, User).join(User, SiteAssignment.user_id == User.id).filter(SiteAssignment.site_id == site.id).all()
    for assign, user in assigns:
        # Default specialty to user role since we don't have a specialty column
        contractors_data.append(SiteContractorSchema(
            id=user.id, name=user.name, specialty=user.role.capitalize(), phone=user.phone
        ))
        
    return SiteDetailSchema(
        id=site.id, name=site.name, location=site.location, status=site.status,
        project_count=project_count, alert_count=alert_count, budget=budget,
        spent=spent, budget_pct=budget_pct, latitude=float(site.latitude) if site.latitude else None,
        longitude=float(site.longitude) if site.longitude else None, location_text=site.location,
        projects=projects_data, inventory=inventory_data, equipment=equipment_data,
        alerts=alerts_data, contractors=contractors_data
    )
