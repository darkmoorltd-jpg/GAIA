import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import uuid
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

st.markdown("""
<style>
    .stApp { background: linear-gradient(160deg, #f4faf5, #eaf5ee, #fdfefb); color: #1b5e20; }
    header, footer { visibility: hidden; }
    .title {
        font-size: 2.8rem; font-weight: 800; text-align: center;
        background: linear-gradient(135deg, #1b5e20, #4caf50);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .subtitle { text-align: center; color: #607d8b; font-size: 1.1rem; margin-bottom: 2rem; }
    .badge-card {
        background: #fff; border-radius: 24px; padding: 2rem 1rem; text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,.05); border: 3px solid transparent;
        transition: all .25s;
    }
    .badge-card:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(46,125,50,.15); }
    .badge-card.bronze { border-color: #cd7f32; }
    .badge-card.silver { border-color: #c0c0c0; }
    .badge-card.gold { border-color: #ffd700; }
    .badge-card.platinum { border-color: #e5e4e2; }
    .badge-card.active { border-width: 4px; box-shadow: 0 12px 35px rgba(46,125,50,.25); }
    .badge-emoji { font-size: 3rem; }
    .badge-name { font-size: 1.4rem; font-weight: 700; }
    .badge-price { font-size: 2rem; font-weight: 900; color: #1b5e20; margin: .5rem 0; }
    .badge-loans { font-size: .9rem; color: #546e7a; margin-bottom: 1rem; }
    .current-badge {
        background: linear-gradient(135deg, #e8f5e9, #c8e6c9); border: 3px solid #2e7d32;
        border-radius: 20px; padding: 1.5rem 2rem; text-align: center; margin-bottom: 2rem;
    }
    .pay-btn {
        background: linear-gradient(135deg, #2e7d32, #43a047); color: #fff;
        border: none; padding: 18px 50px; border-radius: 50px; font-weight: 700;
        font-size: 1.2rem; cursor: pointer; width: 100%; box-shadow: 0 10px 30px rgba(46,125,50,.3);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">Verification Badges</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Subscribe to unlock loans and premium features</div>', unsafe_allow_html=True)

# Show current badge
if current_badge and current_badge.get("status") == "active":
    tier = current_badge["badge_tier"]
    badge = BADGES.get(tier, {})
    exp = current_badge.get("expires_at", "")
    st.markdown(f"""
    <div class="current-badge">
        <h3>Your Current Badge</h3>
        <div style="font-size:3rem;">{badge.get('emoji','')}</div>
        <h2>{badge.get('name','')} Tier</h2>
        <p>Loan Access: {badge.get('loans','')}</p>
        <p style="color:#888;">Expires: {exp[:10] if exp else 'N/A'}</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("You don't have an active badge yet. Subscribe below.")

# Badge cards
st.markdown("### Choose Your Badge Tier")

cols = st.columns(len(BADGES))
for i, (key, badge) in enumerate(BADGES.items()):
    with cols[i]:
        is_active = current_badge and current_badge.get("badge_tier") == key and current_badge.get("status") == "active"
        active_class = "active" if is_active else ""
        st.markdown(f"""
        <div class="badge-card {key} {active_class}">
            <div class="badge-emoji">{badge['emoji']}</div>
            <div class="badge-name">{badge['name']}</div>
            <div class="badge-price">{badge['price']}<span style="font-size:.8rem;color:#888;">/mo</span></div>
            <div class="badge-loans">Loan Access: {badge['loans']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if is_active:
            st.success("Active")
        else:
            if st.button(f"Subscribe", key=f"badge_{key}", use_container_width=True):
                ref = f"GAIA_BADGE_{user.id[:8]}_{key}_{uuid.uuid4().hex[:6]}"
                components.html(f"""
                <script src="https://js.paystack.co/v1/inline.js"></script>
                <script>
                    PaystackPop.setup({{
                        key: '{PAYSTACK_PUBLIC}',
                        email: '{user.email}',
                        amount: {badge['kobo']},
                        currency: 'NGN',
                        ref: '{ref}',
                        label: 'GAIA {badge["name"]} Badge',
                        onClose: function() {{ window.location.reload(); }},
                        callback: function(r) {{
                            window.location.href = '/~/callback?reference=' + r.reference + '&badge={key}';
                        }}
                    }}).openIframe();
                </script>
                """, height=0)

# Manual verify
st.markdown("---")
st.markdown("### Already Paid? Verify Reference")
col1, col2 = st.columns([3,1])
with col1:
    ref_input = st.text_input("Reference", placeholder="e.g., GAIA_BADGE_abc123", key="badge_ref")
with col2:
    st.write("")
    if st.button("Verify", use_container_width=True, key="badge_verify") and ref_input:
        with st.spinner("Checking..."):
            v = verify_payment(ref_input)
            if v["ok"]:
                amt = v["amount"]
                match = None
                for k, b in BADGES.items():
                    if abs(b["kobo"] / 100 - amt) < 1:
                        match = k
                        break
                if match:
                    exp_date = (datetime.now() + timedelta(days=30)).isoformat()
                    db.table("badge_subscriptions").upsert({
                        "user_id": user.id,
                        "badge_tier": match,
                        "status": "active",
                        "subscribed_at": datetime.now().isoformat(),
                        "expires_at": exp_date,
                        "payment_reference": ref_input
                    }).execute()
                    st.success(f"{BADGES[match]['name']} badge activated!")
                    st.rerun()
                else:
                    st.error("Amount doesn't match any badge tier.")
            else:
                st.error("Payment not found.")

st.markdown("---")
st.caption("Badge subscriptions are recurring monthly. Cancel anytime.")

cols = st.columns(6)
cols[0].page_link("pages/1_Dashboard.py", label="Dashboard")
cols[1].page_link("pages/2_Crops.py", label="Crops")
cols[2].page_link("pages/3_Pests.py", label="Pests")
cols[3].page_link("pages/4_Soil.py", label="Soil")
cols[4].page_link("pages/5_Livestock.py", label="Livestock")
cols[5].page_link("pages/9_Buy_Scans.py", label="Buy Scans")
# ---------- Quick Navigation ----------
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(8)
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
    st.page_link("pages/10_Early_Warning.py", label="🛰️ Early Warning")
with cols[7]:
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")