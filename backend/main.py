from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.router import auth, diagnosis, scans, payments, admin

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

app.include_router(auth.router, prefix="/api/auth")
app.include_router(diagnosis.router, prefix="/api/diagnose")
app.include_router(scans.router, prefix="/api/scans")
app.include_router(payments.router, prefix="/api/payments")
app.include_router(admin.router, prefix="/api/admin")

@app.get("/")
def root():
    return {"status": "GAIA API running"}

@app.get("/health")
def health():
    return {"status": "healthy"}
