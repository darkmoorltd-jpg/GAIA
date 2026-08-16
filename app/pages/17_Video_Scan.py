
import streamlit as st
import os, sys, hashlib, time, tempfile
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from collections import Counter

# Try to import OpenCV for video frame extraction
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
# THEME TOGGLE (hidden label, elegant switch)
# ============================================
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
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

# Model keys for crops (matching download_models.py)
CROP_MODEL_KEYS = {
    "millet": "millet_3class",
    "maize": "maize",
    "rice": "rice_10class",
}

# ============================================
# THEME CSS
# ============================================
if theme == "dark":
    st.markdown("""
    <style>
        @keyframes videoGlow {
            0% { text-shadow: 0 0 25px rgba(0,200,83,0.7); }
            100% { text-shadow: 0 0 50px rgba(0,200,83,1), 0 0 80px rgba(0,200,83,0.6); }
        }
        .stApp {
            background: linear-gradient(135deg, #0a0e1a 0%, #1a1a2e 40%, #16213e 100%);
            color: #e2e8f0;
        }
        header, footer { visibility: hidden; }
        .video-title {
            font-size: 3.5rem; font-weight: 900; text-align: center;
            background: linear-gradient(135deg, #00c853, #69f0ae, #00c853);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            animation: videoGlow 2s ease-in-out infinite alternate;
            margin-bottom: 0.3rem;
        }
        .subtitle { text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem; }
        .scan-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 24px;
            padding: 2rem;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.2);
            margin-bottom: 2rem;
        }
        .stat-box {
            background: rgba(0,200,83,0.08);
            border: 1px solid rgba(0,200,83,0.2);
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
        }
        .stButton button:hover { transform: translateY(-3px); box-shadow: 0 10px 25px rgba(0,200,83,0.3); }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @keyframes videoGlowLight {
            0% { text-shadow: 0 0 15px rgba(46,125,50,0.5); }
            100% { text-shadow: 0 0 30px rgba(46,125,50,1), 0 0 60px rgba(46,125,50,0.7); }
        }
        .stApp {
            background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 50%, #fffde7 100%);
            color: #1b5e20;
        }
        header, footer { visibility: hidden; }
        .video-title {
            font-size: 3.5rem; font-weight: 900; text-align: center;
            background: linear-gradient(135deg, #2e7d32, #66bb6a, #2e7d32);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            animation: videoGlowLight 2s ease-in-out infinite alternate;
            margin-bottom: 0.3rem;
        }
        .subtitle { text-align: center; color: #558b2f; font-size: 1.1rem; margin-bottom: 2rem; }
        .scan-card {
            background: rgba(255,255,255,0.9);
            border: 1px solid rgba(0,0,0,0.05);
            border-radius: 24px;
            padding: 2rem;
            box-shadow: 0 8px 30px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
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
# HELPER FUNCTIONS
# ============================================
def load_model_for_scan(scan_type, crop_name=None):
    """Load the appropriate model for crop or soil."""
    from app.utils.download_models import ensure_model
    from app.utils.model_loader import create_model_from_checkpoint

    if scan_type == "Crop Disease":
        key = CROP_MODEL_KEYS.get(crop_name, crop_name)
        checkpoint = ensure_model(key)
        num_classes = len(CROP_CLASSES[crop_name])
    else:  # Soil Analysis
        checkpoint = ensure_model("soil_11class")
        num_classes = len(SOIL_NAMES)

    if checkpoint is None or not os.path.exists(checkpoint):
        return None, None

    model = create_model_from_checkpoint(checkpoint, num_classes)
    model.eval()
    return model, num_classes


def extract_frames_from_video(video_file, interval_sec=0.5):
    """Extract frames from uploaded video."""
    if not HAS_CV2:
        return None

    # Save video to temp file
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
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)
        count += 1
    cap.release()
    os.unlink(tfile.name)
    return frames


def predict_on_frames(model, frames, img_size=224):
    """Run model on each frame and aggregate predictions."""
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


def deduct_scans_for_video(amount=2):
    """Deduct scans for video analysis."""
    if "user" not in st.session_state or st.session_state.user is None:
        return
    from app.utils.scan_util import deduct_scans
    deduct_scans(st.session_state.user.id, amount, "Video Scan")


# ============================================
# HEADER
# ============================================
st.markdown('<div class="video-title">🎥 Video Field Scanner</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Walk through your field and let GAIA analyze every leaf</div>', unsafe_allow_html=True)

# ============================================
# SCAN TYPE SELECTOR (Crop / Soil)
# ============================================
scan_type = st.radio("Select Scan Type", ["🌾 Crop Disease", "🏞️ Soil Analysis"], horizontal=True)

# ============================================
# CROP SELECTION (if crop)
# ============================================
if scan_type == "🌾 Crop Disease":
    crop_name = st.selectbox("Select Crop", list(CROP_CLASSES.keys()))
else:
    crop_name = None

# ============================================
# VIDEO UPLOAD
# ============================================
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

    # ============================================
    # ANALYSIS BUTTON
    # ============================================
    if st.button("🔍 Analyze Video", type="primary", use_container_width=True):
        with st.spinner("🧠 GAIA is scanning your field video..."):
            # Extract frames
            frames = extract_frames_from_video(uploaded_video)

            if frames is None or len(frames) < 3:
                st.error("Could not extract enough frames from video. Please try a different file.")
                st.stop()

            # Load model
            model, num_classes = load_model_for_scan(scan_type, crop_name)
            if model is None:
                st.warning("⚠️ Real model unavailable — using demo predictions.")
                # Demo predictions
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
                class_names = CROP_CLASSES[crop_name] if scan_type == "🌾 Crop Disease" else SOIL_NAMES
                avg_probs, agreement = predict_on_frames(model, frames)

            top_idx = np.argmax(avg_probs)
            top_name = class_names[top_idx]
            confidence = avg_probs[top_idx] * 100
            num_frames = len(frames)

        # ============================================
        # RESULTS DISPLAY
        # ============================================
        st.markdown("---")
        st.subheader("📊 Video Scan Report")

        # Stats row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="stat-box"><div class="stat-number">{num_frames}</div><div class="stat-label">Frames Analyzed</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="stat-box"><div class="stat-number">{confidence:.1f}%</div><div class="stat-label">Confidence</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="stat-box"><div class="stat-number">{agreement*100:.0f}%</div><div class="stat-label">Frame Agreement</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="stat-box"><div class="stat-number">{scan_type.split()[0]}</div><div class="stat-label">Scan Type</div></div>', unsafe_allow_html=True)

        # Main result card
        st.markdown(f"""
        <div class="scan-card" style="border-left: 5px solid #00c853;">
            <h2 style="margin:0; color: {'#00c853' if theme == 'dark' else '#2e7d32'};">🏆 {top_name}</h2>
            <p style="font-size:1.5rem; margin-top:0.5rem;">Confidence: {confidence:.1f}%</p>
            <p style="color: #94a3b8;">{agreement*100:.0f}% of frames agree on this diagnosis</p>
        </div>
        """, unsafe_allow_html=True)

        # Top 5 probabilities
        st.markdown("### Top 5 Probabilities")
        sorted_idx = np.argsort(avg_probs)[::-1][:5]
        for i in sorted_idx:
            st.write(f"**{class_names[i]}**: {avg_probs[i]*100:.1f}%")
            st.progress(float(avg_probs[i]))

        # Deduct scans
        deduct_scans_for_video()

        # DeepSeek explanation (if available)
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

# ============================================
# NAVIGATION
# ============================================
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

st.markdown("### 📱 More Features")
cols2 = st.columns(10)
with cols2[0]: st.page_link("pages/11_Verify_Farmer.py", label="🛡️ Verify")
with cols2[1]: st.page_link("pages/12_Verification_History.py", label="📋 History")
with cols2[2]: st.page_link("pages/14_Wallet.py", label="💰 Wallet")
with cols2[3]: st.page_link("pages/15_Badges.py", label="🏅 Badges")
with cols2[4]: st.page_link("pages/16_Chat.py", label="💬 Chat")
with cols2[5]: st.page_link("pages/20_Marketplace.py", label="🌍 Market")
with cols2[6]: st.page_link("pages/21_Crop_Insurance.py", label="🏦 Insurance")
with cols2[7]: st.page_link("pages/6_Payment_History.py", label="💳 Payments")
with cols2[8]: st.page_link("pages/8_Profile.py", label="👤 Profile")
with cols2[9]: st.page_link("pages/13_Help.py", label="🆘 Help")
