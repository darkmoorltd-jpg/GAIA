
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
    "10 Scans — ₦500": {"key": "10", "scans": 10, "amount": 50000},
    "25 Scans — ₦1,000": {"key": "25", "scans": 25, "amount": 100000},
    "60 Scans — ₦2,000": {"key": "60", "scans": 60, "amount": 200000},
    "250 Scans — ₦8,000": {"key": "250", "scans": 250, "amount": 800000},
    "Unlimited — ₦20,000": {"key": "unlimited", "scans": 9999, "amount": 2000000},
}

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa, #e8f5e9); }
    .title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #2e7d32; }
    .popup-btn {
        background: linear-gradient(135deg, #2e7d32, #4caf50);
        color: #fff; border: none; padding: 20px 40px;
        border-radius: 40px; font-weight: 800; cursor: pointer;
        width: 100%; font-size: 1.3rem; margin-top: 1rem;
    }
    .selected-banner {
        background: #e8f5e9; border: 2px solid #2e7d32; border-radius: 15px;
        padding: 1.5rem; text-align: center; margin: 1rem 0;
    }
    .selected-banner h2 { color: #2e7d32; margin: 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">💳 Buy Scans</div>', unsafe_allow_html=True)
st.metric("Scans Remaining", scans_left)

# ---- STEP 1: Select Plan (Radio Buttons) ----
st.markdown("---")
st.subheader("Step 1: Select a Plan")

plan_choice = st.radio(
    "Choose your plan",
    list(PLANS.keys()),
    index=None,
    format_func=lambda x: f"{x}",
    key="plan_radio"
)

# ---- STEP 2: Pay Button (only shows after selection) ----
if plan_choice:
    plan_data = PLANS[plan_choice]
    plan_key = plan_data["key"]
    ref = f"GAIA_{user.id[:8]}_{plan_key}_{uuid.uuid4().hex[:6]}"
    
    st.markdown(f"""
    <div class="selected-banner">
        <h2>🛒 {plan_choice}</h2>
        <p style="font-size:1.1rem;margin-top:0.5rem;">Click the button below to pay securely with Paystack</p>
    </div>
    """, unsafe_allow_html=True)
    
    # BIG popup — 500px height gives Paystack room to display properly
    paystack_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://js.paystack.co/v1/inline.js"></script>
        <style>
            body {{ margin:0; padding:20px; background: transparent; display:flex; justify-content:center; align-items:center; min-height:400px; }}
            button {{
                background: linear-gradient(135deg, #2e7d32, #4caf50);
                color: #fff; border: none; padding: 25px 50px;
                border-radius: 50px; font-weight: 800; cursor: pointer;
                font-size: 1.4rem; width: 100%; max-width: 500px;
                box-shadow: 0 10px 30px rgba(46,125,50,.3);
                transition: all 0.3s ease;
            }}
            button:hover {{ transform: scale(1.03); box-shadow: 0 15px 40px rgba(46,125,50,.4); }}
        </style>
    </head>
    <body>
        <button onclick="payWithPaystack()">🔒 Pay Securely with Paystack</button>
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
                        window.location.href = 'https://gaiagpt.streamlit.app/~/callback?reference=' + response.reference + '&plan={plan_key}';
                    }}
                }});
                handler.openIframe();
            }}
        </script>
    </body>
    </html>
    """
    components.html(paystack_html, height=500)

# ---- STEP 3: Manual Reference Verification ----
st.markdown("---")
st.subheader("✅ Already Paid? Verify Your Payment")

col1, col2 = st.columns([3, 1])
with col1:
    manual_ref = st.text_input("Paste your Paystack reference number", placeholder="e.g., GAIA_12345_10_a1b2c3", key="manual_ref")
with col2:
    st.write("")
    st.write("")
    if st.button("🔍 Verify Payment", use_container_width=True) and manual_ref:
        with st.spinner("Verifying..."):
            result = verify_payment(manual_ref)
            if result["success"]:
                existing = supabase.table("payment_history").select("*").eq("reference", manual_ref).execute()
                if existing.data and len(existing.data) > 0:
                    st.warning("This reference has already been used.")
                else:
                    amount_paid = result["amount"]
                    plan_match = None
                    for name, pd in PLANS.items():
                        if abs(pd["amount"] / 100 - amount_paid) < 1:
                            plan_match = pd["key"]
                            break
                    
                    if plan_match:
                        scans_to_add = next(p["scans"] for p in PLANS.values() if p["key"] == plan_match)
                        current = supabase.table("user_scans").select("scans_remaining").eq("user_id", user.id).execute()
                        current_scans = current.data[0]["scans_remaining"] if (current.data and len(current.data) > 0) else 0
                        new_total = current_scans + scans_to_add
                        
                        supabase.table("user_scans").update({"scans_remaining": new_total, "plan": plan_match}).eq("user_id", user.id).execute()
                        supabase.table("payment_history").insert({"user_id": user.id, "amount": amount_paid, "scans_added": scans_to_add, "plan": plan_match, "reference": manual_ref}).execute()
                        
                        st.success(f"✅ {scans_to_add} scans added! New balance: {new_total}")
                        st.rerun()
                    else:
                        st.error(f"Amount (₦{amount_paid:,.2f}) doesn't match any plan.")
            else:
                st.error("❌ Payment not found. Check your reference and try again.")

st.markdown("---")
st.caption("Powered by Darkmoor Ltd | Payments by Paystack")

cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
