from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from app.core.config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from pydantic import BaseModel

router = APIRouter()

def get_service() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

class LoginRequest(BaseModel):
    identifier: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    username: str = ""
    state: str = ""
    lga: str = ""
    primary_crop: str = ""
    farm_size_acres: float = 0.0

@router.post("/signup")
def signup(req: SignupRequest):
    service = get_service()
    try:
        auth_res = service.auth.sign_up({"email": req.email, "password": req.password})
        if not auth_res.user:
            raise HTTPException(400, "Email already registered")
        user_id = auth_res.user.id
        service.table("user_profiles").upsert({
            "user_id": user_id, "first_name": req.first_name, "last_name": req.last_name,
            "phone": req.phone, "username": req.username.lower(), "verification_status": "pending"
        }).execute()
        service.table("farmer_registry").upsert({
            "user_id": user_id, "state": req.state, "lga": req.lga,
            "crop": req.primary_crop, "farm_size_acres": req.farm_size_acres,
            "unique_farmer_id": f"GAIA-{user_id[:8].upper()}"
        }).execute()
        service.table("user_scans").upsert({
            "user_id": user_id, "scans_remaining": 30, "plan": "free"
        }).execute()
        return {"success": True, "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e)[:200])

@router.post("/login")
def login(req: LoginRequest):
    service = get_service()
    identifier = req.identifier.strip()
    email = identifier
    if "@" not in identifier:
        res = service.table("user_profiles").select("user_id").or_(f"phone.eq.{identifier},username.eq.{identifier.lower()}").execute()
        if res.data:
            user_id = res.data[0]["user_id"]
            user = service.auth.admin.get_user_by_id(user_id)
            if user and user.email:
                email = user.email
    try:
        res = service.auth.sign_in_with_password({"email": email, "password": req.password})
        return {"success": True, "user": res.user.email}
    except Exception:
        raise HTTPException(401, "Invalid credentials")
