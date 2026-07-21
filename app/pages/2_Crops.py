
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

# ---------- Page config & CSS ----------
st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌿", layout="wide")
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e4efe9 100%); }
    .title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { font-size: 1.2rem; color: #555; margin-bottom: 2rem; }
    .pred-box { background: #f0fdf4; border-left: 5px solid #4caf50; padding: 1rem 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
    .pred-box-high { border-left-color: #2e7d32; background: #e8f5e9; }
    .stProgress > div > div > div > div { background: linear-gradient(90deg, #4caf50, #81c784); }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🌿 Crop Disease Diagnosis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a leaf photo and let AI detect any disease in seconds</div>', unsafe_allow_html=True)

# ---------- Crop definitions ----------
CROP_CLASSES = {
    # New crops (model files exist)
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

    # Old crops (models may be missing – fallback to demo)
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

# ---------- Model loader ----------
@st.cache_resource
def load_crop_model(crop_name: str):
    """Try multiple possible paths for the model file."""
    possible_paths = [
        f"checkpoints/{crop_name}_13class/best_model.pt",
        f"checkpoints/{crop_name}_8class/best_model.pt",
        f"checkpoints/{crop_name}_5class/best_model.pt",
        f"checkpoints/{crop_name}_11class/best_model.pt",
        f"checkpoints/{crop_name}_4class/best_model.pt",
        f"checkpoints/{crop_name}/best_model.pt",
    ]
    
    for checkpoint in possible_paths:
        if os.path.exists(checkpoint):
            from app.utils.model_loader import create_model_from_checkpoint
            num_classes = len(CROP_CLASSES[crop_name])
            model = create_model_from_checkpoint(checkpoint, num_classes)
            return model, checkpoint
    
    # No model found – return None
    return None, None

def predict_image(model, image: Image.Image):
    transform = Compose([
        Resize((224, 224)),
        ToTensor(),
        Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    img_tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        logits = model(img_tensor)
        probs = F.softmax(logits, dim=1)[0].cpu().numpy()
    return probs

# ---------- UI ----------
crop = st.selectbox("🌾 Choose your crop", list(CROP_CLASSES.keys()))
uploaded_file = st.file_uploader("📤 Upload leaf image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Your leaf", width=300)

    st.markdown("---")
    st.subheader("📊 Diagnosis Results")

    model, path = load_crop_model(crop)

    if model is None:
        st.warning(f"⚠️ No trained model found for '{crop}'. Using demo predictions.")
        # Demo predictions
        class_names = CROP_CLASSES[crop]
        import hashlib
        seed = int(hashlib.md5(uploaded_file.name.encode()).hexdigest()[:8], 16)
        np.random.seed(seed)
        probs = np.random.rand(len(class_names))
        probs = probs / probs.sum()
    else:
        try:
            probs = predict_image(model, image)
        except Exception as e:
            st.error(f"Error during inference: {e}")
            st.stop()

    class_names = CROP_CLASSES[crop]
    sorted_idx = np.argsort(probs)[::-1]

    for i, idx in enumerate(sorted_idx):
        disease = class_names[idx]
        percent = probs[idx] * 100
        box_class = "pred-box-high" if i == 0 else "pred-box"
        st.markdown(
            f'<div class="{box_class}"><b>{disease}</b> – {percent:.1f}%</div>',
            unsafe_allow_html=True
        )
        st.progress(float(probs[idx]))

    top_disease = class_names[sorted_idx[0]]
    if "healthy" in top_disease.lower():
        st.success("✅ Your crop looks healthy! Keep up the good work.")
    else:
        st.warning(f"⚠️ Possible **{top_disease}** detected. Consider appropriate treatment.")

    # Scan deduction (if user is logged in)
    try:
        if st.session_state.get("user"):
            from app.utils.supabase_utils import decrement_scan
            decrement_scan(st.session_state.user.id)
            st.success("Scan deducted.")
    except:
        pass
