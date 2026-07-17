import streamlit as st
from PIL import Image
import torch
import torch.nn.functional as F
import numpy as np
import os
import sys

def deduct_and_show():
    """Deduct a scan and display the new remaining balance."""
    import streamlit as st
    from supabase import create_client
    if "user" not in st.session_state or st.session_state.user is None:
        return
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
    user_id = st.session_state.user.id

    # Ensure the user_scans row exists (create if missing)
    supabase.table("user_scans").insert(
        {"user_id": user_id, "scans_remaining": 30, "plan": "free"}
    ).execute()

    # Decrement
    supabase.rpc("decrement_scan", {"uid": user_id}).execute()

    # Fetch the new count
    res = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
    if res.data:
        remaining = res.data[0]["scans_remaining"]
        st.success(f"Scan deducted. Remaining scans: {remaining}")
    else:
        st.warning("Scan deducted, but unable to fetch updated count.")


def deduct_and_show():
    """Deduct a scan and display the new remaining balance."""
    import streamlit as st
    from supabase import create_client
    if "user" not in st.session_state or st.session_state.user is None:
        return
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)

    # Call the RPC function
    supabase.rpc("decrement_scan", {"uid": st.session_state.user.id}).execute()

    # Fetch the new count
    res = supabase.table("user_scans").select("scans_remaining").eq("user_id", st.session_state.user.id).execute()
    if res.data:
        remaining = res.data[0]["scans_remaining"]
        st.success(f"Scan deducted. Remaining scans: {remaining}")
    else:
        st.warning("Scan deducted, but unable to fetch updated count.")


def deduct_and_show():
    """Atomically deduct one scan from the current user's balance."""
    import streamlit as st
    from supabase import create_client
    if "user" not in st.session_state or st.session_state.user is None:
        return
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
    supabase.rpc("decrement_scan", {"uid": st.session_state.user.id}).execute()


sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.models.pretrained_vit import PretrainedViTClassifier
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

# ---------- Page config & CSS ----------
st.set_page_config(page_title="GAIA – Soil Analysis", page_icon="🏞️", layout="wide")
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #efebe9 100%); }
    .title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #5d4037, #8d6e63); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { font-size: 1.2rem; color: #555; margin-bottom: 2rem; }
    .pred-box { background: #efebe9; border-left: 5px solid #8d6e63; padding: 1rem 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
    .pred-box-high { border-left-color: #5d4037; background: #d7ccc8; }
    .stProgress > div > div > div > div { background: linear-gradient(90deg, #8d6e63, #bcaaa4); }
</style>
""", unsafe_allow_html=True)

# ---------- Soil definitions ----------
SOIL_CLASSES = ["Alluvial", "Arid", "Black", "Laterite", "Mountain", "Red", "Yellow"]
NUM_CLASSES = len(SOIL_CLASSES)

# ---------- Model loader ----------
@st.cache_resource
def load_soil_model():
    checkpoint = "checkpoints/soil/best_model.pt"
    if not os.path.exists(checkpoint):
        raise FileNotFoundError(f"Model not found at {checkpoint}")
    model = PretrainedViTClassifier(num_classes=NUM_CLASSES)
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
st.markdown('<div class="title">🏞️ Soil Type Classification</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a close‑up photo of soil to identify its type</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("📤 Upload soil photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Soil sample", width=300)

    st.markdown("---")
    st.subheader("🧪 Soil Analysis Result")

    try:
        model = load_soil_model()
        probs = predict_image(model, image)
    except FileNotFoundError as e:
        st.error(f"🚫 {e}")
        st.info("Please train/save the soil model first.")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.stop()

    top_idx = np.argmax(probs)
    st.markdown(
        f'<div class="pred-box-high"><h3 style="margin:0">{SOIL_CLASSES[top_idx]}</h3>'
        f'<span style="font-size:1.5rem; font-weight:bold;">{probs[top_idx]*100:.1f}%</span></div>',
        unsafe_allow_html=True
    )

    st.markdown("### All soil types")

    # Deduct a scan
    if st.session_state.user:
        deduct_and_show()

    for i, name in enumerate(SOIL_CLASSES):
        st.write(f"**{name}**: {probs[i]*100:.1f}%")
        st.progress(float(probs[i]))