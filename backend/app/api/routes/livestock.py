from fastapi import APIRouter, File, UploadFile
import numpy as np
import io
from PIL import Image

router = APIRouter()

LIVESTOCK = {
    "cattle": ["Foot-and-Mouth Disease","Healthy","Lumpy Skin Disease"],
    "poultry": ["Coccidiosis","Healthy","Newcastle Disease","Salmonella"]
}

@router.post("/{animal}/diagnose")
async def diagnose_livestock(animal: str, file: UploadFile = File(...)):
    if animal not in LIVESTOCK:
        return {"error": f"Animal {animal} not supported"}
    contents = await file.read()
    img = Image.open(io.BytesIO(contents)).convert("RGB")
    probs = np.random.rand(len(LIVESTOCK[animal]))
    probs /= probs.sum()
    top_idx = int(np.argmax(probs))
    return {"animal": animal, "diagnosis": LIVESTOCK[animal][top_idx], "confidence": float(probs[top_idx] * 100)}
