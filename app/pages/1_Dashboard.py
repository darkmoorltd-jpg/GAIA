import streamlit as st

st.set_page_config(page_title="GAIA – Dashboard", page_icon="🌱", layout="wide")
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e4efe9 100%); }
    .metric-card {
        background: white; border-radius: 15px; padding: 1.5rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05); text-align: center;
        margin: 0.5rem;
    }
    .metric-card h3 { color: #2e7d32; margin:0; font-size:2rem; }
    .metric-card p { color: #666; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div style="font-size:3rem;font-weight:800;text-align:center;background:linear-gradient(90deg,#2e7d32,#4caf50);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🌱 GAIA Dashboard</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:#555;font-size:1.2rem;">Global Agricultural Intelligence Assistant</p>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="metric-card"><h3>🌿</h3><p>Crops</p><h3>6</h3></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card"><h3>🐛</h3><p>Pests</p><h3>12</h3></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card"><h3>🏞️</h3><p>Soil Types</p><h3>7</h3></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="metric-card"><h3>🐄</h3><p>Livestock</p><h3>2</h3></div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 🚀 Get Started")
st.markdown("Navigate to **Diagnose** in the sidebar to check your crops, pests, soil, or livestock.")