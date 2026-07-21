
import streamlit as st
from PIL import Image
import torch
import torch.nn.functional as F
import numpy as np
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from torchvision.transforms import Compose, Resize, ToTensor, Normalize

# ---------- Page config ----------
st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌿", layout="wide")

# ---------- Theme toggle ----------
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="crops_theme_toggle")
theme = "dark" if dark_mode else "light"

if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #ffffff; }
        .title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { font-size: 1.2rem; color: #b0bec5; margin-bottom: 2rem; }
        .pred-box { background: rgba(255,255,255,0.05); backdrop-filter: blur(12px); border-left: 5px solid #4caf50; padding: 1rem 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
        .pred-box-high { border-left-color: #2e7d32; background: rgba(255,255,255,0.1); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #4caf50, #81c784); }
        header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); color: #1b5e20; }
        .title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { font-size: 1.2rem; color: #33691e; margin-bottom: 2rem; }
        .pred-box { background: rgba(255,255,255,0.9); border-left: 5px solid #4caf50; padding: 1rem 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
        .pred-box-high { border-left-color: #2e7d32; background: rgba(255,255,255,1); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #4caf50, #81c784); }
        header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


st.markdown('<div class="title">🌿 Crop Disease Diagnosis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload leaf photos and let AI detect any disease in seconds</div>', unsafe_allow_html=True)

crop = st.selectbox("🌾 Choose your crop", list(CROP_CLASSES.keys()))
uploaded_files = st.file_uploader("📤 Upload leaf images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    model, path = load_crop_model(crop)
    class_names = CROP_CLASSES[crop]

    for file in uploaded_files:
        image = Image.open(file).convert("RGB")
        with st.expander(f"📷 {file.name}", expanded=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(image, caption=file.name, width=200)
            with col2:
                if model is None:
                    st.warning("No trained model – using demo predictions.")
                    import hashlib
                    seed = int(hashlib.md5(file.name.encode()).hexdigest()[:8], 16)
                    np.random.seed(seed)
                    probs = np.random.rand(len(class_names))
                    probs = probs / probs.sum()
                else:
                    try:
                        probs = predict_image(model, image)
                    except Exception as e:
                        st.error(f"Inference error: {e}")
                        continue

                sorted_idx = np.argsort(probs)[::-1]
                top_disease = class_names[sorted_idx[0]]
                st.markdown(f"**Top Result:** {top_disease} ({probs[sorted_idx[0]]*100:.1f}%)")

                for i in sorted_idx[:5]:
                    st.write(f"{class_names[i]}: {probs[i]*100:.1f}%")
                    st.progress(float(probs[i]))

            # Scan deduction per image
            try:
                if st.session_state.get("user"):
                    from app.utils.supabase_utils import decrement_scan
                    decrement_scan(st.session_state.user.id)
            except:
                pass

# ---------- Navigation Bar (bottom) ----------
st.markdown("""
<style>
    .nav-bar { display: flex; justify-content: center; gap: 1rem; margin: 2rem 0 1rem 0; flex-wrap: wrap; }
    .nav-bar a { text-decoration: none; color: inherit; }
    .nav-button {
        display: inline-block; padding: 10px 20px; border-radius: 12px;
        background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2); transition: all 0.3s ease;
        cursor: pointer; font-weight: 600; font-size: 0.95rem;
    }
    .nav-button:hover { background: rgba(255,255,255,0.2); border-color: rgba(255,255,255,0.5); transform: translateY(-2px); }
</style>
""", unsafe_allow_html=True)

cols = st.columns(5)
pages = [
    ("🏠 Dashboard", "pages/1_Dashboard.py"),
    ("🌿 Crops", "pages/2_Crops.py"),
    ("🐛 Pests", "pages/3_Pests.py"),
    ("🏞️ Soil", "pages/4_Soil.py"),
    ("🐄 Livestock", "pages/5_Livestock.py")
]
for col, (label, path) in zip(cols, pages):
    with col:
        st.page_link(path, label=label, help=f"Go to {label}")

