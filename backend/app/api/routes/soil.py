from fastapi import APIRouter, File, UploadFile
import numpy as np
import io
from PIL import Image

router = APIRouter()

SOIL_TYPES = ["Alluvial","Sandy","Clay","Loamy","Laterite","Black","Red","Peat","Cinder","Sandy Loam","Yellow"]

@router.post("/diagnose")
async def diagnose_soil(file: UploadFile = File(...)):
    contents = await file.read()
    img = Image.open(io.BytesIO(contents)).convert("RGB")
    probs = np.random.rand(len(SOIL_TYPES))
    probs /= probs.sum()
    top_idx = int(np.argmax(probs))
    return {"soil_type": SOIL_TYPES[top_idx], "confidence": float(probs[top_idx] * 100)}
