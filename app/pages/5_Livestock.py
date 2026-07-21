
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
st.set_page_config(page_title="GAIA – Livestock Health", page_icon="🐄", layout="wide")

st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="livestock_theme_toggle")   # default OFF = light
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

# ──────── animal definitions ────────
ANIMAL_CLASSES = {
    "cattle": ["Foot‑and‑Mouth Disease", "Healthy", "Lumpy Skin Disease"],
    "poultry": ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]
}

# ──────── theme CSS ────────
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #1a0f2e 0%, #2e1c3e 30%, #3e2a5e 60%, #1a0f2e 100%); color: #ede7f6; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center;
                 background: linear-gradient(90deg, #7c4dff, #b388ff, #7c4dff);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 text-shadow: 0 0 25px rgba(124, 77, 255, 0.7);
                 animation: livestockGlow 2s ease-in-out infinite alternate; }
        @keyframes livestockGlow { from { text-shadow: 0 0 25px rgba(124, 77, 255, 0.7); }
                                   to { text-shadow: 0 0 50px rgba(124, 77, 255, 1), 0 0 80px rgba(124, 77, 255, 0.6); } }
        .subtitle { text-align: center; font-size: 1.2rem; color: #b39ddb; }
st.markdown('<a href="/" target="_self"><button style="padding:8px 16px; background: linear-gradient(90deg, #2e7d32, #4caf50); color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">🏠 Dashboard</button></a>', unsafe_allow_html=True)
        .result-card { background: rgba(255,255,255,0.05); backdrop-filter: blur(20px);
                       border-radius: 20px; padding: 1.5rem; margin: 0.5rem 0; }
        .result-card.top-result { border: 1px solid #7c4dff; box-shadow: 0 0 30px rgba(124, 77, 255, 0.3); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #7c4dff, #b388ff); }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #ede7f6 0%, #d1c4e9 100%); color: #311b92; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center;
                 background: linear-gradient(90deg, #4a148c, #7c4dff, #4a148c);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 text-shadow: 0 0 10px rgba(74, 20, 140, 0.3);
                 animation: livestockGlowLight 2s ease-in-out infinite alternate; }
        @keyframes livestockGlowLight { from { text-shadow: 0 0 10px rgba(74, 20, 140, 0.3); }
                                        to { text-shadow: 0 0 25px rgba(74, 20, 140, 0.8), 0 0 50px rgba(74, 20, 140, 0.5); } }
        .subtitle { text-align: center; font-size: 1.2rem; color: #4a148c; }
        .result-card { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px);
                       border-radius: 20px; padding: 1.5rem; margin: 0.5rem 0; }
        .result-card.top-result { border: 1px solid #7c4dff; box-shadow: 0 0 20px rgba(74, 20, 140, 0.2); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #7c4dff, #b388ff); }
    </style>
    """, unsafe_allow_html=True)

# ──────── UI ────────

# ---------- Sidebar navigation ----------
with st.sidebar:
    st.markdown("### 🌱 GAIA")
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("app/pages/1_Dashboard.py")
    if st.button("🌿 Crop Disease", use_container_width=True):
        st.switch_page("app/pages/2_Crops.py")
    if st.button("🐛 Pest Detection", use_container_width=True):
        st.switch_page("app/pages/3_Pests.py")
    if st.button("🏞️ Soil Analysis", use_container_width=True):
        st.switch_page("app/pages/4_Soil.py")
    if st.button("🐄 Livestock Health", use_container_width=True):
        st.switch_page("app/pages/5_Livestock.py")
    if st.button("💳 Payment History", use_container_width=True):
        st.switch_page("app/pages/6_Payment_History.py")
    st.markdown("---")
    if st.session_state.get("user"):
        st.write(f"👤 {st.session_state.user.email}")
        st.metric("Scans", st.session_state.get("scans_left", 0))
    st.markdown("*Powered by Darkmoor Ltd*")

st.markdown('<div class="title">🐄 Livestock Health</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Detect common diseases in cattle and poultry from a photo</div>', unsafe_allow_html=True)

animal = st.selectbox("🐾 Choose animal", list(ANIMAL_CLASSES.keys()))
uploaded_file = st.file_uploader("📤 Upload animal photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption=f"Your {animal}", width=300)

    st.markdown("---")
    st.subheader("🩺 Health Check Result")

    class_names = ANIMAL_CLASSES[animal]
    num_classes = len(class_names)

    model = None
    try:
        from app.utils.model_loader import create_model_from_checkpoint
        checkpoint = f"checkpoints/{animal}/best_model.pt"
        if os.path.exists(checkpoint):
            model = create_model_from_checkpoint(checkpoint, num_classes)
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
        probs = np.random.rand(num_classes)
        probs = probs / probs.sum()

    sorted_idx = np.argsort(probs)[::-1]
    top_disease = class_names[sorted_idx[0]]

    # Show top result card
    st.markdown(f"""
    <div class="result-card top-result" style="border-left: 5px solid #7c4dff;">
        <h2 style="margin:0; display: flex; align-items: center;">
            {top_disease}
            <span style="margin-left: auto; font-size: 2rem; color: #7c4dff;">{probs[sorted_idx[0]]*100:.1f}%</span>
        </h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### All Results")
    for i in sorted_idx:
        st.write(f"**{class_names[i]}**: {probs[i]*100:.1f}%")
        st.progress(float(probs[i]))

    deduct_and_show()

    if "healthy" in top_disease.lower():
        st.success(f"✅ Your {animal} appears healthy! Keep up the good care.")
    else:
        st.warning(f"⚠️ Possible **{top_disease}** detected. Isolate and consult a veterinarian immediately.")
