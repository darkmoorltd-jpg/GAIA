
import streamlit as st
import os, sys, hashlib, time, tempfile
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from collections import Counter

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from timm.models.vision_transformer import VisionTransformer

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(page_title="GAIA – Video Field Scanner", page_icon="🎥", layout="wide")

# ============================================
# THEME TOGGLE
# ============================================
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.4); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="video_theme_toggle")
theme = "dark" if dark_mode else "light"

# ============================================
# CROP & SOIL CLASS DEFINITIONS
# ============================================
CROP_CLASSES = {
    "millet": ["Blast", "Rust", "Healthy"],
    "maize": ["Blight", "Common_Rust", "Gray_Leaf_Spot", "Healthy"],
    "rice": ["Bacterial Leaf Blight","Brown Spot","Healthy Rice Leaf","Leaf Blast","Leaf Scald","Narrow Brown Spot","Neck Blast","Rice Hispa","Sheath Blight","Tungro"],
    "soybean": ["Bacterial Pustule","Frogeye Leaf Spot","Healthy","Mosaic Virus","Rust","Southern blight","Sudden Death Syndrome","Target Leaf Spot","Yellow Mosaic","brown_spot","crestamento","ferrugen","powdery_mildew","septoria"],
    "pepper": ["Aphid","Bacterial spot","Blossom end rot","Burn","Edema","Healthy","Leaf curl","Leaf miners","Mosaic virus","Nutrient deficiency","Powdery mildew","Spider mite","Thrips"],
    "cabbage": ["Alternaria Leaf Spot","Bacterial Spot Rot","Black Rot","Cabbage Aphid Colony","Downy Mildew","Healthy","Club Root","Ring Spot"],
}

SOIL_NAMES = ["Alluvial","Sandy","Clay","Loamy","Laterite","Black","Red","Peat","Cinder","Sandy Loam","Yellow"]

DOWNLOAD_KEYS = {
    "millet": "millet_3class",
    "maize": "maize",
    "rice": "rice_10class",
    "soybean": "soybean_14class",
    "pepper": "pepper_13class",
    "cabbage": "cabbage_8class",
}

