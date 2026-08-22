from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.services.supabase_service import SupabaseService

router = APIRouter()

class SignupRequest(BaseModel):
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""
    phone: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleAuthRequest(BaseModel):
    provider: str = "google"
    redirect_to: str = ""

class PasswordResetRequest(BaseModel):
    email: str

@router.post("/signup")
async def signup(req: SignupRequest):
    service = SupabaseService()
    user, error = service.sign_up(req.email, req.password, req.first_name, req.last_name, req.phone)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "user": user}

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
