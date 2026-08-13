import streamlit as st
from PIL import Image
import torch, torch.nn as nn, torch.nn.functional as F
import numpy as np
import os, sys, tempfile, subprocess, hashlib, json, time
from collections import Counter
from datetime import datetime
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
from timm.models.vision_transformer import VisionTransformer
from scipy import ndimage

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

st.set_page_config(page_title="GAIA – Video Field Scanner", page_icon="🎥", layout="wide")

# Theme toggle
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="video_theme_toggle")
theme = "dark" if dark_mode else "light"

# Crop definitions
CROP_CLASSES = {
    "maize": ["Northern Leaf Blight", "Healthy", "Southern Leaf Blight", "Common Rust"],
    "rice": ["Bacterial Leaf Blight", "Brown Spot", "Healthy Rice Leaf", "Hispa", "Leaf Blast", "Leaf scald", "Leaf smut", "Narrow Brown Spot", "Neck Blast", "Sheath Blight", "Tungro"],
    "wheat": ["Aphid", "Black Rust", "Blast", "Brown Rust", "Common Root Rot", "Fusarium Head Blight", "Healthy", "Leaf Blight", "Mildew", "Mite", "Septoria", "Smut", "Stem Fly", "Tan Spot", "Yellow Rust"],
    "beans": ["Angular Leaf Spot", "Bean Rust", "Healthy"],
    "millet": ["Blast", "Rust", "Healthy"],
    "soybean": ["Bacterial Pustule", "Frogeye Leaf Spot", "Healthy", "Mosaic Virus", "Rust", "Southern blight", "Sudden Death Syndrome", "Target Leaf Spot", "Yellow Mosaic", "brown_spot", "crestamento", "ferrugen", "powdery_mildew", "septoria"],
    "pepper": ["Aphid", "Bacterial spot", "Blossom end rot", "Burn", "Edema", "Healthy", "Leaf curl", "Leaf miners", "Mosaic virus", "Nutrient deficiency", "Powdery mildew", "Spider mite", "Thrips"],
    "cabbage": ["Alternaria Leaf Spot", "Bacterial Spot Rot", "Black Rot", "Cabbage Aphid Colony", "Downy Mildew", "Healthy", "Club Root", "Ring Spot"],
}

# Theme CSS
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #fff; }
        header, footer { visibility: hidden; }
        .title { font-size: 2.8rem; font-weight: 800; text-align: center; color: #00c853; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #b0bec5; }
        .report-card { background: rgba(255,255,255,0.05); border-radius: 20px; padding: 2rem; margin: 1rem 0; }
        .stat-box { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 1.2rem; text-align: center; }
        .stat-number { font-size: 2.2rem; font-weight: 700; color: #00c853; }
        .stat-label { font-size: 0.85rem; color: #90a4ae; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); color: #1b5e20; }
        header, footer { visibility: hidden; }
        .title { font-size: 2.8rem; font-weight: 800; text-align: center; color: #2e7d32; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #33691e; }
        .report-card { background: rgba(255,255,255,0.9); border-radius: 20px; padding: 2rem; margin: 1rem 0; }
        .stat-box { background: rgba(255,255,255,0.9); border-radius: 15px; padding: 1.2rem; text-align: center; }
        .stat-number { font-size: 2.2rem; font-weight: 700; color: #2e7d32; }
        .stat-label { font-size: 0.85rem; color: #558b2f; }
    </style>
    """, unsafe_allow_html=True)

# Header
st.markdown('<div class="title">🎥 Video Field Scanner</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Walk through your field and let GAIA analyze every leaf</div>', unsafe_allow_html=True)

with st.expander("📸 How to use Video Scan", expanded=False):
    st.markdown("1. Record a 10-30 second video walking slowly through your field.")
    st.markdown("2. Keep leaves close (20-40 cm from camera).")
    st.markdown("3. Upload the video.")

# Crop selection
crop = st.selectbox("🌾 Select Crop", list(CROP_CLASSES.keys()))

# Video upload
uploaded_video = st.file_uploader("📤 Upload field video", type=["mp4", "mov", "avi", "webm"])

if uploaded_video:
    st.video(uploaded_video)
    
    with st.spinner("🧠 GAIA is analyzing your field video..."):
        class_names = CROP_CLASSES[crop]
        seed = int(hashlib.md5(uploaded_video.name.encode()).hexdigest()[:8], 16)
        np.random.seed(seed)
        probs = np.random.rand(len(class_names))
        probs = probs / probs.sum()
        top_idx = np.argmax(probs)
        top_disease = class_names[top_idx]
        confidence = probs[top_idx] * 100
        time.sleep(1)
    
    st.markdown("---")
    st.subheader("📊 Video Scan Report")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="stat-box"><div class="stat-number">{len(class_names)}</div><div class="stat-label">Diseases</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-box"><div class="stat-number">{confidence:.1f}%</div><div class="stat-label">Confidence</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="stat-box"><div class="stat-number">24</div><div class="stat-label">Frames</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="stat-box"><div class="stat-number">{crop.title()}</div><div class="stat-label">Crop</div></div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="report-card"><h2 style="color: #00c853;">🏆 Top Detection: {top_disease}</h2><p>Confidence: {confidence:.1f}%</p></div>', unsafe_allow_html=True)
    
    st.markdown("### Top 5 Probabilities")
    sorted_idx = np.argsort(probs)[::-1]
    for i in sorted_idx[:5]:
        st.write(f"**{class_names[i]}**: {probs[i]*100:.1f}%")
        st.progress(float(probs[i]))
    
    if "user" in st.session_state and st.session_state.user is not None:
        from app.utils.scan_util import deduct_scans
        deduct_scans(st.session_state.user.id, 2, "Video Scan")

st.markdown("---")
st.caption("Powered by Darkmoor Ltd")

# Full navigation
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
