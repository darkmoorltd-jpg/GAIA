
import streamlit as st
from PIL import Image
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np, os, sys, timm

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Soil Analysis", page_icon="🏞️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .top-nav { display: flex; justify-content: center; gap: 2rem; padding: 0.8rem; background: rgba(255,255,255,0.9); backdrop-filter: blur(15px); border-radius: 15px; margin-bottom: 2rem; }
    .top-nav a { color: #2e7d32; text-decoration: none; font-weight: 600; font-size: 1rem; padding: 0.5rem 1.5rem; border-radius: 30px; }
</style>
<div class="top-nav"><a href="/" target="_self">🏠 Dashboard</a></div>
""", unsafe_allow_html=True)

if "theme" not in st.session_state: st.session_state.theme = "dark"
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)
dark_mode = st.toggle("", value=(st.session_state.theme == "dark"), key="soil_theme")
st.session_state.theme = "dark" if dark_mode else "light"
theme = st.session_state.theme

if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #1a120b 0%, #2e1c0d 30%, #3e2a14 60%, #1a0f05 100%); color: #f5f0eb; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #d4a373, #f5e6d3, #d4a373); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 30px rgba(212,163,115,0.7); margin-bottom: 0.5rem; animation: soilGlow 2s ease-in-out infinite alternate; }
        @keyframes soilGlow { from { text-shadow: 0 0 25px rgba(212,163,115,0.7); } to { text-shadow: 0 0 50px rgba(212,163,115,1), 0 0 80px rgba(212,163,115,0.6); } }
        .subtitle { text-align: center; font-size: 1.3rem; color: #bcaaa4; margin-bottom: 2rem; }
        .stFileUploader > div { background: rgba(212,163,115,0.03) !important; backdrop-filter: blur(15px) !important; border: 2px dashed rgba(212,163,115,0.3) !important; border-radius: 20px !important; padding: 2rem !important; }
        .stFileUploader > div:hover { border-color: #d4a373 !important; box-shadow: 0 0 30px rgba(212,163,115,0.2); }
        .result-card { background: rgba(0,0,0,0.6); backdrop-filter: blur(25px); border: 1px solid rgba(212,163,115,0.2); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; }
        .top-result { border-color: #d4a373; box-shadow: 0 0 50px rgba(212,163,115,0.4); }
        .scan-left { background: rgba(212,163,115,0.15); border: 1px solid #d4a373; border-radius: 15px; padding: 1rem; text-align: center; margin-top: 1.5rem; font-size: 1.2rem; color: #d4a373; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #efebe9 0%, #d7ccc8 100%); color: #3e2723; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center; color: #5d4037; }
        .subtitle { text-align: center; font-size: 1.3rem; color: #4e342e; margin-bottom: 2rem; }
        .stFileUploader > div { background: rgba(255,255,255,0.8) !important; backdrop-filter: blur(10px) !important; border: 2px dashed rgba(93,64,55,0.3) !important; border-radius: 20px !important; padding: 2rem !important; }
        .result-card { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.08); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; }
        .top-result { border-color: #5d4037; box-shadow: 0 0 15px rgba(93,64,55,0.15); }
        .scan-left { background: rgba(93,64,55,0.1); border: 1px solid #5d4037; border-radius: 15px; padding: 1rem; text-align: center; margin-top: 1.5rem; font-size: 1.2rem; color: #5d4037; }
    </style>
    """, unsafe_allow_html=True)

SOIL_CLASSES = ["alluvial","black","cinder","clay","laterite","loamy","peat","red","sandy","sandy_loam","yellow"]
NUM_CLASSES = len(SOIL_CLASSES)

class SoilViT11(nn.Module):
    def __init__(self): super().__init__(); self.backbone = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=0); self.head = nn.Sequential(nn.Linear(self.backbone.embed_dim,1024),nn.GELU(),nn.Dropout(0.3),nn.Linear(1024,512),nn.GELU(),nn.Dropout(0.2),nn.Linear(512,NUM_CLASSES))
    def forward(self,x): return self.head(self.backbone(x))

@st.cache_resource
def load_soil_model():
    checkpoint = "checkpoints/soil_11class/best_model.pt"
    if not os.path.exists(checkpoint): raise FileNotFoundError(f"Model not found at {checkpoint}")
    model = SoilViT11(); state_dict = torch.load(checkpoint, map_location="cpu", weights_only=False); model.load_state_dict(state_dict); model.eval()
    return model

def predict_image(model, image):
    transform = Compose([Resize((224,224)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
    with torch.no_grad(): return F.softmax(model(transform(image).unsqueeze(0)), dim=1)[0].cpu().numpy()

def deduct_and_show(user_id):
    from supabase import create_client
    url = st.secrets["supabase"]["url"]; key = st.secrets["supabase"]["key"]; supabase = create_client(url, key)
    try: supabase.table("user_scans").insert({"user_id":user_id,"scans_remaining":30,"plan":"free"}).execute()
    except: pass
    try:
        supabase.rpc("decrement_scan",{"uid":user_id}).execute()
        res = supabase.table("user_scans").select("scans_remaining").eq("user_id",user_id).execute()
        if res.data: st.markdown(f'<div class="scan-left">🛰️ Remaining scans: <b>{res.data[0]["scans_remaining"]}</b></div>', unsafe_allow_html=True)
    except: pass

st.markdown('<div class="title">🏞️ Soil Type Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload soil photos for instant classification</div>', unsafe_allow_html=True)
uploaded_files = st.file_uploader("📤 Upload soil photos", type=["jpg","jpeg","png"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file).convert("RGB")
        col1, col2 = st.columns([1,2])
        with col1: st.image(image, caption=uploaded_file.name, width=200)
        with col2:
            try:
                model = load_soil_model(); probs = predict_image(model, image)
                top_idx = np.argmax(probs)
                st.markdown(f'<div class="result-card top-result"><h3 style="margin:0;">{SOIL_CLASSES[top_idx].title()}</h3><span style="font-size:1.5rem;color:#d4a373;">{probs[top_idx]*100:.1f}%</span></div>', unsafe_allow_html=True)
                if st.session_state.get("user"): deduct_and_show(st.session_state.user.id)
            except Exception as e: st.error(str(e))
        st.markdown("---")
