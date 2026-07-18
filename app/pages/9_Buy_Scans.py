
import streamlit as st

st.set_page_config(page_title="GAIA – Buy Scans", page_icon="💳", layout="wide")

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

# ---------- Professional CSS (both themes) ----------
if theme == "dark":
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(145deg, #0a0a0a 0%, #1a1a2e 50%, #0d0d0d 100%);
            color: #e0e0e0;
        }
        header, footer {visibility: hidden;}
        .title {
            font-size: 3rem; font-weight: 900; text-align: center;
            background: linear-gradient(90deg, #00c853, #69f0ae, #00c853);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(0,200,83,0.6);
            margin-bottom: 0.5rem;
        }
        .subtitle { text-align: center; font-size: 1.2rem; color: #90a4ae; margin-bottom: 2rem; }
        .pricing-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 1.5rem; margin: 2rem 0; }
        .pricing-card {
            background: rgba(255,255,255,0.04); backdrop-filter: blur(15px);
            border: 1px solid rgba(255,255,255,0.1); border-radius: 20px;
            padding: 2rem 1.5rem; width: 200px; text-align: center;
            transition: all 0.3s ease; position: relative; overflow: hidden;
        }
        .pricing-card:hover { transform: translateY(-8px); border-color: #00c853; box-shadow: 0 20px 40px rgba(0,200,83,0.2); }
        .pricing-card.popular { border-color: #00c853; box-shadow: 0 0 30px rgba(0,200,83,0.3); }
        .pricing-card.popular::before {
            content: 'POPULAR'; position: absolute; top: 15px; right: -35px;
            background: #00c853; color: #000; font-size: 0.7rem; font-weight: 700;
            padding: 5px 40px; transform: rotate(45deg);
        }
        .plan-name { font-size: 1.3rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; }
        .plan-scans { font-size: 2.5rem; font-weight: 900; background: linear-gradient(90deg, #00c853, #69f0ae); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .plan-price { font-size: 1.8rem; font-weight: 700; color: #00c853; margin: 0.5rem 0; }
        .plan-period { font-size: 0.8rem; color: #78909c; }
        .buy-button {
            display: inline-block; margin-top: 1rem; padding: 12px 30px;
            background: linear-gradient(135deg, #00c853, #00a844); color: #fff;
            text-decoration: none; border-radius: 30px; font-weight: 600;
            transition: all 0.3s ease;
        }
        .buy-button:hover { box-shadow: 0 0 25px rgba(0,200,83,0.5); transform: scale(1.05); }
        .paystack-badge {
            display: flex; align-items: center; justify-content: center;
            gap: 10px; margin: 2rem 0; padding: 1rem;
            background: rgba(255,255,255,0.03); border-radius: 15px;
        }
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
        .pricing-card {
            background: rgba(255,255,255,0.9); backdrop-filter: blur(10px);
            border: 1px solid rgba(0,0,0,0.1); border-radius: 20px;
            padding: 2rem 1.5rem; width: 200px; text-align: center;
            transition: all 0.3s ease;
        }
        .pricing-card:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(46,125,50,0.2); }
        .pricing-card.popular { border-color: #2e7d32; box-shadow: 0 0 20px rgba(46,125,50,0.2); }
        .pricing-card.popular::before {
            content: 'POPULAR'; position: absolute; top: 15px; right: -35px;
            background: #2e7d32; color: #fff; font-size: 0.7rem; font-weight: 700;
            padding: 5px 40px; transform: rotate(45deg);
        }
        .plan-name { font-size: 1.3rem; font-weight: 700; color: #1b5e20; margin-bottom: 0.5rem; }
        .plan-scans { font-size: 2.5rem; font-weight: 900; color: #2e7d32; }
        .plan-price { font-size: 1.8rem; font-weight: 700; color: #2e7d32; margin: 0.5rem 0; }
        .plan-period { font-size: 0.8rem; color: #558b2f; }
        .buy-button {
            display: inline-block; margin-top: 1rem; padding: 12px 30px;
            background: linear-gradient(135deg, #2e7d32, #4caf50); color: #fff;
            text-decoration: none; border-radius: 30px; font-weight: 600;
        }
        .paystack-badge {
            display: flex; align-items: center; justify-content: center;
            gap: 10px; margin: 2rem 0; padding: 1rem;
            background: rgba(46,125,50,0.05); border-radius: 15px;
        }
        .footer-note { text-align: center; color: #6d8a6e; font-size: 0.8rem; margin-top: 3rem; }
        .feature-grid { display: flex; justify-content: center; gap: 3rem; margin: 2rem 0; }
        .feature-item { text-align: center; }
        .feature-icon { font-size: 2rem; margin-bottom: 0.5rem; }
        .feature-text { font-size: 0.9rem; color: #558b2f; }
    </style>
    """, unsafe_allow_html=True)

# ---------- Page content ----------
st.markdown('<div class="title">💳 Buy Scans</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Choose a plan that fits your diagnostic needs</div>', unsafe_allow_html=True)

# Paystack badge with reliable inline SVG
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

# Pricing plans
PAYSTACK_PLANS = {
    "10": {"scans": 10, "price": "$0.50", "url": "https://paystack.shop/pay/e-z03btaq-", "popular": False},
    "25": {"scans": 25, "price": "$1.00", "url": "https://paystack.shop/pay/nc3bs0quuh", "popular": True},
    "60": {"scans": 60, "price": "$2.00", "url": "https://paystack.shop/pay/1j9yrapbt4", "popular": False},
    "250": {"scans": 250, "price": "$8.00", "url": "https://paystack.shop/pay/rln87t1694", "popular": False},
    "unlimited": {"scans": "∞", "price": "$20.00", "url": "https://paystack.shop/pay/07zduaem6l", "popular": False}
}

# Display cards
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
            <a href="{plan_data['url']}" target="_blank" class="buy-button">Buy Now</a>
        </div>
        """, unsafe_allow_html=True)

# Feature grid
st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
st.markdown("""
    <div class="feature-item">
        <div class="feature-icon">🔒</div>
        <div class="feature-text">Secure Payment</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">⚡</div>
        <div class="feature-text">Instant Activation</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">📊</div>
        <div class="feature-text">Track Usage</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">💬</div>
        <div class="feature-text">24/7 Support</div>
    </div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer-note">
    Need help? Contact <a href="mailto:darkmoorltd@gmail.com">darkmoorltd@gmail.com</a><br>
    Powered by <strong>Darkmoor Ltd</strong>
</div>
""", unsafe_allow_html=True)
