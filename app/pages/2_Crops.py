
import streamlit as st
from PIL import Image
import torch, torch.nn.functional as F, numpy as np, os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌾", layout="wide")
st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>", unsafe_allow_html=True)
dark = st.toggle("", value=False, key="crops_theme")
theme = "dark" if dark else "light"

if theme == "dark":
    st.markdown("<style>.stApp{background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);color:#fff}header,footer{visibility:hidden}.title{font-size:2.8rem;font-weight:800;background:linear-gradient(90deg,#2e7d32,#4caf50);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.subtitle{font-size:1.2rem;color:#b0bec5;margin-bottom:2rem}.pred-box{background:rgba(255,255,255,.05);backdrop-filter:blur(12px);border-left:5px solid #4caf50;padding:1rem 1.5rem;border-radius:10px;margin:.5rem 0}.pred-box-high{border-left-color:#2e7d32;background:rgba(255,255,255,.1)}.stProgress>div>div>div>div{background:linear-gradient(90deg,#4caf50,#81c784)}</style>", unsafe_allow_html=True)
else:
    st.markdown("<style>.stApp{background:linear-gradient(135deg,#e8f5e9,#f1f8e9);color:#1b5e20}header,footer{visibility:hidden}.title{font-size:2.8rem;font-weight:800;background:linear-gradient(90deg,#2e7d32,#4caf50);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.subtitle{font-size:1.2rem;color:#33691e;margin-bottom:2rem}.pred-box{background:rgba(255,255,255,.9);border-left:5px solid #4caf50;padding:1rem 1.5rem;border-radius:10px;margin:.5rem 0}.pred-box-high{border-left-color:#2e7d32;background:rgba(255,255,255,1)}.stProgress>div>div>div>div{background:linear-gradient(90deg,#4caf50,#81c784)}</style>", unsafe_allow_html=True)

st.markdown('<div class="title">🌾 Millet Disease Diagnosis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload leaf photos to detect Blast, Rust, or Healthy leaves</div>', unsafe_allow_html=True)

CROP_CLASSES = {"millet": ["Blast", "Rust", "Healthy"]}

@st.cache_resource
def load_crop_model(crop_name: str):
    checkpoint = "checkpoints/millet_3class/best_model.pt"
    if os.path.exists(checkpoint):
        from app.utils.model_loader import create_model_from_checkpoint
        return create_model_from_checkpoint(checkpoint, 3), checkpoint
    return None, None

def get_model_input_size(model):
    """Detect the input size the model expects (224 or 384)."""
    try:
        # For timm ViT models, the backbone has img_size attribute
        if hasattr(model.backbone, 'patch_embed'):
            # timm patch_embed stores img_size as a tuple or list
            if hasattr(model.backbone.patch_embed, 'img_size'):
                sz = model.backbone.patch_embed.img_size
                if isinstance(sz, (list, tuple)):
                    return sz[0]
                return sz
        # Fallback: inspect the positional embedding shape
        pos_embed = model.backbone.pos_embed
        num_patches = pos_embed.shape[1] - 1
        grid = int(num_patches ** 0.5)
        return grid * 16
    except Exception:
        pass
    return 384  # safest default for your ViT‑Small‑384 millet model

def predict(model, img):
    size = get_model_input_size(model)
    t = Compose([Resize((size, size)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
    return F.softmax(model(t(img).unsqueeze(0)), dim=1)[0].cpu().numpy()

crop = "millet"
files = st.file_uploader("📤 Upload leaf images", type=["jpg","jpeg","png"], accept_multiple_files=True)

if files:
    model, _ = load_crop_model(crop)
    class_names = CROP_CLASSES[crop]
    for f in files:
        img = Image.open(f).convert("RGB")
        with st.expander(f"📷 {f.name}", expanded=True):
            c1, c2 = st.columns([1,2])
            c1.image(img, caption=f.name, width=200)
            if model is None:
                c2.warning("No trained model – using demo predictions.")
                import hashlib
                seed = int(hashlib.md5(f.name.encode()).hexdigest()[:8],16)
                np.random.seed(seed)
                probs = np.random.rand(len(class_names)); probs/=probs.sum()
            else:
                try:
                    probs = predict(model, img)
                except Exception as e:
                    c2.error(f"Error: {e}")
                    continue
            si = np.argsort(probs)[::-1]
            c2.markdown(f"**Top Result:** {class_names[si[0]]} ({probs[si[0]]*100:.1f}%)")
            for i in si[:3]:
                c2.write(f"{class_names[i]}: {probs[i]*100:.1f}%")
                c2.progress(float(probs[i]))
            try:
                if st.session_state.get("user"):
                    from app.utils.supabase_utils import decrement_scan
                    decrement_scan(st.session_state.user.id)
            except: pass

cols = st.columns(5)
for col, (label, path) in zip(cols, [("🏠 Dashboard","pages/1_Dashboard.py"),("🌾 Millet","pages/2_Crops.py"),("🐛 Pests","pages/3_Pests.py"),("🏞️ Soil","pages/4_Soil.py"),("🐄 Livestock","pages/5_Livestock.py")]):
    with col:
        st.page_link(path, label=label)
