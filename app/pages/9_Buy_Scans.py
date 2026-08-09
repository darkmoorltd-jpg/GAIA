import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import uuid
import requests
from datetime import datetime

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_PUBLIC = "pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057"
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_service_client():
    return create_client(SUPABASE_URL, SERVICE_KEY)

def verify_payment(ref):
    r = requests.get(f"https://api.paystack.co/transaction/verify/{ref}",
                     headers={"Authorization": f"Bearer {PAYSTACK_SECRET}"}, timeout=10)
    if r.status_code == 200:
        d = r.json()
        if d.get("status") and d["data"]["status"] == "success":
            return {"ok": True, "amount": d["data"]["amount"] / 100}
    return {"ok": False}

def process_successful_payment(user_id, plan_key, amount_paid, reference):
    service = get_service_client()
    p = PLANS[plan_key]
    scans_to_add = p["scans"]
    current = service.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
    current_scans = current.data[0]["scans_remaining"] if current.data else 0
    new_total = current_scans + scans_to_add
    service.table("user_scans").update({
        "scans_remaining": new_total,
        "plan": plan_key
    }).eq("user_id", user_id).execute()
    service.table("payment_history").insert({
        "user_id": user_id,
        "amount": amount_paid,
        "scans_added": scans_to_add,
        "plan": plan_key,
        "reference": reference,
        "paid_at": datetime.now().isoformat()
    }).execute()
    return new_total, scans_to_add

