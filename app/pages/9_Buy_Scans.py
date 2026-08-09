
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import uuid
import requests

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
PAYSTACK_PUBLIC = "pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057"
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_payment(ref):
    r = requests.get(f"https://api.paystack.co/transaction/verify/{ref}",
                     headers={"Authorization": f"Bearer {PAYSTACK_SECRET}"}, timeout=10)
    if r.status_code == 200:
        d = r.json()
        if d.get("status") and d["data"]["status"] == "success":
            return {"ok": True, "amount": d["data"]["amount"] / 100}
    return {"ok": False}

st.set_page_config(page_title="Buy Scans", page_icon="💳", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
db = get_supabase()

res = db.table("user_scans").select("scans_remaining").eq("user_id", user.id).execute()
scans = res.data[0]["scans_remaining"] if res.data else 30

PLANS = {
    "basic":    {"scans": 500,   "price": "₦3,000",   "naira": 3000,   "kobo": 300000},
    "standard": {"scans": 1000,  "price": "₦5,000",   "naira": 5000,   "kobo": 500000},
    "pro":      {"scans": 3000,  "price": "₦10,000",  "naira": 10000,  "kobo": 1000000},
    "max":      {"scans": 15000, "price": "₦25,000",  "naira": 25000,  "kobo": 2500000},
}

st.markdown("""
<style>
    .stApp { background: linear-gradient(160deg, #f4faf5, #eaf5ee, #fdfefb); color: #1b5e20; }
    header, footer { visibility: hidden; }
    .title {
        font-size: 2.8rem; font-weight: 800; text-align: center;
        background: linear-gradient(135deg, #1b5e20, #4caf50);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .subtitle { text-align: center; color: #607d8b; font-size: 1.1rem; margin-bottom: 2rem; }
    .badge {
        background: #fff; border: 1px solid #c8e6c9; border-radius: 18px;
        padding: 1rem 2rem; display: inline-block; box-shadow: 0 6px 20px rgba(0,0,0,.04);
    }
    .badge-num { font-size: 2.5rem; font-weight: 900; color: #2e7d32; }
    .badge-lbl { font-size: .85rem; color: #78909c; text-transform: uppercase; letter-spacing: .08em; }
    .card {
        background: #fff; border-radius: 24px; padding: 2rem 1rem; text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,.05); border: 2px solid transparent;
        transition: all .25s;
    }
    .card:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(46,125,50,.15); border-color: #a5d6a7; }
    .card.sel { border-color: #2e7d32; background: linear-gradient(160deg, #e8f5e9, #fff); }
    .card-name { font-size: 1.1rem; font-weight: 600; color: #546e7a; }
    .card-price { font-size: 2.4rem; font-weight: 900; color: #1b5e20; margin: .5rem 0; }
    .card-scans { font-size: 0.95rem; color: #78909c; }
    .banner {
        background: linear-gradient(135deg, #e8f5e9, #c8e6c9); border: 2px solid #2e7d32;
        border-radius: 20px; padding: 1.5rem 2rem; text-align: center; margin: 1.8rem 0;
    }
    .pay-btn {
        background: linear-gradient(135deg, #0d6efd, #6610f2); color: #fff;
        border: none; padding: 18px 50px; border-radius: 50px; font-weight: 700;
        font-size: 1.2rem; cursor: pointer; width: 100%; box-shadow: 0 10px 30px rgba(13,110,253,.3);
    }
    .pay-btn:hover { transform: scale(1.03); }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">💳 Buy Scans</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Get more AI-powered diagnoses for your farm</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.markdown(f'<div style="text-align:center"><div class="badge"><div class="badge-num">{scans}</div><div class="badge-lbl">Scans Remaining</div></div></div>', unsafe_allow_html=True)

st.markdown("### Choose Your Plan")

if "plan" not in st.session_state:
    st.session_state.plan = None

cols = st.columns(len(PLANS))
for i, (key, p) in enumerate(PLANS.items()):
    with cols[i]:
        label = p['price']
        scans_label = f"{p['scans']:,} scans"
        sel = "sel" if st.session_state.plan == key else ""
        st.markdown(f'<div class="card {sel}"><div class="card-name">{label}</div><div class="card-price">{p["price"]}</div><div class="card-scans">{scans_label}</div></div>', unsafe_allow_html=True)
        if st.button("Select", key=f"btn_{key}", use_container_width=True):
            st.session_state.plan = key
            st.rerun()

if st.session_state.plan:
    p = PLANS[st.session_state.plan]
    label = f"{p['scans']:,} scans"
    ref = f"GAIA_{user.id[:8]}_{st.session_state.plan}_{uuid.uuid4().hex[:6]}"

    st.markdown(f'<div class="banner"><h3 style="margin:0;color:#1b5e20;">{label} — {p["price"]}</h3></div>', unsafe_allow_html=True)

    # Inline Paystack popup (same as Verify Farmer)
    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://js.paystack.co/v1/inline.js"></script>
        <style>
            body {{ margin:0; padding:0; display:flex; justify-content:center; }}
            .btn {{
                padding: 20px 60px; background: linear-gradient(135deg, #0d6efd, #6610f2); color: #fff;
                border: none; border-radius: 30px; font-size: 1.3rem;
                cursor: pointer; font-weight: 600;
            }}
            .btn:hover {{ background: #0b5ed7; }}
        </style>
    </head>
    <body>
        <button class="btn" onclick="payWithPaystack()">💳 Pay {p['price']} Now</button>
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
                        window.location.href = '/~/callback?reference=' + response.reference + '&plan={st.session_state.plan}';
                    }}
                }}).openIframe();
            }}
        </script>
    </body>
    </html>
    """, height=600)

    st.caption("⏳ A payment popup will appear. If blocked, allow popups for this site.")

st.markdown("---")
st.markdown("### Already Paid? Enter Your Reference")

c1, c2 = st.columns([3, 1])
with c1:
    ref_input = st.text_input("Reference", placeholder="e.g. GAIA_abc123")
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
                        if abs(pd["naira"] - amt) < 1:
                            match = k
                            break
                    if match:
                        add = PLANS[match]["scans"]
                        cur = db.table("user_scans").select("scans_remaining").eq("user_id", user.id).execute()
                        cur_scans = cur.data[0]["scans_remaining"] if cur.data else 0
                        new_total = cur_scans + add
                        db.table("user_scans").update({"scans_remaining": new_total}).eq("user_id", user.id).execute()
                        db.table("payment_history").insert({"user_id": user.id, "amount": amt, "scans_added": add, "plan": match, "reference": ref_input}).execute()
                        st.success(f"✅ {add:,} scans added! Balance: {new_total:,}")
                        st.rerun()
                    else:
                        st.error("Amount doesn't match any plan.")
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
