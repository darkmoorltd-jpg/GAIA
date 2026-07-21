
import streamlit as st
from supabase import create_client, Client
import requests
import time

# ---------- Secrets ----------
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

# ---------- Paystack plans ----------
PAYSTACK_PLANS = {
    "10": {"scans": 10},
    "25": {"scans": 25},
    "60": {"scans": 60},
    "250": {"scans": 250},
    "unlimited": {"scans": 9999}
}

# ---------- Country & phone lists ----------
countries = ["Nigeria"]   # shortened for brevity; your full list is fine
country_codes = ["+234"]

# ---------- Supabase helpers ----------
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_service_client() -> Client:
    return create_client(SUPABASE_URL, SERVICE_KEY)

def sign_up(email: str, password: str, first_name: str = "", last_name: str = "",
            phone: str = "", country: str = "", social_media: dict = None):
    supabase = init_supabase()
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            time.sleep(0.5)
            try:
                supabase.table("user_scans").insert({
                    "user_id": res.user.id, "scans_remaining": 30, "plan": "free"
                }).execute()
            except:
                pass
            try:
                supabase.table("user_profiles").insert({
                    "user_id": res.user.id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": phone,
                    "country": country,
                    "social_media": social_media or {}
                }).execute()
            except:
                pass
            st.session_state.user = res.user
        return res.user, None
    except Exception as e:
        return None, str(e)

def sign_in(email: str, password: str):
    supabase = init_supabase()
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        return res.user, None
    except Exception as e:
        return None, str(e)

def sign_out():
    init_supabase().auth.sign_out()
    st.session_state.user = None

def reset_password(email: str):
    supabase = init_supabase()
    try:
        supabase.auth.reset_password_for_email(email)
        return None
    except Exception as e:
        return str(e)

def get_user_scans(user_id: str):
    supabase = init_supabase()
    try:
        res = supabase.table("user_scans").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]
    except:
        pass
    try:
        supabase.table("user_scans").insert({
            "user_id": user_id, "scans_remaining": 30, "plan": "free"
        }).execute()
    except:
        pass
    return {"scans_remaining": 30, "plan": "free"}

def verify_paystack_transaction(reference: str):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        if data["data"]["status"] == "success":
            return data["data"]
    return None

