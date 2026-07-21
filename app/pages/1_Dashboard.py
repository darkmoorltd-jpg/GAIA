
import streamlit as st

st.set_page_config(page_title="GAIA – Dashboard", page_icon="🌱", layout="wide", initial_sidebar_state="expanded")

# Force sidebar visible on all pages
st.markdown("""

""", unsafe_allow_html=True)


# ---------- Light / Dark mode toggle ----------
if "theme" not in st.session_state:
    st.session_state.theme = "light"

st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=st.session_state.theme == "dark", key="dashboard_theme_toggle")

if dark_mode:
    st.session_state.theme = "light"
else:
    st.session_state.theme = "light"

# ---------- CSS for both themes ----------
if st.session_state.theme == "dark":
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            color: #ffffff;
        }
        header, footer {visibility: hidden;}
        .particles {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            z-index: -1; overflow: hidden;
        }
        .particle {
            position: absolute; background: rgba(76, 175, 80, 0.15);
            border-radius: 50%; animation: float 15s infinite ease-in-out;
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
            font-size: 5rem; font-weight: 900; text-align: center;
            background: linear-gradient(90deg, #00c853, #69f0ae, #00c853);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 20px rgba(0,200,83,0.6);
            margin-bottom: 0;
            animation: glow 2s ease-in-out infinite alternate;
        }
        @keyframes glow {
            from { text-shadow: 0 0 20px rgba(0,200,83,0.6); }
            to { text-shadow: 0 0 40px rgba(0,200,83,1), 0 0 80px rgba(0,200,83,0.8); }
        }
        .subtitle { text-align: center; font-size: 1.5rem; color: #b0bec5; margin-bottom: 2rem; }        .stButton > button {
            background: rgba(255,255,255,0.08) !important;
            backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
            border-radius: 20px !important;
            padding: 2rem 1rem !important;
            width: 100% !important;
            height: 120px !important;
            color: #ffffff !important;
            font-size: 1.3rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            white-space: pre-line !important;
            line-height: 1.5 !important;
        }
        .stButton > button:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0,200,83,0.3);
            border-color: #00c853 !important;
            background: rgba(0,200,83,0.15) !important;
        }
        .stat-item { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 1rem 2rem; backdrop-filter: blur(5px); text-align: center; }
        .stat-number { font-size: 2rem; font-weight: 700; color: #00c853; }
        .stat-label { color: #90a4ae; font-size: 0.9rem; }
        .footer { text-align: center; padding: 2rem; color: #78909c; border-top: 1px solid rgba(255,255,255,0.1); margin-top: 3rem; }
        .footer a { color: #00c853; text-decoration: none; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 50%, #fffde7 100%);
            color: #1b5e20;
        }
        header, footer {visibility: hidden;}
        .hero-title {
            font-size: 5rem; font-weight: 900; text-align: center;
            background: linear-gradient(90deg, #2e7d32, #66bb6a, #2e7d32);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 15px rgba(46,125,50,0.5);
            margin-bottom: 0;
            animation: glowLight 2s ease-in-out infinite alternate;
        }
        @keyframes glowLight {
            from { text-shadow: 0 0 15px rgba(46,125,50,0.5); }
            to { text-shadow: 0 0 30px rgba(46,125,50,1), 0 0 60px rgba(46,125,50,0.7); }
        }
        .subtitle { text-align: center; font-size: 1.5rem; color: #33691e; margin-bottom: 2rem; }
        .stButton > button {
            background: rgba(255,255,255,0.9) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(0,0,0,0.1) !important;
            border-radius: 20px !important;
            padding: 2rem 1rem !important;
            width: 100% !important;
            height: 120px !important;
            color: #1b5e20 !important;
            font-size: 1.3rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            white-space: pre-line !important;
            line-height: 1.5 !important;
        }
        .stButton > button:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(46,125,50,0.25);
            border-color: #2e7d32 !important;
            background: rgba(46,125,50,0.1) !important;
        }
        .stat-item { background: rgba(255,255,255,0.9); border-radius: 15px; padding: 1rem 2rem; text-align: center; }
        .stat-number { font-size: 2rem; font-weight: 700; color: #2e7d32; }
        .stat-label { color: #558b2f; font-size: 0.9rem; }
        .footer { text-align: center; padding: 2rem; color: #4e342e; border-top: 1px solid rgba(0,0,0,0.1); margin-top: 3rem; }
        .footer a { color: #2e7d32; text-decoration: none; }
        .particles { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ---------- Floating particles (dark mode only) ----------
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

# ---------- Sidebar Toggle (click if sidebar is hidden) ----------
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("☰ Menu", help="Show sidebar navigation"):
        st.markdown("""
        <script>
            // Force sidebar to open via JavaScript
            const sidebar = parent.document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                sidebar.style.display = 'block';
                sidebar.style.visibility = 'visible';
                sidebar.style.width = '280px';
            }
        </script>
        """, unsafe_allow_html=True)


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
    st.markdown('<div class="stat-item"><div class="stat-number">99.5%</div><div class="stat-label">Top Accuracy</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="stat-item"><div class="stat-number">152</div><div class="stat-label">Diagnostic Classes</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="stat-item"><div class="stat-number">24/7</div><div class="stat-label">Offline Ready</div></div>', unsafe_allow_html=True)

# ---------- Module Cards ----------
st.markdown("### 🚀 Quick Access")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🌿\n\nCrop Disease", key="crops", help="Identify diseases in 6+ crops"):
        st.switch_page("pages/2_Crops.py")
with col2:
    if st.button("🐛\n\nPest Detection\n(102 Species)", key="pests", help="Identify 102 insect pests with 99.5% accuracy"):
        st.switch_page("pages/3_Pests.py")
with col3:
    if st.button("🏞️\n\nSoil Analysis", key="soil", help="Classify 7 soil types"):
        st.switch_page("pages/4_Soil.py")
with col4:
    if st.button("🐄\n\nLivestock Health", key="livestock", help="Diagnose cattle and poultry diseases"):
        st.switch_page("pages/5_Livestock.py")

# ---------- Footer ----------
st.markdown("""
<div class="footer">
    Powered by <strong>Darkmoor Ltd</strong><br>
    <a href="mailto:darkmoorltd@gmail.com">darkmoorltd@gmail.com</a>
</div>
""", unsafe_allow_html=True)


# ---------- Universal Bottom Navigation (safe) ----------
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(6)
with cols[0]:
    st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]:
    st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]:
    st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]:
    st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]:
    st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]:
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
