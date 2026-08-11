
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
countries = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan",
    "Bahrain", "Bangladesh", "Belarus", "Belgium", "Benin", "Bolivia", "Bosnia", "Botswana", "Brazil", "Bulgaria",
    "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Canada", "Chad", "Chile", "China", "Colombia", "Congo",
    "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark", "Ecuador", "Egypt", "Estonia", "Ethiopia",
    "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Guatemala", "Guinea",
    "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel",
    "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kuwait", "Kyrgyzstan", "Laos", "Latvia",
    "Lebanon", "Liberia", "Libya", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Mali", "Malta",
    "Mauritania", "Mauritius", "Mexico", "Moldova", "Mongolia", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nepal",
    "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "Norway", "Oman", "Pakistan", "Palestine",
    "Panama", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda",
    "Saudi Arabia", "Senegal", "Serbia", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Somalia", "South Africa", "South Korea",
    "South Sudan", "Spain", "Sri Lanka", "Sudan", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania",
    "Thailand", "Togo", "Tunisia", "Turkey", "Turkmenistan", "Uganda", "Ukraine", "UAE", "United Kingdom", "United States",
    "Uruguay", "Uzbekistan", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]
country_codes = [
    "+93", "+355", "+213", "+376", "+244", "+54", "+374", "+61", "+43", "+994",
    "+973", "+880", "+375", "+32", "+229", "+591", "+387", "+267", "+55", "+359",
    "+226", "+257", "+855", "+237", "+1", "+235", "+56", "+86", "+57", "+242",
    "+506", "+385", "+53", "+357", "+420", "+45", "+593", "+20", "+372", "+251",
    "+358", "+33", "+241", "+220", "+995", "+49", "+233", "+30", "+502", "+224",
    "+509", "+504", "+36", "+354", "+91", "+62", "+98", "+964", "+353", "+972",
    "+39", "+1", "+81", "+962", "+7", "+254", "+965", "+996", "+856", "+371",
    "+961", "+231", "+218", "+370", "+352", "+261", "+265", "+60", "+223", "+356",
    "+222", "+230", "+52", "+373", "+976", "+212", "+258", "+95", "+264", "+977",
    "+31", "+64", "+505", "+227", "+234", "+850", "+47", "+968", "+92", "+970",
    "+507", "+595", "+51", "+63", "+48", "+351", "+974", "+40", "+7", "+250",
    "+966", "+221", "+381", "+232", "+65", "+421", "+386", "+252", "+27", "+82",
    "+211", "+34", "+94", "+249", "+46", "+41", "+963", "+886", "+992", "+255",
    "+66", "+228", "+216", "+90", "+993", "+256", "+380", "+971", "+44", "+1",
    "+598", "+998", "+58", "+84", "+967", "+260", "+263"
]

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
    """Send a password reset code to the user's email."""
    supabase = init_supabase()
    try:
        supabase.auth.reset_password_for_email(email)
        return None
    except Exception as e:
        return str(e)

def verify_reset_code(email: str, code: str, new_password: str):
    """Verify the reset code and update the password."""
    supabase = init_supabase()
    try:
        # Verify the OTP code
        verify_res = supabase.auth.verify_otp({
            "email": email,
            "token": code,
            "type": "recovery"
        })
        if verify_res.user:
            # Update the password
            supabase.auth.update_user({
                "password": new_password
            })
            return True, None
        return False, "Invalid code."
    except Exception as e:
        return False, str(e)

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
if "pending_payment" not in st.session_state:
    st.session_state.pending_payment = None
if "show_reset_form" not in st.session_state:
    st.session_state.show_reset_form = False
if "reset_email" not in st.session_state:
    st.session_state.reset_email = ""

query_params = st.query_params

