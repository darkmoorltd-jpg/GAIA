from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.supabase_service import SupabaseService

router = APIRouter()

class ScanRequest(BaseModel):
    user_id: str
    amount: int
    feature: str = "diagnosis"

class ScansResponse(BaseModel):
    success: bool
    remaining: int
    message: str

@router.get("/balance/{user_id}")
async def get_balance(user_id: str):
    service = SupabaseService()
    balance = service.get_scan_balance(user_id)
    return {"user_id": user_id, "remaining": balance}

@router.post("/deduct")
async def deduct_scan(req: ScanRequest):
    service = SupabaseService()
    success, remaining = service.deduct_scans(req.user_id, req.amount, req.feature)
    if not success:
        raise HTTPException(status_code=400, detail=f"Not enough scans. Need {req.amount}, have {remaining}")
    return ScansResponse(success=True, remaining=remaining, message="Scan deducted")
