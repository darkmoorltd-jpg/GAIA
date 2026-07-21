
import streamlit as st
from supabase import create_client, Client
import pandas as pd

def bottom_nav():
    st.markdown("---")
    st.markdown("### 🚀 Quick Navigation")
    cols = st.columns(8)
    with cols[0]:
        if st.button("🌿 Crops", key="bn_crops"): st.switch_page("pages/2_Crops.py")
    with cols[1]:
        if st.button("🐛 Pests", key="bn_pests"): st.switch_page("pages/3_Pests.py")
    with cols[2]:
        if st.button("🏞️ Soil", key="bn_soil"): st.switch_page("pages/4_Soil.py")
    with cols[3]:
        if st.button("🐄 Livestock", key="bn_livestock"): st.switch_page("pages/5_Livestock.py")
    with cols[4]:
        if st.button("💳 Buy Scans", key="bn_buy"): st.switch_page("pages/9_Buy_Scans.py")
    with cols[5]:
        if st.button("📋 Payments", key="bn_payments"): st.switch_page("pages/6_Payment_History.py")
    with cols[6]:
        if st.button("🔐 Admin", key="bn_admin"): st.switch_page("pages/7_Admin.py")
    with cols[7]:
        if st.button("🚪 Logout", key="bn_logout"):
            from supabase import create_client
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
            supabase = create_client(url, key)
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()


SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="GAIA – Payment History", page_icon="💳", layout="wide", initial_sidebar_state="expanded")

# Force sidebar visible on all pages
st.markdown("""

""", unsafe_allow_html=True)


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

st.title("💳 Payment History")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in to view your payment history.")
    st.stop()

user_id = st.session_state.user.id
supabase = init_supabase()

try:
    res = supabase.table("payment_history") \
        .select("amount, scans_added, plan, reference, paid_at") \
        .eq("user_id", user_id) \
        .order("paid_at", desc=True) \
        .execute()
    payments = res.data
except Exception as e:
    payments = []
    st.error(f"Could not load payment history: {e}")

if not payments:
    st.info("No payments yet.")
else:
    df = pd.DataFrame(payments)
    df.columns = ["Amount", "Scans Added", "Plan", "Reference", "Paid At"]
    df["Amount"] = df["Amount"].apply(lambda x: f"${x:.2f}")
    df["Paid At"] = pd.to_datetime(df["Paid At"]).dt.strftime("%d %b %Y, %H:%M")
    st.dataframe(df, use_container_width=True)

st.markdown("---")
st.caption("Payments are processed securely by Paystack.")


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
