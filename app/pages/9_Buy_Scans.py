
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

# ---------- CSS ----------
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
        .subtitle {
            text-align: center; font-size: 1.2rem; color: #90a4ae;
            margin-bottom: 2rem;
        }
        .pricing-grid {
            display: flex; flex-wrap: wrap; justify-content: center;
            gap: 1.5rem; margin: 2rem 0;
        }
        .pricing-card {
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px; padding: 2rem 1.5rem;
            width: 200px; text-align: center;
            transition: all 0.3s ease;
            position: relative; overflow: hidden;
        }
        .pricing-card:hover {
            transform: translateY(-8px);
            border-color: #00c853;
            box-shadow: 0 20px 40px rgba(0,200,83,0.2);
        }
        .pricing-card.popular {
            border-color: #00c853;
            box-shadow: 0 0 30px rgba(0,200,83,0.3);
        }
        .pricing-card.popular::before {
            content: 'POPULAR';
            position: absolute; top: 15px; right: -35px;
            background: #00c853; color: #000;
            font-size: 0.7rem; font-weight: 700;
            padding: 5px 40px; transform: rotate(45deg);
        }
        .plan-name {
            font-size: 1.3rem; font-weight: 700; color: #fff;
            margin-bottom: 0.5rem;
        }
        .plan-scans {
            font-size: 2.5rem; font-weight: 900;
            background: linear-gradient(90deg, #00c853, #69f0ae);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .plan-price {
            font-size: 1.8rem; font-weight: 700; color: #00c853;
            margin: 0.5rem 0;
        }
        .plan-period {
            font-size: 0.8rem; color: #78909c;
        }
        .buy-button {
            display: inline-block; margin-top: 1rem;
            padding: 12px 30px;
            background: linear-gradient(135deg, #00c853, #00a844);
            color: #fff; text-decoration: none;
            border-radius: 30px; font-weight: 600;
            transition: all 0.3s ease;
        }
        .buy-button:hover {
            box-shadow: 0 0 25px rgba(0,200,83,0.5);
            transform: scale(1.05);
        }
        .paystack-badge {
            display: flex; align-items: center; justify-content: center;
            gap: 10px; margin: 2rem 0; padding: 1rem;
            background: rgba(255,255,255,0.03); border-radius: 15px;
        }
        .paystack-badge img {
            height: 40px;
        }
        .footer-note {
            text-align: center; color: #546e7a; font-size: 0.8rem;
            margin-top: 3rem;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
            color: #1b5e20;
        }
        header, footer {visibility: hidden;}
        .title {
            font-size: 3rem; font-weight: 900; text-align: center;
            background: linear-gradient(90deg, #2e7d32, #66bb6a);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
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
            display: inline-block; margin-top: 1rem;
            padding: 12px 30px;
            background: linear-gradient(135deg, #2e7d32, #4caf50);
            color: #fff; text-decoration: none;
            border-radius: 30px; font-weight: 600;
        }
        .paystack-badge {
            display: flex; align-items: center; justify-content: center;
            gap: 10px; margin: 2rem 0; padding: 1rem;
            background: rgba(46,125,50,0.05); border-radius: 15px;
        }
        .footer-note { text-align: center; color: #6d8a6e; font-size: 0.8rem; margin-top: 3rem; }
    </style>
    """, unsafe_allow_html=True)

# ---------- Page content ----------
st.markdown('<div class="title">💳 Buy Scans</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Choose a plan that fits your diagnostic needs</div>', unsafe_allow_html=True)

# Paystack badge
st.markdown("""
<div class="paystack-badge">
    <img src="https://paystack.com/assets/paystack-logo-white.svg" alt="Paystack">
    <span style="color: #78909c;">Secure payments powered by Paystack</span>
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

# Info section
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 🔒 Secure Payment")
    st.write("All transactions are encrypted and processed by Paystack, Nigeria's leading payment gateway.")
with col2:
    st.markdown("### ⚡ Instant Activation")
    st.write("Scans are credited to your account immediately after successful payment.")
with col3:
    st.markdown("### 📊 Track Usage")
    st.write("Monitor your remaining scans from the sidebar and Payment History page.")

# Footer
st.markdown("""
<div class="footer-note">
    Need help? Contact <a href="mailto:darkmoorltd@gmail.com">darkmoorltd@gmail.com</a><br>
    Powered by <strong>Darkmoor Ltd</strong>
</div>
""", unsafe_allow_html=True)
