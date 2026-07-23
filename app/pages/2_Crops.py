
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
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); color: #fff; }
        header, footer {visibility: hidden;}
        .title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { font-size: 1.2rem; color: #b0bec5; margin-bottom: 2rem; }
        .pred-box { background: rgba(255,255,255,.05); backdrop-filter: blur(12px); border-left: 5px solid #4caf50; padding: 1rem 1.5rem; border-radius: 10px; margin: .5rem 0; }
        .pred-box-high { border-left-color: #2e7d32; background: rgba(255,255,255,.1); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #4caf50, #81c784); }
        .crop-btn { background: rgba(255,255,255,0.08); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.15); border-radius: 20px; padding: 2rem 1rem; width: 100%; height: 120px; color: #fff !important; font-size: 1.3rem; font-weight: 600; transition: all 0.3s ease; cursor: pointer; text-align: center; }
        .crop-btn:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(0,200,83,0.3); border-color: #00c853; background: rgba(0,200,83,0.15); }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9, #f1f8e9); color: #1b5e20; }
        header, footer {visibility: hidden;}
        .title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { font-size: 1.2rem; color: #33691e; margin-bottom: 2rem; }
        .pred-box { background: rgba(255,255,255,0.9); border-left: 5px solid #4caf50; padding: 1rem 1.5rem; border-radius: 10px; margin: .5rem 0; }
        .pred-box-high { border-left-color: #2e7d32; background: rgba(255,255,255,1); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #4caf50, #81c784); }
        .crop-btn { background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.1); border-radius: 20px; padding: 2rem 1rem; width: 100%; height: 120px; color: #1b5e20 !important; font-size: 1.3rem; font-weight: 600; transition: all 0.3s ease; cursor: pointer; text-align: center; }
        .crop-btn:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(46,125,50,0.2); border-color: #2e7d32; background: rgba(46,125,50,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="title">🌾 Crop Disease Diagnosis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Select a crop, upload leaf photos, and let AI detect diseases in seconds</div>', unsafe_allow_html=True)

CROP_CLASSES = {
    "millet": ["Blast", "Rust", "Healthy"],
    "maize": ["Blight", "Common_Rust", "Gray_Leaf_Spot", "Healthy"],
}

if "selected_crop" not in st.session_state:
    st.session_state.selected_crop = None

@st.cache_resource
def load_crop_model(crop_name: str):
    checkpoint_map = {
        "millet": "checkpoints/millet_3class/best_model.pt",
        "maize": "checkpoints/maize/best_model.pt",
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
            if isinstance(sz, (list, tuple)):
                return sz[0]
            return sz
        pos_embed = model.backbone.pos_embed
        num_patches = pos_embed.shape[1] - 1
        grid = int(num_patches ** 0.5)
        return grid * 16
    except:
        pass
    return 384

def predict(model, img):
    size = get_model_input_size(model)
    t = Compose([Resize((size, size)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
    with torch.no_grad():
        logits = model(t(img).unsqueeze(0))
        probs = F.softmax(logits, dim=1)[0].detach().cpu().numpy()
    return probs

def deduct_one_scan():
    """Robust scan deduction that shows the remaining count."""
    if "user" not in st.session_state or st.session_state.user is None:
        return
    from supabase import create_client
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
    user_id = st.session_state.user.id

    # Ensure row exists
    try:
        supabase.table("user_scans").insert(
            {"user_id": user_id, "scans_remaining": 30, "plan": "free"}
        ).execute()
    except:
        pass

    # Try direct update first
    try:
        supabase.table("user_scans") \
            .update({"scans_remaining": supabase.raw("scans_remaining - 1")}) \
            .eq("user_id", user_id) \
            .execute()
    except:
        # Fallback to RPC
        supabase.rpc("decrement_scan", {"uid": user_id}).execute()

    # Fetch and show
    res = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
    if res.data:
        remaining = res.data[0]["scans_remaining"]
        st.success(f"✅ Scan deducted. Remaining scans: {remaining}")
    else:
        st.info("Scan recorded.")

# ---------- Main UI ----------
if st.session_state.selected_crop is None:
    cols = st.columns(len(CROP_CLASSES))
    for i, crop_name in enumerate(CROP_CLASSES.keys()):
        with cols[i]:
            if st.button(crop_name.title(), key=f"crop_{crop_name}", use_container_width=True):
                st.session_state.selected_crop = crop_name
                st.rerun()
else:
    crop = st.session_state.selected_crop
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
                c1, c2 = st.columns([1, 2])
                c1.image(img, caption=f.name, width=200)

                if model is None:
                    c2.warning("No trained model – using demo predictions.")
                    import hashlib
                    seed = int(hashlib.md5(f.name.encode()).hexdigest()[:8], 16)
                    np.random.seed(seed)
                    probs = np.random.rand(len(class_names))
                    probs /= probs.sum()
                else:
                    try:
                        probs = predict(model, img)
                    except Exception as e:
                        c2.error(f"Inference error: {e}")
                        continue

                si = np.argsort(probs)[::-1]
                c2.markdown(f"**Top Result:** {class_names[si[0]]} ({probs[si[0]]*100:.1f}%)")
                for i in si[:3]:
                    c2.write(f"{class_names[i]}: {probs[i]*100:.1f}%")
                    c2.progress(float(probs[i]))

                # Deduct scan – shown inside the expander, right after the diagnosis
                deduct_one_scan()

# ---------- Bottom navigation bar ----------
cols = st.columns(5)
for col, (label, path) in zip(cols, [
    ("🏠 Dashboard", "pages/1_Dashboard.py"),
    ("🌾 Crops", "pages/2_Crops.py"),
    ("🐛 Pests", "pages/3_Pests.py"),
    ("🏞️ Soil", "pages/4_Soil.py"),
    ("🐄 Livestock", "pages/5_Livestock.py")
]):
    with col:
        st.page_link(path, label=label)
