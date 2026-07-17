
import streamlit as st

st.set_page_config(page_title="GAIA – Dashboard", page_icon="🌱", layout="wide")

# ---------- Custom CSS for the entire page ----------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: #ffffff;
    }
    header, footer {visibility: hidden;}
    .particles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        overflow: hidden;
    }
    .particle {
        position: absolute;
        background: rgba(76, 175, 80, 0.15);
        border-radius: 50%;
        animation: float 15s infinite ease-in-out;
    }
    .particle:nth-child(1) { width: 80px; height: 80px; left: 10%; top: 20%; animation-delay: 0s; }
    .particle:nth-child(2) { width: 60px; height: 60px; left: 80%; top: 60%; animation-delay: 3s; }
    .particle:nth-child(3) { width: 120px; height: 120px; left: 40%; top: 70%; animation-delay: 6s; }
    .particle:nth-child(4) { width: 50px; height: 50px; left: 70%; top: 10%; animation-delay: 9s; }
    .particle:nth-child(5) { width: 100px; height: 100px; left: 25%; top: 40%; animation-delay: 12s; }
    @keyframes float {
        0% { transform: translateY(0px) rotate(0deg); opacity: 0.5; }
        50% { transform: translateY(-30px) rotate(180deg); opacity: 0.8; }
        100% { transform: translateY(0px) rotate(360deg); opacity: 0.5; }
    }
    .hero-title {
        font-size: 5rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(90deg, #00c853, #69f0ae, #00c853);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(0,200,83,0.6);
        margin-bottom: 0;
        animation: glow 2s ease-in-out infinite alternate;
    }
    @keyframes glow {
        from { text-shadow: 0 0 20px rgba(0,200,83,0.6); }
        to { text-shadow: 0 0 40px rgba(0,200,83,1), 0 0 80px rgba(0,200,83,0.8); }
    }
    .subtitle {
        text-align: center;
        font-size: 1.5rem;
        color: #b0bec5;
        margin-bottom: 2rem;
    }
    .module-grid {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 2rem;
        margin: 2rem 0;
    }
    .module-card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 2rem;
        width: 200px;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .module-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0,200,83,0.3);
        border-color: #00c853;
    }
    .module-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    .module-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #ffffff;
    }
    .stats-bar {
        display: flex;
        justify-content: center;
        gap: 3rem;
        margin: 3rem 0;
    }
    .stat-item {
        text-align: center;
        background: rgba(255,255,255,0.05);
        border-radius: 15px;
        padding: 1rem 2rem;
        backdrop-filter: blur(5px);
    }
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #00c853;
    }
    .stat-label {
        color: #90a4ae;
        font-size: 0.9rem;
    }
    .footer {
        text-align: center;
        padding: 2rem;
        color: #78909c;
        border-top: 1px solid rgba(255,255,255,0.1);
        margin-top: 3rem;
    }
    .footer a {
        color: #00c853;
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Floating particles (pure CSS) ----------
st.markdown("""
<div class="particles">
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
</div>
""", unsafe_allow_html=True)

# ---------- Hero Section ----------
st.markdown('<div class="hero-title">GAIA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Global Agricultural Intelligence Assistant</div>', unsafe_allow_html=True)

# ---------- Lettuce image (centered, rounded) ----------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://images.unsplash.com/photo-1556801712-76c8eb07bbc9?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
             caption="", use_column_width=True)
    # Add a subtle glow effect to the image
    st.markdown("""
    <style>
        img {
            border-radius: 20px;
            box-shadow: 0 0 30px rgba(0,200,83,0.4);
        }
    </style>
    """, unsafe_allow_html=True)

# ---------- Stats Bar ----------
st.markdown('<div class="stats-bar">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="stat-item"><div class="stat-number">10+</div><div class="stat-label">Crop Models</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="stat-item"><div class="stat-number">94.9%</div><div class="stat-label">Top Accuracy</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="stat-item"><div class="stat-number">62</div><div class="stat-label">Diagnostic Classes</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="stat-item"><div class="stat-number">24/7</div><div class="stat-label">Offline Ready</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------- Module Cards (interactive) ----------
st.markdown('<div class="module-grid">', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🌿\n\nCrop Disease", key="crops", help="Identify diseases in crops"):
        st.switch_page("pages/2_Crops.py")
with col2:
    if st.button("🐛\n\nPest Detection", key="pests", help="Identify insects and pests"):
        st.switch_page("pages/3_Pests.py")
with col3:
    if st.button("🏞️\n\nSoil Analysis", key="soil", help="Classify soil types"):
        st.switch_page("pages/4_Soil.py")
with col4:
    if st.button("🐄\n\nLivestock Health", key="livestock", help="Diagnose cattle and poultry"):
        st.switch_page("pages/5_Livestock.py")

st.markdown('</div>', unsafe_allow_html=True)

# ---------- Footer ----------
st.markdown("""
<div class="footer">
    Powered by <strong>Darkmoor Ltd</strong><br>
    <a href="mailto:darkmoorltd@gmail.com">darkmoorltd@gmail.com</a>
</div>
""", unsafe_allow_html=True)
