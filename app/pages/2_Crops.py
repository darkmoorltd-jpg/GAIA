import streamlit as st
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os
import sys
import hashlib
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌾", layout="wide")

# ---------- Crop definitions ----------
CROP_CLASSES = {
    "millet": ["Blast", "Rust", "Healthy"],
    "maize": ["Blight", "Common_Rust", "Gray_Leaf_Spot", "Healthy"],
    "rice": ["Bacterial Leaf Blight", "Brown Spot", "Healthy Rice Leaf", "Leaf Blast", "Leaf Scald", "Narrow Brown Spot", "Neck Blast", "Rice Hispa", "Sheath Blight", "Tungro"],
    "soybean": ["Bacterial Pustule", "Frogeye Leaf Spot", "Healthy", "Mosaic Virus", "Rust", "Southern blight", "Sudden Death Syndrome", "Target Leaf Spot", "Yellow Mosaic", "brown_spot", "crestamento", "ferrugen", "powdery_mildew", "septoria"],
    "pepper": ["Aphid", "Bacterial spot", "Blossom end rot", "Burn", "Edema", "Healthy", "Leaf curl", "Leaf miners", "Mosaic virus", "Nutrient deficiency", "Powdery mildew", "Spider mite", "Thrips"],
    "cabbage": ["Alternaria Leaf Spot", "Bacterial Spot Rot", "Black Rot", "Cabbage Aphid Colony", "Downy Mildew", "Healthy", "Club Root", "Ring Spot"],
}

CHECKPOINT_MAP = {
    "millet": "millet_3class",
    "maize": "maize",
    "rice": "rice_10class",
    "soybean": "soybean_14class",
    "pepper": "pepper_13class",
    "cabbage": "cabbage_8class",
}

# ---------- Theme toggle ----------
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark = st.toggle("", value=False, key="crops_theme")
theme = "dark" if dark else "light"