# ---------- Streamlit page ----------
st.set_page_config(page_title="GAIA", page_icon="🌱", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None
if "pending_payment" not in st.session_state:
    st.session_state.pending_payment = None

# ========== PROCESS PENDING PAYMENT ==========
# (This runs after all functions are defined, but before the login page)
query_params = st.query_params
pending_ref = query_params.get("pending_reference", [None])[0]
pending_plan = query_params.get("pending_plan", [None])[0]

# If URL has payment details, store them in session_state
if pending_ref and pending_plan:
    st.session_state.pending_payment = {"reference": pending_ref, "plan": pending_plan}
    st.query_params.clear()
    st.rerun()

# If a pending payment exists and user is logged in, process it
if st.session_state.pending_payment and st.session_state.user:
    pp = st.session_state.pending_payment
    try:
        txn = verify_paystack_transaction(pp["reference"])
        if txn:
            scans_to_add = PAYSTACK_PLANS.get(pp["plan"], {}).get("scans", 0)
            service = get_service_client()
            user_id = st.session_state.user.id

            current = service.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
            current_scans = current.data[0]["scans_remaining"] if current.data else 0
            new_total = current_scans + scans_to_add

            service.table("user_scans").update({
                "scans_remaining": new_total,
                "plan": pp["plan"]
            }).eq("user_id", user_id).execute()

            service.table("payment_history").insert({
                "user_id": user_id,
                "amount": txn["amount"] / 100,
                "scans_added": scans_to_add,
                "plan": pp["plan"],
                "reference": pp["reference"]
            }).execute()

            st.success(f"✅ Payment processed! {scans_to_add} scans added to your account.")
            st.session_state.pending_payment = None
            st.rerun()
        else:
            st.error("Payment verification failed. Please contact darkmoorltd@gmail.com")
            st.session_state.pending_payment = None
    except Exception as e:
        st.error(f"Payment processing error: {e}")
        st.session_state.pending_payment = None

# ----- Google OAuth callback -----
auth_code = query_params.get("code", [None])[0]
if auth_code and st.session_state.user is None:
    supabase = init_supabase()
    try:
        supabase.auth.exchange_code_for_session({"auth_code": auth_code})
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Google sign‑in failed: {e}")

# ----- Restore session -----
if st.session_state.user is None:
    supabase = init_supabase()
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
    except:
        pass

# ========== CLAIM PENDING PAYMENTS (by email) ==========
if st.session_state.user:
    user_email = st.session_state.user.email
    if user_email:
        service = get_service_client()
        # Find unclaimed payments for this email
        pending = service.table("pending_payments").select("*").eq("email", user_email).eq("claimed", False).execute()
        if pending.data:
            for pp in pending.data:
                scans_to_add = pp["scans"]
                user_id = st.session_state.user.id
                
                # Update user scans
                current = service.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
                current_scans = current.data[0]["scans_remaining"] if current.data else 0
                new_total = current_scans + scans_to_add
                service.table("user_scans").update({
                    "scans_remaining": new_total,
                    "plan": pp["plan"]
                }).eq("user_id", user_id).execute()
                
                # Record in payment history
                service.table("payment_history").insert({
                    "user_id": user_id,
                    "amount": pp["amount"],
                    "scans_added": scans_to_add,
                    "plan": pp["plan"],
                    "reference": pp["reference"]
                }).execute()
                
                # Mark as claimed
                service.table("pending_payments").update({"claimed": True}).eq("id", pp["id"]).execute()
                
                st.success(f"✅ Payment claimed! {scans_to_add} scans added to your account.")
                st.rerun()


# ----- Login page -----
if st.session_state.user is None:
    st.title("🌱 GAIA – Sign In / Create Account")
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Sign Up", "🅶 Google"])
    # (login/signup forms remain exactly the same)
    st.stop()

# ---------- Logged‑in area ----------
user_id = st.session_state.user.id
user_data = get_user_scans(user_id)
scans_left = user_data["scans_remaining"]
plan_name = user_data["plan"]

st.sidebar.write(f"👤 {st.session_state.user.email}")
st.sidebar.metric("Scans Remaining", scans_left)
st.sidebar.write(f"Plan: {plan_name}")

if scans_left <= 0:
    st.warning("You have no scans left. Choose a plan to continue.")
    st.stop()

if st.sidebar.button("Logout"):
    sign_out()
    st.rerun()

# ---------- Main navigation ----------
dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard", icon="🏠")
crops_page     = st.Page("pages/2_Crops.py", title="Crop Disease", icon="🌿")
pests_page     = st.Page("pages/3_Pests.py", title="Pest Detection", icon="🐛")
soil_page      = st.Page("pages/4_Soil.py", title="Soil Analysis", icon="🏞️")
livestock_page = st.Page("pages/5_Livestock.py", title="Livestock Health", icon="🐄")
payment_history_page = st.Page("pages/6_Payment_History.py", title="Payment History", icon="💳")
admin_page = st.Page("pages/7_Admin.py", title="Admin Dashboard", icon="🔐")
profile_page = st.Page("pages/8_Profile.py", title="My Profile", icon="👤")
buy_scans_page = st.Page("pages/9_Buy_Scans.py", title="Buy Scans", icon="💳")

pg = st.navigation({
    "GAIA": [dashboard_page],
    "Diagnose": [crops_page, pests_page, soil_page, livestock_page],
    "Account": [payment_history_page, profile_page, buy_scans_page],
    "Admin": [admin_page],
})
pg.run()
