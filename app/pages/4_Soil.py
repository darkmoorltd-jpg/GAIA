
import streamlit as st
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os, sys, timm

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Soil Analysis", page_icon="🏞️", layout="wide", initial_sidebar_state="expanded")

# Force sidebar visible on all pages
st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
    }
</style>
""", unsafe_allow_html=True)


# ---------- Dashboard top nav ----------
st.markdown("""
<style>
    .top-nav {
        display: flex; justify-content: center; gap: 2rem;
        padding: 0.8rem; background: rgba(255,255,255,0.9); backdrop-filter: blur(15px);
        border-radius: 15px; margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .top-nav a {
        color: #2e7d32; text-decoration: none; font-weight: 600;
        font-size: 1rem; padding: 0.5rem 1.5rem; border-radius: 30px;
        transition: all 0.3s ease;
    }
    .top-nav a:hover {
        background: #e8f5e9; color: #1b5e20;
    }
</style>
<div class="top-nav">
    <a href="/" target="_self">🏠 Dashboard</a>
</div>
""", unsafe_allow_html=True)


# Theme toggle
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=(st.session_state.theme == "dark"), key="soil_theme_toggle")
st.session_state.theme = "dark" if dark_mode else "light"
theme = st.session_state.theme

SOIL_CLASSES = [
    "alluvial", "black", "cinder", "clay", "laterite",
    "loamy", "peat", "red", "sandy", "sandy_loam", "yellow"
]
NUM_CLASSES = len(SOIL_CLASSES)

SOIL_COLORS = {
    "alluvial": "#8d6e63", "black": "#3e2723", "cinder": "#616161",
    "clay": "#b7410e", "laterite": "#d84315", "loamy": "#6d4c41",
    "peat": "#4e342e", "red": "#c62828", "sandy": "#d4a373",
    "sandy_loam": "#a1887f", "yellow": "#f9a825"
}

class SoilViT11(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=0)
        self.head = nn.Sequential(
            nn.Linear(self.backbone.embed_dim, 1024), nn.GELU(), nn.Dropout(0.3),
            nn.Linear(1024, 512), nn.GELU(), nn.Dropout(0.2),
            nn.Linear(512, NUM_CLASSES)
        )
    def forward(self, x): return self.head(self.backbone(x))

@st.cache_resource
def load_soil_model():
    checkpoint = "checkpoints/soil_11class/best_model.pt"
    if not os.path.exists(checkpoint):
        raise FileNotFoundError(f"Model not found at {checkpoint}")
    model = SoilViT11()
    state_dict = torch.load(checkpoint, map_location="cpu", weights_only=False)
    model.load_state_dict(state_dict)
    model.eval()
    return model

def predict_image(model, image: Image.Image):
    transform = Compose([
        Resize((224, 224)),
        ToTensor(),
        Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    img_tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        logits = model(img_tensor)
        probs = F.softmax(logits, dim=1)[0].cpu().numpy()
    return probs

def deduct_and_show():
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

# CSS
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #1a120b 0%, #2e1c0d 30%, #3e2a14 60%, #1a0f05 100%); color: #f5f0eb; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #d4a373, #f5e6d3, #d4a373); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 25px rgba(212, 163, 115, 0.7); margin-bottom: 0.5rem; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #bcaaa4; margin-bottom: 2rem; }
        .soil-result-card { background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); border: 1px solid rgba(212, 163, 115, 0.2); border-radius: 20px; padding: 1.5rem; margin: 0.5rem 0; }
        .top-result { border-color: #d4a373; box-shadow: 0 0 30px rgba(212, 163, 115, 0.3); }
        .soil-swatch { display: inline-block; width: 20px; height: 20px; border-radius: 4px; margin-right: 8px; vertical-align: middle; box-shadow: 0 0 10px rgba(0,0,0,0.5); }
        .stProgress > div > div > div > div { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #efebe9 0%, #d7ccc8 100%); color: #3e2723; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #5d4037, #8d6e63, #5d4037); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 10px rgba(93,64,55,0.3); margin-bottom: 0.5rem; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #4e342e; margin-bottom: 2rem; }
        .soil-result-card { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.1); border-radius: 20px; padding: 1.5rem; margin: 0.5rem 0; }
        .top-result { border-color: #5d4037; box-shadow: 0 0 20px rgba(93,64,55,0.2); }
        .soil-swatch { display: inline-block; width: 20px; height: 20px; border-radius: 4px; margin-right: 8px; vertical-align: middle; box-shadow: 0 0 5px rgba(0,0,0,0.2); }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="title">🏞️ Soil Type Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload close‑up photos of soil to identify the type</div>', unsafe_allow_html=True)

uploaded_files = st.file_uploader("📤 Drop your soil photos here", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    model = load_soil_model()
    for uploaded_file in uploaded_files:
        with st.expander(f"🏞️ {uploaded_file.name}", expanded=(len(uploaded_files) == 1)):
            col1, col2 = st.columns([1, 2])
            with col1:
                image = Image.open(uploaded_file).convert("RGB")
                st.image(image, caption=uploaded_file.name, width=300)
            with col2:
                probs = predict_image(model, image)
                top_idx = np.argmax(probs)
                top_soil = SOIL_CLASSES[top_idx]
                top_color = SOIL_COLORS[top_soil]

                st.markdown(f"""
                <div class="soil-result-card top-result" style="border-left: 5px solid {top_color};">
                    <h2 style="margin:0; display: flex; align-items: center;">
                        <span class="soil-swatch" style="background-color: {top_color};"></span>
                        {top_soil.title()}
                        <span style="margin-left: auto; font-size: 2rem; color: {top_color};">{probs[top_idx]*100:.1f}%</span>
                    </h2>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("#### All Soil Types")
                for i, (soil_type, color) in enumerate(SOIL_COLORS.items()):
                    percent = probs[i] * 100
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; margin: 0.5rem 0;">
                        <span class="soil-swatch" style="background-color: {color};"></span>
                        <span style="width: 130px;">{soil_type.title()}</span>
                        <span style="width: 60px; text-align: right;">{percent:.1f}%</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.progress(float(probs[i]))

                deduct_and_show()


# ---------- Universal Bottom Navigation (safe) ----------
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(6)
with cols[0]:
    st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]:
    st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]:
    st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]:
    st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]:
    st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]:
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
