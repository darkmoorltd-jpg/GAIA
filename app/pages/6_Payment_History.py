
import streamlit as st
from supabase import create_client, Client
import pandas as pd

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="GAIA – Payment History", page_icon="💳", layout="wide", initial_sidebar_state="expanded")

# Force sidebar visible on all pages
st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
    }
</style>
""", unsafe_allow_html=True)

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


# ---------- Universal Bottom Navigation ----------


# ---------- Universal Bottom Navigation (only existing pages) ----------
import os
pages_dir = os.path.join(os.path.dirname(__file__))
all_pages = {
    "🏠 Dashboard": "1_Dashboard.py",
    "🌿 Crops": "2_Crops.py",
    "🐛 Pests": "3_Pests.py",
    "🏞️ Soil": "4_Soil.py",
    "🐄 Livestock": "5_Livestock.py",
    "🛰️ Early Warning": "10_Early_Warning.py",
    "💳 Buy Scans": "9_Buy_Scans.py",
    "👤 Profile": "8_Profile.py",
    "📋 Payments": "6_Payment_History.py",
}
existing_links = []
for label, filename in all_pages.items():
    if os.path.exists(os.path.join(pages_dir, filename)):
        existing_links.append((label, f"pages/{filename}"))

if existing_links:
    st.markdown("---")
    st.markdown("### 🔗 Quick Navigation")
    cols = st.columns(len(existing_links))
    for i, (label, path) in enumerate(existing_links):
        with cols[i]:
            st.page_link(path, label=label)
