from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.paystack_service import PaystackService
from backend.services.supabase_service import SupabaseService

router = APIRouter()

class InitializePaymentRequest(BaseModel):
    email: str
    amount: int  # in kobo
    plan: str
    phone: str = ""

class VerifyPaymentRequest(BaseModel):
    reference: str

@router.post("/initialize")
async def initialize_payment(req: InitializePaymentRequest):
    paystack = PaystackService()
    result, error = paystack.initialize_payment(req.email, req.amount, req.plan, req.phone)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return result

@router.post("/verify")
async def verify_payment(req: VerifyPaymentRequest):
    paystack = PaystackService()
    result = paystack.verify_payment(req.reference)
    if not result:
        raise HTTPException(status_code=400, detail="Payment verification failed")
    # Update user scans based on plan
    supabase = SupabaseService()
    email = result.get("customer", {}).get("email", "")
    if email:
        scans = paystack.get_scans_for_plan(result.get("metadata", {}).get("plan", ""))
        if scans > 0:
            supabase.credit_scans_by_email(email, scans, result.get("metadata", {}).get("plan", ""))
    return result
