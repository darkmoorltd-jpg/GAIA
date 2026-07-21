
import streamlit as st
from PIL import Image
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np, os, sys, timm

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

def bottom_nav():
    st.markdown("---")
    st.markdown("### 🚀 Quick Navigation")
    cols = st.columns(8)
    with cols[0]:
        if st.button("🌿 Crops", key="bn_crops"): st.switch_page("pages/2_Crops.py")
    with cols[1]:
        if st.button("🐛 Pests", key="bn_pests"): st.switch_page("pages/3_Pests.py")
    with cols[2]:
        if st.button("🏞️ Soil", key="bn_soil"): st.switch_page("pages/4_Soil.py")
    with cols[3]:
        if st.button("🐄 Livestock", key="bn_livestock"): st.switch_page("pages/5_Livestock.py")
    with cols[4]:
        if st.button("💳 Buy Scans", key="bn_buy"): st.switch_page("pages/9_Buy_Scans.py")
    with cols[5]:
        if st.button("📋 Payments", key="bn_payments"): st.switch_page("pages/6_Payment_History.py")
    with cols[6]:
        if st.button("🔐 Admin", key="bn_admin"): st.switch_page("pages/7_Admin.py")
    with cols[7]:
        if st.button("🚪 Logout", key="bn_logout"):
            from supabase import create_client
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
            supabase = create_client(url, key)
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()


st.set_page_config(page_title="GAIA – Livestock Health", page_icon="🐄", layout="wide", initial_sidebar_state="expanded")
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
dark_mode = st.toggle("", value=(st.session_state.theme == "dark"), key="livestock_theme")
st.session_state.theme = "dark" if dark_mode else "light"
theme = st.session_state.theme

if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(145deg, #0a0a0a 0%, #1a1a2e 50%, #0d0d0d 100%); color: #e0e0e0; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #7c4dff, #b388ff, #7c4dff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 30px rgba(124,77,255,0.6); margin-bottom: 0.5rem; animation: glow 2s ease-in-out infinite alternate; }
        @keyframes glow { from { text-shadow: 0 0 20px rgba(124,77,255,0.6); } to { text-shadow: 0 0 40px rgba(124,77,255,1), 0 0 80px rgba(124,77,255,0.8); } }
        .subtitle { text-align: center; font-size: 1.3rem; color: #90a4ae; margin-bottom: 2rem; }
        .stFileUploader > div { background: rgba(124,77,255,0.03) !important; backdrop-filter: blur(15px) !important; border: 2px dashed rgba(124,77,255,0.3) !important; border-radius: 20px !important; padding: 2rem !important; }
        .stFileUploader > div:hover { border-color: #7c4dff !important; box-shadow: 0 0 30px rgba(124,77,255,0.2); }
        .result-card { background: rgba(0,0,0,0.6); backdrop-filter: blur(25px); border: 1px solid rgba(124,77,255,0.2); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; }
        .top-result { border-color: #7c4dff; box-shadow: 0 0 50px rgba(124,77,255,0.4); }
        .scan-left { background: rgba(124,77,255,0.15); border: 1px solid #7c4dff; border-radius: 15px; padding: 1rem; text-align: center; margin-top: 1.5rem; font-size: 1.2rem; color: #7c4dff; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #ede7f6 0%, #d1c4e9 100%); color: #311b92; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center; color: #4a148c; }
        .subtitle { text-align: center; font-size: 1.3rem; color: #311b92; margin-bottom: 2rem; }
        .stFileUploader > div { background: rgba(255,255,255,0.8) !important; backdrop-filter: blur(10px) !important; border: 2px dashed rgba(74,20,140,0.3) !important; border-radius: 20px !important; padding: 2rem !important; }
        .result-card { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.08); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; }
        .top-result { border-color: #4a148c; box-shadow: 0 0 15px rgba(74,20,140,0.15); }
        .scan-left { background: rgba(74,20,140,0.1); border: 1px solid #4a148c; border-radius: 15px; padding: 1rem; text-align: center; margin-top: 1.5rem; font-size: 1.2rem; color: #4a148c; }
    </style>
    """, unsafe_allow_html=True)

ANIMAL_CLASSES = {
    "cattle": ["Foot‑and‑Mouth Disease","Healthy","Lumpy Skin Disease"],
    "poultry": ["Coccidiosis","Healthy","Newcastle Disease","Salmonella"]
}

class LivestockClassifier(nn.Module):
    def __init__(self, num_classes): super().__init__(); self.backbone = timm.create_model('vit_tiny_patch16_224', pretrained=False, num_classes=0); self.head = nn.Linear(self.backbone.embed_dim, num_classes)
    def forward(self,x): return self.head(self.backbone(x))

@st.cache_resource
def load_animal_model(animal):
    checkpoint = f"checkpoints/{animal}/best_model.pt"
    if not os.path.exists(checkpoint): raise FileNotFoundError(f"Model not found at {checkpoint}")
    model = LivestockClassifier(num_classes=len(ANIMAL_CLASSES[animal]))
    state_dict = torch.load(checkpoint, map_location="cpu", weights_only=False); model.load_state_dict(state_dict); model.eval()
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

st.markdown('<div class="title">🐄 Livestock Health</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload animal photos for instant diagnosis</div>', unsafe_allow_html=True)
animal = st.selectbox("🐾 Choose animal", list(ANIMAL_CLASSES.keys()))
uploaded_files = st.file_uploader("📤 Upload animal photos", type=["jpg","jpeg","png"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file).convert("RGB")
        col1, col2 = st.columns([1,2])
        with col1: st.image(image, caption=uploaded_file.name, width=200)
        with col2:
            try:
                model = load_animal_model(animal); probs = predict_image(model, image)
                class_names = ANIMAL_CLASSES[animal]; top_idx = np.argmax(probs)
                st.markdown(f'<div class="result-card top-result"><h3 style="margin:0;">{class_names[top_idx]}</h3><span style="font-size:1.5rem;color:#7c4dff;">{probs[top_idx]*100:.1f}%</span></div>', unsafe_allow_html=True)
                if st.session_state.get("user"): deduct_and_show(st.session_state.user.id)
            except Exception as e: st.error(str(e))
        st.markdown("---")
