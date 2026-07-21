
import streamlit as st
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os, sys, timm

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

# ---------- Page config (light mode default, sidebar expanded) ----------
st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌿", layout="wide", initial_sidebar_state="expanded")

# FORCE SIDEBAR VISIBLE
st.markdown("""

""", unsafe_allow_html=True)


# Force sidebar visible on all pages
st.markdown("""

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
    .top-nav a:hover { background: #e8f5e9; color: #1b5e20; }
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
        .result-card { background: rgba(0,0,0,0.6); backdrop-filter: blur(25px); border: 1px solid rgba(0,200,83,0.2); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; position: relative; overflow: hidden; }
        .result-card::before { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: conic-gradient(transparent, rgba(0,200,83,0.1), transparent, transparent); animation: rotate 6s linear infinite; }
        @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .result-card > * { position: relative; z-index: 1; }
        .top-result { border-color: #00c853; box-shadow: 0 0 50px rgba(0,200,83,0.4); }
        .top-result h3 { font-size: 1.6rem; text-transform: uppercase; letter-spacing: 2px; background: linear-gradient(90deg, #00ff88, #66ff99); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .progress-container { margin: 0.6rem 0; }
        .progress-label { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem; }
        .progress-label span { font-weight: 600; color: #ddd; }
        .progress-label .percent { color: #00ff88; font-size: 1.1rem; font-weight: 700; }
        .progress-bar { height: 8px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 10px; background: linear-gradient(90deg, #00ff88, #00cc66, #00ff88); background-size: 200% 100%; animation: shimmer 2s ease infinite, grow 1.5s ease-out; box-shadow: 0 0 15px rgba(0,200,83,0.6); }
        @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
        @keyframes grow { from { width: 0% !important; } }
        .counter { font-size: 4rem; font-weight: 900; background: linear-gradient(90deg, #00ff88, #66ff99); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 40px rgba(0,200,83,0.8); animation: pulse 2s ease-in-out infinite; }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
        .scan-left { background: rgba(0,200,83,0.15); border: 1px solid #00c853; border-radius: 15px; padding: 1rem; text-align: center; margin-top: 1.5rem; font-size: 1.2rem; color: #00ff88; }
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
        .result-card { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.08); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; }
        .top-result { border-color: #2e7d32; box-shadow: 0 0 15px rgba(46,125,50,0.15); }
        .top-result h3 { font-size: 1.6rem; color: #1b5e20; }
        .progress-container { margin: 0.6rem 0; }
        .progress-label { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem; }
        .progress-label span { font-weight: 600; color: #1b5e20; }
        .progress-label .percent { color: #2e7d32; font-size: 1.1rem; font-weight: 700; }
        .progress-bar { height: 8px; background: rgba(0,0,0,0.05); border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 10px; background: linear-gradient(90deg, #4caf50, #81c784); animation: grow 1.5s ease-out; }
        @keyframes grow { from { width: 0% !important; } }
        .counter { font-size: 4rem; font-weight: 900; color: #2e7d32; }
        .scan-left { background: rgba(46,125,50,0.1); border: 1px solid #2e7d32; border-radius: 15px; padding: 1rem; text-align: center; margin-top: 1.5rem; font-size: 1.2rem; color: #2e7d32; }
    </style>
    """, unsafe_allow_html=True)

# ---------- All crop definitions (original + new) ----------
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
              "Gall Midge", "Healthy", "Powdery Mildew", "Sooty Mould"],
    "tomato": ["Bacterial_spot", "Early_blight", "Late_blight", "Leaf_Mold",
              "Septoria_leaf_spot", "Spider_mites Two-spotted_spider_mite",
              "Target_Spot", "Tomato_Yellow_Leaf_Curl_Virus", "Tomato_mosaic_virus",
              "healthy", "powdery_mildew"],
    "orange": ["Citrus Canker", "Nutrient Deficiency (Yellow Leaf)",
              "Healthy", "Multiple Diseases", "Young Healthy"],
    "grape": ["Black Measles", "Black Rot", "Healthy", "Leaf Blight"]
}

# ---------- Custom model classes for new crops ----------
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

class TomatoViT11(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=0)
        self.head = nn.Sequential(
            nn.Linear(self.backbone.embed_dim, 1024), nn.GELU(), nn.Dropout(0.3),
            nn.Linear(1024, 512), nn.GELU(), nn.Dropout(0.2),
            nn.Linear(512, len(CROP_CLASSES["tomato"]))
        )
    def forward(self, x): return self.head(self.backbone(x))

