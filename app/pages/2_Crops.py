
import streamlit as st
from PIL import Image
import torch, torch.nn.functional as F, numpy as np, os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌾", layout="wide")

# ---------- Crop definitions ----------
CROP_CLASSES = {
    "millet": ["Blast", "Rust", "Healthy"],
    "maize": ["Blight", "Common_Rust", "Gray_Leaf_Spot", "Healthy"],
    "soybean": ["Bacterial Pustule","Frogeye Leaf Spot","Healthy","Mosaic Virus","Rust","Southern blight","Sudden Death Syndrome","Target Leaf Spot","Yellow Mosaic","brown_spot","crestamento","ferrugen","powdery_mildew","septoria"],
    "pepper": ["Aphid","Bacterial spot","Blossom end rot","Burn","Edema","Healthy","Leaf curl","Leaf miners","Mosaic virus","Nutrient deficiency","Powdery mildew","Spider mite","Thrips"],
}

# ---------- Crop background images (Unsplash) ----------
CROP_BG = {
    "millet": "https://images.unsplash.com/photo-1601275868393-45b4e4b0f3b3?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80",
    "maize": "https://images.unsplash.com/photo-1601024445120-e5b67b5f44b9?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80",
    "soybean": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80",
    "pepper": "https://images.unsplash.com/photo-1563690443-4e3c9e0e3c0d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80",
}

# ---------- Session state ----------
if "selected_crop" not in st.session_state:
    st.session_state.selected_crop = None

crop = st.session_state.selected_crop

# ---------- Theme toggle ----------
st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>", unsafe_allow_html=True)
dark = st.toggle("", value=False, key="crops_theme")
theme = "dark" if dark else "light"

# ---------- Base CSS + dynamic background ----------
overlay = "rgba(0,0,0,0.55)" if theme == "dark" else "rgba(255,255,255,0.75)"
bg_url = CROP_BG.get(crop, "")
bg_css = f'.stApp {{ background: linear-gradient({overlay}, {overlay}), url("{bg_url}") center/cover fixed; }}' if bg_url else ''

if theme == "dark":
    st.markdown(f"""
    <style>
        .stApp {{ background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); color: #fff; }}
        header, footer {{visibility: hidden;}}
        .title {{ font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .subtitle {{ font-size: 1.2rem; color: #b0bec5; margin-bottom: 2rem; }}
        .pred-box {{ background: rgba(255,255,255,.05); backdrop-filter: blur(12px); border-left: 5px solid #4caf50; padding: 1rem 1.5rem; border-radius: 10px; margin: .5rem 0; }}
        .pred-box-high {{ border-left-color: #2e7d32; background: rgba(255,255,255,.1); }}
        .stProgress > div > div > div > div {{ background: linear-gradient(90deg, #4caf50, #81c784); }}
        .crop-btn {{ background: rgba(255,255,255,0.08); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.15); border-radius: 20px; padding: 2rem 1rem; width: 100%; height: 120px; color: #fff !important; font-size: 1.3rem; font-weight: 600; transition: all 0.3s ease; cursor: pointer; text-align: center; }}
        .crop-btn:hover {{ transform: translateY(-8px); box-shadow: 0 20px 40px rgba(0,200,83,0.3); border-color: #00c853; background: rgba(0,200,83,0.15); }}
        {bg_css}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <style>
        .stApp {{ background: linear-gradient(135deg, #e8f5e9, #f1f8e9); color: #1b5e20; }}
        header, footer {{visibility: hidden;}}
        .title {{ font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .subtitle {{ font-size: 1.2rem; color: #33691e; margin-bottom: 2rem; }}
        .pred-box {{ background: rgba(255,255,255,0.9); border-left: 5px solid #4caf50; padding: 1rem 1.5rem; border-radius: 10px; margin: .5rem 0; }}
        .pred-box-high {{ border-left-color: #2e7d32; background: rgba(255,255,255,1); }}
        .stProgress > div > div > div > div {{ background: linear-gradient(90deg, #4caf50, #81c784); }}
        .crop-btn {{ background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.1); border-radius: 20px; padding: 2rem 1rem; width: 100%; height: 120px; color: #1b5e20 !important; font-size: 1.3rem; font-weight: 600; transition: all 0.3s ease; cursor: pointer; text-align: center; }}
        .crop-btn:hover {{ transform: translateY(-8px); box-shadow: 0 20px 40px rgba(46,125,50,0.2); border-color: #2e7d32; background: rgba(46,125,50,0.1); }}
        {bg_css}
    </style>
    """, unsafe_allow_html=True)

