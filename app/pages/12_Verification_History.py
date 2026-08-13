import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

@st.cache_resource
def init_supabase(): return create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="GAIA – Verification History", page_icon="📋", layout="wide")
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = init_supabase()

st.markdown("<style>.stApp{background:linear-gradient(135deg,#f5f7fa,#e8f5e9)}.title{font-size:2.5rem;font-weight:800;text-align:center;color:#2e7d32}</style>", unsafe_allow_html=True)
st.markdown('<div class="title">📋 Verification & Payment History</div>', unsafe_allow_html=True)

history = supabase.table("farmer_verifications").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()

if history.data and len(history.data) > 0:
    for h in history.data:
        status = h.get("status", "?")
        emoji = "✅" if status == "approved" else ("⏳" if status == "pending" else "❌")
        with st.expander(f"{emoji} {status.upper()} — {str(h.get('created_at',''))[:16]}"):
            st.write(f"Name: {h.get('full_name','N/A')}")
            st.write(f"Phone: {h.get('phone','N/A')}")
            st.write(f"State: {h.get('state','N/A')}")
else:
    st.info("No records yet.")
