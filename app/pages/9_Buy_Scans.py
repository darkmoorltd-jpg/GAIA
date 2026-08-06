
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

st.set_page_config(page_title="GAIA – Buy Scans", page_icon="💳", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = init_supabase()

# Get current scans
user_data = supabase.table("user_scans").select("scans_remaining, plan").eq("user_id", user.id).execute()
scans_left = user_data.data[0]["scans_remaining"] if (user_data.data and len(user_data.data) > 0) else 30
current_plan = user_data.data[0]["plan"] if (user_data.data and len(user_data.data) > 0) else "free"

# Get user email and phone
profile = supabase.table("user_profiles").select("phone, first_name, last_name").eq("user_id", user.id).execute()
user_phone = profile.data[0]["phone"] if (profile.data and len(profile.data) > 0) else ""
user_name = f"{profile.data[0].get('first_name','')} {profile.data[0].get('last_name','')}".strip() if (profile.data and len(profile.data) > 0) else ""

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
    .title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #2e7d32; }
    .subtitle { text-align: center; color: #555; margin-bottom: 2rem; }
    .plan-card {
        background: #fff; border-radius: 15px; padding: 1.5rem;
        text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,.05);
        margin: 0.5rem; cursor: pointer; transition: all 0.3s ease;
    }
    .plan-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,.1); }
    .plan-price { font-size: 2rem; font-weight: 900; color: #2e7d32; }
    .plan-scans { font-size: 1.2rem; color: #555; }
    .buy-btn {
        background: linear-gradient(135deg, #2e7d32, #4caf50);
        color: #fff; border: none; padding: 12px 30px;
        border-radius: 30px; font-weight: 600; cursor: pointer;
        width: 100%; margin-top: 1rem; font-size: 1rem;
    }
    .buy-btn:hover { box-shadow: 0 0 20px rgba(46,125,50,.3); }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">💳 Buy Scans</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Pay securely with Paystack — instant activation</div>', unsafe_allow_html=True)

# Show current balance
col1, col2 = st.columns(2)
with col1:
    st.metric("Scans Remaining", scans_left)
with col2:
    st.metric("Current Plan", current_plan.title())

st.markdown("---")
st.markdown("### Select a Plan")

# Display plans in a row
cols = st.columns(len(PLANS))
selected_plan = None

for i, (plan_key, plan_data) in enumerate(PLANS.items()):
    with cols[i]:
        st.markdown(f"""
        <div class="plan-card">
            <div class="plan-scans">{plan_data['scans'] if plan_key != 'unlimited' else '♾️'} scans</div>
            <div class="plan-price">{plan_data['price']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Buy {plan_data['scans']} scans", key=f"buy_{plan_key}", use_container_width=True):
            selected_plan = plan_key
            # Generate unique reference
            ref = f"GAIA_SCAN_{user.id[:8]}_{plan_key}_{uuid.uuid4().hex[:8]}"
            
            # Save pending payment
            supabase.table("pending_payments").insert({
                "user_id": user.id,
                "reference": ref,
                "plan": plan_key,
                "amount": plan_data["amount"] / 100,
                "scans": plan_data["scans"],
                "status": "pending"
            }).execute()
            
            # Build Paystack popup HTML
            paystack_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://js.paystack.co/v1/inline.js"></script>
            </head>
            <body>
                <script>
                    var handler = PaystackPop.setup({{
                        key: '{PAYSTACK_PUBLIC_KEY}',
                        email: '{user.email}',
                        amount: {plan_data['amount']},
                        currency: 'NGN',
                        ref: '{ref}',
                        label: 'GAIA {plan_data["scans"]} Scans',
                        firstname: '{user_name.split()[0] if user_name else "Farmer"}',
                        phone: '{user_phone}',
                        onClose: function() {{
                            window.parent.location.reload();
                        }},
                        callback: function(response) {{
                            var ref = response.reference;
                            window.location.href = 'https://gaiagpt.streamlit.app/~/callback?reference=' + ref + '&plan={plan_key}';
                        }}
                    }});
                    handler.openIframe();
                </script>
            </body>
            </html>
            """
            
            # Display the Paystack popup
            components.html(paystack_html, height=0)
            st.success(f"🔄 Processing payment for {plan_data['scans']} scans...")
            st.info("If popup doesn't appear, allow popups and click the button again.")

st.markdown("---")
st.caption("Payments processed securely by Paystack. Scans added instantly after payment.")

# Quick Navigation
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
