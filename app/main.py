
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

# ---------- Country & phone lists (unchanged) ----------
countries = ["Nigeria"]
country_codes = ["+234"]

# ---------- Supabase helpers ----------
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_service_client() -> Client:
    return create_client(SUPABASE_URL, SERVICE_KEY)

def sign_up(email: str, password: str, first_name: str = "", last_name: str = "",
            phone: str = "", country: str = "", state_city: str = "", address: str = "", social_media: dict = None):
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
                    "state_city": state_city,
                    "address": address,
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
st.set_page_config(page_title="GAIA", page_icon="🌱", layout="wide", initial_sidebar_state="expanded")

if "user" not in st.session_state:
    st.session_state.user = None

query_params = st.query_params

# Google OAuth callback
auth_code = query_params.get("code", [None])[0]
if auth_code and st.session_state.user is None:
    supabase = init_supabase()
    try:
        supabase.auth.exchange_code_for_session({"auth_code": auth_code})
        st.rerun()
    except Exception as e:
        st.error(f"Google sign-in failed: {e}")

# Check existing session
if st.session_state.user is None:
    supabase = init_supabase()
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
    except:
        pass

# ---------- Login Page ----------
if st.session_state.user is None:
    st.title("🌱 GAIA – Sign In / Create Account")
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

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

    st.stop()

# ---------- Logged-in area ----------
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

# ---------- Clean Navigation (NO duplicates) ----------
dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard", icon="🏠")
crops_page = st.Page("pages/2_Crops.py", title="Crop Disease", icon="🌿")
pests_page = st.Page("pages/3_Pests.py", title="Pest Detection", icon="🐛")
soil_page = st.Page("pages/4_Soil.py", title="Soil Analysis", icon="🏞️")
livestock_page = st.Page("pages/5_Livestock.py", title="Livestock Health", icon="🐄")
video_page = st.Page("pages/17_Video_Scan.py", title="Video Scanner", icon="🎥")
satellite_page = st.Page("pages/19_Satellite.py", title="Satellite Monitor", icon="🛰️")
voice_page = st.Page("pages/18_Voice_Agronomist.py", title="Voice Agronomist", icon="🎙️")
early_warning_page = st.Page("pages/10_Early_Warning.py", title="Early Warning", icon="🛰️")
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

pg = st.navigation({
    "GAIA": [dashboard_page],
    "Diagnose": [crops_page, pests_page, soil_page, livestock_page, video_page, satellite_page, voice_page],
    "Account": [profile_page, buy_scans_page, payment_history_page, badges_page, wallet_page],
    "Community": [chat_page, marketplace_page],
    "Protection": [insurance_page, early_warning_page],
    "Support": [help_page, verify_farmer_page, verify_history_page],
    "Admin": [admin_page],
    "Education": [university_page],
})
pg.run()
