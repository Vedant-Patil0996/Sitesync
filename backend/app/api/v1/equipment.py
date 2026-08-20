from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.site import Site
from app.models.equipment import Equipment
from app.models.project import Task
from app.schemas.equipment import EquipmentSchema
from app.schemas.common import PaginatedResponse

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[EquipmentSchema])
async def get_equipment(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role("admin", "pm", "finance"))
):
    query = db.query(Equipment, Site)\
        .join(Site, Equipment.site_id == Site.id)\
        .filter(Site.company_id == current_user.company_id)
        
    total = query.count()
    equipment_db = query.offset(skip).limit(limit).all()
    
    items = []
    for eq, site in equipment_db:
        task_name = None
        if eq.allocated_to_task_id:
            task = db.query(Task).filter(Task.id == eq.allocated_to_task_id).first()
            if task:
                task_name = task.name

        items.append(EquipmentSchema(
            id=eq.id,
            name=eq.name,
            type=eq.type,
            site_id=eq.site_id,
            site_name=site.name,
            allocated_to_task_id=eq.allocated_to_task_id,
            task_name=task_name,
            hours_used=float(eq.hours_used),
            status=eq.status
        ))
        
    return PaginatedResponse[EquipmentSchema](
        items=items,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.get("/by-site/{site_id}")
async def get_site_equipment(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@router.patch("/{equipment_id}/status")
async def update_equipment_status(equipment_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    pass

@router.post("/{equipment_id}/logs")
async def log_equipment_usage(equipment_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "contractor"))):
    pass