# ---------- Model loader ----------
@st.cache_resource
def load_crop_model(crop_name: str):
    checkpoint_map = {
        "millet": "checkpoints/millet_3class/best_model.pt",
        "maize": "checkpoints/maize/best_model.pt",
        "soybean": "checkpoints/soybean_14class/best_model.pt",
        "pepper": "checkpoints/pepper_13class/best_model.pt",
    }
    checkpoint = checkpoint_map.get(crop_name)
    if checkpoint and os.path.exists(checkpoint):
        from app.utils.model_loader import create_model_from_checkpoint
        return create_model_from_checkpoint(checkpoint, len(CROP_CLASSES[crop_name])), checkpoint
    return None, None

def get_model_input_size(model):
    try:
        if hasattr(model.backbone, 'patch_embed') and hasattr(model.backbone.patch_embed, 'img_size'):
            sz = model.backbone.patch_embed.img_size
            if isinstance(sz, (list, tuple)): return sz[0]
            return sz
        pos_embed = model.backbone.pos_embed
        num_patches = pos_embed.shape[1] - 1
        return int(num_patches ** 0.5) * 16
    except: pass
    return 384

def predict(model, img):
    size = get_model_input_size(model)
    t = Compose([Resize((size, size)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
    with torch.no_grad():
        probs = F.softmax(model(t(img).unsqueeze(0)), dim=1)[0].detach().cpu().numpy()
    return probs

def deduct_one_scan():
    if "user" not in st.session_state or st.session_state.user is None: return
    from supabase import create_client
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    uid = st.session_state.user.id
    try: supabase.table("user_scans").insert({"user_id":uid,"scans_remaining":30,"plan":"free"}).execute()
    except: pass
    try:
        supabase.table("user_scans").update({"scans_remaining": supabase.raw("scans_remaining - 1")}).eq("user_id", uid).execute()
    except:
        supabase.rpc("decrement_scan", {"uid": uid}).execute()
    res = supabase.table("user_scans").select("scans_remaining").eq("user_id", uid).execute()
    if res.data:
        st.success(f"✅ Scan deducted. Remaining scans: {res.data[0]['scans_remaining']}")

# ---------- UI ----------
st.markdown('<div class="title">🌾 Crop Disease Diagnosis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Select a crop, upload leaf photos, and let AI detect diseases in seconds</div>', unsafe_allow_html=True)

if crop is None:
    cols = st.columns(len(CROP_CLASSES))
    for i, name in enumerate(CROP_CLASSES.keys()):
        with cols[i]:
            if st.button(name.title(), key=f"crop_{name}", use_container_width=True):
                st.session_state.selected_crop = name
                st.rerun()
else:
    if st.button("← Back to Crops"):
        st.session_state.selected_crop = None
        st.rerun()

    st.markdown(f"### 🌱 Selected Crop: **{crop.title()}**")
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
                    try: probs = predict(model, img)
                    except Exception as e: c2.error(f"Error: {e}"); continue
                si = np.argsort(probs)[::-1]
                c2.markdown(f"**Top Result:** {class_names[si[0]]} ({probs[si[0]]*100:.1f}%)")
                for i in si[:3]:
                    c2.write(f"{class_names[i]}: {probs[i]*100:.1f}%")
                    c2.progress(float(probs[i]))
                deduct_one_scan()

# ---------- Bottom navigation ----------
cols = st.columns(5)
for col, (label, path) in zip(cols, [
    ("🏠 Dashboard", "pages/1_Dashboard.py"),
    ("🌾 Crops", "pages/2_Crops.py"),
    ("🐛 Pests", "pages/3_Pests.py"),
    ("🏞️ Soil", "pages/4_Soil.py"),
    ("🐄 Livestock", "pages/5_Livestock.py")
]):
    with col: st.page_link(path, label=label)
