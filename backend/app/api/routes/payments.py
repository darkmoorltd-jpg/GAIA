from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class PaymentRequest(BaseModel):
    email: str
    amount: float
    plan: str

@router.post("/initialize")
def initialize_payment(req: PaymentRequest):
    return {"success": True, "reference": f"GAIA-{req.plan}-{int(req.amount*100)}"}
