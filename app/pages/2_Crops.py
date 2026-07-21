
import streamlit as st
from PIL import Image
import torch
import torch.nn.functional as F
import numpy as np
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.models.pretrained_vit import PretrainedViTClassifier
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

# ---------- Page config ----------
st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌿", layout="wide")

# ---------- Theme toggle ----------
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="crops_theme_toggle")
theme = "dark" if dark_mode else "light"

# ---------- Theme CSS ----------
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #ffffff; }
        .title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { font-size: 1.2rem; color: #b0bec5; margin-bottom: 2rem; }
        .pred-box { background: rgba(255,255,255,0.05); backdrop-filter: blur(12px); border-left: 5px solid #4caf50; padding: 1rem 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
        .pred-box-high { border-left-color: #2e7d32; background: rgba(255,255,255,0.1); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #4caf50, #81c784); }
        header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); color: #1b5e20; }
        .title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { font-size: 1.2rem; color: #33691e; margin-bottom: 2rem; }
        .pred-box { background: rgba(255,255,255,0.9); border-left: 5px solid #4caf50; padding: 1rem 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
        .pred-box-high { border-left-color: #2e7d32; background: rgba(255,255,255,1); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #4caf50, #81c784); }
        header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ---------- Navigation Bar (bottom) ----------
st.markdown("""
<style>
    .nav-bar { display: flex; justify-content: center; gap: 1rem; margin: 2rem 0 1rem 0; flex-wrap: wrap; }
    .nav-bar a { text-decoration: none; color: inherit; }
    .nav-button {
        display: inline-block; padding: 10px 20px; border-radius: 12px;
        background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2); transition: all 0.3s ease;
        cursor: pointer; font-weight: 600; font-size: 0.95rem;
    }
    .nav-button:hover {
        background: rgba(255,255,255,0.2); border-color: rgba(255,255,255,0.5);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

cols = st.columns(5)
pages = [
    ("🏠 Dashboard", "pages/1_Dashboard.py"),
    ("🌿 Crops", "pages/2_Crops.py"),
    ("🐛 Pests", "pages/3_Pests.py"),
    ("🏞️ Soil", "pages/4_Soil.py"),
    ("🐄 Livestock", "pages/5_Livestock.py")
]
for col, (label, path) in zip(cols, pages):
    with col:
        st.page_link(path, label=label, help=f"Go to {label}")