# ---------- CSS ----------
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); color: #fff; }
        header, footer { visibility: hidden; }
        .title { font-size: 2.8rem; font-weight: 800; text-align: center; background: linear-gradient(90deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #b0bec5; margin-bottom: 2rem; }
        .pred-box { background: rgba(255,255,255,.05); backdrop-filter: blur(12px); border-left: 5px solid #4caf50; padding: 1rem 1.5rem; border-radius: 10px; margin: .5rem 0; }
        .pred-box-high { border-left-color: #2e7d32; background: rgba(255,255,255,.1); font-weight: bold; }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #4caf50, #81c784); }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9, #f1f8e9); color: #1b5e20; }
        header, footer { visibility: hidden; }
        .title { font-size: 2.8rem; font-weight: 800; text-align: center; background: linear-gradient(90deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #33691e; margin-bottom: 2rem; }
        .pred-box { background: rgba(255,255,255,.9); border-left: 5px solid #4caf50; padding: 1rem 1.5rem; border-radius: 10px; margin: .5rem 0; }
        .pred-box-high { border-left-color: #2e7d32; background: #fff; font-weight: bold; }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #4caf50, #81c784); }
    </style>
    """, unsafe_allow_html=True)

# ---------- Session state ----------
if "selected_crop" not in st.session_state:
    st.session_state.selected_crop = None

# ---------- Scan deduction ----------
def deduct_one_scan():
    if "user" not in st.session_state or st.session_state.user is None:
        return
    from supabase import create_client
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    uid = st.session_state.user.id
    try:
        supabase.table("user_scans").insert({"user_id": uid, "scans_remaining": 30, "plan": "free"}).execute()
    except:
        pass
    try:
        supabase.rpc("decrement_scan", {"uid": uid}).execute()
    except:
        pass

# ---------- Model loader ----------
def load_crop_model(crop_name):
    from app.utils.download_models import ensure_model
    
    key = CHECKPOINT_MAP.get(crop_name, crop_name)
    checkpoint = ensure_model(key)
    
    if checkpoint is None or not os.path.exists(checkpoint):
        return None, None
    
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    
    prefix = "backbone." if any(k.startswith("backbone.") for k in state) else "encoder."
    embed_dim = state[f"{prefix}cls_token"].shape[-1]
    pos_embed = state[f"{prefix}pos_embed"]
    num_patches = pos_embed.shape[1] - 1
    grid = int(num_patches ** 0.5)
    img_size = grid * 16
    depth = len([k for k in state if k.startswith(f"{prefix}blocks") and k.endswith(".norm1.weight")])
    num_heads = 6 if embed_dim == 384 else 3
    
    from timm.models.vision_transformer import VisionTransformer
    backbone = VisionTransformer(img_size=img_size, patch_size=16, embed_dim=embed_dim, depth=depth, num_heads=num_heads, num_classes=0, global_pool='token')
    backbone_state = {k.replace(prefix, ""): v for k, v in state.items() if k.startswith(prefix)}
    backbone.load_state_dict(backbone_state, strict=False)
    
    n = len(CROP_CLASSES[crop_name])
    head = nn.Linear(embed_dim, n)
    try:
        head.load_state_dict({"weight": state["head.weight"], "bias": state.get("head.bias", torch.zeros(n))}, strict=False)
    except:
        pass
    
    class CropViT(nn.Module):
        def __init__(self, backbone, head):
            super().__init__()
            self.backbone = backbone
            self.head = head
        def forward(self, x):
            return self.head(self.backbone(x))
    
    model = CropViT(backbone, head)
    model.eval()
    return model, img_size

def predict(model, img, img_size):
    t = Compose([Resize((img_size, img_size)), ToTensor(), Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    with torch.no_grad():
        return F.softmax(model(t(img).unsqueeze(0)), dim=1)[0].detach().cpu().numpy()

# ---------- Hero ----------
st.markdown('<div class="title">🌾 Crop Disease Diagnosis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Select a crop, upload leaf photos, and let AI detect diseases in seconds</div>', unsafe_allow_html=True)

with st.expander("📸 How to take a good leaf photo", expanded=False):
    st.markdown("1. 🌿 Pick a single leaf showing symptoms – place on white paper.
2. 📱 Hold phone 20-30 cm above.
3. ☀️ Avoid shadows.
4. 📤 Upload 2-3 photos for best results.")

# ---------- Crop selection ----------
if st.session_state.selected_crop is None:
    cols = st.columns(len(CROP_CLASSES))
    for i, name in enumerate(CROP_CLASSES.keys()):
        with cols[i]:
            if st.button(name.title(), key=f"crop_btn_{name}", use_container_width=True):
                st.session_state.selected_crop = name
                st.rerun()
else:
    crop = st.session_state.selected_crop
    
    if st.button("← Back to Crops"):
        st.session_state.selected_crop = None
        st.rerun()
    
    st.markdown(f"### 🌱 Selected Crop: **{crop.title()}**")
    
    files = st.file_uploader("📤 Upload leaf images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if files:
        model, img_size = load_crop_model(crop)
        class_names = CROP_CLASSES[crop]
        
        for f in files:
            img = Image.open(f).convert("RGB")
            
            with st.expander(f"📷 {f.name}", expanded=True):
                c1, c2 = st.columns([1, 2])
                c1.image(img, caption=f.name, width=200)
                
                if model is None:
                    c2.warning("No trained model found – using demo predictions.")
                    seed = int(hashlib.md5(f.name.encode()).hexdigest()[:8], 16)
                    np.random.seed(seed)
                    probs = np.random.rand(len(class_names))
                    probs /= probs.sum()
                else:
                    try:
                        probs = predict(model, img, img_size)
                    except Exception as e:
                        c2.error(f"Error: {e}")
                        continue
                
                top_idx = np.argmax(probs)
                top_disease = class_names[top_idx]
                
                c2.markdown(f'<div class="pred-box-high"><b>{top_disease}</b> – {probs[top_idx]*100:.1f}%</div>', unsafe_allow_html=True)
                
                for i in np.argsort(probs)[::-1][1:5]:
                    c2.write(f"{class_names[i]}: {probs[i]*100:.1f}%")
                    c2.progress(float(probs[i]))
                
                deduct_one_scan()
                
                # AI Explanation
                if model is not None:
                    with st.spinner("🧠 GAIA is preparing your treatment guide..."):
                        try:
                            from app.utils.deepseek_explainer import explain_diagnosis
                            explanation, explain_err = explain_diagnosis(top_disease, probs[top_idx] * 100, crop, "crop")
                            if explanation:
                                with st.expander("📋 Complete Treatment Guide (AI-Generated)", expanded=True):
                                    st.markdown(explanation)
                        except Exception as e:
                            st.warning(f"Treatment guide unavailable: {str(e)[:100]}")

# ============================================
# FULL NAVIGATION
# ============================================
st.markdown("---")
st.markdown("### Quick Navigation")
cols = st.columns(10)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="Livestock")
with cols[5]: st.page_link("pages/17_Video_Scan.py", label="Video Scan")
with cols[6]: st.page_link("pages/19_Satellite.py", label="Satellite")
with cols[7]: st.page_link("pages/18_Voice_Agronomist.py", label="Voice AI")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="Buy Scans")
with cols[9]: st.page_link("pages/10_Early_Warning.py", label="Alerts")

st.markdown("### More Features")
cols2 = st.columns(10)
with cols2[0]: st.page_link("pages/11_Verify_Farmer.py", label="Verify")
with cols2[1]: st.page_link("pages/12_Verification_History.py", label="History")
with cols2[2]: st.page_link("pages/14_Wallet.py", label="Wallet")
with cols2[3]: st.page_link("pages/15_Badges.py", label="Badges")
with cols2[4]: st.page_link("pages/16_Chat.py", label="Chat")
with cols2[5]: st.page_link("pages/20_Marketplace.py", label="Market")
with cols2[6]: st.page_link("pages/21_Crop_Insurance.py", label="Insurance")
with cols2[7]: st.page_link("pages/6_Payment_History.py", label="Payments")
with cols2[8]: st.page_link("pages/8_Profile.py", label="Profile")
with cols2[9]: st.page_link("pages/13_Help.py", label="Help")
