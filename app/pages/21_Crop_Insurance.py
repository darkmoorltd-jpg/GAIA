import streamlit as st
user = st.session_state.get("user", None)
if user is None:
    st.warning("Please log in first.")
    st.stop()

if user is None:
    # Allow demo mode
    from supabase import create_client
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
try:
    session = supabase.auth.get_session()
    user = session.user if session else None
except:
    import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime, timedelta
import uuid
from app.utils.phone_util import normalize_phone
import requests

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_PUBLIC = "pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057"
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

@st.cache_resource
def get_db():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA – Crop Insurance", page_icon="🏦", layout="wide")

if user is None:
    st.session_state["user"] = None
    user = user
db = get_db()
service = get_service()

INSURANCE_PLANS = {
    "basic": {"name": "Basic Cover", "premium": 500, "coverage": 50000, "crops": ["Maize", "Rice", "Beans"], "duration": "6 months"},
    "standard": {"name": "Standard Cover", "premium": 1000, "coverage": 100000, "crops": ["Maize", "Rice", "Beans", "Yam", "Cassava"], "duration": "12 months"},
    "premium": {"name": "Premium Cover", "premium": 2000, "coverage": 200000, "crops": ["All crops"], "duration": "12 months"},
}

def verify_paystack(ref):
    r = requests.get(f"https://api.paystack.co/transaction/verify/{ref}",
                     headers={"Authorization": f"Bearer {PAYSTACK_SECRET}"}, timeout=10)
    if r.status_code == 200:
        d = r.json()
        if d.get("status") and d["data"]["status"] == "success":
            return {"ok": True, "amount": d["data"]["amount"] / 100}
    return {"ok": False}

try:
    policies_res = db.table("insurance_policies").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
    my_policies = policies_res.data if policies_res.data else []
except:
    my_policies = []

active_policy = next((p for p in my_policies if p.get("status") == "active"), None)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(160deg, #e8f5e9 0%, #f1f8e9 50%, #fffde7 100%); color: #1b5e20; }
    header, footer { visibility: hidden; }
    .insurance-title {
        font-size: 2.8rem; font-weight: 800; text-align: center;
        background: linear-gradient(135deg, #1b5e20, #4caf50, #1b5e20);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .subtitle { text-align: center; color: #607d8b; font-size: 1.1rem; margin-bottom: 2rem; }
    .plan-card {
        background: #fff; border-radius: 20px; padding: 2rem;
        box-shadow: 0 8px 30px rgba(0,0,0,0.06); text-align: center;
        border: 2px solid transparent; transition: all 0.3s;
    }
    .plan-card:hover { transform: translateY(-6px); box-shadow: 0 16px 40px rgba(46,125,50,0.15); }
    .plan-name { font-size: 1.2rem; font-weight: 700; color: #546e7a; }
    .plan-premium { font-size: 2.5rem; font-weight: 900; color: #1b5e20; margin: 0.5rem 0; }
    .plan-premium small { font-size: 0.8rem; color: #78909c; font-weight: 400; }
    .plan-coverage { font-size: 1rem; color: #2e7d32; font-weight: 600; }
    .stButton button {
        background: #2e7d32 !important; color: #fff !important;
        border: none !important; border-radius: 10px !important;
        padding: 12px 28px !important; font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="insurance-title">🏦 Crop Insurance</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your farm is covered. GAIA monitors your field and files claims automatically.</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📋 My Policies", "🛡️ Get Insurance", "📸 Field Monitoring", "📝 File Claim"])

with tab1:
    if not my_policies:
        st.info("🏦 You don't have any insurance policies yet. Go to **Get Insurance** to protect your farm.")
    else:
        for policy in my_policies:
            status = policy.get("status", "active")
            status_emoji = {"active": "🟢", "expired": "🔴", "cancelled": "⚫"}.get(status, "⚪")
            with st.expander(f"{status_emoji} Policy #{policy.get('policy_number','?')} — {policy.get('crop','')} ({status.upper()})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Crop:** {policy.get('crop','')}")
                    st.write(f"**Field Location:** {policy.get('field_location','N/A')}")
                    st.write(f"**Field Size:** {policy.get('field_size_acres','N/A')} acres")
                with col2:
                    st.write(f"**Coverage:** ₦{policy.get('coverage_amount',0):,}")
                    st.write(f"**Premium:** ₦{policy.get('premium_monthly',0):,}/month")
                    st.write(f"**Start:** {str(policy.get('start_date',''))[:10]}")
                    st.write(f"**End:** {str(policy.get('end_date',''))[:10]}")

with tab2:
    if active_policy:
        st.success(f"✅ You have an active policy for **{active_policy.get('crop','')}** — coverage ₦{active_policy.get('coverage_amount',0):,}")
    else:
        st.markdown("### Choose Your Coverage Plan")
        
        cols = st.columns(3)
        for i, (plan_key, plan) in enumerate(INSURANCE_PLANS.items()):
            with cols[i]:
                st.markdown(f"""
                <div class="plan-card">
                    <div class="plan-name">{plan['name']}</div>
                    <div class="plan-premium">₦{plan['premium']:,}<small>/mo</small></div>
                    <div class="plan-coverage">Coverage: ₦{plan['coverage']:,}</div>
                    <p style="font-size:0.8rem;color:#888;">Crops: {', '.join(plan['crops'])}</p>
                    <p style="font-size:0.8rem;color:#888;">Duration: {plan['duration']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Select {plan['name']}", key=f"plan_{plan_key}", use_container_width=True):
                    st.session_state.selected_insurance_plan = plan_key
                    st.rerun()
        
        if "selected_insurance_plan" in st.session_state:
            selected = st.session_state.selected_insurance_plan
            plan = INSURANCE_PLANS[selected]
            st.markdown("---")
            st.markdown(f"### Selected: {plan['name']} — ₦{plan['premium']:,}/month")
            
            with st.form("insurance_form"):
                crop = st.selectbox("Crop to Insure", plan['crops'])
                field_location = st.text_input("Field Location")
                field_size = st.number_input("Field Size (acres)", min_value=1, value=1)
                
                if st.form_submit_button("💳 Pay Premium", type="primary", use_container_width=True):
                    ref = f"GAIA_INS_{user.id[:8]}_{uuid.uuid4().hex[:6]}"
                    components.html(f"""
                    <script src="https://js.paystack.co/v1/inline.js"></script>
                    <script>
                        PaystackPop.setup({{
                            key: '{PAYSTACK_PUBLIC}',
                            email: '{user.email}',
                            amount: {plan['premium'] * 100},
                            currency: 'NGN',
                            ref: '{ref}',
                            label: 'GAIA {plan['name']}',
                            callback: function(response) {{
                                window.location.href = '/~/callback?reference=' + response.reference + '&plan={selected}';
                            }}
                        }}).openIframe();
                    </script>
                    """, height=150)

with tab3:
    st.markdown("### 📸 Field Monitoring")
    st.info("Upload field photos for GAIA to monitor crop health and file claims automatically.")

with tab4:
    st.markdown("### 📝 File a Claim")
    st.info("Claim filing feature coming soon.")

st.markdown("---")
st.caption("Powered by Darkmoor Ltd")

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
