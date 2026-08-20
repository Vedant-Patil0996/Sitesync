from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.supabase import get_supabase
from app.db.session import SessionLocal
from app.models.user import User
from app.models.site import Site, SiteAssignment
from app.models.audit import AuditLog
from sqlalchemy.orm import Session

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = None, request: Request = None):
    """
    Verify the Supabase JWT from the Authorization header.
    Returns the User row from our own `users` table.
    """
    token = None

    # Extract Bearer token
    auth_header = request.headers.get("Authorization") if request else None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Verify JWT with Supabase admin client
    try:
        sb = get_supabase()
        response = sb.auth.get_user(token)
        supabase_user = response.user
        if not supabase_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token verification failed")

    # Look up user in our own table by email
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == supabase_user.email, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found or inactive")
        return user
    finally:
        db.close()


def require_role(*roles: str):
    """
    Factory for role-gated FastAPI dependencies.
    Usage:  Depends(require_role("admin", "pm"))
    """
    async def checker(request: Request):
        user = await get_current_user(request=request)
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not allowed. Required: {list(roles)}"
            )
        return user
    return checker


def require_site_access(db: Session, user: User, site_id: int, write: bool = False) -> Site:
    site = db.query(Site).filter(Site.id == site_id, Site.company_id == user.company_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if user.role in ("admin", "finance"):
        return site
    assigned = db.query(SiteAssignment).filter(
        SiteAssignment.site_id == site_id,
        SiteAssignment.user_id == user.id,
    ).first()
    if not assigned:
        raise HTTPException(status_code=403, detail="You are not assigned to this site")
    return site


def audit(db: Session, user: User, action: str, entity_type: str, entity_id: int, metadata: dict | None = None):
    db.add(AuditLog(
        user_id=user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        event_metadata=metadata or {},
    ))
