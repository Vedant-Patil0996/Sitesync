from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.deps import get_current_user, require_role, require_site_access, audit
from app.models.user import User
from app.models.site import Site
from app.models.equipment import Equipment
from app.models.project import Task, Project
from app.schemas.equipment import EquipmentSchema, EquipmentStatusSchema, EquipmentLogSchema, EquipmentAllocationSchema
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
    if current_user.role in ("pm", "contractor"):
        from app.models.site import SiteAssignment
        query = query.filter(Site.id.in_(db.query(SiteAssignment.site_id).filter(SiteAssignment.user_id == current_user.id)))
        
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
    require_site_access(db, current_user, site_id)
    rows = db.query(Equipment, Site).join(Site, Equipment.site_id == Site.id).filter(Equipment.site_id == site_id).all()
    return [EquipmentSchema(id=eq.id, name=eq.name, type=eq.type, site_id=eq.site_id, site_name=site.name, allocated_to_task_id=eq.allocated_to_task_id, task_name=None, hours_used=float(eq.hours_used), status=eq.status) for eq, site in rows]

@router.patch("/{equipment_id}/status")
async def update_equipment_status(equipment_id: int, payload: EquipmentStatusSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    if payload.status not in ("active", "idle", "maintenance"):
        raise HTTPException(status_code=400, detail="Invalid equipment status")
    row = db.query(Equipment, Site).join(Site, Equipment.site_id == Site.id).filter(Equipment.id == equipment_id, Site.company_id == current_user.company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Equipment not found")
    equipment, site = row
    require_site_access(db, current_user, site.id, write=True)
    equipment.status = payload.status
    equipment.idle_since = func.now() if payload.status == "idle" else None
    audit(db, current_user, "equipment.status_updated", "equipment", equipment.id, {"status": payload.status})
    db.commit()
    return {"status": payload.status}

@router.post("/{equipment_id}/logs")
async def log_equipment_usage(equipment_id: int, payload: EquipmentLogSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm", "contractor"))):
    if payload.hours <= 0:
        raise HTTPException(status_code=400, detail="Hours must be positive")
    row = db.query(Equipment, Site).join(Site, Equipment.site_id == Site.id).filter(Equipment.id == equipment_id, Site.company_id == current_user.company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Equipment not found")
    equipment, site = row
    require_site_access(db, current_user, site.id, write=True)
    from app.models.equipment import EquipmentLog
    equipment.hours_used += payload.hours
    log = EquipmentLog(equipment_id=equipment.id, logged_by=current_user.id, hours=payload.hours)
    db.add(log)
    db.flush()
    audit(db, current_user, "equipment.usage_logged", "equipment_log", log.id, {"equipment_id": equipment.id, "hours": payload.hours})
    db.commit()
    return {"status": "success"}

@router.patch("/{equipment_id}/allocation")
async def allocate_equipment(equipment_id: int, payload: EquipmentAllocationSchema, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "pm"))):
    row = db.query(Equipment, Site).join(Site, Equipment.site_id == Site.id).filter(Equipment.id == equipment_id, Site.company_id == current_user.company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Equipment not found")
    equipment, site = row
    require_site_access(db, current_user, site.id, write=True)
    if payload.task_id:
        task = db.query(Task).join(Project, Task.project_id == Project.id).filter(Task.id == payload.task_id, Project.site_id == site.id).first()
        if not task:
            raise HTTPException(status_code=400, detail="Task does not belong to this site")
    equipment.allocated_to_task_id = payload.task_id
    audit(db, current_user, "equipment.allocated", "equipment", equipment.id, {"task_id": payload.task_id})
    db.commit()
    return {"status": "success"}
