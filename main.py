import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Import routers — try different paths
try:
    from backend.router import auth, diagnosis, scans, payments, admin
except ImportError:
    try:
        from router import auth, diagnosis, scans, payments, admin
    except ImportError:
        # Fallback: skip routers for now
        auth = diagnosis = scans = payments = admin = None

if auth:
    app.include_router(auth.router, prefix="/api/auth")
if diagnosis:
    app.include_router(diagnosis.router, prefix="/api/diagnose")
if scans:
    app.include_router(scans.router, prefix="/api/scans")
if payments:
    app.include_router(payments.router, prefix="/api/payments")
if admin:
    app.include_router(admin.router, prefix="/api/admin")

@app.get("/")
def root():
    return {"status": "GAIA API running"}

@app.get("/health")
def health():
    return {"status": "healthy"}
