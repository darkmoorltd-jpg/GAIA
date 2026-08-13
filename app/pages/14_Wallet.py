import streamlit as st
from supabase import create_client, Client
import uuid

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]

@st.cache_resource
def init_supabase(): return create_client(SUPABASE_URL, SUPABASE_KEY)
@st.cache_resource
def init_service(): return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA – Digital Wallet", page_icon="💰", layout="wide")
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
service = init_service()

st.markdown('<style>.stApp{background:linear-gradient(135deg,#e8f5e9,#f1f8e9);color:#1b5e20}.card{background:#fff;border-radius:20px;padding:1.5rem;margin:.5rem 0;box-shadow:0 4px 15px rgba(0,0,0,.05)}.balance{font-size:3rem;font-weight:900;color:#2e7d32}</style>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;"><h1>💰 My Wallet</h1></div>', unsafe_allow_html=True)

wallet = service.table("farmer_wallets").select("*").eq("user_id", user.id).execute()
if not wallet.data or len(wallet.data) == 0:
    virtual_acct = f"GAIA-{user.id[:8].upper()}-{uuid.uuid4().hex[:6].upper()}"
    service.table("farmer_wallets").upsert({"user_id": user.id, "balance": 0.00, "virtual_account": virtual_acct, "account_bank": "Wema Bank", "account_name": user.email}).execute()
    wallet_data = {"balance": 0.00, "virtual_account": virtual_acct}
else:
    wallet_data = wallet.data[0]

balance = float(wallet_data.get("balance", 0.00))
virtual_account = wallet_data.get("virtual_account", "N/A")

st.markdown(f'<div class="card" style="text-align:center;"><p style="color:#888;">AVAILABLE BALANCE</p><div class="balance">₦{balance:,.2f}</div><hr style="margin:1.5rem 0;opacity:0.2;"><p style="color:#888;">ACCOUNT: {virtual_account}</p></div>', unsafe_allow_html=True)
st.caption("Powered by Darkmoor Ltd")

# ============================================
# FULL NAVIGATION — ALL PAGES
# ============================================
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(10)
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
    st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[7]:
    st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[8]:
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[9]:
    st.page_link("pages/10_Early_Warning.py", label="⚠️ Alerts")

st.markdown("### 📱 More Features")
cols2 = st.columns(10)
with cols2[0]:
    st.page_link("pages/11_Verify_Farmer.py", label="🛡️ Verify")
with cols2[1]:
    st.page_link("pages/12_Verification_History.py", label="📋 History")
with cols2[2]:
    st.page_link("pages/14_Wallet.py", label="💰 Wallet")
with cols2[3]:
    st.page_link("pages/15_Badges.py", label="🏅 Badges")
with cols2[4]:
    st.page_link("pages/16_Chat.py", label="💬 Chat")
with cols2[5]:
    st.page_link("pages/20_Marketplace.py", label="🌍 Market")
with cols2[6]:
    st.page_link("pages/21_Crop_Insurance.py", label="🏦 Insurance")
with cols2[7]:
    st.page_link("pages/6_Payment_History.py", label="💳 Payments")
with cols2[8]:
    st.page_link("pages/8_Profile.py", label="👤 Profile")
with cols2[9]:
    st.page_link("pages/13_Help.py", label="🆘 Help")
