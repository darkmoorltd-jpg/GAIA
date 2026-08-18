
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

# Mapping used in Crops page (same keys)
DOWNLOAD_KEYS = {
    "millet": "millet_3class",
    "maize": "maize",
    "rice": "rice_10class",
    "soybean": "soybean_14class",
    "pepper": "pepper_13class",
    "cabbage": "cabbage_8class",
}

# ============================================
# MODEL LOADING — COPIED FROM CROPS PAGE (PROVEN)
# ============================================
def load_crop_model_from_checkpoint(crop_name):
    """Load crop model exactly like the Crops page."""
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

    backbone = VisionTransformer(
        img_size=img_size, patch_size=16, embed_dim=embed_dim,
        depth=depth, num_heads=num_heads, num_classes=0, global_pool='token'
    )
    backbone_state = {k.replace(prefix, ""): v for k, v in state.items() if k.startswith(prefix)}
    backbone.load_state_dict(backbone_state, strict=False)

    # Build head
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
        head.load_state_dict({
            "weight": state["head.weight"],
            "bias": state.get("head.bias", torch.zeros(n))
        }, strict=False)

    class CropViT(torch.nn.Module):
        def __init__(self, backbone, head):
            super().__init__()
            self.backbone = backbone
            self.head = head
        def forward(self, x):
            return self.head(self.backbone(x))

    model = CropViT(backbone, head)
    model.eval()
    return model, img_size, len(CROP_CLASSES[crop_name])

def load_soil_model_from_checkpoint():
    """Load soil model like the Soil page."""
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

    backbone = VisionTransformer(
        img_size=img_size, patch_size=16, embed_dim=embed_dim,
        depth=12, num_heads=6, num_classes=0, global_pool='token'
    )
    backbone_state = {k.replace(prefix, ""): v for k, v in state.items() if k.startswith(prefix)}
    backbone.load_state_dict(backbone_state, strict=False)

    n = len(SOIL_NAMES)
    head = nn.Linear(embed_dim, n)
    head_state = {
        "weight": state.get("head.weight"),
        "bias": state.get("head.bias", torch.zeros(n))
    }
    if head_state["weight"] is not None:
        head.load_state_dict({k: v for k, v in head_state.items() if v is not None}, strict=False)

    class SoilViT(torch.nn.Module):
        def __init__(self, backbone, head):
            super().__init__()
            self.backbone = backbone
            self.head = head
        def forward(self, x):
            return self.head(self.backbone(x))

    model = SoilViT(backbone, head)
    model.eval()
    return model, img_size, len(SOIL_NAMES)

# ============================================
# PREDICTION HELPERS
# ============================================
def predict_on_frames(model, frames, img_size):
    transform = Compose([
        Resize((img_size, img_size)),
        ToTensor(),
        Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    all_probs = []
    for frame in frames:
        pil_img = Image.fromarray(frame)
        tensor = transform(pil_img).unsqueeze(0)
        with torch.no_grad():
            logits = model(tensor)
            probs = F.softmax(logits, dim=1)[0].cpu().numpy()
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
        if not ret:
            break
        if count % frame_interval == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)
        count += 1
    cap.release()
    os.unlink(tfile.name)
    return frames

def deduct_scans_for_video(amount=2):
    if "user" not in st.session_state or st.session_state.user is None:
        return
    from app.utils.scan_util import deduct_scans
    deduct_scans(st.session_state.user.id, amount, "Video Scan")

# ============================================
# HEADER
# ============================================
st.markdown('<div class="video-title">🎥 Video Field Scanner</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Walk through your field and let GAIA analyze every leaf</div>', unsafe_allow_html=True)

scan_type = st.radio("Select Scan Type", ["🌾 Crop Disease", "🏞️ Soil Analysis"], horizontal=True)

if scan_type == "🌾 Crop Disease":
    crop_name = st.selectbox("Select Crop", list(CROP_CLASSES.keys()))
else:
    crop_name = None

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

            # Load correct model
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
                seed = int(hashlib.md5(uploaded_video.name.encode()).hexdigest()[:8], 16)
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
        <div class="scan-card" style="border-left: 5px solid #00c853;">
            <h2 style="margin:0; color: {'#00c853' if theme == 'dark' else '#2e7d32'};">🏆 {top_name}</h2>
            <p style="font-size:1.5rem; margin-top:0.5rem;">Confidence: {confidence:.1f}%</p>
            <p style="color: #94a3b8;">{agreement*100:.0f}% of frames agree on this diagnosis</p>
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

# Navigation
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
