
import streamlit as st
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os
import sys
import timm

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from torchvision.transforms import Compose, Resize, ToTensor, Normalize

# ---------- Page config (light mode default) ----------
st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌿", layout="wide", initial_sidebar_state="expanded")

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

# ---------- Theme toggle (light default) ----------
if "theme" not in st.session_state:
    st.session_state.theme = "light"

st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=(st.session_state.theme == "dark"), key="crops_theme_toggle")
st.session_state.theme = "dark" if dark_mode else "light"
theme = st.session_state.theme

# ---------- CSS based on theme ----------
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(145deg, #0a0a0a 0%, #1a1a2e 50%, #0d0d0d 100%); color: #e0e0e0; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #00c853, #69f0ae, #00c853); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 30px rgba(0,200,83,0.6); margin-bottom: 0.5rem; animation: glow 2s ease-in-out infinite alternate; }
        @keyframes glow { from { text-shadow: 0 0 20px rgba(0,200,83,0.6); } to { text-shadow: 0 0 40px rgba(0,200,83,1), 0 0 80px rgba(0,200,83,0.8); } }
        .subtitle { text-align: center; font-size: 1.3rem; color: #90a4ae; margin-bottom: 2rem; }
        .stFileUploader > div { background: rgba(0,200,83,0.03) !important; backdrop-filter: blur(15px) !important; border: 2px dashed rgba(0,200,83,0.3) !important; border-radius: 20px !important; padding: 2rem !important; transition: all 0.3s ease; }
        .stFileUploader > div:hover { border-color: #00c853 !important; box-shadow: 0 0 30px rgba(0,200,83,0.2); }
        .stImage img { border-radius: 20px; box-shadow: 0 0 40px rgba(0,200,83,0.3); border: 1px solid rgba(0,200,83,0.2); }
        .pred-box { background: rgba(0,0,0,0.6); backdrop-filter: blur(25px); border: 1px solid rgba(0,200,83,0.2); border-radius: 15px; padding: 1.2rem; margin: 0.5rem 0; }
        .pred-box-high { border-color: #00c853; box-shadow: 0 0 30px rgba(0,200,83,0.4); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #00c853, #69f0ae); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); color: #1b5e20; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #2e7d32, #66bb6a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 10px rgba(46,125,50,0.3); margin-bottom: 0.5rem; }
        .subtitle { text-align: center; font-size: 1.3rem; color: #33691e; margin-bottom: 2rem; }
        .stFileUploader > div { background: rgba(255,255,255,0.8) !important; backdrop-filter: blur(10px) !important; border: 2px dashed rgba(46,125,50,0.3) !important; border-radius: 20px !important; padding: 2rem !important; }
        .stFileUploader > div:hover { border-color: #2e7d32 !important; background: rgba(46,125,50,0.1) !important; }
        .stImage img { border-radius: 20px; box-shadow: 0 0 20px rgba(0,0,0,0.15); }
        .pred-box { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.08); border-radius: 15px; padding: 1.2rem; margin: 0.5rem 0; }
        .pred-box-high { border-color: #2e7d32; box-shadow: 0 0 15px rgba(46,125,50,0.15); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #4caf50, #81c784); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ---------- Crop definitions ----------
CROP_CLASSES = {
    "rice": ["Bacterial Blight", "Brown Spot", "Leaf Smut"],
    "maize": ["Northern Leaf Blight", "Healthy", "Southern Leaf Blight", "Common Rust"],
    "beans": ["Angular Leaf Spot", "Bean Rust", "Healthy"],
    "potato": ["Bacteria", "Fungi", "Healthy", "Nematode", "Pest", "Phytophthora", "Virus"],
    "wheat": ["Aphid", "Black Rust", "Blast", "Brown Rust", "Common Root Rot",
              "Fusarium Head Blight", "Healthy", "Leaf Blight", "Mildew", "Mite",
              "Septoria", "Smut", "Stem Fly", "Tan Spot", "Yellow Rust"],
    "banana": ["Fusarium Wilt", "Healthy", "Natural Death Leaf", "Rhizome Root"],
    "apple": ["Alternaria Leaf Spot", "Apple Scab", "Apple rot", "Block rot",
              "Brown Spot", "Cedar apple rust", "Frogeye Leaf Spot", "Grey Spot",
              "Healthy", "Leaf Blotch", "Mosaic", "Powdery Mildew", "Rust"],
    "mango": ["Anthracnose", "Bacterial Canker", "Cutting Weevil", "Die Back",
              "Gall Midge", "Healthy", "Powdery Mildew", "Sooty Mould"]
}

# ---------- Custom model classes for Apple and Mango ----------
class AppleViT13(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=0)
        self.head = nn.Sequential(
            nn.Linear(self.backbone.embed_dim, 1024), nn.GELU(), nn.Dropout(0.3),
            nn.Linear(1024, 512), nn.GELU(), nn.Dropout(0.2),
            nn.Linear(512, len(CROP_CLASSES["apple"]))
        )
    def forward(self, x): return self.head(self.backbone(x))

class MangoViT8(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=0)
        self.head = nn.Sequential(
            nn.Linear(self.backbone.embed_dim, 1024), nn.GELU(), nn.Dropout(0.3),
            nn.Linear(1024, 512), nn.GELU(), nn.Dropout(0.2),
            nn.Linear(512, len(CROP_CLASSES["mango"]))
        )
    def forward(self, x): return self.head(self.backbone(x))

# ---------- Model loader ----------
@st.cache_resource
def load_crop_model(crop_name: str):
    if crop_name in ["apple", "mango"]:
        checkpoint = f"checkpoints/{crop_name}_13class/best_model.pt" if crop_name == "apple" else f"checkpoints/{crop_name}_8class/best_model.pt"
        if not os.path.exists(checkpoint):
            raise FileNotFoundError(f"Model not found at {checkpoint}")
        model = AppleViT13() if crop_name == "apple" else MangoViT8()
        state_dict = torch.load(checkpoint, map_location="cpu", weights_only=False)
        model.load_state_dict(state_dict)
        model.eval()
        return model
    else:
        checkpoint = f"checkpoints/{crop_name}/best_model.pt"
        if not os.path.exists(checkpoint):
            raise FileNotFoundError(f"Model not found at {checkpoint}")
        num_classes = len(CROP_CLASSES[crop_name])
        from src.models.pretrained_vit import PretrainedViTClassifier
        model = PretrainedViTClassifier(num_classes=num_classes)
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

# ---------- UI ----------
st.markdown('<div class="title">🌿 Crop Disease Diagnosis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a leaf photo and let AI detect any disease in seconds</div>', unsafe_allow_html=True)

crop = st.selectbox("🌾 Choose your crop", list(CROP_CLASSES.keys()))
uploaded_file = st.file_uploader("📤 Upload leaf image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Your leaf", width=300)

    st.markdown("---")
    st.subheader("📊 Diagnosis Results")

    try:
        model = load_crop_model(crop)
        probs = predict_image(model, image)
    except FileNotFoundError as e:
        st.error(f"🚫 {e}")
        st.info("Please train and save the model first, or contact support.")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred during inference: {e}")
        st.stop()

    class_names = CROP_CLASSES[crop]
    sorted_idx = np.argsort(probs)[::-1]

    for i, idx in enumerate(sorted_idx):
        disease = class_names[idx]
        percent = probs[idx] * 100
        box_class = "pred-box-high" if i == 0 else "pred-box"
        st.markdown(
            f'<div class="{box_class}"><b>{disease}</b> – {percent:.1f}%</div>',
            unsafe_allow_html=True
        )
        st.progress(float(probs[idx]))

    top_disease = class_names[sorted_idx[0]]
    if "healthy" in top_disease.lower():
        st.success("✅ Your crop looks healthy! Keep up the good work.")
    else:
        st.warning(f"⚠️ Possible **{top_disease}** detected. Consider appropriate treatment.")

    if st.session_state.get("user"):
        try:
            from app.utils.supabase_utils import decrement_scan
            decrement_scan(st.session_state.user.id)
            st.success("Scan deducted.")
        except:
            pass
