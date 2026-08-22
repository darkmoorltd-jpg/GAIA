import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'router'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'services'))

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

# Import routers directly
try:
    from router.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/auth")
except Exception as e:
    print(f"Auth router failed: {e}")

try:
    from router.diagnosis import router as diagnosis_router
    app.include_router(diagnosis_router, prefix="/api/diagnose")
except Exception as e:
    print(f"Diagnosis router failed: {e}")

try:
    from router.scans import router as scans_router
    app.include_router(scans_router, prefix="/api/scans")
except Exception as e:
    print(f"Scans router failed: {e}")

try:
    from router.payments import router as payments_router
    app.include_router(payments_router, prefix="/api/payments")
except Exception as e:
    print(f"Payments router failed: {e}")

try:
    from router.admin import router as admin_router
    app.include_router(admin_router, prefix="/api/admin")
except Exception as e:
    print(f"Admin router failed: {e}")

@app.get("/")
def root():
    return {"status": "GAIA API running", "message": "Welcome to GAIA Production API"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api")
def api_root():
    return {"status": "GAIA API", "endpoints": ["/api/auth", "/api/diagnose", "/api/scans", "/api/payments", "/api/admin"]}
