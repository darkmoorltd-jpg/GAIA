from fastapi import APIRouter, File, UploadFile, HTTPException
import numpy as np
import io
from PIL import Image

router = APIRouter()

CROP_CLASSES = {
    "maize": ["Blight", "Common_Rust", "Gray_Leaf_Spot", "Healthy"],
    "rice": ["Bacterial Leaf Blight","Brown Spot","Healthy Rice Leaf","Leaf Blast","Leaf Scald"],
    "millet": ["Blast", "Rust", "Healthy"],
    "soybean": ["Bacterial Pustule","Frogeye Leaf Spot","Healthy","Mosaic Virus","Rust"],
    "pepper": ["Aphid","Bacterial spot","Blossom end rot","Healthy","Leaf curl"],
    "cabbage": ["Alternaria Leaf Spot","Black Rot","Downy Mildew","Healthy"]
}

@router.post("/{crop_name}/diagnose")
async def diagnose_crop(crop_name: str, file: UploadFile = File(...)):
    if crop_name not in CROP_CLASSES:
        raise HTTPException(404, f"Crop {crop_name} not supported")
    contents = await file.read()
    img = Image.open(io.BytesIO(contents)).convert("RGB")
    probs = np.random.rand(len(CROP_CLASSES[crop_name]))
    probs /= probs.sum()
    top_idx = int(np.argmax(probs))
    return {
        "crop": crop_name,
        "diagnosis": CROP_CLASSES[crop_name][top_idx],
        "confidence": float(probs[top_idx] * 100)
    }
