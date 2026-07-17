
import streamlit as st
from PIL import Image
import numpy as np
import hashlib
import os
import sys

# ---------- Real model detection ----------
REAL_MODEL = False
MODEL_LOAD_ERROR = None

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
    from src.models.pretrained_vit import PretrainedViTClassifier
    from torchvision.transforms import Compose, Resize, ToTensor, Normalize
    import torch
    import torch.nn.functional as F
    REAL_MODEL = True
except Exception as e:
    MODEL_LOAD_ERROR = str(e)

# ---------- Scan deduction ----------
def deduct_and_show():
    import streamlit as st
    from supabase import create_client
    if "user" not in st.session_state or st.session_state.user is None:
        return
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
    user_id = st.session_state.user.id
    try:
        supabase.table("user_scans").insert(
            {"user_id": user_id, "scans_remaining": 30, "plan": "free"}
        ).execute()
    except:
        pass
    try:
        supabase.rpc("decrement_scan", {"uid": user_id}).execute()
        res = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
        if res.data:
            remaining = res.data[0]["scans_remaining"]
            st.success(f"Scan deducted. Remaining scans: {remaining}")
    except:
        pass

# ---------- Page config ----------
st.set_page_config(page_title="GAIA – Livestock Health", page_icon="🐄", layout="wide")
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #ede7f6 100%); }
    .title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #4a148c, #7c4dff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { font-size: 1.2rem; color: #555; margin-bottom: 2rem; }
    .pred-box { background: #f3e5f5; border-left: 5px solid #7c4dff; padding: 1rem 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
    .pred-box-high { border-left-color: #4a148c; background: #e1bee7; }
    .stProgress > div > div > div > div { background: linear-gradient(90deg, #7c4dff, #b388ff); }
    .badge-real { background: #4caf50; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; display: inline-block; }
    .badge-demo { background: #ff9800; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; display: inline-block; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🐄 Livestock Health</div>', unsafe_allow_html=True)

# Show which mode is active
if REAL_MODEL:
    st.markdown('<span class="badge-real">✅ Real AI Model Active</span>', unsafe_allow_html=True)
else:
    st.markdown(f'<span class="badge-demo">⚠️ Demo Mode — Real model unavailable ({MODEL_LOAD_ERROR})</span>', unsafe_allow_html=True)

st.markdown('<div class="subtitle">Detect common diseases in cattle and poultry from a photo</div>', unsafe_allow_html=True)

ANIMAL_CLASSES = {
    "cattle": ["Foot‑and‑Mouth Disease", "Healthy", "Lumpy Skin Disease"],
    "poultry": ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]
}

animal = st.selectbox("🐾 Choose animal", list(ANIMAL_CLASSES.keys()))
uploaded_file = st.file_uploader("📤 Upload animal photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption=f"Your {animal}", width=300)
    st.markdown("---")
    st.subheader("🩺 Health Check Result")

    probs = None
    used_real = False

    # ----- Try real model -----
    if REAL_MODEL:
        try:
            from app.utils.download_models import ensure_model
            checkpoint = ensure_model(animal)
            if os.path.exists(checkpoint):
                num_classes = len(ANIMAL_CLASSES[animal])
                model = PretrainedViTClassifier(num_classes=num_classes)
                state_dict = torch.load(checkpoint, map_location="cpu")
                model.load_state_dict(state_dict)
                model.eval()
                transform = Compose([
                    Resize((224, 224)),
                    ToTensor(),
                    Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                ])
                img_tensor = transform(image).unsqueeze(0)
                with torch.no_grad():
                    logits = model(img_tensor)
                    probs = F.softmax(logits, dim=1)[0].cpu().numpy()
                used_real = True
        except Exception as e:
            st.warning(f"Real model error: {e}")

    # ----- Fallback to demo -----
    if probs is None:
        class_names = ANIMAL_CLASSES[animal]
        seed = int(hashlib.md5(uploaded_file.name.encode()).hexdigest()[:8], 16)
        np.random.seed(seed)
        probs = np.random.rand(len(class_names))
        probs = probs / probs.sum()

    class_names = ANIMAL_CLASSES[animal]
    sorted_idx = np.argsort(probs)[::-1]

    for i, idx in enumerate(sorted_idx):
        disease = class_names[idx]
        percent = probs[idx] * 100
        box_class = "pred-box-high" if i == 0 else "pred-box"
        st.markdown(f'<div class="{box_class}"><b>{disease}</b> – {percent:.1f}%</div>', unsafe_allow_html=True)
        st.progress(float(probs[idx]))

    # Only deduct scan if real model was used
    if used_real:
        deduct_and_show()
    else:
        st.info("Demo mode — no scan deducted.")

    top_disease = class_names[sorted_idx[0]]
    if "healthy" in top_disease.lower():
        st.success(f"✅ Your {animal} appears healthy! Keep up the good care.")
    else:
        st.warning(f"⚠️ Possible **{top_disease}** detected. Isolate and consult a veterinarian immediately.")
