
import streamlit as st
from PIL import Image
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np, os, sys, hashlib, datetime
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from timm.models.vision_transformer import VisionTransformer
from collections import Counter
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌾", layout="wide")

CROP_CLASSES = {
    "millet": ["Blast", "Rust", "Healthy"],
    "maize": ["Blight", "Common_Rust", "Gray_Leaf_Spot", "Healthy"],
    "rice": ["Bacterial Leaf Blight","Brown Spot","Healthy Rice Leaf","Leaf Blast","Leaf Scald","Narrow Brown Spot","Neck Blast","Rice Hispa","Sheath Blight","Tungro"],
    "soybean": ["Bacterial Pustule","Frogeye Leaf Spot","Healthy","Mosaic Virus","Rust","Southern blight","Sudden Death Syndrome","Target Leaf Spot","Yellow Mosaic","brown_spot","crestamento","ferrugen","powdery_mildew","septoria"],
    "pepper": ["Aphid","Bacterial spot","Blossom end rot","Burn","Edema","Healthy","Leaf curl","Leaf miners","Mosaic virus","Nutrient deficiency","Powdery mildew","Spider mite","Thrips"],
    "cabbage": ["Alternaria Leaf Spot","Bacterial Spot Rot","Black Rot","Cabbage Aphid Colony","Downy Mildew","Healthy","Club Root","Ring Spot"],
}

CHECKPOINT_MAP = {
    "millet": os.path.join("models", "millet_3class", "model.pt"),
    "maize": os.path.join("models", "maize", "model.pt"),
    "rice": os.path.join("models", "rice_10class", "model.pt"),
    "soybean": os.path.join("models", "soybean_14class", "model.pt"),
    "pepper": os.path.join("models", "pepper_13class", "model.pt"),
    "cabbage": os.path.join("models", "cabbage_8class", "model.pt"),
}

if "selected_crop" not in st.session_state:
    st.session_state.selected_crop = None
crop = st.session_state.selected_crop

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
