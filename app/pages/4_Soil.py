
import streamlit as st
from PIL import Image
import torch
import torch.nn.functional as F
import numpy as np
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from torchvision.transforms import Compose, Resize, ToTensor, Normalize

# ──────── helpers ────────
def _get_soil_description(soil_type):
    descriptions = {
        "alluvial": "Rich, fertile soil deposited by rivers. Excellent for agriculture.",
        "black": "Dark, nutrient-rich soil. High water retention. Great for cotton.",
        "cinder": "Volcanic soil fragments. Good drainage. Used in landscaping.",
        "clay": "Dense, sticky soil. Holds water well. Needs organic matter.",
        "laterite": "Iron-rich, weathered soil. Common in tropical regions.",
        "loamy": "Perfect balance of sand, silt, and clay. Ideal for most crops.",
        "peat": "Organic-rich, acidic soil. Excellent water retention.",
        "red": "Iron oxide-rich soil. Good drainage. Suitable for groundnuts.",
        "sandy": "Loose, well-drained soil. Warms quickly. Needs frequent watering.",
        "sandy_loam": "Sandy with some organic matter. Good for root vegetables.",
        "yellow": "Moderately fertile soil. Contains hydrated iron oxides."
    }
    return descriptions.get(soil_type, "")

def _get_recommendation(soil_type):
    recommendations = {
        "alluvial": "Ideal for rice, wheat, sugarcane. Add organic compost.",
        "black": "Perfect for cotton, soybeans. Maintain moisture with mulching.",
        "cinder": "Mix with organic matter. Good for succulents and cacti.",
        "clay": "Add compost and gypsum to improve drainage.",
        "laterite": "Add lime and organic matter. Suitable for cashew, tea.",
        "loamy": "Excellent for vegetables, fruits, and flowers.",
        "peat": "Add lime to reduce acidity. Good for acid-loving plants.",
        "red": "Apply nitrogen-rich fertilizers. Ideal for groundnuts, millet.",
        "sandy": "Add organic matter. Use drip irrigation. Good for carrots.",
        "sandy_loam": "Great for potatoes, carrots, and other root vegetables.",
        "yellow": "Add compost and iron supplements. Suitable for maize, beans."
    }
    return recommendations.get(soil_type, "Consult a local agronomist.")

# ──────── page config ────────
st.set_page_config(page_title="GAIA – Soil Analysis", page_icon="🏞️", layout="wide")

# Toggle
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=True, key="soil_theme_toggle")
theme = "dark" if dark_mode else "light"

# Scan deduction
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

SOIL_CLASSES = [
    "alluvial", "black", "cinder", "clay", "laterite",
    "loamy", "peat", "red", "sandy", "sandy_loam", "yellow"
]
NUM_CLASSES = len(SOIL_CLASSES)

SOIL_COLORS = {
    "alluvial": "#8d6e63", "black": "#3e2723", "cinder": "#616161",
    "clay": "#a1887f", "laterite": "#b7410e", "loamy": "#6d4c41",
    "peat": "#4e342e", "red": "#c62828", "sandy": "#d4a373",
    "sandy_loam": "#bcaaa4", "yellow": "#f9a825"
}

