import streamlit as st
from supabase import create_client, Client
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
@st.cache_resource
def init_supabase(): return create_client(SUPABASE_URL, SUPABASE_KEY)
st.set_page_config(page_title="GAIA – Verification History", page_icon="📋", layout="wide")
if "user" not in st.session_state or st.session_state.user is None: st.warning("Please log in first."); st.stop()
user = st.session_state.user; supabase = init_supabase()
st.markdown("<style>.stApp{background:linear-gradient(135deg,#f5f7fa,#e8f5e9)}.title{font-size:2.5rem;font-weight:800;text-align:center;color:#2e7d32}</style>", unsafe_allow_html=True)
st.markdown('<div class="title">📋 Verification & Payment History</div>', unsafe_allow_html=True)
history = supabase.table("farmer_verifications").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
if history.data and len(history.data) > 0:
    for h in history.data:
        status = h.get("status","?")
        emoji = "✅" if status=="approved" else ("⏳" if status=="pending" else "❌")
        with st.expander(f"{emoji} {status.upper()} — {h.get('created_at','')[:16]}"):
            st.write(f"Name: {h.get('full_name','N/A')}"); st.write(f"Phone: {h.get('phone','N/A')}"); st.write(f"State: {h.get('state','N/A')}")
else: st.info("No records yet.")
st.markdown("---")
cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[?]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
# ---------- Quick Navigation ----------
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(8)
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
    st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[6]:
    st.page_link("pages/10_Early_Warning.py", label="🛰️ Early Warning")
with cols[7]:
    st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[?]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")