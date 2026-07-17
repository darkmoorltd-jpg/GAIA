
import streamlit as st

st.set_page_config(page_title="GAIA – Dashboard", page_icon="🌱", layout="wide")

# ---------- Theme toggle (session state) ----------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ---------- CSS for toggle and both themes ----------
st.markdown(f"""
<style>
    /* Hide the default checkbox */
    .theme-toggle {{
        position: fixed;
        top: 1.5rem;
        right: 2rem;
        z-index: 100;
    }}
    .theme-toggle input {{
        display: none;
    }}
    .toggle-label {{
        cursor: pointer;
        width: 60px;
        height: 30px;
        background: {'#fdd835' if st.session_state.theme == 'dark' else '#90a4ae'};
        border-radius: 30px;
        position: relative;
        display: inline-block;
        box-shadow: 0 0 10px rgba(0,0,0,0.3);
        transition: background 0.3s;
    }}
    .toggle-label::after {{
        content: "{'☀️' if st.session_state.theme == 'dark' else '🌙'}";
        font-size: 18px;
        position: absolute;
        top: 2px;
        left: {'32px' if st.session_state.theme == 'dark' else '4px'};
        transition: all 0.3s;
    }}

    /* ---- Dark Theme ---- */
    .stApp {{
        background: {'linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)' if st.session_state.theme == 'dark' else 'linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 50%, #fffde7 100%)'};
        color: {'#ffffff' if st.session_state.theme == 'dark' else '#1b5e20'};
    }}
    header, footer {{visibility: hidden;}}

    .hero-title {{
        font-size: 5rem; font-weight: 900; text-align: center;
        background: {'linear-gradient(90deg, #00c853, #69f0ae, #00c853)' if st.session_state.theme == 'dark' else 'linear-gradient(90deg, #2e7d32, #66bb6a, #2e7d32)'};
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0;
        animation: {'glowDark 2s ease-in-out infinite alternate' if st.session_state.theme == 'dark' else 'glowLight 2s ease-in-out infinite alternate'};
    }}

    @keyframes glowDark {{
        from {{ text-shadow: 0 0 20px rgba(0,200,83,0.6); }}
        to {{ text-shadow: 0 0 40px rgba(0,200,83,1), 0 0 80px rgba(0,200,83,0.8); }}
    }}
    @keyframes glowLight {{
        from {{ text-shadow: 0 0 15px rgba(46,125,50,0.5); }}
        to {{ text-shadow: 0 0 30px rgba(46,125,50,1), 0 0 60px rgba(46,125,50,0.7); }}
    }}

    .subtitle {{ text-align: center; font-size: 1.5rem; color: {'#b0bec5' if st.session_state.theme == 'dark' else '#33691e'}; margin-bottom: 2rem; }}

    .stButton > button {{
        background: {'rgba(255,255,255,0.08)' if st.session_state.theme == 'dark' else 'rgba(255,255,255,0.9)'} !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid {'rgba(255,255,255,0.15)' if st.session_state.theme == 'dark' else 'rgba(0,0,0,0.1)'} !important;
        border-radius: 20px !important;
        padding: 2rem 1rem !important;
        width: 100% !important;
        height: 120px !important;
        color: {'#ffffff' if st.session_state.theme == 'dark' else '#1b5e20'} !important;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        white-space: pre-line !important;
        line-height: 1.5 !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-8px);
        box-shadow: 0 20px 40px {'rgba(0,200,83,0.3)' if st.session_state.theme == 'dark' else 'rgba(46,125,50,0.25)'};
        border-color: {'#00c853' if st.session_state.theme == 'dark' else '#2e7d32'} !important;
    }}

    .stat-item {{ background: {'rgba(255,255,255,0.05)' if st.session_state.theme == 'dark' else 'rgba(255,255,255,0.9)'}; border-radius: 15px; padding: 1rem 2rem; text-align: center; }}
    .stat-number {{ font-size: 2rem; font-weight: 700; color: {'#00c853' if st.session_state.theme == 'dark' else '#2e7d32'}; }}
    .stat-label {{ color: {'#90a4ae' if st.session_state.theme == 'dark' else '#558b2f'}; font-size: 0.9rem; }}
    .footer {{ text-align: center; padding: 2rem; color: {'#78909c' if st.session_state.theme == 'dark' else '#4e342e'}; border-top: 1px solid {'rgba(255,255,255,0.1)' if st.session_state.theme == 'dark' else 'rgba(0,0,0,0.1)'}; margin-top: 3rem; }}
    .footer a {{ color: {'#00c853' if st.session_state.theme == 'dark' else '#2e7d32'}; text-decoration: none; }}
</style>
""", unsafe_allow_html=True)

# ---------- Toggle (checkbox styled as switch) ----------
with st.container():
    st.markdown('<div class="theme-toggle">', unsafe_allow_html=True)
    toggle = st.checkbox("", value=(st.session_state.theme == "light"), key="theme_toggle")
    st.markdown('</div>', unsafe_allow_html=True)

# Update theme based on checkbox
if toggle:
    st.session_state.theme = "light"
else:
    st.session_state.theme = "dark"

# ---------- Hero Section ----------
st.markdown('<div class="hero-title">GAIA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Global Agricultural Intelligence Assistant</div>', unsafe_allow_html=True)

# ---------- Lettuce image ----------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://images.unsplash.com/photo-1556801712-76c8eb07bbc9?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
             caption="", use_column_width=True)

# ---------- Stats Bar ----------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="stat-item"><div class="stat-number">10+</div><div class="stat-label">Crop Models</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="stat-item"><div class="stat-number">94.9%</div><div class="stat-label">Top Accuracy</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="stat-item"><div class="stat-number">62</div><div class="stat-label">Diagnostic Classes</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="stat-item"><div class="stat-number">24/7</div><div class="stat-label">Offline Ready</div></div>', unsafe_allow_html=True)

# ---------- Module Cards ----------
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

# ---------- Footer ----------
st.markdown("""
<div class="footer">
    Powered by <strong>Darkmoor Ltd</strong><br>
    <a href="mailto:darkmoorltd@gmail.com">darkmoorltd@gmail.com</a>
</div>
""", unsafe_allow_html=True)
