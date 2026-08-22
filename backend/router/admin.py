from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.supabase_service import SupabaseService

router = APIRouter()

class CreateUserRequest(BaseModel):
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""
    phone: str = ""

class UpdateScansRequest(BaseModel):
    user_id: str
    amount: int

class KYCRequest(BaseModel):
    user_id: str
    status: str  # approved or rejected

@router.get("/users")
async def list_users():
    service = SupabaseService()
    users = service.get_all_users()
    return {"users": users}

@router.post("/create-user")
async def create_user(req: CreateUserRequest):
    service = SupabaseService()
    success, error = service.create_user(req.email, req.password, req.first_name, req.last_name, req.phone)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True}

@router.post("/update-scans")
async def update_scans(req: UpdateScansRequest):
    service = SupabaseService()
    success, error = service.add_scans(req.user_id, req.amount)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True}

@router.post("/kyc")
async def kyc_action(req: KYCRequest):
    service = SupabaseService()
    if req.status == "approved":
        service.approve_kyc(req.user_id)
    elif req.status == "rejected":
        service.reject_kyc(req.user_id)
    return {"success": True}
