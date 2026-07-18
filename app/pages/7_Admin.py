
import streamlit as st
from supabase import create_client, Client
import pandas as pd

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="GAIA – Admin", page_icon="🔐", layout="wide")

ADMIN_EMAIL = "darkmoorltd@gmail.com"
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

if st.session_state.user.email != ADMIN_EMAIL:
    st.error("Access denied. Admin only.")
    st.stop()

st.title("🔐 GAIA Admin Dashboard")
supabase = init_supabase()

col1, col2, col3, col4 = st.columns(4)

try:
    user_scans = supabase.table("user_scans").select("user_id, scans_remaining, plan").execute()
    total_users = len(user_scans.data) if user_scans.data else 0
    total_scans_used = sum(30 - row["scans_remaining"] for row in user_scans.data) if user_scans.data else 0
    free_users = sum(1 for row in user_scans.data if row["plan"] == "free") if user_scans.data else 0
    paid_users = sum(1 for row in user_scans.data if row["plan"] != "free") if user_scans.data else 0
except Exception as e:
    total_users = total_scans_used = free_users = paid_users = 0
    st.error(f"Error fetching user data: {e}")

col1.metric("Total Users", total_users)
col2.metric("Total Scans Used", total_scans_used)
col3.metric("Free Users", free_users)
col4.metric("Paid Users", paid_users)

st.markdown("---")
st.subheader("💳 Recent Payments")
try:
    payments = supabase.table("payment_history").select("*").order("paid_at", desc=True).limit(20).execute()
    if payments.data:
        df_payments = pd.DataFrame(payments.data)
        df_payments["amount"] = df_payments["amount"].apply(lambda x: f"${x:.2f}")
        df_payments["paid_at"] = pd.to_datetime(df_payments["paid_at"]).dt.strftime("%d %b %Y, %H:%M")
        st.dataframe(df_payments, use_container_width=True)
        total_revenue = sum(float(row["amount"]) for row in payments.data)
        st.metric("Total Revenue", f"${total_revenue:.2f}")
    else:
        st.info("No payments yet.")
except Exception as e:
    st.error(f"Error fetching payments: {e}")

st.markdown("---")
st.subheader("📊 User Scans Overview")
if user_scans and user_scans.data:
    df_users = pd.DataFrame(user_scans.data)
    df_users["scans_used"] = 30 - df_users["scans_remaining"]
    st.bar_chart(df_users.set_index("user_id")["scans_used"])
else:
    st.info("No scan data available.")

st.caption("Data refreshes on page load.")
