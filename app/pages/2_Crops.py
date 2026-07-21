
import streamlit as st
from PIL import Image
import torch
import torch.nn.functional as F
import numpy as np
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from torchvision.transforms import Compose, Resize, ToTensor, Normalize

# ──────── theme toggle (default LIGHT) ────────
st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌿", layout="wide")

st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="crops_theme_toggle")   # default OFF = light
theme = "dark" if dark_mode else "light"

# ──────── scan deduction ────────
def deduct_and_show():
    import streamlit as st
    from supabase import create_client
    if "user" not in st.session_state or st.session_state.user is None:
        return
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
    user_id = st.session_state.user.id
    try:
        supabase.table("user_scans").insert(
            {"user_id": user_id, "scans_remaining": 30, "plan": "free"}
        ).execute()
    except:
        pass
    try:
        supabase.rpc("decrement_scan", {"uid": user_id}).execute()
        res = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
        if res.data:
            remaining = res.data[0]["scans_remaining"]
            st.success(f"Scan deducted. Remaining scans: {remaining}")
    except:
        pass

# ──────── crop definitions ────────
CROP_CLASSES = {
    "apple": [
        "Alternaria Leaf Spot", "Apple Scab", "Apple rot", "Block rot",
        "Brown Spot", "Cedar apple rust", "Frogeye Leaf Spot", "Grey Spot",
        "Healthy", "Leaf Blotch", "Mosaic", "Powdery Mildew", "Rust"
    ],
    "mango": [
        "Anthracnose", "Bacterial Canker", "Cutting Weevil", "Die Back",
        "Gall Midge", "Healthy", "Powdery Mildew", "Sooty Mould"
    ],
    "orange": [
        "Citrus Canker", "Nutrient Deficiency (Yellow Leaf)", "Healthy",
        "Multiple Diseases", "Young Healthy"
    ],
    "grape": [
        "Black Measles", "Black Rot", "Healthy", "Leaf Blight"
    ],
    "rice": ["Bacterial Blight", "Brown Spot", "Leaf Smut"],
    "maize": ["Northern Leaf Blight", "Healthy", "Southern Leaf Blight", "Common Rust"],
    "beans": ["Angular Leaf Spot", "Bean Rust", "Healthy"],
    "potato": ["Bacteria", "Fungi", "Healthy", "Nematode", "Pest", "Phytophthora", "Virus"],
    "wheat": [
        "Aphid", "Black Rust", "Blast", "Brown Rust", "Common Root Rot",
        "Fusarium Head Blight", "Healthy", "Leaf Blight", "Mildew", "Mite",
        "Septoria", "Smut", "Stem Fly", "Tan Spot", "Yellow Rust"
    ],
    "banana": ["Fusarium Wilt", "Healthy", "Natural Death Leaf", "Rhizome Root"]
}

