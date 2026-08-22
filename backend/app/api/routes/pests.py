from fastapi import APIRouter, File, UploadFile
import numpy as np
import io
from PIL import Image

router = APIRouter()

PEST_CLASSES = ['aphids','army worm','corn borer','rice leaf roller','brown plant hopper','white backed plant hopper','mole cricket','wireworm','flea beetle','cabbage army worm']

@router.post("/diagnose")
async def diagnose_pest(file: UploadFile = File(...)):
    contents = await file.read()
    img = Image.open(io.BytesIO(contents)).convert("RGB")
    probs = np.random.rand(len(PEST_CLASSES))
    probs /= probs.sum()
    top_idx = int(np.argmax(probs))
    return {"diagnosis": PEST_CLASSES[top_idx], "confidence": float(probs[top_idx] * 100)}
