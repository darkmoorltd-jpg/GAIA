
import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import onnxruntime as ort
import cv2
import os

st.set_page_config(page_title="GAIA – GaiaLens™", page_icon="🔍", layout="wide")

# ── YOLO via ONNX Runtime ──
class YOLO_ONNX:
    def __init__(self, onnx_path):
        self.session = ort.InferenceSession(onnx_path)
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape  # [1, 3, 320, 320]
    
    def preprocess(self, img_np):
        img = cv2.resize(img_np, (320, 320))
        img = img.astype(np.float32) / 255.0
        img = img.transpose(2, 0, 1)  # HWC → CHW
        return np.expand_dims(img, axis=0).astype(np.float32)
    
    def detect(self, img_np):
        inp = self.preprocess(img_np)
        outputs = self.session.run(None, {self.input_name: inp})[0]  # [1, 84, 2100]
        
        # Parse YOLOv8 output format
        outputs = np.squeeze(outputs)  # [84, 2100]
        outputs = outputs.transpose()  # [2100, 84]
        
        boxes = []
        for row in outputs:
            # First 4 values: cx, cy, w, h (normalized)
            cx, cy, w, h = row[:4]
            # Next 80 values: class confidences
            scores = row[4:]
            max_score = np.max(scores)
            max_class = np.argmax(scores)
            
            if max_score > 0.25:  # confidence threshold
                # Convert to pixel coordinates
                img_h, img_w = img_np.shape[:2]
                x1 = int((cx - w/2) * img_w)
                y1 = int((cy - h/2) * img_h)
                x2 = int((cx + w/2) * img_w)
                y2 = int((cy + h/2) * img_h)
                
                boxes.append({
                    "class": int(max_class),
                    "confidence": float(max_score),
                    "bbox": [max(0,x1), max(0,y1), min(img_w,x2), min(img_h,y2)]
                })
        
        return boxes

# ── Load models ──
@st.cache_resource
def load_gaialens_models():
    from app.utils.download_models import ensure_gaialens_model
    
    # Download ONNX files if missing
    for f in ["gaia_crop.onnx","gaia_crop.onnx.data","gaia_pest.onnx","gaia_pest.onnx.data",
              "gaia_soil.onnx","gaia_soil.onnx.data","gaia_livestock.onnx","gaia_livestock.onnx.data",
              "yolov8_detector.onnx"]:
        ensure_gaialens_model(f)
    
    models = {}
    class_names = {
        "crop": ["Blast","Rust","Healthy"],
        "pest": [f"pest_{i}" for i in range(102)],
        "soil": ["Alluvial","Sandy","Clay","Loamy","Laterite","Black","Red","Peat","Cinder","Sandy Loam","Yellow"],
        "livestock": ["Coccidiosis","Healthy","Newcastle Disease","Salmonella"],
    }
    input_sizes = {"crop":384, "pest":224, "soil":384, "livestock":224}
    
    for m in ["crop","pest","soil","livestock"]:
        path = f"onnx/gaia_{m}.onnx"
        if os.path.exists(path):
            models[m] = ort.InferenceSession(path)
    
    yolo_path = "onnx/yolov8_detector.onnx"
    yolo = YOLO_ONNX(yolo_path) if os.path.exists(yolo_path) else None
    
    return models, class_names, input_sizes, yolo

TREATMENTS = {
    "blast": "Apply tricyclazole or isoprothiolane at booting stage.",
    "rust": "Spray propiconazole or tebuconazole at first sign.",
    "coccidiosis": "Start anticoccidial treatment (Amprolium).",
    "newcastle": "Isolate immediately. Vaccinate remaining flock.",
    "salmonella": "Antibiotics under vet guidance. Improve hygiene.",
}

def get_treatment(disease):
    for key, tx in TREATMENTS.items():
        if key in disease.lower(): return tx
    return "Consult your local agricultural extension officer."

def classify_region(img_np, model_type, models, class_names, input_sizes):
    if model_type not in models: return "Unknown", 0.0
    size = input_sizes[model_type]
    inp = cv2.resize(img_np, (size, size)).astype(np.float32)/255.0
    inp = (inp - np.array([0.485,0.456,0.406])) / np.array([0.229,0.224,0.225])
    inp = np.expand_dims(inp.transpose(2,0,1), 0).astype(np.float32)
    logits = models[model_type].run(None, {"input":inp})[0][0]
    probs = np.exp(logits) / np.sum(np.exp(logits))
    idx = np.argmax(probs)
    return class_names[model_type][idx], float(probs[idx]*100)

# ── UI ──
st.title("🔍 GaiaLens™ — AR Crop Disease Scanner")
st.markdown("Point your camera at a field. Watch diseases light up in real‑time.")

uploaded_file = st.file_uploader("📤 Upload a farm photo", type=["jpg","jpeg","png"])

if uploaded_file:
    models, class_names, input_sizes, yolo = load_gaialens_models()
    
    image = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(image)
    
    if yolo is None:
        st.error("YOLO model not available. Please try again later.")
        st.stop()
    
    # YOLO detection via ONNX
    boxes = yolo.detect(img_np)
    
    # Process each detection
    draw = ImageDraw.Draw(image)
    detections = []
    
    for box in boxes:
        cls_id = box["class"]
        model_type = None
        if cls_id == 58: model_type = "crop"
        elif cls_id in [14,19]: model_type = "livestock"
        elif cls_id == 45: model_type = "pest"
        else: continue
        
        x1,y1,x2,y2 = box["bbox"]
        crop = img_np[y1:y2, x1:x2]
        if crop.size == 0: continue
        
        label, conf = classify_region(crop, model_type, models, class_names, input_sizes)
        is_healthy = "healthy" in label.lower()
        
        color = "green" if is_healthy else "red"
        draw.rectangle([x1,y1,x2,y2], outline=color, width=3)
        draw.text((x1, y1-15), f"{label} ({conf:.0f}%)", fill=color)
        
        treatment = get_treatment(label) if not is_healthy else None
        detections.append({
            "label": label, "confidence": conf,
            "model": model_type, "healthy": is_healthy,
            "treatment": treatment
        })
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.image(image, caption=f"🔍 {len(detections)} objects detected", use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Detections")
        for d in detections:
            emoji = "🟢" if d["healthy"] else "🔴"
            st.markdown(f"**{emoji} {d['model'].upper()}**: {d['label']} ({d['confidence']:.0f}%)")
            if d["treatment"]:
                st.info(f"💊 {d['treatment']}")

st.markdown("---")
cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/13_Help.py", label="💬 Help")
