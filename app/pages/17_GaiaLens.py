
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import onnxruntime as ort
import os, requests

st.set_page_config(page_title="GAIA – GaiaLens™", page_icon="🔍", layout="wide")

# ── INLINE DOWNLOAD ──
BASE = "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v2.0-gaialens"
GAIA_LENS_MODELS = {
    "gaia_crop.onnx": f"{BASE}/gaia_crop.onnx",
    "gaia_crop.onnx.data": f"{BASE}/gaia_crop.onnx.data",
    "gaia_pest.onnx": f"{BASE}/gaia_pest.onnx",
    "gaia_pest.onnx.data": f"{BASE}/gaia_pest.onnx.data",
    "gaia_soil.onnx": f"{BASE}/gaia_soil.onnx",
    "gaia_soil.onnx.data": f"{BASE}/gaia_soil.onnx.data",
    "gaia_livestock.onnx": f"{BASE}/gaia_livestock.onnx",
    "gaia_livestock.onnx.data": f"{BASE}/gaia_livestock.onnx.data",
}

def ensure_onnx(filename):
    os.makedirs("onnx", exist_ok=True)
    dest = os.path.join("onnx", filename)
    if not os.path.exists(dest) or os.path.getsize(dest) < 1000:
        url = GAIA_LENS_MODELS.get(filename)
        if url:
            with st.spinner(f"⬇️ Downloading {filename}..."):
                r = requests.get(url, stream=True, timeout=300)
                if r.status_code == 200:
                    with open(dest, "wb") as f:
                        for chunk in r.iter_content(32768):
                            f.write(chunk)
    return dest

def pil_resize(img_np, size):
    return np.array(Image.fromarray(img_np).resize((size, size), Image.BILINEAR))

def preprocess_gaia(img_np, size):
    img = pil_resize(img_np, size).astype(np.float32) / 255.0
    img = (img - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
    img = img.transpose(2, 0, 1)
    return np.expand_dims(img, axis=0).astype(np.float32)

@st.cache_resource
def load_gaia_models():
    for f in GAIA_LENS_MODELS:
        ensure_onnx(f)
    
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
    
    return models, class_names, input_sizes

def classify_image(img_np, model_type, models, class_names, input_sizes):
    if model_type not in models: return "N/A", 0.0
    size = input_sizes[model_type]
    inp = preprocess_gaia(img_np, size)
    logits = models[model_type].run(None, {"input":inp})[0][0]
    probs = np.exp(logits) / np.sum(np.exp(logits))
    top3_idx = np.argsort(probs)[-3:][::-1]
    results = []
    for idx in top3_idx:
        results.append({
            "label": class_names[model_type][idx],
            "confidence": float(probs[idx] * 100)
        })
    return results

# ── UI ──
st.title("🔍 GaiaLens™ — Multi‑AI Farm Scanner")
st.markdown("Upload a farm photo. All 4 GAIA models analyze it simultaneously — crops, pests, soil, and livestock.")

# Model selection
st.sidebar.markdown("### 🎯 Select Models")
scan_crop = st.sidebar.checkbox("🌿 Crop Disease", value=True)
scan_pest = st.sidebar.checkbox("🐛 Pest Detection", value=True)
scan_soil = st.sidebar.checkbox("🏞️ Soil Analysis", value=True)
scan_livestock = st.sidebar.checkbox("🐄 Livestock Health", value=True)

uploaded_file = st.file_uploader("📤 Upload a farm photo", type=["jpg","jpeg","png"])

if uploaded_file:
    models, class_names, input_sizes = load_gaia_models()
    
    image = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(image)
    
    st.image(image, caption="📸 Your Farm Photo", use_container_width=True)
    
    st.markdown("---")
    st.markdown("## 🔬 GAIA Multi‑Model Analysis")
    
    active_models = []
    if scan_crop: active_models.append(("crop", "🌿 Crop Disease"))
    if scan_pest: active_models.append(("pest", "🐛 Pest Detection"))
    if scan_soil: active_models.append(("soil", "🏞️ Soil Analysis"))
    if scan_livestock: active_models.append(("livestock", "🐄 Livestock Health"))
    
    if not active_models:
        st.warning("Select at least one model from the sidebar.")
        st.stop()
    
    cols = st.columns(len(active_models))
    
    for i, (model_key, model_label) in enumerate(active_models):
        with cols[i]:
            st.markdown(f"### {model_label}")
            
            with st.spinner(f"Analyzing with {model_label}..."):
                results = classify_image(img_np, model_key, models, class_names, input_sizes)
            
            top = results[0]
            is_healthy = "healthy" in top["label"].lower()
            emoji = "✅" if is_healthy else "⚠️"
            
            st.markdown(f"### {emoji} {top['label']}")
            st.markdown(f"**Confidence: {top['confidence']:.1f}%**")
            st.progress(top["confidence"] / 100)
            
            if len(results) > 1:
                st.markdown("**Other possibilities:**")
                for r in results[1:]:
                    st.write(f"• {r['label']} ({r['confidence']:.1f}%)")
    
    # Summary
    st.markdown("---")
    st.markdown("## 📋 Field Summary")
    
    summary_cols = st.columns(len(active_models))
    for i, (model_key, model_label) in enumerate(active_models):
        with summary_cols[i]:
            results = classify_image(img_np, model_key, models, class_names, input_sizes)
            top = results[0]
            st.metric(
                label=model_label,
                value=top["label"],
                delta=f"{top['confidence']:.0f}% confidence"
            )

st.markdown("---")
st.markdown("### 💡 How GaiaLens Works")
st.markdown("""
1. **Upload** any farm photo
2. **GAIA analyzes** it simultaneously with crop, pest, soil, and livestock AI models
3. **Each model** returns its top prediction with confidence scores
4. **AR version coming soon** — real‑time bounding boxes on live camera feed
""")

st.markdown("---")
cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/13_Help.py", label="💬 Help")
