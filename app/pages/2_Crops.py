
import streamlit as st
from PIL import Image
import torch, torch.nn as nn, torch.nn.functional as F
import numpy as np, os, sys, hashlib, requests
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌾", layout="wide")

# ── Crop class definitions ──
CROP_CLASSES = {
    "apple": ["Black Rot", "Healthy", "Rust", "Scab"],
    "cassava": ["Bacterial Blight", "Brown Streak Disease", "Green Mottle", "Healthy", "Mosaic Disease"],
    "coffee": ["Cercospora Leaf Spot", "Healthy", "Red Spider Mite", "Rust"],
    "grape": ["Black Measles", "Black Rot", "Healthy", "Leaf Blight"],
    "sugarcane": ["Bacterial Blight", "Healthy", "Red Rot", "Red Stripe", "Rust"],
    "tea": ["Algal Leaf", "Anthracnose", "Bird Eye Spot", "Brown Blight", "Healthy", "Red Leaf Spot"],
}

# ── Model download URLs (GitHub Releases) ──
MODEL_URLS = {
    "apple": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/gaia_apple.pt",
    "cassava": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/gaia_cassava.pt",
    "coffee": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/gaia_coffee.pt",
    "grape": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/gaia_grape.pt",
    "sugarcane": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/gaia_sugarcane.pt",
    "tea": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/gaia_tea.pt",
}

def download_model(crop_name):
    """Download model if not present."""
    model_dir = f"models/{crop_name}"
    model_path = os.path.join(model_dir, "model.pt")
    if os.path.exists(model_path) and os.path.getsize(model_path) > 10000:
        return model_path
    
    os.makedirs(model_dir, exist_ok=True)
    url = MODEL_URLS.get(crop_name)
    if not url:
        return None
    
    with st.spinner(f"Downloading {crop_name} model..."):
        r = requests.get(url, stream=True, timeout=300)
        r.raise_for_status()
        with open(model_path, 'wb') as f:
            for chunk in r.iter_content(32768):
                f.write(chunk)
    return model_path

def load_crop_model(crop_name):
    """Load model and return (model, num_classes)."""
    model_path = download_model(crop_name)
    if not model_path or not os.path.exists(model_path):
        return None, 0
    
    from timm.models.vision_transformer import VisionTransformer
    
    num_classes = len(CROP_CLASSES[crop_name])
    state_dict = torch.load(model_path, map_location="cpu", weights_only=False)
    
    # Build ViT-Small
    model = VisionTransformer(
        img_size=224, patch_size=16, embed_dim=384,
        depth=12, num_heads=6, num_classes=num_classes
    )
    
    # Handle state dict keys
    new_state = {}
    for k, v in state_dict.items():
        if k.startswith("backbone."):
            new_state[k.replace("backbone.", "")] = v
        elif k.startswith("head."):
            continue  # skip head — we rebuild it
        else:
            new_state[k] = v
    
    # Load what we can
    model.load_state_dict(new_state, strict=False)
    model.eval()
    return model, num_classes

# ── Theme toggle ──
st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>", unsafe_allow_html=True)
dark = st.toggle("", value=False, key="crops_theme")
theme = "dark" if dark else "light"

# ── UI ──
st.title("🌾 Crop Disease Detection")
st.markdown("Select a crop and upload a leaf photo for instant AI diagnosis")

crop = st.selectbox("🌱 Choose a crop", list(CROP_CLASSES.keys()))

uploaded_file = st.file_uploader("📤 Upload a leaf photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, width=300)
    
    st.markdown("---")
    st.subheader("📊 Diagnosis Results")
    
    model, num_classes = load_crop_model(crop)
    if model is None:
        st.error("Model not available yet.")
        st.stop()
    
    transform = Compose([
        Resize((224, 224)),
        ToTensor(),
        Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    img_tensor = transform(image).unsqueeze(0)
    
    with torch.no_grad():
        logits = model(img_tensor)
        probs = F.softmax(logits, dim=1)[0]
    
    sorted_idx = torch.argsort(probs, descending=True)
    for idx in sorted_idx:
        disease = CROP_CLASSES[crop][idx]
        percent = probs[idx] * 100
        st.write(f"**{disease}**: {percent:.1f}%")
        st.progress(float(probs[idx]))
    
    top_disease = CROP_CLASSES[crop][sorted_idx[0]]
    if "healthy" in top_disease.lower():
        st.success("✅ Crop appears healthy!")
    else:
        st.warning(f"⚠️ **{top_disease}** detected. Consider treatment.")
