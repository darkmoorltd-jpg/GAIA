
import streamlit as st
# Get user from session state
    # Allow demo mode
    from supabase import create_client
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
try:
    session = supabase.auth.get_session()
    user = session.user if session else None
except:
    import streamlit.components.v1 as components
from supabase import create_client, Client
import uuid
import requests
import sys
import os

user = st.session_state.get("user", None)
if user is None:
    st.warning("Please log in first.")
    st.stop()
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_PUBLIC = "pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057"
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

def normalize_phone(phone):
    if not phone:
        return ""
    phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    if phone.startswith("0"):
        return "234" + phone[1:]
    elif phone.startswith("234"):
        return phone
    else:
        return "234" + phone

def verify_payment(ref):
    r = requests.get(f"https://api.paystack.co/transaction/verify/{ref}",
                     headers={"Authorization": f"Bearer {PAYSTACK_SECRET}"}, timeout=10)
    if r.status_code == 200:
        d = r.json()
        if d.get("status") and d["data"]["status"] == "success":
            return {"ok": True, "amount": d["data"]["amount"] / 100}
    return {"ok": False}

st.set_page_config(page_title="Buy Scans", page_icon="💳", layout="wide")

    st.session_state["user"] = None
    user = user
db = get_supabase()
service = get_service()

# Fetch current scans
    st.warning("⚠️ Please log in first.")
    st.stop()

    res = service.table("user_scans").select("scans_remaining, plan").eq("user_id", user.id).execute()
if res.data and len(res.data) > 0:
    scans = res.data[0].get("scans_remaining", 30)
    current_plan = res.data[0].get("plan", "free")
else:
    scans = 30
    current_plan = "free"

# Fetch user phone
user_phone = ""
try:
    profile_res = service.table("user_profiles").select("phone").eq("user_id", user.id).execute()
    if profile_res.data and len(profile_res.data) > 0:
        raw_phone = profile_res.data[0].get("phone", "")
        user_phone = normalize_phone(raw_phone)
except Exception:
    pass

if not user_phone:
    st.warning("⚠️ Please update your profile with your phone number to receive SMS receipts.")

# ============================================
# NEW PLANS
# ============================================
PLANS = {
    "starter":   {"name": "Starter",    "scans": 150,   "price": "₦3,000",  "kobo": 300000},
    "pro":       {"name": "Pro",        "scans": 300,   "price": "₦5,000",  "kobo": 500000},
    "business":  {"name": "Business",   "scans": 1000,  "price": "₦10,000", "kobo": 1000000},
    "enterprise":{"name": "Enterprise", "scans": 5000,  "price": "₦20,000", "kobo": 2000000},
}

