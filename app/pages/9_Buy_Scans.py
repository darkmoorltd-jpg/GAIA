
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
    """Verify a Paystack transaction and return details."""
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    try:
        r = req.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") and data["data"]["status"] == "success":
                tx = data["data"]
                return {
                    "success": True,
                    "amount": tx["amount"] / 100,
                    "reference": tx["reference"],
                    "email": tx.get("customer", {}).get("email", "")
                }
    except:
        pass
    return {"success": False}

st.set_page_config(page_title="GAIA – Buy Scans", page_icon="💳", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = init_supabase()

# Get current scans
user_data = supabase.table("user_scans").select("scans_remaining, plan").eq("user_id", user.id).execute()
scans_left = user_data.data[0]["scans_remaining"] if (user_data.data and len(user_data.data) > 0) else 30

PLANS = {
    "10": {"scans": 10, "price": "₦500", "amount": 50000},
    "25": {"scans": 25, "price": "₦1,000", "amount": 100000},
    "60": {"scans": 60, "price": "₦2,000", "amount": 200000},
    "250": {"scans": 250, "price": "₦8,000", "amount": 800000},
    "unlimited": {"scans": 9999, "price": "₦20,000", "amount": 2000000},
}

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa, #e8f5e9); }
    .title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #2e7d32; }
    .plan-card {
        background: #fff; border-radius: 15px; padding: 1.5rem;
        text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,.05);
        margin: 0.5rem; cursor: pointer; transition: all 0.3s ease;
    }
    .plan-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,.1); }
    .plan-price { font-size: 2rem; font-weight: 900; color: #2e7d32; }
    .plan-scans { font-size: 1.2rem; color: #555; }
    .popup-btn {
        background: linear-gradient(135deg, #2e7d32, #4caf50);
        color: #fff; border: none; padding: 12px 20px;
        border-radius: 30px; font-weight: 600; cursor: pointer;
        width: 100%; margin-top: 0.5rem; font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">💳 Buy Scans</div>', unsafe_allow_html=True)
st.metric("Scans Remaining", scans_left)

# ---- TAB 1: Pay with Paystack ----
st.markdown("---")
st.subheader("🔵 Pay with Paystack (Instant)")

cols = st.columns(len(PLANS))
for i, (plan_key, plan_data) in enumerate(PLANS.items()):
    with cols[i]:
        st.markdown(f"""
        <div class="plan-card">
            <div class="plan-scans">{plan_data['scans'] if plan_key != 'unlimited' else '♾️'} scans</div>
            <div class="plan-price">{plan_data['price']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        ref = f"GAIA_{user.id[:8]}_{plan_key}_{uuid.uuid4().hex[:6]}"
        
        paystack_popup = f"""
        <!DOCTYPE html>
        <html>
        <head><script src="https://js.paystack.co/v1/inline.js"></script></head>
        <body>
            <button onclick="payWithPaystack()" class="popup-btn">Pay {plan_data['price']}</button>
            <script>
                function payWithPaystack() {{
                    var handler = PaystackPop.setup({{
                        key: '{PAYSTACK_PUBLIC_KEY}',
                        email: '{user.email}',
                        amount: {plan_data['amount']},
                        currency: 'NGN',
                        ref: '{ref}',
                        label: 'GAIA {plan_data["scans"]} Scans',
                        onClose: function() {{ alert('Payment cancelled. You can try again.'); }},
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
        components.html(paystack_popup, height=50)

# ---- TAB 2: Already Paid? Confirm Here ----
st.markdown("---")
st.subheader("✅ Already Paid? Enter Your Reference")

col1, col2 = st.columns([3, 1])
with col1:
    manual_ref = st.text_input("Paste your Paystack reference number", placeholder="e.g., GAIA_12345_10_a1b2c3")
with col2:
    st.write("")
    st.write("")
    if st.button("🔍 Verify Payment", use_container_width=True) and manual_ref:
        with st.spinner("Verifying your payment..."):
            result = verify_payment(manual_ref)
            if result["success"]:
                # Check if this reference was already used
                existing = supabase.table("payment_history").select("*").eq("reference", manual_ref).execute()
                if existing.data and len(existing.data) > 0:
                    st.warning("This reference has already been used.")
                else:
                    # Determine which plan based on amount
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
                        
                        supabase.table("user_scans").update({
                            "scans_remaining": new_total,
                            "plan": plan_match
                        }).eq("user_id", user.id).execute()
                        
                        supabase.table("payment_history").insert({
                            "user_id": user.id,
                            "amount": amount_paid,
                            "scans_added": scans_to_add,
                            "plan": plan_match,
                            "reference": manual_ref
                        }).execute()
                        
                        st.success(f"✅ Payment verified! {scans_to_add} scans added. New balance: {new_total}")
                        st.rerun()
                    else:
                        st.error(f"Payment amount (₦{amount_paid:,.2f}) doesn't match any plan.")
            else:
                st.error("❌ Payment not found. Check your reference and try again.")

st.markdown("---")
st.caption("Payments processed securely by Paystack | Contact darkmoorltd@gmail.com for support")

# Quick Navigation
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
