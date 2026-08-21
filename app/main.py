
import streamlit as st
import datetime
from supabase import create_client, Client
import hashlib
import requests
import time
import uuid

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_ANON_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

PAYSTACK_PLANS = {
    "starter": {"scans": 150, "price": "₦3,000", "kobo": 300000},
    "pro": {"scans": 300, "price": "₦5,000", "kobo": 500000},
    "business": {"scans": 1000, "price": "₦10,000", "kobo": 1000000},
    "enterprise": {"scans": 5000, "price": "₦20,000", "kobo": 2000000},
}

def get_anon_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_service_client() -> Client:
    return create_client(SUPABASE_URL, SERVICE_KEY)

# ============================================
# URL TOKEN HELPERS
# ============================================
def generate_auth_token():
    return uuid.uuid4().hex

def save_auth_token(token, user_id, access_token, refresh_token):
    # Use service client to bypass RLS
    supabase = get_service_client()
    try:
        res = supabase.table("gaia_auth_tokens").upsert({
            "token": token,
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "created_at": datetime.datetime.now().isoformat()
        }).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def restore_from_auth_token(token):
    supabase = get_service_client()
    try:
        res = supabase.table("gaia_auth_tokens").select("*").eq("token", token).execute()
        if res.data:
            row = res.data[0]
            supabase = get_anon_client()
            supabase.auth.set_session(row["access_token"], row["refresh_token"])
            session = supabase.auth.get_session()
            if session and session.user:
                return session.user
    except:
        pass
    return None

def delete_auth_token(token):
    supabase = get_service_client()
    try:
        supabase.table("gaia_auth_tokens").delete().eq("token", token).execute()
    except:
        pass

# ============================================
# AUTH FUNCTIONS
# ============================================
def sign_up(email, password, first_name="", last_name="", phone="", state=""):
    supabase = get_anon_client()
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
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
            if res.session:
                token = generate_auth_token()
                ok, err = save_auth_token(token, res.user.id, res.session.access_token, res.session.refresh_token)
                if ok:
                    st.query_params["auth_token"] = token
                    st.session_state.user = res.user
                else:
                    st.session_state.user = res.user
                    st.warning(f"Token not saved: {err}")
        return res.user, None
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    supabase = get_anon_client()
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.session:
            token = generate_auth_token()
            ok, err = save_auth_token(token, res.user.id, res.session.access_token, res.session.refresh_token)
            if ok:
                st.query_params["auth_token"] = token
                st.session_state.user = res.user
                return res.user, None
            else:
                return None, f"Token save failed: {err}"
        return res.user, None
    except Exception as e:
        return None, str(e)

def sign_out():
    try:
        get_anon_client().auth.sign_out()
    except:
        pass
    token = st.query_params.get("auth_token")
    if token:
        delete_auth_token(token)
        st.query_params.clear()
    st.session_state.user = None

def reset_password(email):
    supabase = get_anon_client()
    try:
        supabase.auth.reset_password_for_email(email)
        return None
    except Exception as e:
        return str(e)

def get_user_scans(user_id):
    supabase = get_service_client()
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

