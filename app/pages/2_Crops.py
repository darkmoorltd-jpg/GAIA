
import streamlit as st
from PIL import Image
import torch
import torch.nn.functional as F
import numpy as np
import os
import sys
import yaml

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.models.gaia_model import GAIAModel
from src.models.pretrained_vit import PretrainedViTClassifier
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

# ---------- Theme toggle (default light) ----------
st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌿", layout="wide")

st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

# Default to light mode
if "crop_theme" not in st.session_state:
    st.session_state.crop_theme = "light"

dark_mode = st.toggle("", value=(st.session_state.crop_theme == "dark"), key="crop_theme_toggle")

if dark_mode:
    st.session_state.crop_theme = "dark"
else:
    st.session_state.crop_theme = "light"

theme = st.session_state.crop_theme

# ---------- Crop definitions ----------
CROP_CLASSES = {
    "rice": ["Bacterial Blight", "Brown Spot", "Leaf Smut"],
    "maize": ["Northern Leaf Blight", "Healthy", "Southern Leaf Blight", "Common Rust"],
    "beans": ["Angular Leaf Spot", "Bean Rust", "Healthy"],
    "potato": ["Bacteria", "Fungi", "Healthy", "Nematode", "Pest", "Phytophthora", "Virus"],
    "wheat": ["Aphid", "Black Rust", "Blast", "Brown Rust", "Common Root Rot", "Fusarium Head Blight", "Healthy", "Leaf Blight", "Mildew", "Mite", "Septoria", "Smut", "Stem Fly", "Tan Spot", "Yellow Rust"],
    "banana": ["Fusarium Wilt", "Healthy", "Natural Death Leaf", "Rhizome Root"]
}

# ---------- Model loader ----------
@st.cache_resource
def load_crop_model(crop_name: str):
    checkpoint_path = f"checkpoints/{crop_name}/best_model.pt"
    config_path = f"configs/{crop_name}.yaml"
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"No trained model found at {checkpoint_path}")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
        model_type = cfg.get("model_type", "tinyvit")
        num_classes = cfg["num_classes"]
        in_chans = cfg.get("in_channels", 1)
    else:
        num_classes = len(CROP_CLASSES[crop_name])
        model_type = "vit_pretrained"
        in_chans = 3
    if model_type == "vit_pretrained":
        model = PretrainedViTClassifier(num_classes=num_classes)
    else:
        model = GAIAModel(num_classes=num_classes, in_chans=in_chans)
    state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
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

# Scan deduction
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
        supabase.table("user_scans").insert({"user_id": user_id, "scans_remaining": 30, "plan": "free"}).execute()
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

