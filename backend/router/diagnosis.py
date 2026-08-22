from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from backend.services.ml_service import MLService
from backend.services.supabase_service import SupabaseService
from backend.services.deepseek_service import DeepSeekService
import uuid

router = APIRouter()

@router.post("/crop")
async def diagnose_crop(
    crop: str = Form(...),
    file: UploadFile = File(...)
):
    image_bytes = await file.read()
    ml = MLService()
    result = ml.predict_crop(crop, image_bytes)
    if result is None:
        raise HTTPException(status_code=400, detail="Model unavailable")
    return result

@router.post("/pest")
async def diagnose_pest(file: UploadFile = File(...)):
    image_bytes = await file.read()
    ml = MLService()
    result = ml.predict_pest(image_bytes)
    if result is None:
        raise HTTPException(status_code=400, detail="Model unavailable")
    return result

@router.post("/soil")
async def diagnose_soil(file: UploadFile = File(...)):
    image_bytes = await file.read()
    ml = MLService()
    result = ml.predict_soil(image_bytes)
    if result is None:
        raise HTTPException(status_code=400, detail="Model unavailable")
    return result

@router.post("/livestock")
async def diagnose_livestock(
    animal: str = Form(...),
    file: UploadFile = File(...)
):
    image_bytes = await file.read()
    ml = MLService()
    result = ml.predict_livestock(animal, image_bytes)
    if result is None:
        raise HTTPException(status_code=400, detail="Model unavailable")
    return result

@router.post("/video")
async def diagnose_video(
    scan_type: str = Form(...),
    crop: str = Form(...),
    file: UploadFile = File(...)
):
    video_bytes = await file.read()
    ml = MLService()
    result = ml.predict_video(scan_type, crop, video_bytes)
    return result

@router.post("/treatment-guide")
async def get_treatment_guide(
    diagnosis: str = Form(...),
    context_type: str = Form(...),
    confidence: float = Form(...)
):
    deepseek = DeepSeekService()
    guide, error = deepseek.explain_diagnosis(diagnosis, confidence, "crop", context_type)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"guide": guide}