st.set_page_config(page_title="Buy Scans", page_icon="💳", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
db = get_supabase()

res = db.table("user_scans").select("scans_remaining, plan").eq("user_id", user.id).execute()
scans = res.data[0]["scans_remaining"] if res.data else 30
current_plan = res.data[0].get("plan", "free") if res.data else "free"

PLANS = {
    "basic":    {"scans": 500,   "price": "₦3,000",   "naira": 3000,   "kobo": 300000},
    "standard": {"scans": 1000,  "price": "₦5,000",   "naira": 5000,   "kobo": 500000},
    "pro":      {"scans": 3000,  "price": "₦10,000",  "naira": 10000,  "kobo": 1000000},
    "max":      {"scans": 15000, "price": "₦25,000",  "naira": 25000,  "kobo": 2500000},
}

# Auto-verify on return from Paystack
query_params = st.query_params
url_ref = query_params.get("reference", [None])[0]
url_plan = query_params.get("plan", [None])[0]

if url_ref and url_plan and url_plan in PLANS:
    with st.spinner("Verifying your payment..."):
        v = verify_payment(url_ref)
        if v["ok"]:
            exist = db.table("payment_history").select("*").eq("reference", url_ref).execute()
            if not exist.data:
                new_total, scans_added = process_successful_payment(user.id, url_plan, v["amount"], url_ref)
                st.success(f"Payment successful! {scans_added:,} scans added.")
                st.success(f"New balance: {new_total:,} scans. Plan: {url_plan.upper()}")
                st.balloons()
                st.query_params.clear()
                st.rerun()
            else:
                st.info("This payment has already been credited.")
                st.query_params.clear()
                st.rerun()
        else:
            st.error("Payment verification failed. Contact support if money was deducted.")
            st.query_params.clear()
            st.rerun()

st.markdown("""
<style>
    .stApp { background: linear-gradient(160deg, #f4faf5, #eaf5ee, #fdfefb); color: #1b5e20; }
    header, footer { visibility: hidden; }
    .title { font-size: 2.8rem; font-weight: 800; text-align: center; background: linear-gradient(135deg, #1b5e20, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { text-align: center; color: #607d8b; font-size: 1.1rem; margin-bottom: 2rem; }
    .badge { background: #fff; border: 1px solid #c8e6c9; border-radius: 18px; padding: 1rem 2rem; display: inline-block; box-shadow: 0 6px 20px rgba(0,0,0,.04); }
    .badge-num { font-size: 2.5rem; font-weight: 900; color: #2e7d32; }
    .badge-lbl { font-size: .85rem; color: #78909c; text-transform: uppercase; letter-spacing: .08em; }
    .plan-badge { background: #2e7d32; color: #fff; padding: 3px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .card { background: #fff; border-radius: 24px; padding: 2rem 1rem; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,.05); border: 2px solid transparent; transition: all .25s; }
    .card:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(46,125,50,.15); border-color: #a5d6a7; }
    .card.sel { border-color: #2e7d32; background: linear-gradient(160deg, #e8f5e9, #fff); }
    .card-name { font-size: 1.1rem; font-weight: 600; color: #546e7a; }
    .card-price { font-size: 2.4rem; font-weight: 900; color: #1b5e20; margin: .5rem 0; }
    .card-scans { font-size: 0.95rem; color: #78909c; }
    .banner { background: linear-gradient(135deg, #e8f5e9, #c8e6c9); border: 2px solid #2e7d32; border-radius: 20px; padding: 1.5rem 2rem; text-align: center; margin: 1.8rem 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">Buy Scans</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Get more AI-powered diagnoses for your farm</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.markdown(f'<div style="text-align:center"><div class="badge"><div class="badge-num">{scans:,}</div><div class="badge-lbl">Scans Remaining <span class="plan-badge">{current_plan}</span></div></div></div>', unsafe_allow_html=True)

st.markdown("### Choose Your Plan")

if "plan" not in st.session_state:
    st.session_state.plan = None

cols = st.columns(len(PLANS))
for i, (key, p) in enumerate(PLANS.items()):
    with cols[i]:
        scans_label = f"{p['scans']:,} scans"
        sel = "sel" if st.session_state.plan == key else ""
        st.markdown(f'<div class="card {sel}"><div class="card-name">{scans_label}</div><div class="card-price">{p["price"]}</div><div class="card-scans">₦{p["naira"]/p["scans"]:.2f} per scan</div></div>', unsafe_allow_html=True)
        if st.button("Select", key=f"btn_{key}", use_container_width=True):
            st.session_state.plan = key
            st.rerun()

if st.session_state.plan:
    p = PLANS[st.session_state.plan]
    label = f"{p['scans']:,} scans"
    ref = f"GAIA_{user.id[:8]}_{st.session_state.plan}_{uuid.uuid4().hex[:6]}"
    st.markdown(f'<div class="banner"><h3 style="margin:0;color:#1b5e20;">{label} — {p["price"]}</h3></div>', unsafe_allow_html=True)
    paystack_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://js.paystack.co/v1/inline.js"></script>
        <style>
            body {{ margin:0; padding:0; display:flex; justify-content:center; align-items:center; min-height:400px; }}
            .btn {{
                padding: 30px 80px; background: linear-gradient(135deg, #0d6efd, #6610f2); color: #fff;
                border: none; border-radius: 30px; font-size: 1.5rem;
                cursor: pointer; font-weight: 600; width: 100%;
            }}
            .btn:hover {{ background: #0b5ed7; }}
        </style>
    </head>
    <body>
        <button class="btn" onclick="payWithPaystack()">💳 Pay {p['price']} — {label}</button>
        <script>
            function payWithPaystack() {{
                PaystackPop.setup({{
                    key: '{PAYSTACK_PUBLIC}',
                    email: '{user.email}',
                    amount: {p['kobo']},
                    currency: 'NGN',
                    ref: '{ref}',
                    label: 'GAIA {label}',
                    onClose: function() {{ window.location.reload(); }},
                    callback: function(response) {{
                        window.location.href = '/?reference=' + response.reference + '&plan={st.session_state.plan}';
                    }}
                }}).openIframe();
            }}
        </script>
    </body>
    </html>
    """
    components.html(paystack_html, height=500)
    st.caption("⏳ A payment popup will appear. If blocked, allow popups for this site.")

st.markdown("---")
st.markdown("### Already Paid? Enter Your Reference")
st.markdown("---")
st.subheader("✅ Already Paid? Verify Your Payment to Continue")
col1, col2 = st.columns([3, 1])
with col1:
    ref_input = st.text_input("Enter your Paystack reference", placeholder="e.g., GAIA_VERIFY_abc123", key="buy_ref")
with col2:
    st.write("")
    if st.button("🔍 Verify Payment", use_container_width=True) and ref_input:
        with st.spinner("Checking..."):
            v = verify_payment(ref_input)
            if v["ok"]:
                exist = db.table("payment_history").select("*").eq("reference", ref_input).execute()
                if exist.data:
                    st.warning("Already used.")
                else:
                    amt = v["amount"]
                    match = None
                    for k, pd in PLANS.items():
                        if abs(pd["naira"] - amt) < 1:
                            match = k
                            break
                    if match:
                        new_total, scans_added = process_successful_payment(user.id, match, amt, ref_input)
                        st.success(f"{scans_added:,} scans added! Balance: {new_total:,}. Plan: {match.upper()}")
                        st.rerun()
                    else:
                        st.error("Amount does not match any plan.")
            else:
                st.error("Payment not found.")

st.markdown("---")
st.caption("Secure payments by Paystack. Darkmoor Ltd")

cols = st.columns(6)
cols[0].page_link("pages/1_Dashboard.py", label="Dashboard")
cols[1].page_link("pages/2_Crops.py", label="Crops")
cols[2].page_link("pages/3_Pests.py", label="Pests")
cols[3].page_link("pages/4_Soil.py", label="Soil")
cols[4].page_link("pages/5_Livestock.py", label="Livestock")
cols[5].page_link("pages/9_Buy_Scans.py", label="Buy Scans")
