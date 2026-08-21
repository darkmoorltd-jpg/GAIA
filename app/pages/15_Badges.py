
import streamlit as st
user = st.session_state.get("user", None)
if user is None:
    user = None  # Allow demo mode
from supabase import create_client
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
try:
    session = supabase.auth.get_session()
    user = session.user if session else None
except:
    user = None
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

# Badge definitions with monthly pricing
BADGES = {
    "bronze": {
        "name": "Bronze",
        "emoji": "🥉",
        "price_monthly": "₦500",
        "kobo": 50000,
        "loans": "Up to ₦50,000",
        "color": "#cd7f32",
        "gradient": "linear-gradient(135deg, #cd7f32, #e6a869)",
        "benefits": ["Basic loan access", "Marketplace listing", "Community chat"],
    },
    "silver": {
        "name": "Silver",
        "emoji": "🥈",
        "price_monthly": "₦1,500",
        "kobo": 150000,
        "loans": "Up to ₦200,000",
        "color": "#c0c0c0",
        "gradient": "linear-gradient(135deg, #c0c0c0, #e8e8e8)",
        "benefits": ["Higher loan limit", "Priority support", "Featured marketplace listing"],
    },
    "gold": {
        "name": "Gold",
        "emoji": "🥇",
        "price_monthly": "₦3,000",
        "kobo": 300000,
        "loans": "Up to ₦500,000",
        "color": "#ffd700",
        "gradient": "linear-gradient(135deg, #ffd700, #fff2a8)",
        "benefits": ["Premium loan access", "Free insurance consultation", "Exclusive badges"],
    },
    "platinum": {
        "name": "Platinum",
        "emoji": "💎",
        "price_monthly": "₦5,000",
        "kobo": 500000,
        "loans": "Up to ₦2,000,000",
        "color": "#e5e4e2",
        "gradient": "linear-gradient(135deg, #e5e4e2, #ffffff)",
        "benefits": ["Highest loan limit", "Dedicated account manager", "All premium features"],
    },
}

st.set_page_config(page_title="GAIA – Badges", page_icon="🏅", layout="wide")

if user is None:
    st.session_state["user"] = None
    user = None

user = user
db = get_service()

# Check verification
verify = db.table("farmer_verifications").select("status").eq("user_id", user.id if user else "demo_user").execute()
is_verified = verify.data and len(verify.data) > 0 and verify.data[0].get("status") == "approved"

if not is_verified:
    st.warning("⚠️ You need to verify your identity first.")
    st.page_link("pages/11_Verify_Farmer.py", label="Go to Verification")
    st.stop()

# Get current badge
badge_res = db.table("badge_subscriptions").select("*").eq("user_id", user.id if user else "demo_user").execute()
current_badge = badge_res.data[0] if badge_res.data else None

