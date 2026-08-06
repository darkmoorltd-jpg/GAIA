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

st.markdown("<style>.stApp{background:linear-gradient(135deg,#f5f7fa,#e8f5e9)}.title{font-size:2.5rem;font-weight:800;text-align:center;color:#2e7d32}.subtitle{text-align:center;color:#555;margin-bottom:2rem}.plan-card{background:#fff;border-radius:15px;padding:1.5rem;text-align:center;box-shadow:0 4px 15px rgba(0,0,0,.05);margin:0.5rem}.plan-price{font-size:2rem;font-weight:900;color:#2e7d32}</style>", unsafe_allow_html=True)

st.markdown('<div class="title">💳 Buy Scans</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Pay securely with Paystack — popup payment, instant scans, SMS receipt</div>', unsafe_allow_html=True)

user_data = supabase.table("user_scans").select("scans_remaining, plan").eq("user_id", user.id).execute()
scans_left = user_data.data[0]["scans_remaining"] if (user_data.data and len(user_data.data) > 0) else 30
current_plan = user_data.data[0]["plan"] if (user_data.data and len(user_data.data) > 0) else "free"
st.sidebar.metric("Scans Remaining", scans_left)
st.sidebar.caption(f"Plan: {current_plan}")

profile = supabase.table("user_profiles").select("phone").eq("user_id", user.id).execute()
user_phone = profile.data[0]["phone"] if (profile.data and len(profile.data) > 0) else ""

query_params = st.query_params
ref = query_params.get("reference", [None])[0]

if ref:
    result = verify_payment(ref)
    if result["paid"]:
        plan_key = query_params.get("plan", ["10"])[0]
        scans_to_add = PLANS.get(plan_key, {}).get("scans", 10)
        
        current = supabase.table("user_scans").select("scans_remaining").eq("user_id", user.id).execute()
        current_scans = current.data[0]["scans_remaining"] if (current.data and len(current.data) > 0) else 0
        new_total = current_scans + scans_to_add
        
        supabase.table("user_scans").update({
            "scans_remaining": new_total, "plan": plan_key
        }).eq("user_id", user.id).execute()
        
        supabase.table("payment_history").insert({
            "user_id": user.id, "amount": result["amount"],
            "scans_added": scans_to_add, "plan": plan_key, "reference": ref
        }).execute()
        
        st.success(f"✅ Payment successful! {scans_to_add} scans added.")
        st.rerun()
    else:
        st.error("Payment not completed or verification failed.")

cols = st.columns(len(PLANS))
for i, (plan_key, plan_data) in enumerate(PLANS.items()):
    with cols[i]:
        scans_display = "UNLIMITED" if plan_key == "unlimited" else f"{plan_data['scans']} SCANS"
        st.markdown(f"""
        <div class="plan-card">
            <h3>{scans_display}</h3>
            <div class="plan-price">{plan_data['price']}</div>
            <p style="color:#888;">per month</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Buy {plan_data['scans']} scans", key=f"buy_{plan_key}"):
            ref = f"GAIA_{user.id[:8]}_{plan_key}_{uuid.uuid4().hex[:8]}"
            
            paystack_code = f"""
            <script src="https://js.paystack.co/v1/inline.js"></script>
            <script>
                var handler = PaystackPop.setup({{
                    key: '{PAYSTACK_PUBLIC_KEY}',
                    email: '{user.email}',
                    amount: {plan_data['amount'] * 100},
                    currency: 'NGN',
                    ref: '{ref}',
                    metadata: {{
                        plan: '{plan_key}',
                        user_id: '{user.id}'
                    }},
                    callback: function(response) {{
                        window.location.href = 'https://gaiagpt.streamlit.app/~/9_Buy_Scans?reference=' + response.reference + '&plan={plan_key}';
                    }},
                    onClose: function() {{
                        alert('Payment cancelled.');
                    }}
                }});
                handler.openIframe();
            </script>
            """
            components.html(paystack_code, height=0)

st.markdown("---")
st.caption("Payments are processed securely by Paystack. | Darkmoor Ltd")