def verify_paystack_transaction(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        if data["data"]["status"] == "success":
            return data["data"]
    return None

st.set_page_config(page_title="GAIA", page_icon="🌱", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None

query_params = st.query_params

# Google OAuth callback
auth_code = query_params.get("code", [None])[0]
if auth_code and st.session_state.user is None:
    supabase = get_anon_client()
    try:
        supabase.auth.exchange_code_for_session({"auth_code": auth_code})
        session = supabase.auth.get_session()
        if session and session.user:
            token = generate_auth_token()
            save_auth_token(token, session.user.id, session.access_token, session.refresh_token)
            st.query_params["auth_token"] = token
            st.session_state.user = session.user
        st.rerun()
    except Exception as e:
        st.error(f"Google sign-in failed: {e}")

# Paystack callback
reference = query_params.get("reference", [None])[0]
plan = query_params.get("plan", [None])[0]
if reference and plan and plan in PAYSTACK_PLANS:
    txn = verify_paystack_transaction(reference)
    if txn:
        user_id = st.session_state.user.id if st.session_state.user else None
        if user_id:
            supabase = get_service_client()
            scans_to_add = PAYSTACK_PLANS[plan]["scans"]
            supabase.table("user_scans").update({
                "scans_remaining": scans_to_add,
                "plan": plan
            }).eq("user_id", user_id).execute()
            try:
                supabase.table("payment_history").insert({
                    "user_id": user_id,
                    "amount": txn["amount"] / 100,
                    "scans_added": scans_to_add,
                    "plan": plan,
                    "reference": reference
                }).execute()
            except:
                pass
            st.success(f"Payment successful! {scans_to_add} scans added.")
            st.query_params.clear()
            st.rerun()

# Restore from URL token on refresh
if st.session_state.user is None:
    token = query_params.get("auth_token", [None])[0]
    if token:
        restored_user = restore_from_auth_token(token)
        if restored_user:
            st.session_state.user = restored_user
            st.rerun()

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
                        st.success("Account created! 30 free scans added.")
                        st.rerun()
    with tab3:
        st.write("Sign in instantly with Google.")
        google_auth_url = "https://pxvtvuwlpzwlkdoxjrep.supabase.co/auth/v1/authorize?provider=google&redirect_to=https://gaiagpt.streamlit.app"
        st.markdown(f'<a href="{google_auth_url}" target="_blank"><button style="padding:10px 20px;background:#4285f4;color:white;border:none;border-radius:5px;">Sign in with Google</button></a>', unsafe_allow_html=True)
    st.stop()

user = st.session_state.user
user_id = user.id
user_data = get_user_scans(user_id)
scans_left = user_data["scans_remaining"]
plan_name = user_data["plan"]

st.sidebar.write(f"👤 {user.email}")
st.sidebar.metric("Scans Remaining", scans_left)
st.sidebar.write(f"Plan: {plan_name}")

if scans_left <= 0:
    st.warning("No scans left. Choose a plan.")
    st.markdown("### Choose a Plan")
    cols = st.columns(len(PAYSTACK_PLANS))
    for i, (key, p) in enumerate(PAYSTACK_PLANS.items()):
        with cols[i]:
            scans_txt = "Unlimited" if key == "unlimited" else f"{p['scans']} scans"
            st.markdown(f"**{scans_txt}**")
            st.markdown(f'<a href="{p["url"]}" target="_blank"><button style="width:100%;padding:10px;background:#0d6efd;color:#fff;border:none;border-radius:5px;">Select</button></a>', unsafe_allow_html=True)
    st.stop()

if st.sidebar.button("Logout"):
    sign_out()
    st.rerun()

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
farming_calendar_page = st.Page("pages/23_Farming_Calendar.py", title="Farming Calendar", icon="📅")

farmer_db_page = st.Page("pages/25_Farmer_Database.py", title="Farmer Database", icon="🌍")
loan_page = st.Page("pages/26_Loan_Management.py", title="Loan Management", icon="🏦")
extension_page = st.Page("pages/27_Extension_Dashboard.py", title="Extension", icon="🧑‍🌾")

gaia_meet_page = st.Page("pages/23_GAIA_Meet.py", title="GAIA Meet", icon="🎥")

pg = st.navigation({
    "GAIA": [dashboard_page, farming_calendar_page, gaia_meet_page],
    "Diagnose": [crops_page, pests_page, soil_page, livestock_page, video_page, satellite_page, voice_page],
    "Account": [profile_page, buy_scans_page, payment_history_page, badges_page, wallet_page],
    "Community": [chat_page, marketplace_page],
    "Protection": [insurance_page, early_warning_page],
    "Support": [help_page, verify_farmer_page, verify_history_page],
    "Admin": [admin_page, farmer_db_page, loan_page, extension_page],
    "Education": [university_page],
})
pg.run()