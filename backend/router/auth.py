import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import create_client

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SERVICE_KEY = os.getenv("SERVICE_KEY", "")

def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_service_client():
    return create_client(SUPABASE_URL, SERVICE_KEY)

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

@router.post("/signup")
async def signup(req: SignupRequest):
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    supabase = get_client()
    service = get_service_client()

    try:
        res = supabase.auth.sign_up({"email": req.email, "password": req.password})
        if not res.user:
            raise HTTPException(status_code=400, detail="Signup failed. User not created.")

        user_id = res.user.id

        # Create user_scans row with 30 free scans
        try:
            service.table("user_scans").insert({
                "user_id": user_id,
                "scans_remaining": 30,
                "plan": "free"
            }).execute()
        except Exception:
            pass

        # Create user_profiles if name/phone provided
        if req.first_name or req.last_name or req.phone:
            service.table("user_profiles").insert({
                "user_id": user_id,
                "first_name": req.first_name,
                "last_name": req.last_name,
                "phone": req.phone,
                "verification_status": "pending"
            }).execute()

        return {
            "success": True,
            "message": "Account created successfully. 30 free scans added.",
            "user": {"id": user_id, "email": req.email}
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(req: LoginRequest):
    supabase = get_client()
    try:
        res = supabase.auth.sign_in_with_password({"email": req.email, "password": req.password})
        return {"success": True, "user": {"id": res.user.id, "email": res.user.email}}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/google")
async def google_auth(req: GoogleAuthRequest):
    supabase = get_client()
    try:
        res = supabase.auth.sign_in_with_oauth({
            "provider": req.provider,
            "options": {"redirect_to": req.redirect_to} if req.redirect_to else {}
        })
        return {"success": True, "auth_url": res.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset-password")
async def reset_password(req: PasswordResetRequest):
    supabase = get_client()
    try:
        supabase.auth.reset_password_for_email(req.email)
        return {"success": True, "message": "Password reset email sent"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/logout")
async def logout():
    supabase = get_client()
    supabase.auth.sign_out()
    return {"success": True}
