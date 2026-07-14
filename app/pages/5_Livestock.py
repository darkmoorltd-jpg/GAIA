
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
st.set_page_config(page_title="GAIA – Livestock Health", page_icon="🐄", layout="wide")
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #ede7f6 100%); }
    .title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #4a148c, #7c4dff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { font-size: 1.2rem; color: #555; margin-bottom: 2rem; }
    .pred-box { background: #f3e5f5; border-left: 5px solid #7c4dff; padding: 1rem 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
    .pred-box-high { border-left-color: #4a148c; background: #e1bee7; }
    .stProgress > div > div > div > div { background: linear-gradient(90deg, #7c4dff, #b388ff); }
</style>
""", unsafe_allow_html=True)

# ---------- Livestock definitions ----------
ANIMAL_CLASSES = {
    "cattle": ["Foot‑and‑Mouth Disease", "Healthy", "Lumpy Skin Disease"],
    "poultry": ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]
}

# ---------- Model loader with auto‑download ----------
@st.cache_resource
def load_animal_model(animal: str):
    from app.utils.download_models import ensure_model
    checkpoint = ensure_model(animal)
    if not os.path.exists(checkpoint):
        raise FileNotFoundError(f"Model not found at {checkpoint}")
    num_classes = len(ANIMAL_CLASSES[animal])
    model = PretrainedViTClassifier(num_classes=num_classes)
    state_dict = torch.load(checkpoint, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()
    return model

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
st.markdown('<div class="title">🐄 Livestock Health</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Detect common diseases in cattle and poultry from a photo</div>', unsafe_allow_html=True)

animal = st.selectbox("🐾 Choose animal", list(ANIMAL_CLASSES.keys()))
uploaded_file = st.file_uploader("📤 Upload animal photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption=f"Your {animal}", width=300)

    st.markdown("---")
    st.subheader("🩺 Health Check Result")

    try:
        model = load_animal_model(animal)
        probs = predict_image(model, image)
    except FileNotFoundError as e:
        st.error(f"🚫 {e}")
        st.info("The model file could not be found. Please check your internet connection or try again later.")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.stop()

    class_names = ANIMAL_CLASSES[animal]
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
        st.success(f"✅ Your {animal} appears healthy! Keep up the good care.")
    else:
        st.warning(f"⚠️ Possible **{top_disease}** detected. Isolate and consult a veterinarian immediately.")
