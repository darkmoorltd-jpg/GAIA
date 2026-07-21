
import streamlit as st
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os, sys, timm

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Livestock Health", page_icon="🐄", layout="wide", initial_sidebar_state="expanded")

# FORCE SIDEBAR VISIBLE
st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        width: 280px !important;
    }
</style>
""", unsafe_allow_html=True)


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

dark_mode = st.toggle("", value=(st.session_state.theme == "dark"), key="livestock_theme_toggle")
st.session_state.theme = "dark" if dark_mode else "light"
theme = st.session_state.theme

ANIMAL_CLASSES = {
    "cattle": ["Foot‑and‑Mouth Disease", "Healthy", "Lumpy Skin Disease"],
    "poultry": ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]
}

class LivestockClassifier(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.backbone = timm.create_model('vit_tiny_patch16_224', pretrained=False, num_classes=0)
        self.head = nn.Linear(self.backbone.embed_dim, num_classes)
    def forward(self, x): return self.head(self.backbone(x))

@st.cache_resource
def load_animal_model(animal: str):
    checkpoint = f"checkpoints/{animal}/best_model.pt"
    if not os.path.exists(checkpoint):
        raise FileNotFoundError(f"Model not found at {checkpoint}")
    num_classes = len(ANIMAL_CLASSES[animal])
    model = LivestockClassifier(num_classes=num_classes)
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
        .stApp { background: linear-gradient(145deg, #0a0a0a 0%, #1a1a2e 50%, #0d0d0d 100%); color: #e0e0e0; }
        header, footer {visibility: hidden;}
        .title { font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #7c4dff, #b388ff, #7c4dff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 30px rgba(124,77,255,0.6); margin-bottom: 0.5rem; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #90a4ae; margin-bottom: 2rem; }
        .pred-box { background: rgba(0,0,0,0.6); backdrop-filter: blur(25px); border: 1px solid rgba(124,77,255,0.2); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; }
        .top-result { border-color: #7c4dff; box-shadow: 0 0 50px rgba(124,77,255,0.4); }
        .counter { font-size: 3rem; font-weight: 900; background: linear-gradient(90deg, #7c4dff, #b388ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #7c4dff, #b388ff); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); color: #1b5e20; }
        header, footer {visibility: hidden;}
        .title { font-size: 3rem; font-weight: 900; text-align: center; color: #4a148c; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #33691e; margin-bottom: 2rem; }
        .pred-box { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.08); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; }
        .top-result { border-color: #7c4dff; box-shadow: 0 0 15px rgba(124,77,255,0.15); }
        .counter { font-size: 3rem; font-weight: 900; color: #4a148c; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="title">🐄 Livestock Health</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Detect common diseases in cattle and poultry from photos</div>', unsafe_allow_html=True)

animal = st.selectbox("🐾 Choose animal", list(ANIMAL_CLASSES.keys()))
uploaded_files = st.file_uploader("📤 Upload animal photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    model = load_animal_model(animal)
    for uploaded_file in uploaded_files:
        with st.expander(f"🐄 {uploaded_file.name}", expanded=(len(uploaded_files) == 1)):
            col1, col2 = st.columns([1, 2])
            with col1:
                image = Image.open(uploaded_file).convert("RGB")
                st.image(image, caption=uploaded_file.name, width=300)
            with col2:
                probs = predict_image(model, image)
                class_names = ANIMAL_CLASSES[animal]
                top_idx = np.argmax(probs)
                top_prob = probs[top_idx] * 100

                st.markdown(f"""
                <div class="pred-box top-result">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <p style="margin:0; font-size:0.8rem; text-transform:uppercase; letter-spacing:2px; color:#90a4ae;">Diagnosis</p>
                            <h3 style="margin:0.5rem 0;">{class_names[top_idx]}</h3>
                        </div>
                        <div class="counter">{top_prob:.1f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("#### All Conditions")
                sorted_idx = np.argsort(probs)[::-1]
                for idx in sorted_idx:
                    st.write(f"**{class_names[idx]}**: {probs[idx]*100:.1f}%")
                    st.progress(float(probs[idx]))

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
