from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User

from pydantic import BaseModel
from app.core.supabase import get_supabase

class LoginRequest(BaseModel):
    email: str
    password: str

router = APIRouter()

@router.post("/login")
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    sb = get_supabase()
    try:
        # Authenticate with Supabase
        auth_response = sb.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        # Verify user exists in our DB
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user:
            raise HTTPException(status_code=403, detail="User not registered in system")
            
        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "name": user.name
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid credentials or error: {str(e)}"
        )

@router.post("/register")
async def register():
    # Will be implemented: Create company and admin user
    pass

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "company_id": current_user.company_id,
        "is_active": current_user.is_active
    }
