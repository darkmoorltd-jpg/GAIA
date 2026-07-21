
import streamlit as st
from PIL import Image
import torch, torch.nn.functional as F, numpy as np, os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌿", layout="wide")
st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>",unsafe_allow_html=True)
dark = st.toggle("",value=False,key="crops_theme")
theme = "dark" if dark else "light"
if theme=="dark":
    st.markdown("<style>.stApp{background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);color:#fff}header,footer{visibility:hidden}.title{font-size:2.8rem;font-weight:800;background:linear-gradient(90deg,#2e7d32,#4caf50);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.subtitle{font-size:1.2rem;color:#b0bec5;margin-bottom:2rem}.pred-box{background:rgba(255,255,255,.05);backdrop-filter:blur(12px);border-left:5px solid #4caf50;padding:1rem 1.5rem;border-radius:10px;margin:.5rem 0}.pred-box-high{border-left-color:#2e7d32;background:rgba(255,255,255,.1)}.stProgress>div>div>div>div{background:linear-gradient(90deg,#4caf50,#81c784)}</style>",unsafe_allow_html=True)
else:
    st.markdown("<style>.stApp{background:linear-gradient(135deg,#e8f5e9,#f1f8e9);color:#1b5e20}header,footer{visibility:hidden}.title{font-size:2.8rem;font-weight:800;background:linear-gradient(90deg,#2e7d32,#4caf50);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.subtitle{font-size:1.2rem;color:#33691e;margin-bottom:2rem}.pred-box{background:rgba(255,255,255,.9);border-left:5px solid #4caf50;padding:1rem 1.5rem;border-radius:10px;margin:.5rem 0}.pred-box-high{border-left-color:#2e7d32;background:rgba(255,255,255,1)}.stProgress>div>div>div>div{background:linear-gradient(90deg,#4caf50,#81c784)}</style>",unsafe_allow_html=True)

CROP_CLASSES = {
    "apple":["Alternaria Leaf Spot","Apple Scab","Apple rot","Block rot","Brown Spot","Cedar apple rust","Frogeye Leaf Spot","Grey Spot","Healthy","Leaf Blotch","Mosaic","Powdery Mildew","Rust"],
    "mango":["Anthracnose","Bacterial Canker","Cutting Weevil","Die Back","Gall Midge","Healthy","Powdery Mildew","Sooty Mould"],
    "orange":["Citrus Canker","Nutrient Deficiency (Yellow Leaf)","Healthy","Multiple Diseases","Young Healthy"],
    "grape":["Black Measles","Black Rot","Healthy","Leaf Blight"],
    "rice":["Bacterial Blight","Brown Spot","Leaf Smut"],
    "maize":["Northern Leaf Blight","Healthy","Southern Leaf Blight","Common Rust"],
    "beans":["Angular Leaf Spot","Bean Rust","Healthy"],
    "potato":["Bacteria","Fungi","Healthy","Nematode","Pest","Phytophthora","Virus"],
    "wheat":["Aphid","Black Rust","Blast","Brown Rust","Common Root Rot","Fusarium Head Blight","Healthy","Leaf Blight","Mildew","Mite","Septoria","Smut","Stem Fly","Tan Spot","Yellow Rust"],
    "banana":["Fusarium Wilt","Healthy","Natural Death Leaf","Rhizome Root"]
}

@st.cache_resource
def load_crop_model(crop_name):
    possible = [f"checkpoints/{crop_name}_13class/best_model.pt",f"checkpoints/{crop_name}_8class/best_model.pt",f"checkpoints/{crop_name}_5class/best_model.pt",f"checkpoints/{crop_name}_11class/best_model.pt",f"checkpoints/{crop_name}_4class/best_model.pt",f"checkpoints/{crop_name}/best_model.pt"]
    for cp in possible:
        if os.path.exists(cp):
            from app.utils.model_loader import create_model_from_checkpoint
            return create_model_from_checkpoint(cp, len(CROP_CLASSES[crop_name])), cp
    return None,None

def predict(model, img):
    t = Compose([Resize((224,224)),ToTensor(),Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
    return F.softmax(model(t(img).unsqueeze(0)),dim=1)[0].cpu().numpy()

st.markdown('<div class="title">🌿 Crop Disease Diagnosis</div>',unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload leaf photos and let AI detect any disease in seconds</div>',unsafe_allow_html=True)
crop = st.selectbox("🌾 Choose your crop", list(CROP_CLASSES.keys()))
files = st.file_uploader("📤 Upload leaf images", type=["jpg","jpeg","png"], accept_multiple_files=True)

if files:
    model,path = load_crop_model(crop)
    names = CROP_CLASSES[crop]
    for f in files:
        img = Image.open(f).convert("RGB")
        with st.expander(f"📷 {f.name}", expanded=True):
            c1,c2 = st.columns([1,2])
            c1.image(img, caption=f.name, width=200)
            if model is None:
                c2.warning("No trained model – using demo predictions.")
                import hashlib
                seed = int(hashlib.md5(f.name.encode()).hexdigest()[:8],16)
                np.random.seed(seed)
                probs = np.random.rand(len(names)); probs/=probs.sum()
            else:
                try: probs = predict(model, img)
                except Exception as e: c2.error(f"Error: {e}"); continue
            si = np.argsort(probs)[::-1]
            c2.markdown(f"**Top Result:** {names[si[0]]} ({probs[si[0]]*100:.1f}%)")
            for i in si[:5]:
                c2.write(f"{names[i]}: {probs[i]*100:.1f}%")
                c2.progress(float(probs[i]))
            try:
                if st.session_state.get("user"):
                    from app.utils.supabase_utils import decrement_scan
                    decrement_scan(st.session_state.user.id)
            except: pass


# ---------- Navigation ----------
st.markdown("""
<style>
    .nav-bar { display: flex; justify-content: center; gap: 1rem; margin-top: 2rem; flex-wrap: wrap; }
    .nav-bar a { text-decoration: none; color: inherit; }
    .nav-button {
        display: inline-block; padding: 10px 20px; border-radius: 12px;
        background: rgba(0,0,0,0.05); backdrop-filter: blur(10px);
        border: 1px solid rgba(0,0,0,0.1); transition: all 0.3s ease;
        cursor: pointer; font-weight: 600; font-size: 0.95rem;
    }
    .nav-button:hover { background: rgba(0,0,0,0.1); transform: translateY(-2px); }
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
