
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import uuid
import requests as req

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
PAYSTACK_PUBLIC_KEY = "pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057"
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_payment(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    try:
        r = req.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") and data["data"]["status"] == "success":
                tx = data["data"]
                return {"success": True, "amount": tx["amount"] / 100, "reference": tx["reference"]}
    except:
        pass
    return {"success": False}

st.set_page_config(page_title="GAIA – Buy Scans", page_icon="💳", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = init_supabase()

user_data = supabase.table("user_scans").select("scans_remaining, plan").eq("user_id", user.id).execute()
scans_left = user_data.data[0]["scans_remaining"] if (user_data.data and len(user_data.data) > 0) else 30

PLANS = {
    "10": {"scans": 10, "price": "₦500", "amount": 50000, "color": "#4caf50", "icon": "🌱"},
    "25": {"scans": 25, "price": "₦1,000", "amount": 100000, "color": "#2196f3", "icon": "🌿"},
    "60": {"scans": 60, "price": "₦2,000", "amount": 200000, "color": "#ff9800", "icon": "🌳"},
    "250": {"scans": 250, "price": "₦8,000", "amount": 800000, "color": "#9c27b0", "icon": "🏆"},
    "unlimited": {"scans": 9999, "price": "₦20,000", "amount": 2000000, "color": "#f44336", "icon": "👑"},
}

# ========== WORLD-CLASS LIGHT MODE CSS ==========
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(160deg, #f8fafc 0%, #f0fdf4 30%, #ecfdf5 60%, #f8fafc 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    header, footer {visibility: hidden;}
    
    .hero-title {
        font-size: 3.2rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(135deg, #166534, #22c55e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
        margin-bottom: 0.3rem;
    }
    .hero-subtitle {
        text-align: center;
        font-size: 1.1rem;
        color: #64748b;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    .balance-badge {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.8rem;
        background: white;
        border-radius: 20px;
        padding: 1.2rem 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        border: 1px solid rgba(34,197,94,0.15);
        max-width: 400px;
        margin: 0 auto 2rem auto;
    }
    .balance-number {
        font-size: 2.4rem;
        font-weight: 700;
        color: #166534;
    }
    .balance-label {
        font-size: 0.9rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .plan-card {
        background: white;
        border-radius: 24px;
        padding: 2rem 1.5rem;
        width: 190px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 16px rgba(0,0,0,0.04);
        border: 2px solid transparent;
        position: relative;
        overflow: hidden;
    }
    .plan-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.08);
    }
    .plan-card.selected {
        border-color: #22c55e;
        box-shadow: 0 8px 32px rgba(34,197,94,0.15);
        transform: translateY(-6px);
    }
    .plan-icon {
        font-size: 2.4rem;
        margin-bottom: 0.8rem;
    }
    .plan-scans {
        font-size: 1rem;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .plan-price {
        font-size: 2rem;
        font-weight: 800;
        color: #166534;
        margin-bottom: 0.3rem;
    }
    
    .selected-banner {
        background: linear-gradient(135deg, #f0fdf4, #dcfce7);
        border: 2px solid #22c55e;
        border-radius: 20px;
        padding: 1.5rem 2rem;
        text-align: center;
        margin: 1.5rem 0;
        animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.2); }
        50% { box-shadow: 0 0 0 12px rgba(34,197,94,0); }
    }
    .selected-banner h3 {
        color: #166534;
        margin: 0;
        font-size: 1.4rem;
    }
    
    .manual-section {
        max-width: 600px;
        margin: 2rem auto;
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.03);
        border: 1px solid rgba(0,0,0,0.06);
    }
    
    .footer-line {
        text-align: center;
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)

# ========== HERO ==========
st.markdown('<div class="hero-title">💳 Upgrade Your Scans</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Get more AI‑powered diagnoses for your farm</div>', unsafe_allow_html=True)

# ========== BALANCE ==========
st.markdown(f"""
<div class="balance-badge">
    <div>
        <div class="balance-label">Scans Remaining</div>
        <div class="balance-number">{scans_left}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ========== PLAN CARDS ==========
st.markdown("### Choose Your Plan")

if "chosen_plan" not in st.session_state:
    st.session_state.chosen_plan = None

cols = st.columns(len(PLANS))
for i, (plan_key, plan_data) in enumerate(PLANS.items()):
    with cols[i]:
        selected_class = "selected" if st.session_state.chosen_plan == plan_key else ""
        st.markdown(f"""
        <div class="plan-card {selected_class}" style="border-top: 4px solid {plan_data['color']};">
            <div class="plan-icon">{plan_data['icon']}</div>
            <div class="plan-scans">{plan_data['scans'] if plan_key != 'unlimited' else '♾️'} scans</div>
            <div class="plan-price">{plan_data['price']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Select", key=f"select_{plan_key}", use_container_width=True):
            st.session_state.chosen_plan = plan_key
            st.rerun()

# ========== PAYMENT SECTION ==========
if st.session_state.chosen_plan:
    plan_data = PLANS[st.session_state.chosen_plan]
    
    st.markdown(f"""
    <div class="selected-banner">
        <h3>{plan_data['icon']} {plan_data['scans']} scans — {plan_data['price']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    ref = f"GAIA_{user.id[:8]}_{st.session_state.chosen_plan}_{uuid.uuid4().hex[:6]}"
    
    # FULL SCREEN Paystack Popup (standard, not iframe)
    paystack_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://js.paystack.co/v1/inline.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                background: transparent;
            }}
            .pay-now-btn {{
                background: linear-gradient(135deg, #16a34a, #22c55e);
                color: white;
                border: none;
                padding: 20px 60px;
                border-radius: 50px;
                font-weight: 700;
                font-size: 1.2rem;
                cursor: pointer;
                box-shadow: 0 8px 24px rgba(22,163,74,0.3);
                transition: all 0.3s ease;
                letter-spacing: 0.3px;
                width: 100%;
                max-width: 400px;
            }}
            .pay-now-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 14px 32px rgba(22,163,74,0.4);
                background: linear-gradient(135deg, #15803d, #16a34a);
            }}
        </style>
    </head>
    <body>
        <button class="pay-now-btn" onclick="payWithPaystack()">
            💳 Pay {plan_data['price']} Now
        </button>
        <script>
            function payWithPaystack() {{
                var handler = PaystackPop.setup({{
                    key: '{PAYSTACK_PUBLIC_KEY}',
                    email: '{user.email}',
                    amount: {plan_data['amount']},
                    currency: 'NGN',
                    ref: '{ref}',
                    label: 'GAIA {plan_data["scans"]} Scans',
                    onClose: function() {{ window.parent.location.reload(); }},
                    callback: function(response) {{
                        window.location.href = 'https://gaiagpt.streamlit.app/~/callback?reference=' + response.reference + '&plan={st.session_state.chosen_plan}';
                    }}
                }});
                handler.openIframe();
            }}
        </script>
    </body>
    </html>
    """
    components.html(paystack_html, height=80)

# ========== MANUAL VERIFICATION ==========
st.markdown("---")
with st.container():
    st.markdown('<div class="manual-section">', unsafe_allow_html=True)
    st.markdown("#### ✅ Already Paid?")
    st.markdown("Enter your Paystack reference below to verify your payment.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        manual_ref = st.text_input("Paystack reference", placeholder="e.g., GAIA_12345_10_a1b2c3", label_visibility="collapsed")
    with col2:
        if st.button("🔍 Verify", use_container_width=True) and manual_ref:
            with st.spinner("Verifying…"):
                result = verify_payment(manual_ref)
                if result["success"]:
                    existing = supabase.table("payment_history").select("*").eq("reference", manual_ref).execute()
                    if existing.data and len(existing.data) > 0:
                        st.warning("⚠️ This reference has already been used.")
                    else:
                        amount_paid = result["amount"]
                        plan_match = None
                        for pk, pd in PLANS.items():
                            if abs(pd["amount"] / 100 - amount_paid) < 1:
                                plan_match = pk
                                break
                        if plan_match:
                            scans_to_add = PLANS[plan_match]["scans"]
                            current = supabase.table("user_scans").select("scans_remaining").eq("user_id", user.id).execute()
                            current_scans = current.data[0]["scans_remaining"] if (current.data and len(current.data) > 0) else 0
                            new_total = current_scans + scans_to_add
                            supabase.table("user_scans").update({"scans_remaining": new_total, "plan": plan_match}).eq("user_id", user.id).execute()
                            supabase.table("payment_history").insert({"user_id": user.id, "amount": amount_paid, "scans_added": scans_to_add, "plan": plan_match, "reference": manual_ref}).execute()
                            st.success(f"✅ {scans_to_add} scans added! Your new balance: **{new_total}**")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"Amount ₦{amount_paid:,.2f} doesn't match any plan.")
                else:
                    st.error("❌ Payment not found. Check your reference or try again.")
    st.markdown('</div>', unsafe_allow_html=True)

# ========== FOOTER ==========
st.markdown("""
<div class="footer-line">
    🔒 Secure payments by <strong>Paystack</strong> &nbsp;|&nbsp; Powered by <strong>Darkmoor Ltd</strong>
</div>
""", unsafe_allow_html=True)

# ========== QUICK NAV ==========
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(8)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/10_Early_Warning.py", label="🛰️ Early Warning")
with cols[6]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[7]: st.page_link("pages/13_Help.py", label="💬 Help")