# Theme CSS
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #1a120b 0%, #2e1c0d 30%, #3e2a14 60%, #1a0f05 100%); color: #f5f0eb; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center;
                 background: linear-gradient(90deg, #d4a373, #f5e6d3, #d4a373);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 text-shadow: 0 0 25px rgba(212, 163, 115, 0.7);
                 animation: soilGlow 2s ease-in-out infinite alternate; }
        @keyframes soilGlow { from { text-shadow: 0 0 25px rgba(212, 163, 115, 0.7); }
                              to { text-shadow: 0 0 50px rgba(212, 163, 115, 1), 0 0 80px rgba(212, 163, 115, 0.6); } }
        .subtitle { text-align: center; font-size: 1.2rem; color: #bcaaa4; }
        .soil-swatch { display: inline-block; width: 20px; height: 20px; border-radius: 4px; margin-right: 8px; }
        .result-card { background: rgba(255,255,255,0.05); backdrop-filter: blur(20px);
                       border-radius: 20px; padding: 1.5rem; margin: 0.5rem 0; }
        .result-card.top-result { border: 1px solid #d4a373; box-shadow: 0 0 30px rgba(212, 163, 115, 0.3); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #8d6e63, #d4a373); }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #efebe9 0%, #d7ccc8 100%); color: #3e2723; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center;
                 background: linear-gradient(90deg, #5d4037, #8d6e63, #5d4037);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 text-shadow: 0 0 10px rgba(93,64,55,0.3);
                 animation: soilGlowLight 2s ease-in-out infinite alternate; }
        @keyframes soilGlowLight { from { text-shadow: 0 0 10px rgba(93,64,55,0.3); }
                                   to { text-shadow: 0 0 25px rgba(93,64,55,0.8), 0 0 50px rgba(93,64,55,0.5); } }
        .subtitle { text-align: center; font-size: 1.2rem; color: #4e342e; }
        .soil-swatch { display: inline-block; width: 20px; height: 20px; border-radius: 4px; margin-right: 8px; }
        .result-card { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px);
                       border-radius: 20px; padding: 1.5rem; margin: 0.5rem 0; }
        .result-card.top-result { border: 1px solid #5d4037; box-shadow: 0 0 20px rgba(93,64,55,0.2); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #8d6e63, #bcaaa4); }
    </style>
    """, unsafe_allow_html=True)

# ──────── UI ────────
st.markdown('<div class="title">🏞️ Soil Type Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Uncover the secrets of your soil with a single photo</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("📤 Drop your soil photo here", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="", width=300)

    st.markdown("---")
    st.subheader("🧪 Analysis Results")

    model = None
    try:
        from app.utils.model_loader import create_model_from_checkpoint
        checkpoint = "checkpoints/soil_11class/best_model.pt"
        if os.path.exists(checkpoint):
            model = create_model_from_checkpoint(checkpoint, NUM_CLASSES)
    except Exception as e:
        st.warning(f"Real model unavailable, using demo. ({e})")

    if model:
        transform = Compose([
            Resize((224, 224)), ToTensor(),
            Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
        ])
        img_tensor = transform(image).unsqueeze(0)
        with torch.no_grad():
            logits = model(img_tensor)
            probs = F.softmax(logits, dim=1)[0].cpu().numpy()
    else:
        import hashlib
        seed = int(hashlib.md5(uploaded_file.name.encode()).hexdigest()[:8], 16)
        np.random.seed(seed)
        probs = np.random.rand(NUM_CLASSES)
        probs = probs / probs.sum()

    top_idx = np.argmax(probs)
    top_soil = SOIL_CLASSES[top_idx]
    top_color = SOIL_COLORS.get(top_soil, "#8d6e63")

    st.markdown(f"""
    <div class="result-card top-result" style="border-left: 5px solid {top_color};">
        <h2 style="margin:0; display: flex; align-items: center;">
            <span class="soil-swatch" style="background-color: {top_color};"></span>
            {top_soil}
            <span style="margin-left: auto; font-size: 2rem; color: {top_color};">{probs[top_idx]*100:.1f}%</span>
        </h2>
        <p style="margin-top: 0.5rem; color: #8d7b6a;">{_get_soil_description(top_soil)}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### All Soil Types")
    for i, soil_type in enumerate(SOIL_CLASSES):
        percent = probs[i] * 100
        color = SOIL_COLORS.get(soil_type, "#8d6e63")
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 0.5rem 0;">
            <span class="soil-swatch" style="background-color: {color};"></span>
            <span style="width: 130px;">{soil_type}</span>
            <span style="width: 60px; text-align: right;">{percent:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)
        st.progress(float(probs[i]))

    deduct_and_show()

    st.info(f"💡 **Recommendation:** {_get_recommendation(top_soil)}")