# ============================================
# CUSTOM CSS (Facebook‑inspired)
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #f0f2f5; color: #1c1e21; }
    header, footer { visibility: hidden; }
    .page-title {
        font-size: 2.5rem; font-weight: 900; text-align: center; color: #1877f2;
        margin-bottom: 0.5rem;
    }
    .subtitle { text-align: center; color: #65676b; font-size: 1.1rem; margin-bottom: 2rem; }
    .badge-container {
        display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;
        margin-bottom: 2rem;
    }
    .badge-card {
        background: #fff; border-radius: 16px; padding: 2rem 1.5rem;
        width: 220px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        transition: all 0.3s ease; cursor: pointer; position: relative;
    }
    .badge-card:hover { transform: translateY(-5px); box-shadow: 0 8px 20px rgba(0,0,0,0.12); }
    .badge-icon {
        width: 80px; height: 80px; border-radius: 50%;
        background: var(--gradient);
        display: flex; align-items: center; justify-content: center;
        font-size: 2.5rem; margin: 0 auto 1rem;
    }
    .badge-name { font-size: 1.2rem; font-weight: 700; color: #1c1e21; }
    .badge-price { font-size: 1.5rem; font-weight: 900; color: #1877f2; margin: 0.5rem 0; }
    .badge-loans { font-size: 0.85rem; color: #65676b; margin-bottom: 0.5rem; }
    .current-badge {
        background: #fff; border: 2px solid #1877f2; border-radius: 20px;
        padding: 2rem; text-align: center; margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    .current-badge .badge-icon { margin-bottom: 0.5rem; }
    .stButton button {
        background: #1877f2 !important; color: #fff !important;
        border: none !important; border-radius: 8px !important;
        padding: 10px 20px !important; font-weight: 600 !important;
        width: 100%;
    }
    .benefits-list {
        text-align: left; font-size: 0.8rem; color: #65676b;
        margin-top: 0.5rem; padding-left: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# PAGE CONTENT
# ============================================
st.markdown('<div class="page-title">🏅 GAIA Badges</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Subscribe to a monthly badge and unlock premium features</div>', unsafe_allow_html=True)

# Show current badge if active and not expired
if current_badge:
    plan = current_badge.get("plan")
    expiry = current_badge.get("expiry")
    if plan and plan in BADGES:
        expiry_date = None
        if expiry:
            try:
                expiry_date = datetime.fromisoformat(expiry)
            except:
                expiry_date = None
        if expiry_date and expiry_date > datetime.now():
            badge = BADGES[plan]
            st.markdown(f"""
                <div class="current-badge">
                    <div class="badge-icon" style="background:{badge['gradient']};">
                        {badge['emoji']}
                    </div>
                    <div class="badge-name">{badge['name']} Badge Active</div>
                    <div class="badge-loans">Expires: {expiry_date.strftime('%d %b %Y')}</div>
                    <div class="badge-price">{badge['price_monthly']}/month</div>
                </div>
            """, unsafe_allow_html=True)
            st.success("✅ Your badge is active! Enjoy your benefits.")
        else:
            st.info("Your badge has expired. Renew below.")
    else:
        st.info("No badge found. Choose a plan below.")

# ============================================
# BADGE OPTIONS
# ============================================
st.markdown("### Choose Your Monthly Badge")
badge_cols = st.columns(len(BADGES))
for i, (key, badge) in enumerate(BADGES.items()):
    with badge_cols[i]:
        st.markdown(f"""
            <div class="badge-card">
                <div class="badge-icon" style="background:{badge['gradient']};">
                    {badge['emoji']}
                </div>
                <div class="badge-name">{badge['name']}</div>
                <div class="badge-price">{badge['price_monthly']}<small style="font-size:0.7rem;">/mo</small></div>
                <div class="badge-loans">{badge['loans']}</div>
                <div class="benefits-list">
                    {'<br>'.join(['• ' + b for b in badge['benefits']])}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Payment button
        if st.button(f"Subscribe {badge['name']}", key=f"badge_btn_{key}", use_container_width=True):
            ref = f"GAIA_BADGE_{user.id if user else "demo_user"[:8]}_{key}_{uuid.uuid4().hex[:6]}"
            phone_for_sms = ""
            try:
                profile = db.table("user_profiles").select("phone").eq("user_id", user.id if user else "demo_user").execute()
                if profile.data and len(profile.data) > 0:
                    phone_for_sms = normalize_phone(profile.data[0].get("phone", ""))
            except:
                pass
            phone_for_sms = phone_for_sms or "08000000000"

            components.html(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://js.paystack.co/v1/inline.js"></script>
            </head>
            <body>
                <button onclick="payForBadge()" style="background:#1877f2;color:#fff;border:none;padding:12px 30px;border-radius:8px;font-weight:700;cursor:pointer;">Pay {badge['price_monthly']}</button>
                <script>
                    function payForBadge() {{
                        PaystackPop.setup({{
                            key: '{PAYSTACK_PUBLIC}',
                            email: '{user.email}',
                            phone: '{phone_for_sms}',
                            amount: {badge['kobo']},
                            currency: 'NGN',
                            ref: '{ref}',
                            label: 'GAIA {badge['name']} Badge',
                            onClose: function() {{ window.location.reload(); }},
                            callback: function(response) {{
                                window.location.href = '/~/callback?reference=' + response.reference + '&plan=badge_{key}';
                            }}
                        }}).openIframe();
                    }}
                </script>
            </body>
            </html>
            """, height=100)

# ============================================
# NAVIGATION
# ============================================
st.markdown("---")
st.markdown("### Quick Navigation")
cols = st.columns(10)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[6]: st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[7]: st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[9]: st.page_link("pages/10_Early_Warning.py", label="⚠️ Alerts")

st.markdown("### 📱 More Features")
cols2 = st.columns(10)
with cols2[0]: st.page_link("pages/11_Verify_Farmer.py", label="🛡️ Verify")
with cols2[1]: st.page_link("pages/12_Verification_History.py", label="📋 History")
with cols2[2]: st.page_link("pages/14_Wallet.py", label="💰 Wallet")
with cols2[3]: st.page_link("pages/15_Badges.py", label="🏅 Badges")
with cols2[4]: st.page_link("pages/16_Chat.py", label="💬 Chat")
with cols2[5]: st.page_link("pages/20_Marketplace.py", label="🌍 Market")
with cols2[6]: st.page_link("pages/21_Crop_Insurance.py", label="🏦 Insurance")
with cols2[7]: st.page_link("pages/6_Payment_History.py", label="💳 Payments")
with cols2[8]: st.page_link("pages/8_Profile.py", label="👤 Profile")
with cols2[9]: st.page_link("pages/13_Help.py", label="🆘 Help")
