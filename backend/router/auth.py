from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from services.supabase_service import SupabaseService

router = APIRouter()

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str = ""
    last_name: str = ""
    phone: str = ""

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    provider: str = "google"
    redirect_to: str = ""

class PasswordResetRequest(BaseModel):
    email: EmailStr

class SignupResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None

@router.post("/signup", response_model=SignupResponse)
async def signup(req: SignupRequest):
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    
    service = SupabaseService()
    user, error = service.sign_up(
        email=req.email,
        password=req.password,
        first_name=req.first_name,
        last_name=req.last_name,
        phone=req.phone
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "success": True,
        "message": "Account created successfully. 30 free scans added.",
        "user": user
    }

@router.post("/login")
async def login(req: LoginRequest):
    service = SupabaseService()
    user, error = service.sign_in(req.email, req.password)
    if error:
        raise HTTPException(status_code=401, detail=error)
    return {"success": True, "user": user}

@router.post("/google")
async def google_auth(req: GoogleAuthRequest):
    service = SupabaseService()
    url, error = service.sign_in_with_google(req.redirect_to)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "auth_url": url}

@router.post("/reset-password")
async def reset_password(req: PasswordResetRequest):
    service = SupabaseService()
    error = service.reset_password(req.email)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "message": "Password reset email sent"}

@router.post("/logout")
async def logout():
    service = SupabaseService()
    service.sign_out()
    return {"success": True}