class GrapeViT4(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=0)
        self.head = nn.Sequential(
            nn.Linear(self.backbone.embed_dim, 512), nn.GELU(), nn.Dropout(0.3),
            nn.Linear(512, 256), nn.GELU(), nn.Dropout(0.2),
            nn.Linear(256, len(CROP_CLASSES["grape"]))
        )
    def forward(self, x): return self.head(self.backbone(x))

class OrangeViT5(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=0)
        self.head = nn.Sequential(
            nn.Linear(self.backbone.embed_dim, 1024), nn.GELU(), nn.Dropout(0.3),
            nn.Linear(1024, 512), nn.GELU(), nn.Dropout(0.2),
            nn.Linear(512, len(CROP_CLASSES["orange"]))
        )
    def forward(self, x): return self.head(self.backbone(x))

# ---------- Model loader with CORRECTED paths ----------
@st.cache_resource
def load_crop_model(crop_name: str):
    """Load the correct model for the given crop."""
    
    # Define checkpoint path per crop
    checkpoint_map = {
        "rice": "checkpoints/rice/best_model.pt",
        "maize": "checkpoints/maize/best_model.pt",
        "beans": "checkpoints/beans/best_model.pt",
        "potato": "checkpoints/potato/best_model.pt",
        "wheat": "checkpoints/wheat/best_model.pt",
        "banana": "checkpoints/banana/best_model.pt",
        "apple": "checkpoints/apple_13class/best_model.pt",
        "mango": "checkpoints/mango_8class/best_model.pt",
        "tomato": "checkpoints/tomato_11class/best_model.pt",
        "orange": "checkpoints/orange_5class/best_model.pt",
        "grape": "checkpoints/grape_4class/best_model.pt"
    }
    
    checkpoint = checkpoint_map.get(crop_name, f"checkpoints/{crop_name}/best_model.pt")
    
    if not os.path.exists(checkpoint):
        raise FileNotFoundError(f"Model not found at {checkpoint}")
    
    num_classes = len(CROP_CLASSES[crop_name])
    
    # Choose the right model class
    if crop_name == "apple":
        model = AppleViT13()
    elif crop_name == "mango":
        model = MangoViT8()
    elif crop_name == "tomato":
        model = TomatoViT11()
    elif crop_name == "grape":
        model = GrapeViT4()
    elif crop_name == "orange":
        model = OrangeViT5()
    else:
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

# ---------- Scan deduction ----------
def deduct_and_show(user_id):
    from supabase import create_client
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
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
            st.markdown(f'<div class="scan-left">🛰️ Scans remaining after this diagnosis: <b>{remaining}</b></div>', unsafe_allow_html=True)
    except:
        st.warning("Scan deduction unavailable.")

# ---------- UI ----------
st.markdown('<div class="title">🌿 Crop Disease Diagnosis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a leaf photo and let AI detect any disease in seconds</div>', unsafe_allow_html=True)

# ---------- Sidebar Toggle (click if sidebar is hidden) ----------
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("☰ Menu", help="Show sidebar navigation"):
        st.markdown("""
        <script>
            // Force sidebar to open via JavaScript
            const sidebar = parent.document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                sidebar.style.display = 'block';
                sidebar.style.visibility = 'visible';
                sidebar.style.width = '280px';
            }
        </script>
        """, unsafe_allow_html=True)


crop = st.selectbox("🌾 Choose your crop", list(CROP_CLASSES.keys()))
uploaded_files = st.file_uploader("📤 Upload leaf images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Your leaf", width=300)

    st.markdown("---")

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
    top_idx = np.argmax(probs)
    top_prob = probs[top_idx] * 100

    # Top result card
    st.markdown(f"""
    <div class="result-card top-result">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <p style="color: #66ff99; margin: 0; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 2px;">Identified Disease</p>
                <h3 style="margin: 0.5rem 0;">{class_names[top_idx]}</h3>
            </div>
            <div class="counter">{top_prob:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔬 PROBABILITY BREAKDOWN")
    sorted_idx = np.argsort(probs)[::-1]

    for i in sorted_idx:
        disease = class_names[i]
        percent = probs[i] * 100
        bar_class = " warning" if percent < 40 else (" danger" if percent < 20 else "")

        st.markdown(f"""
        <div class="result-card">
            <div class="progress-container">
                <div class="progress-label">
                    <span>{disease.upper()}</span>
                    <span class="percent">{percent:.1f}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill{bar_class}" style="width: {percent}%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    top_disease = class_names[top_idx]
    if "healthy" in top_disease.lower():
        st.success("✅ Your crop looks healthy! Keep up the good work.")
    else:
        st.warning(f"⚠️ Possible **{top_disease}** detected. Consider appropriate treatment.")

    if st.session_state.get("user"):
        deduct_and_show(st.session_state.user.id)


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
