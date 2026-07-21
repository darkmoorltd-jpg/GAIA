
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
countries = ["Nigeria", "Ghana", "Kenya", "United Kingdom", "United States"]
country_codes = ["+234", "+233", "+254", "+44", "+1"]

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

query_params = st.query_params

# ========== PROCESS PENDING PAYMENT (by email) ==========
# After login, check for any unclaimed payments matching user's email
if st.session_state.user:
    user_email = st.session_state.user.email
    if user_email:
        try:
            service = get_service_client()
            pending = service.table("pending_payments").select("*").eq("email", user_email).eq("claimed", False).execute()
            if pending.data:
                for pp in pending.data:
                    scans_to_add = pp["scans"]
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
                        "amount": pp["amount"],
                        "scans_added": scans_to_add,
                        "plan": pp["plan"],
                        "reference": pp["reference"]
                    }).execute()
                    
                    service.table("pending_payments").update({"claimed": True}).eq("id", pp["id"]).execute()
                    
                    st.success(f"✅ Payment claimed! {scans_to_add} scans added.")
                    st.rerun()
        except Exception as e:
            st.error(f"Error processing payment: {e}")

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
                            st.success("Password reset email sent!")

    with tab2:
        with st.form("signup_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_first_name = st.text_input("First Name")
            with col2:
                new_last_name = st.text_input("Last Name")
            new_email = st.text_input("Email *")
            new_password = st.text_input("Password (min 6 characters) *", type="password")
            col1, col2 = st.columns(2)
            with col1:
                new_country = st.selectbox("Country", options=[""] + countries)
            with col2:
                new_phone_code = st.selectbox("Country Code", options=[""] + country_codes)
            new_phone = st.text_input("Phone Number", placeholder="+2347012345678")
            
            st.markdown("**Social Media (optional)**")
            col1, col2, col3 = st.columns(3)
            with col1:
                twitter = st.text_input("Twitter/X", placeholder="@username")
            with col2:
                linkedin = st.text_input("LinkedIn", placeholder="linkedin.com/in/username")
            with col3:
                instagram = st.text_input("Instagram", placeholder="@username")
            
            if st.form_submit_button("Create Account"):
                if not new_email or not new_password:
                    st.error("Email and password are required.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    full_phone = new_phone.strip()
                    if new_phone_code and not full_phone.startswith("+"):
                        full_phone = f"{new_phone_code}{full_phone}"
                    
                    social = {}
                    if twitter.strip(): social["twitter"] = twitter.strip()
                    if linkedin.strip(): social["linkedin"] = linkedin.strip()
                    if instagram.strip(): social["instagram"] = instagram.strip()
                    
                    user, error = sign_up(
                        new_email, new_password,
                        first_name=new_first_name.strip(),
                        last_name=new_last_name.strip(),
                        phone=full_phone,
                        country=new_country,
                        social_media=social
                    )
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
            st.markdown(f'<a href="https://paystack.shop/pay/{plan_key}" target="_blank"><button style="width:100%;padding:10px;background:#0d6efd;color:white;border:none;border-radius:5px;">Select</button></a>', unsafe_allow_html=True)
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
