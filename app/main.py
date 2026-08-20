
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
    "starter": {"scans": 150, "price": "₦3,000", "kobo": 300000},
    "pro": {"scans": 300, "price": "₦5,000", "kobo": 500000},
    "business": {"scans": 1000, "price": "₦10,000", "kobo": 1000000},
    "enterprise": {"scans": 5000, "price": "₦20,000", "kobo": 2000000},
}

# ---------- Supabase helpers ----------
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def init_service() -> Client:
    return create_client(SUPABASE_URL, SERVICE_KEY)

def sign_up(email: str, password: str, first_name: str = "", last_name: str = "",
            phone: str = "", state: str = ""):
    supabase = init_supabase()
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            time.sleep(0.5)
            try:
                supabase.table("user_scans").insert({
                    "user_id": res.user.id,
                    "scans_remaining": 30,
                    "plan": "free"
                }).execute()
            except:
                pass
            if first_name or last_name or phone or state:
                supabase.table("user_profiles").insert({
                    "user_id": res.user.id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": phone,
                    "state": state
                }).execute()
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
            supabase.table("payment_history").insert({
                "user_id": user_id,
                "amount": txn["amount"] / 100,
                "scans_added": scans_to_add,
                "plan": plan,
                "reference": reference
            }).execute()
            st.success(f"Payment successful! {scans_to_add} scans added.")
            st.query_params.clear()
            st.rerun()

# ----- Try restore session -----
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
            first_name = st.text_input("First Name (optional)")
            last_name = st.text_input("Last Name (optional)")
            phone = st.text_input("Phone (optional)")
            state = st.text_input("State (optional)")
            if st.form_submit_button("Create Account"):
                if len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    user, error = sign_up(new_email, new_password, first_name, last_name, phone, state)
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

# ---------- Logged‑in user ----------
user_id = st.session_state.user.id
user_data = get_user_scans(user_id)
scans_left = user_data["scans_remaining"]
plan_name = user_data["plan"]

st.sidebar.write(f"👤 {st.session_state.user.email}")
st.sidebar.metric("Scans Remaining", scans_left)
st.sidebar.write(f"Plan: {plan_name}")

if st.sidebar.button("Logout"):
    sign_out()
    st.rerun()

# ---------- Main navigation ----------
dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard", icon="🏠")
crops_page = st.Page("pages/2_Crops.py", title="Crop Disease", icon="🌿")
pests_page = st.Page("pages/3_Pests.py", title="Pest Detection", icon="🐛")
soil_page = st.Page("pages/4_Soil.py", title="Soil Analysis", icon="🏞️")
livestock_page = st.Page("pages/5_Livestock.py", title="Livestock Health", icon="🐄")
video_page = st.Page("pages/17_Video_Scan.py", title="Video Scanner", icon="🎥")
satellite_page = st.Page("pages/19_Satellite.py", title="Satellite Monitor", icon="🛰️")
voice_page = st.Page("pages/18_Voice_Agronomist.py", title="Voice Agronomist", icon="🎙️")
early_warning_page = st.Page("pages/10_Early_Warning.py", title="Early Warning", icon="🛰️")
gaia_meet_page = st.Page("pages/23_GAIA_Meet.py", title="GAIA Meet", icon="🎥")
buy_scans_page = st.Page("pages/9_Buy_Scans.py", title="Buy Scans", icon="💳")
payment_history_page = st.Page("pages/6_Payment_History.py", title="Payment History", icon="💳")
admin_page = st.Page("pages/7_Admin.py", title="Admin Dashboard", icon="🔐")
profile_page = st.Page("pages/8_Profile.py", title="My Profile", icon="👤")
chat_page = st.Page("pages/16_Chat.py", title="Chat", icon="💬")
marketplace_page = st.Page("pages/20_Marketplace.py", title="Marketplace", icon="🌍")
help_page = st.Page("pages/13_Help.py", title="Help & Support", icon="🆘")
verify_farmer_page = st.Page("pages/11_Verify_Farmer.py", title="Verify Farmer", icon="🛡️")
verify_history_page = st.Page("pages/12_Verification_History.py", title="Verification History", icon="📋")
wallet_page = st.Page("pages/14_Wallet.py", title="Digital Wallet", icon="💰")
badges_page = st.Page("pages/15_Badges.py", title="Badges", icon="🏅")
insurance_page = st.Page("pages/21_Crop_Insurance.py", title="Crop Insurance", icon="🏦")
university_page = st.Page("pages/22_University.py", title="University", icon="🎓")
live_consultation_page = st.Page("pages/23_Live_Consultation.py", title="Live Consultation", icon="🎥")
farming_calendar_page = st.Page("pages/23_Farming_Calendar.py", title="Farming Calendar", icon="📅")

pg = st.navigation({
    "GAIA": [dashboard_page, farming_calendar_page],
    "Diagnose": [crops_page, pests_page, soil_page, livestock_page, video_page, satellite_page, voice_page],
    "Account": [profile_page, buy_scans_page, payment_history_page, badges_page, wallet_page],
    "Community": [chat_page, marketplace_page, live_consultation_page],
    "Protection": [insurance_page, early_warning_page],
    "Support": [help_page, verify_farmer_page, verify_history_page],
    "Admin": [admin_page],
    "Education": [university_page],
})
pg.run()
