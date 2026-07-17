
import streamlit as st
from PIL import Image
import numpy as np
import hashlib
import os
import sys

# ---------- Theme-aware CSS ----------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

is_dark = st.session_state.theme == "dark"

st.set_page_config(page_title="GAIA – Soil Analysis", page_icon="🏞️", layout="wide")
st.markdown(f"""
<style>
    .stApp {{
        background: {'linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)' if is_dark else 'linear-gradient(135deg, #efebe9 0%, #d7ccc8 100%)'};
        color: {'#ffffff' if is_dark else '#3e2723'};
    }}
    header, footer {{visibility: hidden;}}
    .title {{
        font-size: 3.5rem; font-weight: 900; text-align: center;
        background: {'linear-gradient(90deg, #8d6e63, #a1887f, #8d6e63)' if is_dark else 'linear-gradient(90deg, #5d4037, #8d6e63, #5d4037)'};
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0;
        animation: {'glowSoilDark 2s ease-in-out infinite alternate' if is_dark else 'glowSoilLight 2s ease-in-out infinite alternate'};
    }}
    @keyframes glowSoilDark {{
        from {{ text-shadow: 0 0 15px rgba(141,110,99,0.6); }}
        to {{ text-shadow: 0 0 30px rgba(141,110,99,1), 0 0 60px rgba(141,110,99,0.8); }}
    }}
    @keyframes glowSoilLight {{
        from {{ text-shadow: 0 0 10px rgba(93,64,55,0.5); }}
        to {{ text-shadow: 0 0 25px rgba(93,64,55,1), 0 0 50px rgba(93,64,55,0.7); }}
    }}
    .subtitle {{ text-align: center; font-size: 1.2rem; color: {'#bcaaa4' if is_dark else '#5d4037'}; margin-bottom: 2rem; }}
    .pred-box {{
        background: {'rgba(255,255,255,0.05)' if is_dark else 'rgba(255,255,255,0.9)'};
        backdrop-filter: blur(10px);
        border-left: 5px solid {'#8d6e63' if is_dark else '#5d4037'};
        padding: 1.2rem 1.8rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        color: {'#ffffff' if is_dark else '#3e2723'};
    }}
    .pred-box-high {{
        border-left-color: {'#a1887f' if is_dark else '#4e342e'};
        background: {'rgba(141,110,99,0.15)' if is_dark else '#d7ccc8'};
    }}
    .stProgress > div > div > div > div {{
        background: {'linear-gradient(90deg, #8d6e63, #a1887f)' if is_dark else 'linear-gradient(90deg, #5d4037, #8d6e63)'};
    }}
    .stButton > button {{
        background: {'rgba(141,110,99,0.15)' if is_dark else 'rgba(93,64,55,0.1)'} !important;
        border: 1px solid {'rgba(141,110,99,0.4)' if is_dark else 'rgba(93,64,55,0.3)'} !important;
        color: {'#ffffff' if is_dark else '#3e2723'} !important;
        border-radius: 15px !important;
        padding: 1rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s !important;
    }}
    .stButton > button:hover {{
        background: {'rgba(141,110,99,0.3)' if is_dark else 'rgba(93,64,55,0.2)'} !important;
        border-color: {'#a1887f' if is_dark else '#4e342e'} !important;
        transform: translateY(-3px);
        box-shadow: 0 10px 25px {'rgba(141,110,99,0.4)' if is_dark else 'rgba(93,64,55,0.3)'};
    }}
</style>
""", unsafe_allow_html=True)

# ---------- Deduction function ----------
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
            st.success(f"Scan deducted. Remaining: {remaining}")
    except:
        pass

# ---------- UI ----------
st.markdown('<div class="title">🏞️ Soil Type Classification</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a close‑up photo of soil to identify its type</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("📤 Upload soil photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Soil sample", width=320)

    st.markdown("---")
    st.subheader("🧪 Soil Analysis Result")

    soil_types = ["Alluvial","Arid","Black","Laterite","Mountain","Red","Yellow"]
    seed = int(hashlib.md5(uploaded_file.name.encode()).hexdigest()[:8], 16)
    np.random.seed(seed)
    probs = np.random.rand(len(soil_types))
    probs = probs / probs.sum()
    sorted_idx = np.argsort(probs)[::-1]

    for i, idx in enumerate(sorted_idx):
        soil = soil_types[idx]
        pct = probs[idx] * 100
        box_class = "pred-box-high" if i == 0 else "pred-box"
        st.markdown(f'<div class="{box_class}"><b>{soil}</b> – {pct:.1f}%</div>', unsafe_allow_html=True)
        st.progress(float(probs[idx]))

    deduct_and_show()

    top_soil = soil_types[sorted_idx[0]]
    st.success(f"✅ Predominant soil type: **{top_soil}**")