# ========== PROCESS PENDING PAYMENT (by email) ==========
# After login, check for any unclaimed payments matching user's email
if st.session_state.user:
    user_email = st.session_state.user.email
    if user_email:
        try:
            service = get_service_client()
            pending = service.table("payment_history").select("*").eq("email", user_email).eq("claimed", False).execute()
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
                    
                    service.table("payment_history").update({"claimed": True}).eq("id", pp["id"]).execute()
                    
                    st.success(f"✅ Payment claimed! {scans_to_add} scans added.")
                    st.rerun()
        except Exception as e:
            # Payment processing is handled by Paystack callback
            pass

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
                        st.success("Logged in!")
                        st.rerun()
            with col2:
                if st.form_submit_button("Forgot Password?"):
                    if email:
                        st.session_state.reset_email = email
                        err = reset_password(email)
                        if err:
                            st.error(err)
                        else:
                            st.success("A 8‑digit code has been sent to your email.")
                            st.session_state.show_reset_form = True
                            st.rerun()
                    else:
                        st.warning("Enter your email first.")

    with tab2:
        with st.form("signup_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_first_name = st.text_input("First Name *")
            with col2:
                new_last_name = st.text_input("Last Name *")
            new_email = st.text_input("Email *")
            new_password = st.text_input("Password (min 6 characters) *", type="password")
            col1, col2 = st.columns(2)
            with col1:
                new_country = st.selectbox("Country *", options=[""] + countries)
            with col2:
                new_phone_code = st.selectbox("Country Code *", options=[""] + country_codes)
            new_phone = st.text_input("Phone Number *", placeholder="+2347012345678")
            col1, col2 = st.columns(2)
            with col1:
                new_state_city = st.text_input("State/City *", placeholder="e.g., Lagos, London, New York")
            with col2:
                new_address = st.text_input("Address *", placeholder="e.g., 123 Main Street")
            
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
                elif not new_first_name.strip() or not new_last_name.strip():
                    st.error("First name and last name are required.")
                elif not new_country:
                    st.error("Country is required.")
                elif not new_phone.strip():
                    st.error("Phone number is required.")
                elif not new_state_city.strip():
                    st.error("State/City is required.")
                elif not new_address.strip():
                    st.error("Address is required.")
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
                        state_city=new_state_city.strip(),
                        address=new_address.strip(),
                        social_media=social
                    )
                    if error:
                        st.error(f"Sign up failed: {error}")
                    else:
                        st.success("Account created! You are logged in with 30 free scans.")
                        st.rerun()


    # Password reset form (appears after user clicks "Forgot Password")
    if st.session_state.get("show_reset_form"):
        st.markdown("---")
        st.subheader("🔑 Reset Your Password")
        with st.form("reset_code_form"):
            reset_code = st.text_input("Enter 8‑digit code from email", max_chars=8, placeholder="12345678")
            new_pass = st.text_input("New password (min 6 characters)", type="password")
            confirm_pass = st.text_input("Confirm new password", type="password")
            if st.form_submit_button("Reset Password"):
                if not reset_code or len(reset_code) < 8:
                    st.error("Please enter the 8‑digit code from your email.")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                else:
                    email = st.session_state.get("reset_email", "")
                    success, err = verify_reset_code(email, reset_code, new_pass)
                    if success:
                        st.success("Password reset successfully! You can now log in with your new password.")
                        st.session_state.show_reset_form = False
                        st.session_state.reset_email = ""
                        st.rerun()
                    else:
                        st.error(f"Failed: {err}")
        
        if st.button("Cancel"):
            st.session_state.show_reset_form = False
            st.session_state.reset_email = ""
            st.rerun()

    st.stop()

# ---------- Logged‑in area ----------
user_id = st.session_state.user.id
user_data = get_user_scans(user_id)
scans_left = user_data["scans_remaining"]
plan_name = user_data["plan"]

st.sidebar.write(f"👤 {st.session_state.user.email}")
st.sidebar.metric("Scans Remaining", scans_left)
st.sidebar.write(f"Plan: {plan_name}")