# ──────── theme CSS ────────
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #e8f5e9; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center;
                 background: linear-gradient(90deg, #00c853, #69f0ae, #00c853);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 text-shadow: 0 0 25px rgba(0,200,83,0.7);
                 animation: cropGlow 2s ease-in-out infinite alternate; }
        @keyframes cropGlow { from { text-shadow: 0 0 25px rgba(0,200,83,0.7); }
                              to { text-shadow: 0 0 50px rgba(0,200,83,1), 0 0 80px rgba(0,200,83,0.6); } }
        .subtitle { text-align: center; font-size: 1.2rem; color: #a5d6a7; }
        .result-card { background: rgba(255,255,255,0.05); backdrop-filter: blur(20px);
                       border-radius: 20px; padding: 1.5rem; margin: 0.5rem 0; }
        .result-card.top-result { border: 1px solid #00c853; box-shadow: 0 0 30px rgba(0,200,83,0.3); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #00c853, #69f0ae); }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); color: #1b5e20; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center;
                 background: linear-gradient(90deg, #2e7d32, #66bb6a, #2e7d32);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 text-shadow: 0 0 10px rgba(46,125,50,0.3);
                 animation: cropGlowLight 2s ease-in-out infinite alternate; }
        @keyframes cropGlowLight { from { text-shadow: 0 0 10px rgba(46,125,50,0.3); }
                                   to { text-shadow: 0 0 25px rgba(46,125,50,0.8), 0 0 50px rgba(46,125,50,0.5); } }
        .subtitle { text-align: center; font-size: 1.2rem; color: #33691e; }
        .result-card { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px);
                       border-radius: 20px; padding: 1.5rem; margin: 0.5rem 0; }
        .result-card.top-result { border: 1px solid #2e7d32; box-shadow: 0 0 20px rgba(46,125,50,0.2); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #2e7d32, #66bb6a); }
    </style>
    """, unsafe_allow_html=True)

# ──────── model loader ────────
@st.cache_resource
def load_crop_model(crop_name: str):
    """Try multiple possible paths for the model file, with detailed error logging."""
    possible_paths = [
        f"checkpoints/{crop_name}_13class/best_model.pt",
        f"checkpoints/{crop_name}_8class/best_model.pt",
        f"checkpoints/{crop_name}_5class/best_model.pt",
        f"checkpoints/{crop_name}_11class/best_model.pt",
        f"checkpoints/{crop_name}_4class/best_model.pt",
        f"checkpoints/{crop_name}/best_model.pt",
    ]
    
    errors = []
    for checkpoint in possible_paths:
        if os.path.exists(checkpoint):
            try:
                from app.utils.model_loader import create_model_from_checkpoint
                num_classes = len(CROP_CLASSES[crop_name])
                model = create_model_from_checkpoint(checkpoint, num_classes)
                return model, checkpoint, None
            except Exception as e:
                errors.append(f"{checkpoint}: {str(e)[:200]}")
                continue
    
    # Try downloading from Google Drive
    try:
        from app.utils.download_models import ensure_crop_model
        downloaded_path = ensure_crop_model(crop_name)
        if downloaded_path and os.path.exists(downloaded_path):
            from app.utils.model_loader import create_model_from_checkpoint
            num_classes = len(CROP_CLASSES[crop_name])
            model = create_model_from_checkpoint(downloaded_path, num_classes)
            return model, downloaded_path, None
    except Exception as e:
        errors.append(f"download: {str(e)[:200]}")
    
    return None, None, errors

# ──────── UI ────────
st.markdown('<div class="title">🌿 Crop Disease Diagnosis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a leaf photo and let AI detect any disease in seconds</div>', unsafe_allow_html=True)

crop = st.selectbox("🌾 Choose your crop", list(CROP_CLASSES.keys()))
uploaded_file = st.file_uploader("📤 Upload leaf image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Your leaf", width=300)

    st.markdown("---")
    st.subheader("📊 Diagnosis Results")

    model, path, load_errors = load_crop_model(crop)
    class_names = CROP_CLASSES[crop]

    if model is None:
        if load_errors:
        st.error(f"🚫 Model loading errors: {load_errors}")
    st.warning(f"⚠️ No trained model found for '{crop}'. Using demo predictions.")
        import hashlib
        seed = int(hashlib.md5(uploaded_file.name.encode()).hexdigest()[:8], 16)
        np.random.seed(seed)
        probs = np.random.rand(len(class_names))
        probs = probs / probs.sum()
    else:
        transform = Compose([
            Resize((224, 224)), ToTensor(),
            Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
        ])
        img_tensor = transform(image).unsqueeze(0)
        with torch.no_grad():
            logits = model(img_tensor)
            probs = F.softmax(logits, dim=1)[0].cpu().numpy()

    sorted_idx = np.argsort(probs)[::-1]
    top_disease = class_names[sorted_idx[0]]

    # Top result card
    st.markdown(f"""
    <div class="result-card top-result" style="border-left: 5px solid {'#00c853' if theme=='dark' else '#2e7d32'};">
        <h2 style="margin:0; display: flex; align-items: center;">
            {top_disease}
            <span style="margin-left: auto; font-size: 2rem; color: {'#00c853' if theme=='dark' else '#2e7d32'};">{probs[sorted_idx[0]]*100:.1f}%</span>
        </h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### All Results")
    for i in sorted_idx:
        st.write(f"**{class_names[i]}**: {probs[i]*100:.1f}%")
        st.progress(float(probs[i]))

    deduct_and_show()

    if "healthy" in top_disease.lower():
        st.success("✅ Your crop looks healthy! Keep up the good work.")
    else:
        st.warning(f"⚠️ Possible **{top_disease}** detected. Consider appropriate treatment.")
