
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime, timedelta
import uuid
from app.utils.phone_util import normalize_phone
import requests

# ===== CONFIG =====
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_PUBLIC = "pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057"
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]
PULA_API_KEY = st.secrets.get("pula", {}).get("api_key", "")

@st.cache_resource
def get_db():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA – Crop Insurance", page_icon="🏦", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
db = get_db()
service = get_service()

# ===== SESSION STATE =====
if "insurance_tab" not in st.session_state:
    st.session_state.insurance_tab = "overview"

# ===== INSURANCE PLANS =====
INSURANCE_PLANS = {
    "basic": {"name": "Basic Cover", "premium": 500, "coverage": 50000, "crops": ["Maize", "Rice", "Beans"], "duration": "6 months"},
    "standard": {"name": "Standard Cover", "premium": 1000, "coverage": 100000, "crops": ["Maize", "Rice", "Beans", "Yam", "Cassava"], "duration": "12 months"},
    "premium": {"name": "Premium Cover", "premium": 2000, "coverage": 200000, "crops": ["All crops"], "duration": "12 months"},
}

# ===== PULA API INTEGRATION =====
def register_with_pula(policy_data):
    """Register policy with Pula if API key exists."""
    if not PULA_API_KEY:
        return None, "Pula API not configured"
    
    try:
        resp = requests.post(
            "https://api.pula.io/v1/policies",
            headers={"Authorization": f"Bearer {PULA_API_KEY}", "Content-Type": "application/json"},
            json=policy_data,
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json(), None
        return None, f"Pula error: {resp.status_code}"
    except Exception as e:
        return None, str(e)

def verify_paystack(ref):
    r = requests.get(f"https://api.paystack.co/transaction/verify/{ref}",
                     headers={"Authorization": f"Bearer {PAYSTACK_SECRET}"}, timeout=10)
    if r.status_code == 200:
        d = r.json()
        if d.get("status") and d["data"]["status"] == "success":
            return {"ok": True, "amount": d["data"]["amount"] / 100}
    return {"ok": False}

# ===== FETCH USER POLICIES =====
try:
    policies_res = db.table("insurance_policies").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
    my_policies = policies_res.data if policies_res.data else []
except:
    my_policies = []

active_policy = next((p for p in my_policies if p.get("status") == "active"), None)

# ===== STYLING =====

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
