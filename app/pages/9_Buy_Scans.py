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
    "10": {"scans": 10, "price": "₦500", "amount": 50000},
    "25": {"scans": 25, "price": "₦1,000", "amount": 100000},
    "60": {"scans": 60, "price": "₦2,000", "amount": 200000},
    "250": {"scans": 250, "price": "₦8,000", "amount": 800000},
    "unlimited": {"scans": 9999, "price": "₦20,000", "amount": 2000000},
}

st.markdown('''
<style>
    .stApp {
        background: linear-gradient(160deg, #f4faf5 0%, #eaf5ee 30%, #fdfefb 100%);
        color: #1b5e20;
    }
    header, footer {visibility: hidden;}
    .page-title {
        font-size: 2.8rem; font-weight: 800; text-align: center;
        background: linear-gradient(135deg, #1b5e20, #4caf50);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .page-subtitle { text-align: center; color: #607d8b; font-size: 1.1rem; margin-bottom: 2.5rem; }
    .scan-badge {
        background: linear-gradient(135deg, #ffffff, #f1f8e9);
        border: 1px solid #c8e6c9;
        border-radius: 18px; padding: 1rem 2rem;
        display: inline-block; box-shadow: 0 6px 20px rgba(0,0,0,0.04);
        margin-bottom: 2rem;
    }
    .scan-number { font-size: 2.5rem; font-weight: 900; color: #2e7d32; }
    .scan-label { font-size: 0.85rem; color: #78909c; text-transform: uppercase; letter-spacing: 0.08em; }
    .plan-card {
        background: #ffffff;
        border-radius: 24px;
        padding: 2rem 1rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        border: 2px solid transparent;
        transition: all 0.25s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    .plan-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(46,125,50,0.15);
        border-color: #a5d6a7;
    }
    .plan-card.selected {
        border-color: #2e7d32;
        background: linear-gradient(160deg, #e8f5e9, #ffffff);
        box-shadow: 0 12px 35px rgba(46,125,50,0.25);
    }
    .plan-scans { font-size: 1.1rem; font-weight: 600; color: #546e7a; margin-bottom: 0.5rem; }
    .plan-price { font-size: 2.4rem; font-weight: 900; color: #1b5e20; margin: 0.5rem 0; }
    .selected-banner {
        background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
        border: 2px solid #2e7d32; border-radius: 20px;
        padding: 1.5rem 2rem; text-align: center; margin: 1.8rem 0;
    }
</style>
''', unsafe_allow_html=True)

st.markdown('<div class="page-title">💳 Buy Scans</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Get more AI-powered diagnoses for your farm</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f'<div style="text-align:center;"><div class="scan-badge"><div class="scan-number">{scans_left}</div><div class="scan-label">Scans Remaining</div></div></div>', unsafe_allow_html=True)

st.markdown("### 📦 Choose Your Plan")

if "chosen_plan" not in st.session_state:
    st.session_state.chosen_plan = None

cols = st.columns(len(PLANS))
for i, (plan_key, plan_data) in enumerate(PLANS.items()):
    with cols[i]:
        scans_display = "♾️ Unlimited" if plan_key == "unlimited" else f"{plan_data['scans']} scans"
        selected_class = "selected" if st.session_state.chosen_plan == plan_key else ""
        st.markdown(f'<div class="plan-card {selected_class}"><div class="plan-scans">{scans_display}</div><div class="plan-price">{plan_data["price"]}</div></div>', unsafe_allow_html=True)
        if st.button("Select", key=f"select_{plan_key}", use_container_width=True):
            st.session_state.chosen_plan = plan_key
            st.rerun()

if st.session_state.chosen_plan:
    plan_data = PLANS[st.session_state.chosen_plan]
    scans_display = "♾️ Unlimited" if st.session_state.chosen_plan == "unlimited" else f"{plan_data['scans']} scans"
    
    st.markdown(f'<div class="selected-banner"><h3 style="margin:0;color:#1b5e20;">🛒 {scans_display} — {plan_data["price"]}</h3></div>', unsafe_allow_html=True)
    
    ref = f"GAIA_{user.id[:8]}_{st.session_state.chosen_plan}_{uuid.uuid4().hex[:6]}"
    
    paystack_html = f'''<!DOCTYPE html>
<html>
<head>
    <script src="https://js.paystack.co/v1/inline.js"></script>
    <style>
        body {{ margin:0; padding:0; }}
        .pay-btn {{
            background: linear-gradient(135deg, #2e7d32, #43a047);
            color: #fff; border: none; padding: 18px 50px;
            border-radius: 50px; font-weight: 700; font-size: 1.2rem;
            cursor: pointer; width: 100%; box-shadow: 0 10px 30px rgba(46,125,50,0.3);
        }}
        .pay-btn:hover {{ transform: scale(1.03); }}
        .overlay {{
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.55); z-index: 9998; display: none;
        }}
        .popup-container {{
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 600px; height: 600px; z-index: 9999; display: none;
            background: #fff; border-radius: 28px; box-shadow: 0 30px 60px rgba(0,0,0,0.3);
        }}
    </style>
</head>
<body>
    <button class="pay-btn" onclick="openPaystackPopup()">💳 Pay {plan_data['price']} Now</button>
    <div id="overlay" class="overlay"></div>
    <div id="popupContainer" class="popup-container"></div>
    <script>
        function openPaystackPopup() {{
            document.getElementById('overlay').style.display = 'block';
            var container = document.getElementById('popupContainer');
            container.style.display = 'block';
            container.innerHTML = '';
            
            var handler = PaystackPop.setup({{
                key: '{PAYSTACK_PUBLIC_KEY}',
                email: '{user.email}',
                amount: {plan_data['amount']},
                currency: 'NGN',
                ref: '{ref}',
                label: 'GAIA {scans_display}',
                onClose: function() {{
                    document.getElementById('overlay').style.display = 'none';
                    container.style.display = 'none';
                    window.location.reload();
                }},
                callback: function(response) {{
                    window.location.href = 'https://gaiagpt.streamlit.app/~/callback?reference=' + response.reference + '&plan={st.session_state.chosen_plan}';
                }}
            }});
            handler.openIframe();
            
            setTimeout(function() {{
                var iframe = document.querySelector('iframe[name="paystack-popup"]');
                if (iframe) {{
                    iframe.style.width = '600px';
                    iframe.style.height = '600px';
                    iframe.style.border = 'none';
                    iframe.style.borderRadius = '28px';
                    container.appendChild(iframe);
                }}
            }}, 600);
        }}
    </script>
</body>
</html>'''
    components.html(paystack_html, height=120)

st.markdown("---")
st.markdown("### ✅ Already Paid? Enter Your Reference")

col1, col2 = st.columns([3, 1])
with col1:
    manual_ref = st.text_input("Paste your Paystack reference", placeholder="e.g., GAIA_12345_10_a1b2c3")
with col2:
    st.write("")
    st.write("")
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
                        st.success(f"✅ {scans_to_add} scans added! New balance: {new_total}")
                        st.rerun()
                    else:
                        st.error(f"Amount ₦{amount_paid:,.2f} doesn't match any plan.")
            else:
                st.error("❌ Payment not found.")

st.markdown("---")
st.caption("🔒 Secure payments powered by **Paystack** · **Darkmoor Ltd**")

cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
