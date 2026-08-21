import pandas as pd
import streamlit as st
# Allow demo mode
from supabase import create_client
supabase = create_client(
    st.secrets["supabase"]["url"],
    st.secrets["supabase"]["key"])
try:
    session = supabase.auth.get_session()
    user = session.user if session else None
except BaseException:
    from supabase import create_client, Client

user = st.session_state.get("user", None)
if user is None:
    st.warning("Please log in first.")
    st.stop()
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]


@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


st.set_page_config(
    page_title="GAIA – Payment History",
    page_icon="💳",
    layout="wide")

st.session_state["user"] = None
user_id = user.id
supabase = init_supabase()

st.title("💳 Payment History")

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
    df["Paid At"] = pd.to_datetime(
        df["Paid At"]).dt.strftime("%d %b %Y, %H:%M")
    st.dataframe(df, use_container_width=True)

st.markdown("---")
st.caption("Payments are processed securely by Paystack.")


# ---------- Quick Navigation ----------
st.markdown("---")

# ============================================
# FULL NAVIGATION
# ============================================
st.markdown("---")
st.markdown("### Quick Navigation")
cols = st.columns(10)
with cols[0]:
    st.page_link("pages/1_Dashboard.py", label="Dashboard")
with cols[1]:
   st.page_link("pages/2_Crops.py", label="Crops")
with cols[2]:
    st.page_link("pages/3_Pests.py", label="Pests")
with cols[3]:
   st.page_link("pages/4_Soil.py", label="Soil")
with cols[4]:
    st.page_link("pages/5_Livestock.py", label="Livestock")
with cols[5]:
   st.page_link("pages/17_Video_Scan.py", label="Video Scan")
with cols[6]:
    st.page_link("pages/19_Satellite.py", label="Satellite")
with cols[7]:
   st.page_link("pages/18_Voice_Agronomist.py", label="Voice AI")
with cols[8]:
    st.page_link("pages/9_Buy_Scans.py", label="Buy Scans")
with cols[9]:
   st.page_link("pages/10_Early_Warning.py", label="Alerts")

st.markdown("### More Features")
cols2 = st.columns(10)
with cols2[0]:
    st.page_link("pages/11_Verify_Farmer.py", label="Verify")
with cols2[1]:
   st.page_link("pages/12_Verification_History.py", label="History")
with cols2[2]:
    st.page_link("pages/14_Wallet.py", label="Wallet")
with cols2[3]:
   st.page_link("pages/15_Badges.py", label="Badges")
with cols2[4]:
    st.page_link("pages/16_Chat.py", label="Chat")
with cols2[5]:
   st.page_link("pages/20_Marketplace.py", label="Market")
with cols2[6]:
    st.page_link("pages/21_Crop_Insurance.py", label="Insurance")
with cols2[7]:
   st.page_link("pages/6_Payment_History.py", label="Payments")
with cols2[8]:
    st.page_link("pages/8_Profile.py", label="Profile")
with cols2[9]:
   st.page_link("pages/13_Help.py", label="Help")