# ============================================
# UI
# ============================================
st.markdown("""
<style>
    .stApp { background: linear-gradient(160deg, #f4faf5, #eaf5ee, #fdfefb); color: #1b5e20; }
    header, footer { visibility: hidden; }
    .title { font-size: 2.8rem; font-weight: 800; text-align: center;
             background: linear-gradient(135deg, #1b5e20, #4caf50);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { text-align: center; color: #607d8b; font-size: 1.1rem; margin-bottom: 2rem; }
    .badge { background: #fff; border: 1px solid #c8e6c9; border-radius: 18px;
             padding: 1rem 2rem; display: inline-block; box-shadow: 0 6px 20px rgba(0,0,0,.04); }
    .badge-num { font-size: 2.5rem; font-weight: 900; color: #2e7d32; }
    .badge-lbl { font-size: .85rem; color: #78909c; text-transform: uppercase; letter-spacing: .08em; }
    .card { background: #fff; border-radius: 24px; padding: 2rem 1rem; text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,.05); border: 2px solid transparent; }
    .card.sel { border-color: #2e7d32; background: linear-gradient(160deg, #e8f5e9, #fff); }
    .card-name { font-size: 1.1rem; font-weight: 600; color: #546e7a; }
    .card-price { font-size: 2rem; font-weight: 900; color: #1b5e20; margin: .5rem 0; }
    .card-scans { font-size: 0.9rem; color: #888; margin-bottom: 0.5rem; }
    .banner { background: linear-gradient(135deg, #e8f5e9, #c8e6c9); border: 2px solid #2e7d32;
              border-radius: 20px; padding: 1.5rem 2rem; text-align: center; margin: 1.8rem 0; }
    .stButton button { background: #2e7d32 !important; color: #fff !important; border: none !important;
                       border-radius: 10px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">Buy Scans</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Get more AI-powered diagnoses for your farm</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.markdown(f'<div style="text-align:center"><div class="badge"><div class="badge-num">{scans}</div><div class="badge-lbl">Scans Remaining</div></div></div>', unsafe_allow_html=True)
    if current_plan != "free":
        st.markdown(f'<p style="text-align:center;color:#2e7d32;">Current Plan: {current_plan.title()}</p>', unsafe_allow_html=True)

st.markdown("### Choose Your Plan")

if "selected_plan" not in st.session_state:
    st.session_state.selected_plan = None

cols = st.columns(len(PLANS))
for i, (key, p) in enumerate(PLANS.items()):
    with cols[i]:
        sel = "sel" if st.session_state.selected_plan == key else ""
        st.markdown(f'<div class="card {sel}"><div class="card-name">{p["name"]}</div><div class="card-scans">{p["scans"]} scans</div><div class="card-price">{p["price"]}</div></div>', unsafe_allow_html=True)
        if st.button("Select", key=f"btn_{key}", use_container_width=True):
            st.session_state.selected_plan = key
            st.rerun()

if st.session_state.selected_plan:
    p = PLANS[st.session_state.selected_plan]
    label = f"{p['name']} ({p['scans']} scans)"
    ref = f"GAIA_{user.id[:8]}_{st.session_state.selected_plan}_{uuid.uuid4().hex[:6]}"

    st.markdown(f'<div class="banner"><h3 style="margin:0;color:#1b5e20;">{label} - {p["price"]}</h3></div>', unsafe_allow_html=True)

    phone_for_sms = user_phone if user_phone else "08000000000"

    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://js.paystack.co/v1/inline.js"></script>
    </head>
    <body>
        <button onclick="payWithPaystack()" style="background:linear-gradient(135deg,#2e7d32,#4caf50);color:#fff;border:none;padding:18px 50px;border-radius:50px;font-weight:700;font-size:1.2rem;cursor:pointer;">Pay {p['price']} Now</button>
        <script>
            function payWithPaystack() {{
                PaystackPop.setup({{
                    key: '{PAYSTACK_PUBLIC}',
                    email: '{user.email}',
                    phone: '{phone_for_sms}',
                    amount: {p['kobo']},
                    currency: 'NGN',
                    ref: '{ref}',
                    label: 'GAIA {p['name']}',
                    onClose: function() {{ window.location.reload(); }},
                    callback: function(response) {{
                        window.location.href = '/~/callback?reference=' + response.reference + '&plan={st.session_state.selected_plan}';
                    }}
                }}).openIframe();
            }}
        </script>
    </body>
    </html>
    """, height=120)

st.markdown("---")
st.markdown("### Already Paid? Enter Your Reference")

c1, c2 = st.columns([3, 1])
with c1:
    ref_input = st.text_input("Reference", placeholder="e.g. GAIA_abc123", key="ref_input")
with c2:
    st.write("")
    if st.button("Verify", use_container_width=True) and ref_input:
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
                        if abs(pd["kobo"] / 100 - amt) < 1:
                            match = k
                            break
                    if match:
                        add = PLANS[match]["scans"]
                        cur = db.table("user_scans").select("scans_remaining").eq("user_id", user.id).execute()
                        cur_scans = cur.data[0]["scans_remaining"] if cur.data else 0
                        new_total = cur_scans + add
                        db.table("user_scans").update({"scans_remaining": new_total, "plan": match}).eq("user_id", user.id).execute()
                        db.table("payment_history").insert({"user_id": user.id, "amount": amt, "scans_added": add, "plan": match, "reference": ref_input}).execute()
                        st.success(f"{add} scans added! Balance: {new_total}")
                        st.rerun()
                    else:
                        st.error("Amount doesn't match any plan.")
            else:
                st.error("Payment not found.")

st.markdown("---")
st.caption("Secure payments by Paystack. Darkmoor Ltd")

# Navigation (same as before)
cols = st.columns(9)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/8_Profile.py", label="👤 Profile")
with cols[6]: st.page_link("pages/20_Marketplace.py", label="🌍 Market")
with cols[7]: st.page_link("pages/21_Crop_Insurance.py", label="🏦 Insurance")
with cols[8]: st.page_link("pages/7_Admin.py", label="🔐 Admin")
