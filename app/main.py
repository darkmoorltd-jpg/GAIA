
import streamlit as st
from supabase import create_client, Client
import requests
import time

# ---------- Secrets ----------
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

# ---------- Paystack plans ----------
PAYSTACK_PLANS = {
    "10": {"scans": 10, "url": "https://paystack.shop/pay/e-z03btaq-"},
    "25": {"scans": 25, "url": "https://paystack.shop/pay/nc3bs0quuh"},
    "60": {"scans": 60, "url": "https://paystack.shop/pay/1j9yrapbt4"},
    "250": {"scans": 250, "url": "https://paystack.shop/pay/rln87t1694"},
    "unlimited": {"scans": 9999, "url": "https://paystack.shop/pay/07zduaem6l"}
}

# ---------- Supabase helpers ----------
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def sign_up(email: str, password: str):
    supabase = init_supabase()
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            # Wait a bit for the auth user to be fully persisted
            time.sleep(0.5)
            # Create user_scans row (ignore if already exists)
            try:
                supabase.table("user_scans").insert({
                    "user_id": res.user.id,
                    "scans_remaining": 30,
                    "plan": "free"
                }).execute()
            except:
                pass
            # Store user in session state
            st.session_state.user = res.user
        return res.user, None
    except Exception as e:
        return None, str(e)

def sign_in(email: str, password: str):
    supabase = init_supabase()
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        # Store user in session state (this is the key fix)
        st.session_state.user = res.user
        return res.user, None
    except Exception as e:
        return None, str(e)

def sign_out():
    supabase = init_supabase()
    try:
        supabase.auth.sign_out()
    except:
        pass
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
    # Create row if missing
    try:
        supabase.table("user_scans").insert({
            "user_id": user_id,
            "scans_remaining": 30,
            "plan": "free"
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

# ----- Google OAuth callback -----
query_params = st.query_params
auth_code = query_params.get("code", [None])[0]

if auth_code and st.session_state.user is None:
    supabase = init_supabase()
    try:
        supabase.auth.exchange_code_for_session({"auth_code": auth_code})
        # After exchanging code, try to get the session
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
        st.rerun()
    except Exception as e:
        st.error(f"Google sign‑in failed: {e}")

# ----- Paystack callback -----
reference = query_params.get("reference", [None])[0]
plan = query_params.get("plan", [None])[0]

if reference and plan and plan in PAYSTACK_PLANS:
    txn = verify_paystack_transaction(reference)
    if txn:
        supabase = init_supabase()
        user_id = st.session_state.user.id if st.session_state.user else None
        if user_id:
            scans_to_add = PAYSTACK_PLANS[plan]["scans"]
            supabase.table("user_scans").update({
                "scans_remaining": scans_to_add,
                "plan": plan
            }).eq("user_id", user_id).execute()

            # Record payment history
            supabase.table("payment_history").insert({
                "user_id": user_id,
                "amount": txn["amount"] / 100,
                "scans_added": scans_to_add,
                "plan": plan,
                "reference": reference
            }).execute()

            st.success(f"Payment successful! {scans_to_add} scans added to your account.")
            st.query_params.clear()
            st.rerun()

# ----- Try to restore session from Supabase cookies (if page reloaded) -----
if st.session_state.user is None:
    supabase = init_supabase()
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
    except:
        pass

# ----- Login page -----
if st.session_state.user is None:
    st.title("🌱 GAIA – Sign In / Create Account")
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Sign Up", "🅶 Google"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Login"):
                    user, error = sign_in(email, password)
                    if error:
                        st.error(f"Login failed: {error}")
                    else:
                        st.success("Logged in!")
                        st.rerun()
            with col2:
                if st.form_submit_button("Forgot Password?"):
                    if email:
                        err = reset_password(email)
                        if err:
                            st.error(err)
                        else:
                            st.success("Password reset email sent.")

    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email")
            new_password = st.text_input("Password (min 6 characters)", type="password")
            if st.form_submit_button("Create Account"):
                if len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    user, error = sign_up(new_email, new_password)
                    if error:
                        st.error(f"Sign up failed: {error}")
                    else:
                        st.success("Account created! You are logged in with 30 free scans.")
                        st.rerun()

    with tab3:
        st.write("Sign in instantly with your Google account.")
        google_auth_url = "https://pxvtvuwlpzwlkdoxjrep.supabase.co/auth/v1/authorize?provider=google&redirect_to=https://gaiagpt.streamlit.app"
        st.markdown(f'<a href="{google_auth_url}" target="_blank"><button style="padding:10px 20px;background:#4285f4;color:white;border:none;border-radius:5px;cursor:pointer;">Sign in with Google</button></a>', unsafe_allow_html=True)

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
    st.markdown("### Choose a Plan")
    cols = st.columns(len(PAYSTACK_PLANS))
    for i, (plan_key, plan_data) in enumerate(PAYSTACK_PLANS.items()):
        scans_text = f"{plan_data['scans']} scans" if plan_key != "unlimited" else "Unlimited"
        with cols[i]:
            st.markdown(f"**{scans_text}**")
            st.markdown(f'<a href="{plan_data["url"]}" target="_blank"><button style="width:100%;padding:10px;background:#0d6efd;color:white;border:none;border-radius:5px;">Select</button></a>', unsafe_allow_html=True)
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

pg = st.navigation({
    "GAIA": [dashboard_page],
    "Diagnose": [crops_page, pests_page, soil_page, livestock_page],
    "Account": [payment_history_page],
    "Admin": [admin_page],
})
pg.run()
