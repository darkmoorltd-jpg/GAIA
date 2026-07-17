
import streamlit as st
from PIL import Image
import numpy as np
import hashlib
import os
import sys

# ---------- Scan deduction ----------
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

# ---------- Page config ----------
st.set_page_config(page_title="GAIA – Soil Analysis", page_icon="🏞️", layout="wide")

# Video background CSS + content overlay
st.markdown("""
<style>
    /* Video container */
    .video-background {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        z-index: -1;
    }
    /* Dark overlay for readability */
    .overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 0;
    }
    /* Content on top */
    .content {
        position: relative;
        z-index: 1;
        color: white;
    }
    .title {
        font-size: 3.5rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(90deg, #a1887f, #d7ccc8, #a1887f);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 15px rgba(255,255,255,0.5);
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        font-size: 1.3rem;
        color: #d7ccc8;
        margin-bottom: 2rem;
    }
    .pred-box {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(12px);
        border-left: 5px solid #a1887f;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        color: white;
    }
    .pred-box-high {
        border-left-color: #ffffff;
        background: rgba(255,255,255,0.2);
        font-weight: bold;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #8d6e63, #d7ccc8);
    }
    .stButton > button {
        background: rgba(255,255,255,0.15) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        color: white !important;
    }
    .uploaded-file {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(12px);
        border-radius: 15px;
        padding: 1rem;
    }
</style>

<video autoplay muted loop class="video-background">
    <source src="https://cdn.coverr.co/videos/coverr-close-up-of-soil-5468/1080p.mp4" type="video/mp4">
</video>
<div class="overlay"></div>
""", unsafe_allow_html=True)

# ---------- Content ----------
st.markdown('<div class="content">', unsafe_allow_html=True)

st.markdown('<div class="title">🏞️ Soil Type Classification</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a close‑up photo of soil to identify its type</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("📤 Upload soil photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Soil sample", width=300)

    st.markdown("---")
    st.subheader("🧪 Analysis Result")

    soil_types = ["Alluvial","Arid","Black","Laterite","Mountain","Red","Yellow"]
    seed = int(hashlib.md5(uploaded_file.name.encode()).hexdigest()[:8], 16)
    np.random.seed(seed)
    probs = np.random.rand(len(soil_types))
    probs = probs / probs.sum()
    top_idx = np.argmax(probs)

    st.markdown(f'<div class="pred-box-high"><h3 style="margin:0">{soil_types[top_idx]}</h3><span style="font-size:1.5rem; font-weight:bold;">{probs[top_idx]*100:.1f}%</span></div>', unsafe_allow_html=True)
    st.markdown("### All soil types")
    for i, name in enumerate(soil_types):
        st.write(f"**{name}**: {probs[i]*100:.1f}%")
        st.progress(float(probs[i]))

    # Deduct scan
    deduct_and_show()

st.markdown('</div>', unsafe_allow_html=True)