# Show badge if active
try:
    badge_res = supabase.table("badge_subscriptions").select("badge_tier").eq("user_id", user_id).eq("status", "active").execute()
    if badge_res.data:
        badge_emojis = {"bronze": "🥉", "silver": "🥈", "gold": "🥇", "platinum": "💎"}
        badge_tier = badge_res.data[0]["badge_tier"]
        st.sidebar.markdown(f"### {badge_emojis.get(badge_tier, '')} {badge_tier.title()} Farmer")
except:
    pass

# Show badge if active (safe fallback)
try:
    badge_res = supabase.table("badge_subscriptions").select("badge_tier").eq("user_id", user_id).eq("status", "active").execute()
    if badge_res.data:
        badge_emojis = {"bronze": "🥉", "silver": "🥈", "gold": "🥇", "platinum": "💎"}
        badge_tier = badge_res.data[0]["badge_tier"]
        st.sidebar.markdown(f"### {badge_emojis.get(badge_tier, '')} {badge_tier.title()} Farmer")
except:
    pass

if scans_left <= 0:
    st.warning("You have no scans left. Choose a plan to continue.")
    st.markdown("### Choose a Plan")
    cols = st.columns(len(PAYSTACK_PLANS))
    for i, (plan_key, plan_data) in enumerate(PAYSTACK_PLANS.items()):
        scans_text = f"{plan_data['scans']} scans" if plan_key != "unlimited" else "Unlimited"
        with cols[i]:
            st.markdown(f"**{scans_text}**")
            st.markdown(f'<a href="https://paystack.shop/pay/{plan_key}" target="_blank"><button style="width:100%;padding:10px;background:#0d6efd;color:white;border:none;border-radius:5px;">Select</button></a>', unsafe_allow_html=True)
    # 

if st.sidebar.button("Logout"):
    sign_out()
    st.rerun()

# ---------- Main navigation ----------
dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard", icon="🏠")
crops_page     = st.Page("pages/2_Crops.py", title="Crop Disease", icon="🌿")
pests_page     = st.Page("pages/3_Pests.py", title="Pest Detection", icon="🐛")
soil_page      = st.Page("pages/4_Soil.py", title="Soil Analysis", icon="🏞️")
livestock_page = st.Page("pages/5_Livestock.py", title="Livestock Health", icon="🐄")
video_page     = st.Page("pages/17_Video_Scan.py", title="Video Scanner", icon="🎥")
payment_history_page = st.Page("pages/6_Payment_History.py", title="Payment History", icon="💳")
admin_page = st.Page("pages/7_Admin.py", title="Admin Dashboard", icon="🔐")
profile_page = st.Page("pages/8_Profile.py", title="My Profile", icon="👤")
buy_scans_page = st.Page("pages/9_Buy_Scans.py", title="Buy Scans", icon="💳")


early_warning_page = st.Page("pages/10_Early_Warning.py", title="Early Warning", icon="🛰️")
badges_page = st.Page("pages/15_Badges.py", title="Badges", icon="🏅")
chat_page = st.Page("pages/16_Chat.py", title="Chat", icon="💬")
help_page = st.Page("pages/13_Help.py", title="Help & Support", icon="🆘")
verify_farmer_page = st.Page("pages/11_Verify_Farmer.py", title="Verify Farmer", icon="🛡️")
verify_history_page = st.Page("pages/12_Verification_History.py", title="Verification History", icon="📋")
wallet_page = st.Page("pages/14_Wallet.py", title="Digital Wallet", icon="💰")

pg = st.navigation({
    "GAIA": [dashboard_page],
    "Diagnose": [crops_page, pests_page, soil_page, livestock_page, early_warning_page],
    "Account": [payment_history_page, profile_page, buy_scans_page, verify_farmer_page, verify_history_page, wallet_page, badges_page],
    "Admin": [admin_page],
    "Community": [chat_page],
    "Support": [help_page],
})
pg.run()