# ============================================
# BADASS UI CSS (inspired by farming calendar)
# ============================================
if theme == "dark":
    st.markdown("""
    <style>
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes orbFloat {
            0% { transform: translate(0, 0) scale(1); opacity: 0.6; }
            25% { transform: translate(40px, -30px) scale(1.2); opacity: 0.9; }
            50% { transform: translate(-30px, 30px) scale(0.9); opacity: 0.7; }
            75% { transform: translate(20px, 50px) scale(1.1); opacity: 0.85; }
            100% { transform: translate(0, 0) scale(1); opacity: 0.6; }
        }
        @keyframes videoGlow {
            0%, 100% { text-shadow: 0 0 25px rgba(0,200,83,0.7); }
            50% { text-shadow: 0 0 50px rgba(0,200,83,1), 0 0 80px rgba(0,200,83,0.6); }
        }
        .stApp {
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1500937386664-56d1dfef3854?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80'); background-size: cover; background-attachment: fixed;
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
            color: #e2e8f0;
        }
        header, footer { visibility: hidden; }
        .video-title {
            font-size: 3.5rem; font-weight: 900; text-align: center;
            background: linear-gradient(135deg, #00c853, #69f0ae, #00c853);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            animation: videoGlow 2s ease-in-out infinite alternate;
            margin-bottom: 0.3rem;
            position: relative; z-index: 10;
        }
        .subtitle {
            text-align: center; color: #94a3b8; font-size: 1.1rem;
            margin-bottom: 2rem; position: relative; z-index: 10;
        }
        .orb {
            position: fixed; border-radius: 50%;
            filter: blur(80px); z-index: 0; pointer-events: none;
            opacity: 0.7;
        }
        .orb-1 { width: 300px; height: 300px; top: 5%; left: 5%; background: #00c853; animation: orbFloat 10s infinite; }
        .orb-2 { width: 200px; height: 200px; bottom: 10%; right: 5%; background: #7c4dff; animation: orbFloat 12s infinite reverse; }
        .orb-3 { width: 250px; height: 250px; top: 50%; left: 60%; background: #ff9800; animation: orbFloat 14s infinite; }
        .orb-4 { width: 150px; height: 150px; bottom: 20%; left: 20%; background: #00bcd4; animation: orbFloat 11s infinite; }
        .grid-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-image: linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
            background-size: 40px 40px; z-index: 1; pointer-events: none;
        }
        .content-wrapper { position: relative; z-index: 5; }
        .scan-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 24px;
            padding: 2rem;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 40px rgba(0,0,0,0.3);
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }
        .scan-card::before {
            content: '';
            position: absolute; top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, #00c853, transparent);
        }
        .stat-box {
            background: rgba(0,200,83,0.1);
            border: 1px solid rgba(0,200,83,0.25);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
        }
        .stat-number { font-size: 2.2rem; font-weight: 800; color: #00c853; }
        .stat-label { font-size: 0.85rem; color: #94a3b8; }
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #00c853, #69f0ae);
            border-radius: 10px;
        }
        .stButton button {
            background: linear-gradient(135deg, #00c853, #4caf50) !important;
            color: #fff !important; border: none !important;
            border-radius: 12px !important; padding: 12px 40px !important;
            font-weight: 700 !important; font-size: 1.1rem !important;
            transition: all 0.3s !important;
            position: relative; z-index: 5;
        }
        .stButton button:hover { transform: translateY(-3px); box-shadow: 0 10px 25px rgba(0,200,83,0.4); }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @keyframes gradientShiftLight {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes orbFloatLight {
            0% { transform: translate(0, 0) scale(1); opacity: 0.4; }
            50% { transform: translate(30px, -20px) scale(1.2); opacity: 0.7; }
            100% { transform: translate(0, 0) scale(1); opacity: 0.4; }
        }
        @keyframes videoGlowLight {
            0%, 100% { text-shadow: 0 0 15px rgba(46,125,50,0.5); }
            50% { text-shadow: 0 0 30px rgba(46,125,50,1), 0 0 60px rgba(46,125,50,0.7); }
        }
        .stApp {
            background: linear-gradient(rgba(255,255,255,0.75), rgba(255,255,255,0.75)), url('https://images.unsplash.com/photo-1500937386664-56d1dfef3854?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80'); background-size: cover; background-attachment: fixed;
            background-size: 400% 400%;
            animation: gradientShiftLight 15s ease infinite;
            color: #1b5e20;
        }
        header, footer { visibility: hidden; }
        .video-title {
            font-size: 3.5rem; font-weight: 900; text-align: center;
            background: linear-gradient(135deg, #2e7d32, #66bb6a, #2e7d32);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            animation: videoGlowLight 2s ease-in-out infinite alternate;
            margin-bottom: 0.3rem;
            position: relative; z-index: 10;
        }
        .subtitle {
            text-align: center; color: #558b2f; font-size: 1.1rem;
            margin-bottom: 2rem; position: relative; z-index: 10;
        }
        .orb {
            position: fixed; border-radius: 50%;
            filter: blur(80px); z-index: 0; pointer-events: none;
            opacity: 0.5;
        }
        .orb-1 { width: 280px; height: 280px; top: 5%; left: 5%; background: #a5d6a7; animation: orbFloatLight 8s infinite; }
        .orb-2 { width: 180px; height: 180px; bottom: 10%; right: 5%; background: #b39ddb; animation: orbFloatLight 10s infinite reverse; }
        .orb-3 { width: 220px; height: 220px; top: 50%; left: 60%; background: #ffe0b2; animation: orbFloatLight 12s infinite; }
        .orb-4 { width: 130px; height: 130px; bottom: 20%; left: 20%; background: #b2dfdb; animation: orbFloatLight 9s infinite; }
        .grid-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-image: linear-gradient(rgba(0,0,0,0.02) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(0,0,0,0.02) 1px, transparent 1px);
            background-size: 40px 40px; z-index: 1; pointer-events: none;
        }
        .content-wrapper { position: relative; z-index: 5; }
        .scan-card {
            background: rgba(255,255,255,0.85);
            border: 1px solid rgba(0,0,0,0.05);
            border-radius: 24px;
            padding: 2rem;
            box-shadow: 0 8px 30px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }
        .scan-card::before {
            content: '';
            position: absolute; top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, #2e7d32, transparent);
        }
        .stat-box {
            background: rgba(46,125,50,0.08);
            border: 1px solid rgba(46,125,50,0.2);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
        }
        .stat-number { font-size: 2.2rem; font-weight: 800; color: #2e7d32; }
        .stat-label { font-size: 0.85rem; color: #558b2f; }
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #2e7d32, #66bb6a);
            border-radius: 10px;
        }
        .stButton button {
            background: linear-gradient(135deg, #2e7d32, #4caf50) !important;
            color: #fff !important; border: none !important;
            border-radius: 12px !important; padding: 12px 40px !important;
            font-weight: 700 !important; font-size: 1.1rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# BACKGROUND ELEMENTS
# ============================================
st.markdown("""
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>
<div class="orb orb-4"></div>
<div class="grid-overlay"></div>
""", unsafe_allow_html=True)

st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

# ============================================
# MODEL LOADING (same as crop page)
# ============================================
def load_crop_model_from_checkpoint(crop_name):
    from app.utils.download_models import ensure_model
    key = DOWNLOAD_KEYS.get(crop_name, crop_name)
    checkpoint = ensure_model(key)
    if checkpoint is None or not os.path.exists(checkpoint):
        return None, None, None
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    prefix = "backbone." if any(k.startswith("backbone.") for k in state) else "encoder."
    embed_dim = state[f"{prefix}cls_token"].shape[-1]
    pos_embed = state[f"{prefix}pos_embed"]
    num_patches = pos_embed.shape[1] - 1
    grid = int(num_patches ** 0.5)
    img_size = grid * 16
    depth = len([k for k in state if k.startswith(f"{prefix}blocks") and k.endswith(".norm1.weight")])
    num_heads = 6 if embed_dim == 384 else 3
    backbone = VisionTransformer(img_size=img_size, patch_size=16, embed_dim=embed_dim, depth=depth, num_heads=num_heads, num_classes=0, global_pool='token')
    backbone_state = {k.replace(prefix, ""): v for k, v in state.items() if k.startswith(prefix)}
    backbone.load_state_dict(backbone_state, strict=False)
    head_keys = [k for k in state if k.startswith("head.")]
    if any(".0.weight" in k for k in head_keys):
        w_keys = sorted([k for k in head_keys if k.endswith(".weight")], key=lambda x: int(x.split('.')[1]))
        layers = []
        in_feat = embed_dim
        for w_key in w_keys:
            w = state[w_key]
            out_feat = w.shape[0]
            layers.append(nn.Linear(in_feat, out_feat))
            if w_key != w_keys[-1]:
                layers.extend([nn.GELU(), nn.Dropout(0.2)])
            in_feat = out_feat
        head = nn.Sequential(*layers)
        head_state = {k.replace("head.", ""): v for k, v in state.items() if k.startswith("head.")}
        head.load_state_dict(head_state, strict=False)
    else:
        n = len(CROP_CLASSES[crop_name])
        head = nn.Linear(embed_dim, n)
        head.load_state_dict({"weight": state["head.weight"], "bias": state.get("head.bias", torch.zeros(n))}, strict=False)
    class CropViT(torch.nn.Module):
        def __init__(self, backbone, head):
            super().__init__(); self.backbone = backbone; self.head = head
        def forward(self, x): return self.head(self.backbone(x))
    model = CropViT(backbone, head)
    model.eval()
    return model, img_size, len(CROP_CLASSES[crop_name])

def load_soil_model_from_checkpoint():
    from app.utils.download_models import ensure_model
    checkpoint = ensure_model("soil_11class")
    if checkpoint is None or not os.path.exists(checkpoint):
        return None, None, None
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    prefix = "backbone." if any(k.startswith("backbone.") for k in state) else "encoder."
    embed_dim = state[f"{prefix}cls_token"].shape[-1]
    pos = state[f"{prefix}pos_embed"]
    num_patches = pos.shape[1] - 1
    grid = int(num_patches ** 0.5)
    img_size = grid * 16
    backbone = VisionTransformer(img_size=img_size, patch_size=16, embed_dim=embed_dim, depth=12, num_heads=6, num_classes=0, global_pool='token')
    backbone_state = {k.replace(prefix, ""): v for k, v in state.items() if k.startswith(prefix)}
    backbone.load_state_dict(backbone_state, strict=False)
    n = len(SOIL_NAMES)
    head = nn.Linear(embed_dim, n)
    head_state = {"weight": state.get("head.weight"), "bias": state.get("head.bias", torch.zeros(n))}
    if head_state["weight"] is not None:
        head.load_state_dict({k: v for k, v in head_state.items() if v is not None}, strict=False)
    class SoilViT(torch.nn.Module):
        def __init__(self, backbone, head):
            super().__init__(); self.backbone = backbone; self.head = head
        def forward(self, x): return self.head(self.backbone(x))
    model = SoilViT(backbone, head)
    model.eval()
    return model, img_size, len(SOIL_NAMES)

def predict_on_frames(model, frames, img_size):
    transform = Compose([Resize((img_size, img_size)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
    all_probs = []
    for frame in frames:
        pil_img = Image.fromarray(frame)
        tensor = transform(pil_img).unsqueeze(0)
        with torch.no_grad():
            probs = F.softmax(model(tensor), dim=1)[0].cpu().numpy()
        all_probs.append(probs)
    if not all_probs:
        return None, 0
    avg_probs = np.mean(all_probs, axis=0)
    consensus_idx = np.argmax(avg_probs)
    agreement = sum(1 for p in all_probs if np.argmax(p) == consensus_idx) / len(all_probs)
    return avg_probs, agreement

def extract_frames_from_video(video_file, interval_sec=0.5):
    if not HAS_CV2:
        return None
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(video_file.read())
    tfile.close()
    cap = cv2.VideoCapture(tfile.name)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_interval = max(1, int(fps * interval_sec))
    frames = []
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        if count % frame_interval == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)
        count += 1
    cap.release()
    os.unlink(tfile.name)
    return frames

def deduct_scans_for_video(amount=2):
    if "user" in st.session_state and st.session_state.user:
        from app.utils.scan_util import deduct_scans
        deduct_scans(st.session_state.user.id, amount, "Video Scan")

# ============================================
# HEADER
# ============================================
st.markdown('<div class="video-title">🎥 Video Field Scanner</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Walk through your field and let GAIA analyze every leaf</div>', unsafe_allow_html=True)

scan_type = st.radio("Select Scan Type", ["🌾 Crop Disease", "🏞️ Soil Analysis"], horizontal=True)
crop_name = None
if scan_type == "🌾 Crop Disease":
    crop_name = st.selectbox("Select Crop", list(CROP_CLASSES.keys()))

with st.expander("📸 How to record the best video", expanded=False):
    st.markdown("""
    1. Walk slowly through your field, holding the phone 20‑30 cm from leaves.
    2. Record for 10‑30 seconds, covering multiple affected plants.
    3. Keep the camera steady; avoid fast swings.
    4. Ensure good lighting (natural daylight preferred).
    """)

uploaded_video = st.file_uploader("📤 Upload field video", type=["mp4", "mov", "avi", "webm"])

if uploaded_video:
    st.video(uploaded_video)
    if st.button("🔍 Analyze Video", type="primary", use_container_width=True):
        with st.spinner("🧠 GAIA is scanning your field video..."):
            frames = extract_frames_from_video(uploaded_video)
            if frames is None or len(frames) < 3:
                st.error("Could not extract enough frames. Try a different video.")
                st.stop()

            if scan_type == "🌾 Crop Disease":
                model, img_size, num_classes = load_crop_model_from_checkpoint(crop_name)
                class_names = CROP_CLASSES[crop_name]
            else:
                model, img_size, num_classes = load_soil_model_from_checkpoint()
                class_names = SOIL_NAMES

            if model is None:
                st.warning("⚠️ Real model unavailable — using demo.")
                if scan_type == "🌾 Crop Disease":
                    class_names = CROP_CLASSES[crop_name]
                else:
                    class_names = SOIL_NAMES
                seed = int(hashlib.md5(uploaded_video.name.encode()).hexdigest()[:8],16)
                np.random.seed(seed)
                avg_probs = np.random.rand(len(class_names))
                avg_probs /= avg_probs.sum()
                agreement = 0.8
            else:
                avg_probs, agreement = predict_on_frames(model, frames, img_size)
                if len(avg_probs) != len(class_names):
                    class_names = class_names[:len(avg_probs)] + [f"Class_{i}" for i in range(len(class_names), len(avg_probs))]

            top_idx = np.argmax(avg_probs)
            top_name = class_names[top_idx]
            confidence = avg_probs[top_idx] * 100
            num_frames = len(frames)

        st.markdown("---")
        st.subheader("📊 Video Scan Report")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="stat-box"><div class="stat-number">{num_frames}</div><div class="stat-label">Frames Analyzed</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="stat-box"><div class="stat-number">{confidence:.1f}%</div><div class="stat-label">Confidence</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="stat-box"><div class="stat-number">{agreement*100:.0f}%</div><div class="stat-label">Frame Agreement</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="stat-box"><div class="stat-number">{scan_type.split()[0]}</div><div class="stat-label">Scan Type</div></div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="scan-card" style="border-left:5px solid #00c853;">
            <h2 style="margin:0;color:{'#00c853' if theme == 'dark' else '#2e7d32'};">🏆 {top_name}</h2>
            <p style="font-size:1.5rem;margin-top:0.5rem;">Confidence: {confidence:.1f}%</p>
            <p style="color:#94a3b8;">{agreement*100:.0f}% of frames agree</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Top 5 Probabilities")
        sorted_idx = np.argsort(avg_probs)[::-1][:5]
        for i in sorted_idx:
            st.write(f"**{class_names[i]}**: {avg_probs[i]*100:.1f}%")
            st.progress(float(avg_probs[i]))

        deduct_scans_for_video()

        if model is not None:
            with st.spinner("🧠 Generating treatment guide..."):
                try:
                    from app.utils.deepseek_explainer import explain_diagnosis
                    explanation, _ = explain_diagnosis(top_name, confidence,
                                                       crop_name if scan_type == "🌾 Crop Disease" else "soil",
                                                       "crop" if scan_type == "🌾 Crop Disease" else "soil")
                    if explanation:
                        with st.expander("📋 Complete Treatment Guide", expanded=True):
                            st.markdown(explanation)
                except:
                    pass

else:
    st.info("👆 Upload a video to begin analysis")

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(10)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[6]: st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[7]: st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[9]: st.page_link("pages/10_Early_Warning.py", label="⚠️ Alerts")
