
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
    "10": {"scans": 10, "price": "₦500", "amount": 50000, "badge": "", "savings": ""},
    "25": {"scans": 25, "price": "₦1,000", "amount": 100000, "badge": "🔥 POPULAR", "savings": ""},
    "60": {"scans": 60, "price": "₦2,000", "amount": 200000, "badge": "💎 BEST VALUE", "savings": "Save 40%"},
    "250": {"scans": 250, "price": "₦8,000", "amount": 800000, "badge": "", "savings": ""},
    "unlimited": {"scans": 9999, "price": "₦20,000", "amount": 2000000, "badge": "🚀 PRO", "savings": ""},
}

# ---------- WORLD-CLASS CSS ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .stApp {
        background: linear-gradient(160deg, #0a0f0a 0%, #0d1a0d 30%, #0f220f 60%, #0a0f0a 100%);
        color: #e8f5e9;
    }
    header, footer {visibility: hidden;}
    
    /* ── Hero ── */
    .hero {
        text-align: center;
        padding: 2rem 0 1rem;
    }
    .hero-title {
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(135deg, #00e676, #69f0ae, #00e676);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 60px rgba(0,230,118,0.4);
        letter-spacing: -1px;
        animation: titleGlow 3s ease-in-out infinite alternate;
    }
    @keyframes titleGlow {
        from { filter: brightness(1); }
        to { filter: brightness(1.3); }
    }
    .hero-subtitle {
        font-size: 1.3rem;
        color: #81c784;
        font-weight: 400;
        margin-top: 0.5rem;
    }
    
    /* ── Balance Card ── */
    .balance-ring {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        background: conic-gradient(#00e676 0deg, #00e676 var(--scan-deg, 180deg), rgba(255,255,255,0.05) var(--scan-deg, 180deg));
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem;
        position: relative;
        box-shadow: 0 0 40px rgba(0,230,118,0.2);
    }
    .balance-inner {
        width: 110px;
        height: 110px;
        border-radius: 50%;
        background: #0d1a0d;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .balance-number {
        font-size: 2.2rem;
        font-weight: 900;
        color: #00e676;
        line-height: 1;
    }
    .balance-label {
        font-size: 0.7rem;
        color: #81c784;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    /* ── Plan Cards ── */
    .plan-grid {
        display: flex;
        gap: 1rem;
        justify-content: center;
        flex-wrap: wrap;
        margin: 2rem 0;
    }
    .plan-card {
        background: rgba(255,255,255,0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 24px;
        padding: 1.8rem 1.5rem;
        width: 185px;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    .plan-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at center, rgba(0,230,118,0.08) 0%, transparent 70%);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    .plan-card:hover {
        transform: translateY(-12px);
        border-color: rgba(0,230,118,0.3);
        box-shadow: 0 30px 60px rgba(0,230,118,0.15);
    }
    .plan-card:hover::before { opacity: 1; }
    .plan-card.selected {
        border-color: #00e676;
        background: rgba(0,230,118,0.08);
        box-shadow: 0 0 50px rgba(0,230,118,0.25);
        transform: translateY(-8px);
    }
    .plan-badge {
        position: absolute;
        top: 12px;
        right: 12px;
        background: linear-gradient(135deg, #00e676, #00c853);
        color: #000;
        font-size: 0.6rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        letter-spacing: 0.5px;
    }
    .plan-scans {
        font-size: 2rem;
        font-weight: 900;
        color: #fff;
        margin-bottom: 0.3rem;
    }
    .plan-scans span { font-size: 0.9rem; color: #81c784; }
    .plan-price {
        font-size: 1.8rem;
        font-weight: 800;
        color: #00e676;
        margin-bottom: 0.2rem;
    }
    .plan-savings {
        font-size: 0.75rem;
        color: #00e676;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    
    /* ── Pay Button ── */
    .pay-container {
        text-align: center;
        margin: 2rem 0;
    }
    .pay-btn {
        background: linear-gradient(135deg, #00e676, #00c853);
        color: #000;
        border: none;
        padding: 18px 50px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 1.15rem;
        cursor: pointer;
        box-shadow: 0 10px 40px rgba(0,230,118,0.35);
        transition: all 0.3s ease;
        letter-spacing: 0.3px;
    }
    .pay-btn:hover {
        transform: scale(1.06);
        box-shadow: 0 20px 60px rgba(0,230,118,0.5);
    }
    
    /* ── Selected Banner ── */
    .selected-banner {
        background: rgba(0,230,118,0.06);
        border: 2px solid rgba(0,230,118,0.25);
        border-radius: 20px;
        padding: 1.5rem 2rem;
        text-align: center;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    .selected-banner h3 {
        color: #00e676;
        margin: 0;
        font-size: 1.4rem;
        font-weight: 700;
    }
    
    /* ── Manual Reference ── */
    .manual-section {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        backdrop-filter: blur(10px);
    }
    .manual-section h3 {
        color: #e8f5e9;
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    
    /* ── Footer ── */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #4a5a4a;
        font-size: 0.8rem;
        border-top: 1px solid rgba(255,255,255,0.04);
        margin-top: 3rem;
    }
    .footer strong { color: #81c784; }
    
    /* ── Navigation ── */
    .nav-section {
        border-top: 1px solid rgba(255,255,255,0.06);
        padding-top: 1.5rem;
        margin-top: 1rem;
    }
    .nav-section h3 { color: #81c784; font-size: 1rem; }
    
    /* ── Input Styling ── */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        color: #fff;
        padding: 12px 16px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #00e676;
        box-shadow: 0 0 0 2px rgba(0,230,118,0.2);
    }
    .stButton > button {
        background: linear-gradient(135deg, #00e676, #00c853) !important;
        color: #000 !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 12px 24px !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: scale(1.03) !important;
        box-shadow: 0 8px 25px rgba(0,230,118,0.3) !important;
    }
    .stMetric { background: rgba(255,255,255,0.02); border-radius: 16px; padding: 1rem !important; }
</style>
""", unsafe_allow_html=True)

# ---------- HERO ----------
st.markdown('<div class="hero"><div class="hero-title">Power Up GAIA</div><div class="hero-subtitle">Unlock unlimited AI diagnostics for your farm</div></div>', unsafe_allow_html=True)

# ---------- BALANCE RING ----------
scan_pct = min(scans_left / 30, 1.0)
scan_deg = int(scan_pct * 360)
st.markdown(f"""
<div style="text-align:center;">
    <div class="balance-ring" style="--scan-deg:{scan_deg}deg;">
        <div class="balance-inner">
            <div class="balance-number">{scans_left}</div>
            <div class="balance-label">Scans Left</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- PLAN SELECTION ----------
st.markdown("### 📦 Choose Your Plan")

if "chosen_plan" not in st.session_state:
    st.session_state.chosen_plan = None

cols = st.columns(len(PLANS))
for i, (plan_key, plan_data) in enumerate(PLANS.items()):
    with cols[i]:
        selected_class = "selected" if st.session_state.chosen_plan == plan_key else ""
        badge_html = f'<div class="plan-badge">{plan_data["badge"]}</div>' if plan_data["badge"] else ""
        savings_html = f'<div class="plan-savings">{plan_data["savings"]}</div>' if plan_data["savings"] else '<div style="height:1.5rem;"></div>'
        
        st.markdown(f"""
        <div class="plan-card {selected_class}">
            {badge_html}
            <div class="plan-scans">{plan_data['scans'] if plan_key != 'unlimited' else '♾️'} <span>scans</span></div>
            <div class="plan-price">{plan_data['price']}</div>
            {savings_html}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Select", key=f"select_{plan_key}", use_container_width=True):
            st.session_state.chosen_plan = plan_key
            st.rerun()

# ---------- PAYMENT SECTION ----------
if st.session_state.chosen_plan:
    plan_data = PLANS[st.session_state.chosen_plan]
    
    st.markdown(f"""
    <div class="selected-banner">
        <h3>🛒 {plan_data['scans'] if st.session_state.chosen_plan != 'unlimited' else 'Unlimited'} Scans — {plan_data['price']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    ref = f"GAIA_{user.id[:8]}_{st.session_state.chosen_plan}_{uuid.uuid4().hex[:6]}"
    
    # LARGE Paystack popup (increased size via container & scaling)
    paystack_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://js.paystack.co/v1/inline.js"></script>
        <style>
            body {{ margin:0; padding:0; display:flex; justify-content:center; align-items:center; height:200px; }}
            .pay-btn {{
                background: linear-gradient(135deg, #00e676, #00c853);
                color: #000; border: none; padding: 22px 60px;
                border-radius: 50px; font-weight: 700; font-size: 1.2rem;
                cursor: pointer; box-shadow: 0 10px 40px rgba(0,230,118,0.35);
                transition: all 0.3s ease; letter-spacing: 0.3px;
            }}
            .pay-btn:hover {{ transform: scale(1.06); box-shadow: 0 20px 60px rgba(0,230,118,0.5); }}
        </style>
    </head>
    <body>
        <button class="pay-btn" onclick="payWithPaystack()">💳 Pay {plan_data['price']} Now</button>
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
    
    # Increase the iframe height to make the popup larger
    components.html(paystack_html, height=220)

# ---------- MANUAL REFERENCE ----------
st.markdown('<div class="manual-section">', unsafe_allow_html=True)
st.markdown("### ✅ Already Paid? Enter Your Reference")

col1, col2 = st.columns([3, 1])
with col1:
    manual_ref = st.text_input("Paste your Paystack reference", placeholder="e.g., GAIA_12345_10_a1b2c3", label_visibility="collapsed")
with col2:
    if st.button("🔍 Verify", use_container_width=True) and manual_ref:
        with st.spinner("Verifying..."):
            result = verify_payment(manual_ref)
            if result["success"]:
                existing = supabase.table("payment_history").select("*").eq("reference", manual_ref).execute()
                if existing.data and len(existing.data) > 0:
                    st.warning("Reference already used.")
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
                        st.success(f"✅ {scans_to_add} scans added! Balance: {new_total}")
                        st.rerun()
                    else:
                        st.error(f"Amount ₦{amount_paid:,.2f} doesn't match any plan.")
            else:
                st.error("❌ Payment not found.")
st.markdown('</div>', unsafe_allow_html=True)

# ---------- FOOTER ----------
st.markdown('<div class="footer">Powered by <strong>Darkmoor Ltd</strong> | Secure payments by <strong>Paystack</strong></div>', unsafe_allow_html=True)

# ---------- NAVIGATION ----------
st.markdown('<div class="nav-section"><h3>🔗 Quick Navigation</h3></div>', unsafe_allow_html=True)
cols = st.columns(8)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/10_Early_Warning.py", label="🛰️ Early Warning")
with cols[6]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[7]: st.page_link("pages/13_Help.py", label="💬 Help")
