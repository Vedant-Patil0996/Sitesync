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
from app.schemas.site import SiteSchema
from app.schemas.common import PaginatedResponse

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
    
    items = []
    for site in sites_db:
        project_count = db.query(Project).filter(Project.site_id == site.id).count()
        alert_count = db.query(Alert).filter(Alert.site_id == site.id, Alert.status == 'open').count()
        
        projects = db.query(Project).filter(Project.site_id == site.id).all()
        budget = sum(float(p.budget_allocated) for p in projects)
        
        expenses = db.query(Expense).filter(Expense.site_id == site.id).all()
        spent = sum(float(e.amount) for e in expenses)
        
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
            budget_pct=budget_pct
        ))
        
    return PaginatedResponse[SiteSchema](
        items=items,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )
