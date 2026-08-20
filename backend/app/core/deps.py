from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.supabase import get_supabase
from app.db.session import SessionLocal
from app.models.user import User

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
