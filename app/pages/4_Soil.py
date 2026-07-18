
import streamlit as st
from PIL import Image
import numpy as np
import hashlib
import time
import os
import sys

# ---------- Theme toggle ----------
st.set_page_config(page_title="GAIA – Soil Analysis", page_icon="🏞️", layout="wide")

# Custom toggle styling
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="soil_theme_toggle")

if dark_mode:
    theme = "dark"
else:
    theme = "light"

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

# ---------- Soil type color palette ----------
SOIL_COLORS = {
    "Alluvial": "#8d6e63",
    "Arid": "#d4a373",
    "Black": "#3e2723",
    "Laterite": "#b7410e",
    "Mountain": "#78909c",
    "Red": "#c62828",
    "Yellow": "#f9a825"
}

SOIL_TYPES = list(SOIL_COLORS.keys())

# ---------- Theme-dependent CSS ----------
if theme == "dark":
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #1a120b 0%, #2e1c0d 30%, #3e2a14 60%, #1a0f05 100%);
            color: #f5f0eb;
        }
        /* header and footer are NOT hidden – sidebar will be visible */
        
        .soil-particle {
            position: fixed; border-radius: 50%;
            background: radial-gradient(circle, rgba(139, 119, 90, 0.4), transparent);
            animation: soilFloat 8s infinite ease-in-out; z-index: 0; pointer-events: none;
        }
        .soil-particle:nth-child(1) { width: 150px; height: 150px; top: 10%; left: 5%; animation-delay: 0s; }
        .soil-particle:nth-child(2) { width: 100px; height: 100px; top: 60%; left: 85%; animation-delay: 2s; }
        .soil-particle:nth-child(3) { width: 200px; height: 200px; top: 75%; left: 15%; animation-delay: 4s; }
        .soil-particle:nth-child(4) { width: 80px; height: 80px; top: 20%; left: 70%; animation-delay: 6s; }
        .soil-particle:nth-child(5) { width: 120px; height: 120px; top: 50%; left: 40%; animation-delay: 5s; }
        @keyframes soilFloat {
            0% { transform: translateY(0px) scale(1); opacity: 0.3; }
            50% { transform: translateY(-40px) scale(1.2); opacity: 0.6; }
            100% { transform: translateY(0px) scale(1); opacity: 0.3; }
        }
        
        .scan-ring {
            position: absolute; top: 50%; left: 50%;
            width: 300px; height: 300px; border-radius: 50%;
            border: 3px solid rgba(212, 163, 115, 0.6);
            transform: translate(-50%, -50%);
            animation: scanPulse 2s infinite ease-out; z-index: 2; pointer-events: none;
        }
        .scan-ring:nth-child(2) { animation-delay: 0.7s; }
        .scan-ring:nth-child(3) { animation-delay: 1.4s; }
        @keyframes scanPulse {
            0% { width: 100px; height: 100px; opacity: 1; }
            100% { width: 400px; height: 400px; opacity: 0; }
        }
        
        .title {
            font-size: 3.5rem; font-weight: 900; text-align: center;
            background: linear-gradient(90deg, #d4a373, #f5e6d3, #d4a373);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 25px rgba(212, 163, 115, 0.7);
            margin-bottom: 0.5rem; position: relative; z-index: 1;
            animation: soilGlow 2s ease-in-out infinite alternate;
        }
        @keyframes soilGlow {
            from { text-shadow: 0 0 25px rgba(212, 163, 115, 0.7); }
            to { text-shadow: 0 0 50px rgba(212, 163, 115, 1), 0 0 80px rgba(212, 163, 115, 0.6); }
        }
        .subtitle { text-align: center; font-size: 1.2rem; color: #bcaaa4; margin-bottom: 2rem; position: relative; z-index: 1; }
        
        .stFileUploader { position: relative; z-index: 3; }
        .stFileUploader > div {
            background: rgba(255,255,255,0.05) !important; backdrop-filter: blur(12px) !important;
            border: 2px dashed rgba(212, 163, 115, 0.4) !important; border-radius: 20px !important;
            padding: 2rem !important; transition: all 0.3s ease;
        }
        .stFileUploader > div:hover {
            border-color: #d4a373 !important; background: rgba(212, 163, 115, 0.1) !important;
        }
        
        .stImage img { border-radius: 20px; box-shadow: 0 0 40px rgba(212, 163, 115, 0.3); }
        
        .soil-result-card {
            background: rgba(255,255,255,0.05); backdrop-filter: blur(20px);
            border: 1px solid rgba(212, 163, 115, 0.2); border-radius: 20px;
            padding: 1.5rem; margin: 0.5rem 0; transition: all 0.3s ease; position: relative; overflow: hidden;
        }
        .soil-result-card::before {
            content: ''; position: absolute; top: 0; left: 0; width: 5px; height: 100%; border-radius: 3px;
        }
        .soil-result-card.top-result { border-color: #d4a373; box-shadow: 0 0 30px rgba(212, 163, 115, 0.3); }
        .soil-result-card.top-result::before { background: #d4a373; }
        
        .soil-swatch {
            display: inline-block; width: 20px; height: 20px; border-radius: 4px;
            margin-right: 8px; vertical-align: middle; box-shadow: 0 0 10px rgba(0,0,0,0.5);
        }
        
        .stProgress > div > div > div > div { border-radius: 10px; transition: width 1s ease; }
        
        .action-box {
            background: rgba(212, 163, 115, 0.15); border: 1px solid rgba(212, 163, 115, 0.3);
            border-radius: 15px; padding: 1.5rem; text-align: center; margin-top: 1rem;
            backdrop-filter: blur(10px);
        }
    </style>
    
    <div class="soil-particle"></div>
    <div class="soil-particle"></div>
    <div class="soil-particle"></div>
    <div class="soil-particle"></div>
    <div class="soil-particle"></div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #efebe9 0%, #d7ccc8 100%);
            color: #3e2723;
        }
        /* header and footer are NOT hidden */
        .soil-particle { display: none; }
        .scan-ring { display: none; }
        .title {
            font-size: 3.5rem; font-weight: 900; text-align: center;
            background: linear-gradient(90deg, #5d4037, #8d6e63, #5d4037);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 10px rgba(93,64,55,0.3);
            margin-bottom: 0.5rem;
            animation: soilGlowLight 2s ease-in-out infinite alternate;
        }
        @keyframes soilGlowLight {
            from { text-shadow: 0 0 10px rgba(93,64,55,0.3); }
            to { text-shadow: 0 0 25px rgba(93,64,55,0.8), 0 0 50px rgba(93,64,55,0.5); }
        }
        .subtitle { text-align: center; font-size: 1.2rem; color: #4e342e; margin-bottom: 2rem; }
        
        .stFileUploader > div {
            background: rgba(255,255,255,0.8) !important; backdrop-filter: blur(10px) !important;
            border: 2px dashed rgba(93,64,55,0.3) !important; border-radius: 20px !important;
            padding: 2rem !important;
        }
        .stFileUploader > div:hover {
            border-color: #5d4037 !important; background: rgba(141,110,99,0.1) !important;
        }
        
        .stImage img { border-radius: 20px; box-shadow: 0 0 20px rgba(0,0,0,0.2); }
        
        .soil-result-card {
            background: rgba(255,255,255,0.8); backdrop-filter: blur(10px);
            border: 1px solid rgba(0,0,0,0.1); border-radius: 20px;
            padding: 1.5rem; margin: 0.5rem 0; transition: all 0.3s ease;
        }
        .soil-result-card.top-result { border-color: #5d4037; box-shadow: 0 0 20px rgba(93,64,55,0.2); }
        .soil-swatch {
            display: inline-block; width: 20px; height: 20px; border-radius: 4px;
            margin-right: 8px; vertical-align: middle; box-shadow: 0 0 5px rgba(0,0,0,0.2);
        }
        .stProgress > div > div > div > div { border-radius: 10px; }
        .action-box {
            background: rgba(141,110,99,0.1); border: 1px solid rgba(93,64,55,0.2);
            border-radius: 15px; padding: 1.5rem; text-align: center; margin-top: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

# ---------- Hero Section ----------
st.markdown('<div class="title">🏞️ Soil Type Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Uncover the secrets of your soil with a single photo</div>', unsafe_allow_html=True)

# ---------- Upload Section ----------
uploaded_file = st.file_uploader("📤 Drop your soil photo here", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(image, caption="", use_column_width=True)
        if theme == "dark":
            st.markdown("""
            <div style="position:relative; height:0;">
                <div class="scan-ring"></div>
                <div class="scan-ring"></div>
                <div class="scan-ring"></div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🧪 Analysis Results")

    # Generate demo predictions
    seed = int(hashlib.md5(uploaded_file.name.encode()).hexdigest()[:8], 16)
    np.random.seed(seed)
    probs = np.random.rand(len(SOIL_TYPES))
    probs = probs / probs.sum()
    top_idx = np.argmax(probs)

    top_soil = SOIL_TYPES[top_idx]
    top_color = SOIL_COLORS[top_soil]
    st.markdown(f"""
    <div class="soil-result-card top-result" style="border-left: 5px solid {top_color};">
        <h2 style="margin:0; display: flex; align-items: center;">
            <span class="soil-swatch" style="background-color: {top_color};"></span>
            {top_soil}
            <span style="margin-left: auto; font-size: 2rem; color: {top_color};">{probs[top_idx]*100:.1f}%</span>
        </h2>
        <p style="margin-top: 0.5rem; color: #8d7b6a;">
            {_get_soil_description(top_soil)}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### All Soil Types")
    for i, (soil_type, color) in enumerate(SOIL_COLORS.items()):
        percent = probs[i] * 100
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 0.5rem 0;">
            <span class="soil-swatch" style="background-color: {color};"></span>
            <span style="width: 130px;">{soil_type}</span>
            <span style="width: 60px; text-align: right;">{percent:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)
        st.progress(float(probs[i]))

    deduct_and_show()

    st.markdown(f"""
    <div class="action-box">
        <h3 style="color: {top_color}; margin: 0;">💡 Recommendation</h3>
        <p style="margin-top: 0.5rem;">{_get_recommendation(top_soil)}</p>
    </div>
    """, unsafe_allow_html=True)

else:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="height: 300px; display: flex; align-items: center; justify-content: center; 
                    background: rgba(255,255,255,{'0.03' if theme=='dark' else '0.8'}); border-radius: 20px; 
                    backdrop-filter: blur(10px); border: 2px dashed rgba(212, 163, 115, 0.3);">
            <p style="color: {'#8d7b6a' if theme=='dark' else '#5d4037'}; font-size: 1.2rem; text-align: center;">
                🌱 Your soil scan will appear here<br>
                <span style="font-size: 0.9rem;">Upload a photo to begin analysis</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

# ---------- Helper functions ----------
def _get_soil_description(soil_type):
    descriptions = {
        "Alluvial": "Rich, fertile soil deposited by rivers. Excellent for agriculture.",
        "Arid": "Dry, sandy soil found in desert regions. Low organic matter.",
        "Black": "Dark, nutrient-rich soil. High water retention. Great for cotton.",
        "Laterite": "Iron-rich, weathered soil. Common in tropical regions.",
        "Mountain": "Rocky, well-drained soil. Found in hilly and mountainous areas.",
        "Red": "Iron oxide-rich soil. Good drainage. Suitable for groundnuts and millet.",
        "Yellow": "Moderately fertile soil. Contains hydrated iron oxides."
    }
    return descriptions.get(soil_type, "")

def _get_recommendation(soil_type):
    recommendations = {
        "Alluvial": "Ideal for rice, wheat, sugarcane. Add organic compost for best results.",
        "Arid": "Use drought-resistant crops like millet, sorghum. Consider drip irrigation.",
        "Black": "Perfect for cotton, soybeans. Maintain moisture with mulching.",
        "Laterite": "Add lime and organic matter. Suitable for cashew, tea, coffee.",
        "Mountain": "Terrace farming recommended. Good for potatoes, tea, and fruit orchards.",
        "Red": "Apply nitrogen-rich fertilizers. Ideal for groundnuts, millet, and pulses.",
        "Yellow": "Add compost and iron supplements. Suitable for maize, beans, and vegetables."
    }
    return recommendations.get(soil_type, "Consult a local agronomist for specific advice.")
