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
    "10": {"scans": 10, "price": "N500", "amount": 50000},
    "25": {"scans": 25, "price": "N1,000", "amount": 100000},
    "60": {"scans": 60, "price": "N2,000", "amount": 200000},
    "250": {"scans": 250, "price": "N8,000", "amount": 800000},
    "unlimited": {"scans": 9999, "price": "N20,000", "amount": 2000000},
}

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa, #e8f5e9); }
    .title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #2e7d32; margin-bottom: 1rem; }
    .subtitle { text-align: center; color: #555; margin-bottom: 2rem; }
    .plan-card {
        background: #fff; border-radius: 20px; padding: 1.5rem;
        text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,.06);
        margin: 0.5rem; cursor: pointer; transition: all 0.3s ease;
        border: 3px solid transparent;
    }
    .plan-card:hover { transform: translateY(-8px); box-shadow: 0 12px 30px rgba(0,0,0,.1); }
    .plan-card.selected { border-color: #2e7d32; background: #e8f5e9; }
    .plan-price { font-size: 2.2rem; font-weight: 900; color: #2e7d32; }
    .plan-scans { font-size: 1.1rem; color: #555; margin-bottom: 0.5rem; }
    .selected-banner {
        background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
        border: 2px solid #2e7d32; border-radius: 15px;
        padding: 1.5rem; text-align: center; margin: 1.5rem 0;
    }
    .selected-banner h3 { color: #2e7d32; margin: 0; font-size: 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">Buy Scans</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Get more AI diagnoses for your farm</div>', unsafe_allow_html=True)

st.metric("Scans Remaining", scans_left)

st.markdown("---")
st.markdown("### Select a Plan")

if "chosen_plan" not in st.session_state:
    st.session_state.chosen_plan = None

cols = st.columns(len(PLANS))
for i, (plan_key, plan_data) in enumerate(PLANS.items()):
    with cols[i]:
        selected_class = "selected" if st.session_state.chosen_plan == plan_key else ""
        st.markdown(f'<div class="plan-card {selected_class}"><div class="plan-scans">{plan_data["scans"] if plan_key != "unlimited" else "Unlimited"} scans</div><div class="plan-price">{plan_data["price"]}</div></div>', unsafe_allow_html=True)
        if st.button(f"Select {plan_data['scans']} scans", key=f"select_{plan_key}", use_container_width=True):
            st.session_state.chosen_plan = plan_key
            st.rerun()

if st.session_state.chosen_plan:
    plan_data = PLANS[st.session_state.chosen_plan]
    st.markdown(f'<div class="selected-banner"><h3>{plan_data["scans"]} scans — {plan_data["price"]}</h3></div>', unsafe_allow_html=True)
    
    ref = f"GAIA_{user.id[:8]}_{st.session_state.chosen_plan}_{uuid.uuid4().hex[:6]}"
    
    paystack_html = f"""<!DOCTYPE html>
<html>
<head>
    <script src="https://js.paystack.co/v1/inline.js"></script>
    <style>
        body {{ margin:0; padding:0; display:flex; justify-content:center; align-items:center; }}
        .pay-btn {{
            background: linear-gradient(135deg, #2e7d32, #4caf50);
            color: #fff; border: none; padding: 20px 50px;
            border-radius: 40px; font-weight: 700; font-size: 1.2rem;
            cursor: pointer; box-shadow: 0 8px 25px rgba(46,125,50,.3);
            transition: all 0.3s ease;
        }}
        .pay-btn:hover {{ transform: scale(1.05); }}
    </style>
</head>
<body>
    <button class="pay-btn" onclick="payWithPaystack()">Pay {plan_data['price']} Now</button>
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
</html>"""
    components.html(paystack_html, height=80)

st.markdown("---")
st.subheader("Already Paid? Enter Your Reference")

col1, col2 = st.columns([3, 1])
with col1:
    manual_ref = st.text_input("Paste your Paystack reference", placeholder="e.g., GAIA_12345_10_a1b2c3")
with col2:
    st.write("")
    st.write("")
    if st.button("Verify", use_container_width=True) and manual_ref:
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
                        st.success(f"{scans_to_add} scans added! New balance: {new_total}")
                        st.rerun()
                    else:
                        st.error(f"Amount N{amount_paid:,.2f} doesn't match any plan.")
            else:
                st.error("Payment not found.")

st.markdown("---")
st.caption("Secure payments powered by Paystack | Darkmoor Ltd")

cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="Livestock")
with cols[5]: st.page_link("pages/9_Buy_Scans.py", label="Buy Scans")
