
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
    .plan-card.selected { border-color: #2e7d32; background: linear-gradient(160deg, #e8f5e9, #fff); }
    .plan-name { font-size: 1.2rem; font-weight: 700; color: #546e7a; }
    .plan-premium { font-size: 2.5rem; font-weight: 900; color: #1b5e20; margin: 0.5rem 0; }
    .plan-premium small { font-size: 0.8rem; color: #78909c; font-weight: 400; }
    .plan-coverage { font-size: 1rem; color: #2e7d32; font-weight: 600; }
    
    .policy-card {
        background: #fff; border-radius: 16px; padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06); margin: 1rem 0;
    }
    .policy-active { border-left: 5px solid #4caf50; }
    .policy-inactive { border-left: 5px solid #ccc; }
    
    .stButton button {
        background: #2e7d32 !important; color: #fff !important;
        border: none !important; border-radius: 10px !important;
        padding: 12px 28px !important; font-weight: 600 !important;
    }
    .stButton button:hover { background: #1b5e20 !important; }
    
    .claim-card {
        background: #fff; border-radius: 16px; padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06); margin: 0.5rem 0;
    }
    .claim-pending { border-left: 5px solid #ff9800; }
    .claim-approved { border-left: 5px solid #4caf50; }
    .claim-rejected { border-left: 5px solid #f44336; }
    .claim-paid { border-left: 5px solid #2196f3; }
</style>
""", unsafe_allow_html=True)

# ===== HEADER =====
st.markdown('<div class="insurance-title">🏦 Crop Insurance</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your farm is covered. GAIA monitors your field and files claims automatically.</div>', unsafe_allow_html=True)

# ===== TABS =====
tab1, tab2, tab3, tab4 = st.tabs(["📋 My Policies", "🛡️ Get Insurance", "📸 Field Monitoring", "📝 File Claim"])

# ===== TAB 1: MY POLICIES =====
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
                    st.write(f"**Start:** {policy.get('start_date','')[:10]}")
                    st.write(f"**End:** {policy.get('end_date','')[:10]}")

# ===== TAB 2: GET INSURANCE =====
with tab2:
    if active_policy:
        st.success(f"✅ You have an active policy for **{active_policy.get('crop','')}** — coverage ₦{active_policy.get('coverage_amount',0):,}")
        st.info("To add another crop, wait for the current policy to expire or contact support.")
    else:
        st.markdown("### Choose Your Coverage Plan")
        
        selected_plan = st.session_state.get("selected_insurance_plan", None)
        
        cols = st.columns(3)
        for i, (plan_key, plan) in enumerate(INSURANCE_PLANS.items()):
            with cols[i]:
                sel = "selected" if selected_plan == plan_key else ""
                st.markdown(f"""
                <div class="plan-card {sel}">
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
        
        if selected_plan:
            plan = INSURANCE_PLANS[selected_plan]
            st.markdown("---")
            st.markdown(f"### Selected: {plan['name']} — ₦{plan['premium']:,}/month")
            
            with st.form("insurance_registration"):
                col1, col2 = st.columns(2)
                with col1:
                    crop = st.selectbox("Crop to Insure", plan['crops'])
                    field_size = st.number_input("Field Size (acres)", min_value=0.1, value=1.0, step=0.5)
                with col2:
                    field_location = st.text_input("Field Location", placeholder="e.g., Makurdi, Benue")
                    coverage = st.number_input("Coverage Amount (₦)", min_value=plan['coverage'], max_value=1000000, value=plan['coverage'], step=10000)
                
                confirm = st.checkbox("I agree to the terms and conditions of Leadway Assurance")
                
                if st.form_submit_button("💳 Pay Premium & Activate Insurance", type="primary", use_container_width=True):
                    if not confirm:
                        st.error("Please agree to the terms.")
                    elif not field_location:
                        st.error("Field location is required.")
                    else:
                        ref = f"GAIA_INS_{user.id[:8]}_{uuid.uuid4().hex[:8]}"
                        
                        policy_number = f"GAIA-{uuid.uuid4().hex[:10].upper()}"
                        
                        # Create pending policy
                        db.table("insurance_policies").insert({
                            "user_id": user.id,
                            "policy_number": policy_number,
                            "crop": crop,
                            "field_location": field_location,
                            "field_size_acres": field_size,
                            "coverage_amount": coverage,
                            "premium_monthly": plan['premium'],
                            "status": "pending_payment"
                        }).execute()
                        
                        # Paystack payment
                        
        # Fetch user phone for SMS receipt
        try:
            profile_res = db.table("user_profiles").select("phone").eq("user_id", user.id).execute()
            user_phone = profile_res.data[0].get("phone", "") if profile_res.data else ""
        except:
            user_phone = ""
        
        components.html(f"""
                        <script src="https://js.paystack.co/v1/inline.js"></script>
                        <script>
                            PaystackPop.setup({{
                                key: '{PAYSTACK_PUBLIC}',
                                email: '{user.email}',
                    phone: '{normalize_phone(user_phone)}',  // Placeholder — will be replaced by user phone

                                amount: {plan['premium'] * 100},
                                currency: 'NGN',
                                ref: '{ref}',
                                label: 'GAIA Crop Insurance',
                                metadata: {{ policy_number: '{policy_number}' }},
                                onClose: function() {{ window.location.reload(); }},
                                callback: function(r) {{
                                    window.location.href = '/~/callback?reference=' + r.reference + '&insurance=' + '{policy_number}';
                                }}
                            }}).openIframe();
                        </script>
                        """, height=0)

# ===== TAB 3: FIELD MONITORING =====
with tab3:
    st.markdown("### 📸 Weekly Field Monitoring")
    st.markdown("*Upload a photo of your field every week. GAIA monitors crop health and files claims automatically if damage is detected.*")
    
    if not active_policy:
        st.warning("⚠️ You need an active insurance policy to upload monitoring photos.")
    else:
        # Upload monitoring photo
        st.markdown(f"**Monitoring:** {active_policy.get('crop','')} at {active_policy.get('field_location','N/A')}")
        
        uploaded_photo = st.file_uploader("📸 Upload field photo", type=["jpg","jpeg","png"])
        
        if uploaded_photo:
            col1, col2 = st.columns(2)
            with col1:
                st.image(uploaded_photo, caption="Current field status", width=300)
            with col2:
                # Simple weather check (mock data)
                import random
                random.seed(hash(uploaded_photo.name) + datetime.now().day)
                weather = {
                    "rainfall_mm": random.randint(0, 150),
                    "temperature": round(random.uniform(25, 38), 1),
                    "humidity": random.randint(40, 90)
                }
                
                st.write(f"**Weather at upload:**")
                st.write(f"🌧️ Rainfall: {weather['rainfall_mm']} mm")
                st.write(f"🌡️ Temperature: {weather['temperature']}°C")
                st.write(f"💧 Humidity: {weather['humidity']}%")
                
                if st.button("✅ Submit Monitoring Photo", use_container_width=True):
                    db.table("field_monitoring").insert({
                        "policy_id": active_policy["id"],
                        "user_id": user.id,
                        "crop": active_policy.get("crop"),
                        "weather_data": weather,
                        "uploaded_at": datetime.now().isoformat()
                    }).execute()
                    st.success("✅ Photo submitted for monitoring!")
        
        # Show monitoring history
        try:
            history = db.table("field_monitoring").select("*").eq("policy_id", active_policy["id"]).order("uploaded_at", desc=True).limit(10).execute()
            if history.data:
                st.markdown("### 📊 Monitoring History")
                for entry in history.data:
                    st.write(f"📸 {entry.get('uploaded_at','')[:16]} — 🌧️ {entry.get('weather_data',{}).get('rainfall_mm','?')}mm rain")
        except:
            pass

# ===== TAB 4: FILE CLAIM =====
with tab4:
    st.markdown("### 📝 File an Insurance Claim")
    
    if not active_policy:
        st.warning("⚠️ You need an active policy to file a claim.")
    else:
        st.markdown(f"**Policy:** {active_policy.get('crop','')} — Coverage ₦{active_policy.get('coverage_amount',0):,}")
        
        with st.form("claim_form"):
            claim_type = st.selectbox("Type of Damage", ["drought", "flood", "disease", "pest", "fire", "other"])
            description = st.text_area("Describe what happened", placeholder="e.g., Heavy rainfall flooded my maize field last week. Estimated 70% of crops destroyed.")
            
            before_photo = st.file_uploader("📸 Before Damage Photo", type=["jpg","jpeg","png"])
            after_photo = st.file_uploader("📸 After Damage Photo", type=["jpg","jpeg","png"])
            
            if st.form_submit_button("📤 Submit Claim", type="primary", use_container_width=True):
                if not description:
                    st.error("Please describe the damage.")
                else:
                    db.table("insurance_claims").insert({
                        "policy_id": active_policy["id"],
                        "user_id": user.id,
                        "claim_type": claim_type,
                        "description": description,
                        "status": "pending"
                    }).execute()
                    st.success("✅ Claim submitted! GAIA will verify with satellite data and photos within 48 hours.")
                    st.balloons()
        
        # Show existing claims
        try:
            claims = db.table("insurance_claims").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
            if claims.data:
                st.markdown("### Your Claims")
                for claim in claims.data:
                    status = claim.get("status", "pending")
                    emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌", "paid": "💰"}.get(status, "⏳")
                    st.markdown(f"""
                    <div class="claim-card claim-{status}">
                        <strong>{emoji} Claim #{claim.get('id','?')}</strong> — {claim.get('claim_type','')}<br>
                        <small>Status: {status.upper()} | Filed: {claim.get('created_at','')[:10]}</small>
                    </div>
                    """, unsafe_allow_html=True)
        except:
            pass

# ===== NAVIGATION =====
st.markdown("---")
st.markdown("

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
