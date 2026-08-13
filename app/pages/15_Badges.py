import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import uuid
from app.utils.phone_util import normalize_phone
import requests
from datetime import datetime, timedelta

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_PUBLIC = "pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057"
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

def verify_payment(ref):
    r = requests.get(f"https://api.paystack.co/transaction/verify/{ref}",
                     headers={"Authorization": f"Bearer {PAYSTACK_SECRET}"}, timeout=10)
    if r.status_code == 200:
        d = r.json()
        if d.get("status") and d["data"]["status"] == "success":
            return {"ok": True, "amount": d["data"]["amount"] / 100}
    return {"ok": False}

BADGES = {
    "bronze":  {"name": "Bronze",  "emoji": "🥉", "price": "N500",   "kobo": 50000,  "loans": "Up to N50,000"},
    "silver":  {"name": "Silver",  "emoji": "🥈", "price": "N1,500", "kobo": 150000, "loans": "Up to N200,000"},
    "gold":    {"name": "Gold",    "emoji": "🥇", "price": "N3,000", "kobo": 300000, "loans": "Up to N500,000"},
    "platinum":{"name": "Platinum","emoji": "💎", "price": "N5,000", "kobo": 500000, "loans": "Up to N2,000,000"},
}

st.set_page_config(page_title="GAIA – Badges", page_icon="🏅", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
db = get_service()

# Check if user is verified
verify = db.table("farmer_verifications").select("status").eq("user_id", user.id).execute()
is_verified = verify.data and verify.data[0].get("status") == "approved"

if not is_verified:
    st.warning("You need to verify your identity first. Go to **Verify Farmer** page.")
    st.page_link("pages/11_Verify_Farmer.py", label="Go to Verification")
    st.stop()

# Get current badge
badge_res = db.table("badge_subscriptions").select("*").eq("user_id", user.id).execute()
current_badge = badge_res.data[0] if badge_res.data else None

# ============================================
# FULL NAVIGATION
# ============================================
st.markdown("---")
st.markdown("### Quick Navigation")
cols = st.columns(10)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="Livestock")
with cols[5]: st.page_link("pages/17_Video_Scan.py", label="Video Scan")
with cols[6]: st.page_link("pages/19_Satellite.py", label="Satellite")
with cols[7]: st.page_link("pages/18_Voice_Agronomist.py", label="Voice AI")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="Buy Scans")
with cols[9]: st.page_link("pages/10_Early_Warning.py", label="Alerts")

st.markdown("### More Features")
cols2 = st.columns(10)
with cols2[0]: st.page_link("pages/11_Verify_Farmer.py", label="Verify")
with cols2[1]: st.page_link("pages/12_Verification_History.py", label="History")
with cols2[2]: st.page_link("pages/14_Wallet.py", label="Wallet")
with cols2[3]: st.page_link("pages/15_Badges.py", label="Badges")
with cols2[4]: st.page_link("pages/16_Chat.py", label="Chat")
with cols2[5]: st.page_link("pages/20_Marketplace.py", label="Market")
with cols2[6]: st.page_link("pages/21_Crop_Insurance.py", label="Insurance")
with cols2[7]: st.page_link("pages/6_Payment_History.py", label="Payments")
with cols2[8]: st.page_link("pages/8_Profile.py", label="Profile")
with cols2[9]: st.page_link("pages/13_Help.py", label="Help")
