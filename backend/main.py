from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

app = FastAPI(
    title="GAIA Production API",
    version="1.0.0",
    description="Production backend for GAIA agricultural intelligence"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Pydantic Models ----------
class SignupRequest(BaseModel):
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""
    phone: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

class ScanRequest(BaseModel):
    user_id: str
    amount: int
    feature: str = "diagnosis"

class PaymentRequest(BaseModel):
    email: str
    amount: int
    plan: str
    phone: str = ""

# ---------- Auth Endpoints ----------
@app.post("/api/auth/signup")
async def signup(req: SignupRequest):
    return {"success": True, "message": "Signup endpoint ready", "email": req.email}

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    return {"success": True, "message": "Login endpoint ready", "email": req.email}

# ---------- Diagnosis Endpoints ----------
@app.post("/api/diagnose/crop")
async def diagnose_crop(crop: str = Form(...), file: UploadFile = File(...)):
    return {"success": True, "crop": crop, "diagnosis": "Healthy", "confidence": 95.0, "message": "Model inference placeholder"}

@app.post("/api/diagnose/pest")
async def diagnose_pest(file: UploadFile = File(...)):
    return {"success": True, "diagnosis": "Aphids", "confidence": 92.0, "message": "Model inference placeholder"}

@app.post("/api/diagnose/soil")
async def diagnose_soil(file: UploadFile = File(...)):
    return {"success": True, "soil_type": "Loamy", "confidence": 88.0, "message": "Model inference placeholder"}

@app.post("/api/diagnose/livestock")
async def diagnose_livestock(animal: str = Form(...), file: UploadFile = File(...)):
    return {"success": True, "animal": animal, "diagnosis": "Healthy", "confidence": 94.0, "message": "Model inference placeholder"}

# ---------- Scans Endpoints ----------
@app.get("/api/scans/balance/{user_id}")
async def get_balance(user_id: str):
    return {"user_id": user_id, "remaining": 30}

@app.post("/api/scans/deduct")
async def deduct_scan(req: ScanRequest):
    return {"success": True, "remaining": 29, "message": "Scan deducted"}

# ---------- Payments Endpoints ----------
@app.post("/api/payments/initialize")
async def initialize_payment(req: PaymentRequest):
    return {"success": True, "reference": "GAIA-TEST-123", "plan": req.plan, "amount": req.amount}

@app.post("/api/payments/verify")
async def verify_payment(reference: str):
    return {"success": True, "reference": reference, "status": "success"}

# ---------- Admin Endpoints ----------
@app.get("/api/admin/users")
async def list_users():
    return {"users": []}

# ---------- Health & Root ----------
@app.get("/")
def root():
    return {"status": "GAIA API running", "message": "Welcome to GAIA Production API"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api")
def api_root():
    return {"status": "GAIA API", "version": "1.0.0", "endpoints": ["/api/auth", "/api/diagnose", "/api/scans", "/api/payments", "/api/admin"]}
