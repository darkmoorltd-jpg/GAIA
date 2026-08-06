
import streamlit as st
from supabase import create_client, Client
import requests as req

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
PAYSTACK_PUBLIC_KEY = "pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057"
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_payment(reference):
    """Verify a Paystack transaction."""
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    try:
        r = req.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status"):
                tx = data.get("data", {})
                return {
                    "paid": tx.get("status") == "success",
                    "email": tx.get("customer", {}).get("email", ""),
                    "amount": tx.get("amount", 0) / 100
                }
    except:
        pass
    return {"paid": False, "email": "", "amount": 0}

st.set_page_config(page_title="GAIA – Buy Scans", page_icon="💳", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = init_supabase()

PLANS = {
    "10": {"scans": 10, "price": "N500", "amount": 500},
    "25": {"scans": 25, "price": "N1,000", "amount": 1000},
    "60": {"scans": 60, "price": "N2,000", "amount": 2000},
    "250": {"scans": 250, "price": "N8,000", "amount": 8000},
    "unlimited": {"scans": 9999, "price": "N20,000", "amount": 20000},
}

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa, #e8f5e9); }
    .title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #2e7d32; }
    .subtitle { text-align: center; color: #555; margin-bottom: 2rem; }
    .plan-card {
        background: #fff; border-radius: 15px; padding: 1.5rem;
        text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,.05);
        margin: 0.5rem; transition: all 0.3s ease;
    }
    .plan-card:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(46,125,50,.15); }
    .plan-price { font-size: 2rem; font-weight: 900; color: #2e7d32; }
    .plan-name { font-size: 1.1rem; color: #555; }
    .popular-badge {
        position: absolute; top: -10px; right: 20px;
        background: #2e7d32; color: #fff; padding: 5px 15px;
        border-radius: 20px; font-size: 0.8rem; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">💳 Buy Scans</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Secure payment via Paystack — instant activation</div>', unsafe_allow_html=True)

# Show current scans
user_data = supabase.table("user_scans").select("scans_remaining, plan").eq("user_id", user.id).execute()
scans_left = user_data.data[0]["scans_remaining"] if (user_data.data and len(user_data.data) > 0) else 30
st.sidebar.metric("Scans Remaining", scans_left)

# Handle Paystack callback
query_params = st.query_params
reference = query_params.get("reference", [None])[0]

if reference:
    result = verify_payment(reference)
    if result["paid"]:
        plan_key = query_params.get("plan", ["10"])[0]
        scans_to_add = PLANS.get(plan_key, PLANS["10"])["scans"]
        
        current = supabase.table("user_scans").select("scans_remaining").eq("user_id", user.id).execute()
        current_scans = current.data[0]["scans_remaining"] if (current.data and len(current.data) > 0) else 0
        new_total = current_scans + scans_to_add
        
        supabase.table("user_scans").update({
            "scans_remaining": new_total,
            "plan": plan_key
        }).eq("user_id", user.id).execute()
        
        supabase.table("payment_history").insert({
            "user_id": user.id,
            "amount": result["amount"],
            "scans_added": scans_to_add,
            "plan": plan_key,
            "reference": reference
        }).execute()
        
        st.success(f"✅ Payment successful! {scans_to_add} scans added. New balance: {new_total}")
        st.query_params.clear()
        st.rerun()
    else:
        st.error("Payment verification failed. Please contact support.")

# Pricing cards
st.markdown("### Choose Your Plan")
cols = st.columns(len(PLANS))

for i, (plan_key, plan_data) in enumerate(PLANS.items()):
    with cols[i]:
        popular = plan_key == "60"
        st.markdown(f"""
        <div class="plan-card" style="position: relative;">
            {'<div class="popular-badge">MOST POPULAR</div>' if popular else ''}
            <div class="plan-name">{plan_data['scans']} SCANS</div>
            <div class="plan-price">{plan_data['price']}</div>
            <p style="color: #888; font-size: 0.8rem;">per month</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate Paystack payment URL
        paystack_url = f"https://paystack.shop/pay/{plan_key}?reference=GAIA_{user.id[:8]}_{plan_key}"
        
        if st.button(f"Buy {plan_data['scans']} Scans", key=f"buy_{plan_key}"):
            st.markdown(f'<meta http-equiv="refresh" content="0; url={paystack_url}">', unsafe_allow_html=True)

st.markdown("---")
st.caption("Payments processed securely by Paystack | Darkmoor Ltd")

# Quick Navigation
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
