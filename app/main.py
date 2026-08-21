import streamlit as st
from supabase import create_client, Client
import requests
import time

st.set_page_config(page_title="GAIA", page_icon="🌱", layout="wide")

# ============================================
# CONFIG
# ============================================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]


@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================
# AUTH FUNCTIONS
# ============================================


def sign_in(email, password):
    supabase = get_supabase()
    try:
        res = supabase.auth.sign_in_with_password(
            {"email": email, "password": password})
        st.session_state["user"] = res.user
        st.session_state["logged_in"] = True
        return True, None
    except Exception as e:
        return False, str(e)


def sign_up(email, password):
    supabase = get_supabase()
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            st.session_state["user"] = res.user
            st.session_state["logged_in"] = True
            try:
                supabase.table("user_scans").insert({
                    "user_id": res.user.id,
                    "scans_remaining": 30,
                    "plan": "free"
                }).execute()
            except BaseException:
                pass
            return True, None
        return False, "Sign up failed"
    except Exception as e:
        return False, str(e)


def sign_out():
    st.session_state["user"] = None
    st.session_state["logged_in"] = False


# ============================================
# SESSION STATE
# ============================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None

# ============================================
# LOGIN PAGE
# ============================================
if not st.session_state["logged_in"]:
    st.title("🌱 GAIA — Sign In")

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login", use_container_width=True):
                ok, err = sign_in(email, password)
                if ok:
                    st.success("✅ Logged in!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Login failed: {err}")

    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email")
            new_password = st.text_input(
                "Password (min 6 chars)", type="password")
            if st.form_submit_button(
                "Create Account",
                    use_container_width=True):
                ok, err = sign_up(new_email, new_password)
                if ok:
                    st.success("✅ Account created!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Sign up failed: {err}")

    st.stop()

# ============================================
# LOGGED IN
# ============================================
user = st.session_state["user"]

st.sidebar.write(f"👤 {user.email if user else 'Unknown'}")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    sign_out()
    st.rerun()

# ============================================
# NAVIGATION
# ============================================
dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard", icon="🏠")
crops_page = st.Page("pages/2_Crops.py", title="Crop Disease", icon="🌿")
pests_page = st.Page("pages/3_Pests.py", title="Pest Detection", icon="🐛")
soil_page = st.Page("pages/4_Soil.py", title="Soil Analysis", icon="🏞️")
livestock_page = st.Page(
    "pages/5_Livestock.py",
    title="Livestock Health",
    icon="🐄")
video_page = st.Page("pages/17_Video_Scan.py", title="Video Scanner", icon="🎥")
satellite_page = st.Page(
    "pages/19_Satellite.py",
    title="Satellite Monitor",
    icon="🛰️")
voice_page = st.Page(
    "pages/18_Voice_Agronomist.py",
    title="Voice Agronomist",
    icon="🎙️")
early_warning_page = st.Page(
    "pages/10_Early_Warning.py",
    title="Early Warning",
    icon="🛰️")
gaia_meet_page = st.Page("pages/23_GAIA_Meet.py", title="GAIA Meet", icon="🎥")
buy_scans_page = st.Page("pages/9_Buy_Scans.py", title="Buy Scans", icon="💳")
payment_history_page = st.Page(
    "pages/6_Payment_History.py",
    title="Payment History",
    icon="💳")
admin_page = st.Page("pages/7_Admin.py", title="Admin Dashboard", icon="🔐")
profile_page = st.Page("pages/8_Profile.py", title="My Profile", icon="👤")
chat_page = st.Page("pages/16_Chat.py", title="Chat", icon="💬")
marketplace_page = st.Page(
    "pages/20_Marketplace.py",
    title="Marketplace",
    icon="🌍")
help_page = st.Page("pages/13_Help.py", title="Help & Support", icon="🆘")
verify_farmer_page = st.Page(
    "pages/11_Verify_Farmer.py",
    title="Verify Farmer",
    icon="🛡️")
verify_history_page = st.Page(
    "pages/12_Verification_History.py",
    title="Verification History",
    icon="📋")
wallet_page = st.Page("pages/14_Wallet.py", title="Digital Wallet", icon="💰")
badges_page = st.Page("pages/15_Badges.py", title="Badges", icon="🏅")
insurance_page = st.Page(
    "pages/21_Crop_Insurance.py",
    title="Crop Insurance",
    icon="🏦")
university_page = st.Page(
    "pages/22_University.py",
    title="University",
    icon="🎓")
live_consultation_page = st.Page(
    "pages/23_Live_Consultation.py",
    title="Live Consultation",
    icon="🎥")
farming_calendar_page = st.Page(
    "pages/23_Farming_Calendar.py",
    title="Farming Calendar",
    icon="📅")

pg = st.navigation(
    {
        "GAIA": [
            dashboard_page,
            farming_calendar_page,
            gaia_meet_page],
        "Diagnose": [
            crops_page,
            pests_page,
            soil_page,
            livestock_page,
            video_page,
            satellite_page,
            voice_page],
        "Account": [
            profile_page,
            buy_scans_page,
            payment_history_page,
            badges_page,
            wallet_page],
        "Community": [
            chat_page,
            marketplace_page,
            live_consultation_page],
        "Protection": [
            insurance_page,
            early_warning_page],
        "Support": [
            help_page,
            verify_farmer_page,
            verify_history_page],
        "Admin": [admin_page],
        "Education": [university_page],
    })
pg.run()
