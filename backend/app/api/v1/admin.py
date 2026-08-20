from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.common import PaginatedResponse
from app.schemas.admin import UserSchema, AuditLogSchema

router = APIRouter()

@router.get("/users", response_model=PaginatedResponse[UserSchema])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role("admin"))
):
    query = db.query(User).filter(User.company_id == current_user.company_id)
        
    total = query.count()
    users_db = query.offset(skip).limit(limit).all()
    
    items = []
    for user in users_db:
        items.append(UserSchema(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        ))
        
    return PaginatedResponse[UserSchema](
        items=items,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.post("/users/invite")
async def invite_user(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    pass

@router.patch("/users/{user_id}/role")
async def update_user_role(user_id: int, role: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.role = role
        db.commit()
    return {"status": "success"}

@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = False
        db.commit()
    return {"status": "success"}

@router.patch("/users/{user_id}/activate")
async def activate_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = True
        db.commit()
    return {"status": "success"}

@router.get("/audit-log", response_model=PaginatedResponse[AuditLogSchema])
async def get_audit_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role("admin"))
):
    query = db.query(AuditLog, User)\
        .outerjoin(User, AuditLog.user_id == User.id)\
        .order_by(AuditLog.created_at.desc())
        
    total = query.count()
    logs_db = query.offset(skip).limit(limit).all()
    
    items = []
    for log, user in logs_db:
        items.append(AuditLogSchema(
            id=log.id,
            user_name=user.name if user else "System",
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            metadata=log.event_metadata,
            created_at=log.created_at
        ))
        
    return PaginatedResponse[AuditLogSchema](
        items=items,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )
