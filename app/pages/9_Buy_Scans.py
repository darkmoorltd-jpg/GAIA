
import streamlit as st
from supabase import create_client, Client
import uuid
import time

def bottom_nav():
    st.markdown("---")
    st.markdown("### 🚀 Quick Navigation")
    cols = st.columns(8)
    with cols[0]:
        if st.button("🌿 Crops", key="bn_crops"): st.switch_page("pages/2_Crops.py")
    with cols[1]:
        if st.button("🐛 Pests", key="bn_pests"): st.switch_page("pages/3_Pests.py")
    with cols[2]:
        if st.button("🏞️ Soil", key="bn_soil"): st.switch_page("pages/4_Soil.py")
    with cols[3]:
        if st.button("🐄 Livestock", key="bn_livestock"): st.switch_page("pages/5_Livestock.py")
    with cols[4]:
        if st.button("💳 Buy Scans", key="bn_buy"): st.switch_page("pages/9_Buy_Scans.py")
    with cols[5]:
        if st.button("📋 Payments", key="bn_payments"): st.switch_page("pages/6_Payment_History.py")
    with cols[6]:
        if st.button("🔐 Admin", key="bn_admin"): st.switch_page("pages/7_Admin.py")
    with cols[7]:
        if st.button("🚪 Logout", key="bn_logout"):
            from supabase import create_client
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
            supabase = create_client(url, key)
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()


SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]

@st.cache_resource
def get_service_client():
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA – Buy Scans", page_icon="💳", layout="wide", initial_sidebar_state="expanded")

# FORCE SIDEBAR VISIBLE
st.markdown("""

""", unsafe_allow_html=True)


# Force sidebar visible on all pages
st.markdown("""

""", unsafe_allow_html=True)


# ---------- Theme ----------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)
dark_mode = st.toggle("", value=st.session_state.theme == "dark", key="buy_theme_toggle")
st.session_state.theme = "dark" if dark_mode else "light"
theme = st.session_state.theme