# ---------- CSS based on theme ----------
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(145deg, #0a0a0a 0%, #1a2a1a 50%, #0d0d0d 100%); color: #e0e0e0; }
        header, footer {visibility: hidden;}
        .particles { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; overflow: hidden; }
        .particle { position: absolute; background: rgba(76,175,80,0.1); border-radius: 50%; animation: float 12s infinite ease-in-out; }
        .particle:nth-child(1) { width: 200px; height: 200px; top: 10%; left: 5%; }
        .particle:nth-child(2) { width: 150px; height: 150px; top: 70%; left: 80%; animation-delay: 3s; }
        .particle:nth-child(3) { width: 300px; height: 300px; top: 50%; left: 40%; animation-delay: 6s; }
        @keyframes float {
            0% { transform: translateY(0px) scale(1); opacity: 0.3; }
            50% { transform: translateY(-40px) scale(1.1); opacity: 0.6; }
            100% { transform: translateY(0px) scale(1); opacity: 0.3; }
        }
        .scanlines { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,100,0.02) 2px, rgba(0,255,100,0.02) 4px); z-index: 0; pointer-events: none; }
        .title { font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #00ff88, #00cc66, #00ff88); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 30px rgba(0,255,100,0.5); animation: titleGlow 2s ease-in-out infinite alternate; position: relative; z-index: 1; }
        @keyframes titleGlow { from { text-shadow: 0 0 30px rgba(0,255,100,0.5); } to { text-shadow: 0 0 60px rgba(0,255,100,0.9), 0 0 100px rgba(0,255,100,0.5); } }
        .subtitle { text-align: center; font-size: 1.1rem; color: #66ff99; margin-bottom: 2rem; position: relative; z-index: 1; }
        .stFileUploader > div { background: rgba(0,255,100,0.03) !important; backdrop-filter: blur(15px) !important; border: 2px dashed rgba(0,255,100,0.3) !important; border-radius: 20px !important; padding: 2rem !important; position: relative; z-index: 1; }
        .stFileUploader > div:hover { border-color: #00ff88 !important; box-shadow: 0 0 30px rgba(0,255,100,0.2); }
        .stImage img { border-radius: 20px; box-shadow: 0 0 40px rgba(0,255,100,0.3); border: 1px solid rgba(0,255,100,0.2); }
        .result-card { background: rgba(0,0,0,0.6); backdrop-filter: blur(25px); border: 1px solid rgba(0,255,100,0.2); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; position: relative; overflow: hidden; }
        .result-card::before { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: conic-gradient(transparent, rgba(0,255,100,0.1), transparent, transparent); animation: rotate 6s linear infinite; }
        @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .result-card > * { position: relative; z-index: 1; }
        .top-result { background: rgba(0,0,0,0.8); border: 2px solid #00ff88; box-shadow: 0 0 50px rgba(0,255,100,0.4), inset 0 0 30px rgba(0,255,100,0.05); }
        .top-result h3 { font-size: 1.2rem; text-transform: uppercase; letter-spacing: 2px; color: #00ff88; margin: 0.3rem 0; }
        .counter { font-size: 2rem; font-weight: 900; color: #00ff88; text-shadow: 0 0 30px rgba(0,255,100,0.8); animation: pulse 2s ease-in-out infinite; }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
        .progress-container { margin: 0.6rem 0; }
        .progress-label { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem; }
        .progress-label span { font-weight: 600; color: #ddd; }
        .progress-label .percent { color: #00ff88; font-size: 1rem; font-weight: 700; }
        .progress-bar { height: 6px; background: rgba(255,255,255,0.05); border-radius: 8px; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 8px; background: linear-gradient(90deg, #00ff88, #00cc66, #00ff88); background-size: 200% 100%; animation: shimmer 2s ease infinite, grow 1.5s ease-out; box-shadow: 0 0 10px rgba(0,255,100,0.6); transition: width 1s ease; }
        @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
        @keyframes grow { from { width: 0% !important; } }
        .progress-fill.warning { background: linear-gradient(90deg, #ffaa00, #ff8800, #ffaa00); box-shadow: 0 0 10px rgba(255,170,0,0.6); }
        .progress-fill.danger { background: linear-gradient(90deg, #ff4444, #ff0000, #ff4444); box-shadow: 0 0 10px rgba(255,0,0,0.6); }
        .action-box { background: rgba(0,255,100,0.05); border: 1px solid rgba(0,255,100,0.3); border-radius: 15px; padding: 1rem; text-align: center; margin-top: 1rem; backdrop-filter: blur(10px); }
    </style>
    <div class="scanlines"></div>
    <div class="particles"><div class="particle"></div><div class="particle"></div><div class="particle"></div></div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); color: #1b5e20; }
        .title { font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #2e7d32, #66bb6a, #2e7d32); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 15px rgba(46,125,50,0.3); animation: titleGlow 2s ease-in-out infinite alternate; }
        @keyframes titleGlow { from { text-shadow: 0 0 15px rgba(46,125,50,0.3); } to { text-shadow: 0 0 30px rgba(46,125,50,0.8), 0 0 60px rgba(46,125,50,0.5); } }
        .subtitle { text-align: center; font-size: 1.1rem; color: #2e7d32; margin-bottom: 2rem; }
        .stFileUploader > div { background: rgba(255,255,255,0.8) !important; backdrop-filter: blur(10px) !important; border: 2px dashed rgba(46,125,50,0.3) !important; border-radius: 20px !important; padding: 2rem !important; }
        .stImage img { border-radius: 20px; box-shadow: 0 0 20px rgba(0,0,0,0.2); }
        .result-card { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.1); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; }
        .top-result { border: 2px solid #2e7d32; box-shadow: 0 0 20px rgba(46,125,50,0.2); background: rgba(232,245,233,0.9); }
        .top-result h3 { font-size: 1.2rem; color: #1b5e20; }
        .counter { font-size: 2rem; font-weight: 900; color: #2e7d32; }
        .progress-container { margin: 0.6rem 0; }
        .progress-label { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem; }
        .progress-label span { font-weight: 600; color: #1b5e20; }
        .progress-label .percent { color: #2e7d32; font-size: 1rem; font-weight: 700; }
        .progress-bar { height: 6px; background: rgba(0,0,0,0.05); border-radius: 8px; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 8px; background: linear-gradient(90deg, #4caf50, #81c784); animation: grow 1.5s ease-out; }
        @keyframes grow { from { width: 0% !important; } }
        .action-box { background: rgba(46,125,50,0.05); border: 1px solid rgba(46,125,50,0.2); border-radius: 15px; padding: 1rem; text-align: center; margin-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# ---------- UI ----------
st.markdown('<div class="title">🌿 CROP DISEASE DIAGNOSIS</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a leaf photo. AI detects disease instantly.</div>', unsafe_allow_html=True)

crop = st.selectbox("🌾 Choose your crop", list(CROP_CLASSES.keys()))
uploaded_file = st.file_uploader("📤 DROP YOUR LEAF PHOTO HERE", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="", width=300)

    st.markdown("---")

    try:
        model = load_crop_model(crop)
        probs = predict_image(model, image)
    except FileNotFoundError as e:
        st.error(f"🚫 {e}")
        st.stop()
    except Exception as e:
        st.error(f"Scan failed: {e}")
        st.stop()

    class_names = CROP_CLASSES[crop]
    top_idx = np.argmax(probs)
    top_prob = probs[top_idx] * 100

    # Top result
    st.markdown(f"""
    <div class="result-card top-result">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <p style="color: {'#66ff99' if theme=='dark' else '#2e7d32'}; margin: 0; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px;">Diagnosis</p>
                <h3 style="margin: 0.3rem 0;">{class_names[top_idx]}</h3>
            </div>
            <div class="counter">{top_prob:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 DIAGNOSTIC PANEL")
    sorted_idx = np.argsort(probs)[::-1]

    for i, idx in enumerate(sorted_idx):
        disease = class_names[idx]
        percent = probs[idx] * 100
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

    deduct_and_show()

    top_disease = class_names[top_idx]
    if "healthy" in top_disease.lower():
        st.success("✅ Your crop looks healthy!")
    else:
        st.warning(f"⚠️ **{top_disease}** detected. Consider appropriate treatment.")