if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(145deg, #0a0a0a 0%, #1a1a2e 50%, #0d0d0d 100%); color: #e0e0e0; }
        header, footer {visibility: hidden;}
        .title { font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #00c853, #69f0ae, #00c853); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 30px rgba(0,200,83,0.6); margin-bottom: 0.5rem; animation: glow 2s ease-in-out infinite alternate; }
        @keyframes glow { from { text-shadow: 0 0 20px rgba(0,200,83,0.6); } to { text-shadow: 0 0 40px rgba(0,200,83,1), 0 0 80px rgba(0,200,83,0.8); } }
        .subtitle { text-align: center; font-size: 1.2rem; color: #90a4ae; margin-bottom: 2rem; }
        .pricing-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 1.5rem; margin: 2rem 0; }
        .pricing-card { background: rgba(255,255,255,0.04); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 2rem 1.5rem; width: 200px; text-align: center; transition: all 0.3s ease; position: relative; overflow: hidden; }
        .pricing-card:hover { transform: translateY(-8px); border-color: #00c853; box-shadow: 0 20px 40px rgba(0,200,83,0.2); }
        .pricing-card.popular { border-color: #00c853; box-shadow: 0 0 30px rgba(0,200,83,0.3); }
        .pricing-card.popular::before { content: 'POPULAR'; position: absolute; top: 15px; right: -35px; background: #00c853; color: #000; font-size: 0.7rem; font-weight: 700; padding: 5px 40px; transform: rotate(45deg); }
        .plan-name { font-size: 1.3rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; }
        .plan-price { font-size: 1.8rem; font-weight: 700; color: #00c853; margin: 0.5rem 0; }
        .plan-period { font-size: 0.8rem; color: #78909c; }
        .buy-button { display: inline-block; margin-top: 1rem; padding: 12px 30px; background: linear-gradient(135deg, #00c853, #00a844); color: #fff; text-decoration: none; border-radius: 30px; font-weight: 600; transition: all 0.3s ease; cursor: pointer; border: none; }
        .buy-button:hover { box-shadow: 0 0 25px rgba(0,200,83,0.5); transform: scale(1.05); }
        .paystack-badge { display: flex; align-items: center; justify-content: center; gap: 10px; margin: 2rem 0; padding: 1rem; background: rgba(255,255,255,0.03); border-radius: 15px; }
        .footer-note { text-align: center; color: #546e7a; font-size: 0.8rem; margin-top: 3rem; }
        .feature-grid { display: flex; justify-content: center; gap: 3rem; margin: 2rem 0; }
        .feature-item { text-align: center; }
        .feature-icon { font-size: 2rem; margin-bottom: 0.5rem; }
        .feature-text { font-size: 0.9rem; color: #90a4ae; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); color: #1b5e20; }
        header, footer {visibility: hidden;}
        .title { font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #2e7d32, #66bb6a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #33691e; margin-bottom: 2rem; }
        .pricing-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 1.5rem; margin: 2rem 0; }
        .pricing-card { background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.1); border-radius: 20px; padding: 2rem 1.5rem; width: 200px; text-align: center; transition: all 0.3s ease; position: relative; overflow: hidden; }
        .pricing-card:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(46,125,50,0.2); }
        .pricing-card.popular { border-color: #2e7d32; box-shadow: 0 0 20px rgba(46,125,50,0.2); }
        .pricing-card.popular::before { content: 'POPULAR'; position: absolute; top: 15px; right: -35px; background: #2e7d32; color: #fff; font-size: 0.7rem; font-weight: 700; padding: 5px 40px; transform: rotate(45deg); }
        .plan-name { font-size: 1.3rem; font-weight: 700; color: #1b5e20; margin-bottom: 0.5rem; }
        .plan-price { font-size: 1.8rem; font-weight: 700; color: #2e7d32; margin: 0.5rem 0; }
        .plan-period { font-size: 0.8rem; color: #558b2f; }
        .buy-button { display: inline-block; margin-top: 1rem; padding: 12px 30px; background: linear-gradient(135deg, #2e7d32, #4caf50); color: #fff; text-decoration: none; border-radius: 30px; font-weight: 600; transition: all 0.3s ease; cursor: pointer; border: none; }
        .buy-button:hover { box-shadow: 0 0 25px rgba(46,125,50,0.5); transform: scale(1.05); }
        .paystack-badge { display: flex; align-items: center; justify-content: center; gap: 10px; margin: 2rem 0; padding: 1rem; background: rgba(0,0,0,0.05); border-radius: 15px; }
        .footer-note { text-align: center; color: #6d8a6e; font-size: 0.8rem; margin-top: 3rem; }
        .feature-grid { display: flex; justify-content: center; gap: 3rem; margin: 2rem 0; }
        .feature-item { text-align: center; }
        .feature-icon { font-size: 2rem; margin-bottom: 0.5rem; }
        .feature-text { font-size: 0.9rem; color: #558b2f; }
    </style>
    """, unsafe_allow_html=True)

# ---------- Content ----------
st.markdown('<div class="title">💳 Buy Scans</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Choose a plan that fits your diagnostic needs</div>', unsafe_allow_html=True)


# Paystack badge
st.markdown("""
<div class="paystack-badge">
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="40" height="40" rx="8" fill="#0BA4A4"/>
        <path d="M10 20L16 14L22 20L28 14L34 20L28 26L22 20L16 26L10 20Z" fill="white"/>
        <path d="M16 14L10 20L16 26L22 20L16 14Z" fill="#0BA4A4"/>
        <path d="M28 14L22 20L28 26L34 20L28 14Z" fill="white"/>
    </svg>
    <span style="color: #78909c; font-size: 0.9rem;">Secure payments powered by <strong>Paystack</strong></span>
</div>
""", unsafe_allow_html=True)

# Check if user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in to buy scans.")
    st.stop()

user = st.session_state.user
service_client = get_service_client()

# Pricing plans
PAYSTACK_PLANS = {
    "10": {"scans": 10, "price": "$0.50", "url": "https://paystack.shop/pay/e-z03btaq-", "popular": False},
    "25": {"scans": 25, "price": "$1.00", "url": "https://paystack.shop/pay/nc3bs0quuh", "popular": True},
    "60": {"scans": 60, "price": "$2.00", "url": "https://paystack.shop/pay/1j9yrapbt4", "popular": False},
    "250": {"scans": 250, "price": "$8.00", "url": "https://paystack.shop/pay/rln87t1694", "popular": False},
    "unlimited": {"scans": 9999, "price": "$20.00", "url": "https://paystack.shop/pay/07zduaem6l", "popular": False}
}

# Display cards with proper pending payment handling
cols = st.columns(len(PAYSTACK_PLANS))
for i, (plan_key, plan_data) in enumerate(PAYSTACK_PLANS.items()):
    with cols[i]:
        card_class = "pricing-card popular" if plan_data["popular"] else "pricing-card"
        scans_display = "UNLIMITED" if plan_key == "unlimited" else f"{plan_data['scans']} SCANS"
        
        st.markdown(f"""
        <div class="{card_class}">
            <div class="plan-name">{scans_display}</div>
            <div class="plan-price">{plan_data['price']}</div>
            <div class="plan-period">per month</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate a unique reference and save pending payment before redirect
        if st.button(f"Buy {plan_data['scans']} scans", key=f"buy_{plan_key}"):
            ref = f"GAIA_{user.id[:8]}_{plan_key}_{uuid.uuid4().hex[:8]}"
            try:
                service_client.table("pending_payments").insert({
                    "user_id": user.id,
                    "reference": ref,
                    "plan": plan_key,
                    "amount": float(plan_data['price'].replace('$',''))
                }).execute()
                st.success("Redirecting to Paystack...")
                # Redirect with our custom reference
                paystack_url = f"{plan_data['url']}?reference={ref}"
                st.markdown(f'<meta http-equiv="refresh" content="1; url={paystack_url}">', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Failed to initiate payment: {e}")

# Feature grid
st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
st.markdown("""
    <div class="feature-item"><div class="feature-icon">🔒</div><div class="feature-text">Secure Payment</div></div>
    <div class="feature-item"><div class="feature-icon">⚡</div><div class="feature-text">Instant Activation</div></div>
    <div class="feature-item"><div class="feature-icon">📊</div><div class="feature-text">Track Usage</div></div>
    <div class="feature-item"><div class="feature-icon">💬</div><div class="feature-text">24/7 Support</div></div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer-note">
    Need help? Contact <a href="mailto:darkmoorltd@gmail.com">darkmoorltd@gmail.com</a><br>
    Powered by <strong>Darkmoor Ltd</strong>
</div>
""", unsafe_allow_html=True)


# ---------- Universal Bottom Navigation (safe) ----------
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(6)
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
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
