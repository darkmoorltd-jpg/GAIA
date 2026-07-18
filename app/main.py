
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

# ---------- Country & phone lists ----------
countries = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia",
    "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin",
    "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi",
    "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia",
    "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Democratic Republic of the Congo",
    "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea",
    "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany",
    "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary",
    "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan",
    "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia",
    "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali",
    "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia",
    "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand",
    "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau",
    "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar",
    "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
    "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone",
    "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan",
    "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand",
    "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda",
    "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu",
    "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

country_codes = [
    "+93", "+355", "+213", "+376", "+244", "+1-268", "+54", "+374", "+61", "+43", "+994", "+1-242", "+973", "+880",
    "+1-246", "+375", "+32", "+501", "+229", "+975", "+591", "+387", "+267", "+55", "+673", "+359", "+226", "+257",
    "+238", "+855", "+237", "+1", "+236", "+235", "+56", "+86", "+57", "+269", "+242", "+506", "+385", "+53", "+357",
    "+420", "+243", "+45", "+253", "+1-767", "+1-809", "+593", "+20", "+503", "+240", "+291", "+372", "+268", "+251",
    "+679", "+358", "+33", "+241", "+220", "+995", "+49", "+233", "+30", "+1-473", "+502", "+224", "+245", "+592",
    "+509", "+504", "+36", "+354", "+91", "+62", "+98", "+964", "+353", "+972", "+39", "+1-876", "+81", "+962",
    "+7", "+254", "+686", "+965", "+996", "+856", "+371", "+961", "+266", "+231", "+218", "+423", "+370", "+352",
    "+261", "+265", "+60", "+960", "+223", "+356", "+692", "+222", "+230", "+52", "+691", "+373", "+377", "+976",
    "+382", "+212", "+258", "+95", "+264", "+674", "+977", "+31", "+64", "+505", "+227", "+234", "+850", "+389",
    "+47", "+968", "+92", "+680", "+970", "+507", "+675", "+595", "+51", "+63", "+48", "+351", "+974", "+40", "+7",
    "+250", "+1-869", "+1-758", "+1-784", "+685", "+378", "+239", "+966", "+221", "+381", "+248", "+232", "+65",
    "+421", "+386", "+677", "+252", "+27", "+82", "+211", "+34", "+94", "+249", "+597", "+46", "+41", "+963", "+992",
    "+255", "+66", "+670", "+228", "+676", "+1-868", "+216", "+90", "+993", "+688", "+256", "+380", "+971", "+44",
    "+1", "+598", "+998", "+678", "+39-06", "+58", "+84", "+967", "+260", "+263"
]

# ---------- Supabase helpers ----------
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def sign_up(email: str, password: str, first_name: str = "", last_name: str = "",
            phone: str = "", country: str = "", social_media: dict = None):
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

query_params = st.query_params
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
            st.success(f"Payment successful! {scans_to_add} scans added to your account.")
            st.query_params.clear()
            st.rerun()

if st.session_state.user is None:
    supabase = init_supabase()
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
    except:
        pass

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
                    else:
                        st.warning("Enter your email first.")

    with tab2:
        with st.form("signup_form"):
            col1, col2 = st.columns(2)
            with col1: new_first_name = st.text_input("First Name")
            with col2: new_last_name = st.text_input("Last Name")
            new_email = st.text_input("Email *")
            new_password = st.text_input("Password (min 6 characters) *", type="password")
            col1, col2 = st.columns(2)
            with col1: new_country = st.selectbox("Country", options=[""] + countries)
            with col2: new_phone_code = st.selectbox("Country Code", options=[""] + country_codes)
            new_phone = st.text_input("Phone Number", placeholder="+2347012345678")
            st.markdown("**Social Media (optional)**")
            col1, col2, col3 = st.columns(3)
            with col1: twitter = st.text_input("Twitter/X", placeholder="@username")
            with col2: linkedin = st.text_input("LinkedIn", placeholder="linkedin.com/in/username")
            with col3: instagram = st.text_input("Instagram", placeholder="@username")
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
                        phone=full_phone, country=new_country,
                        social_media=social
                    )
                    if error:
                        st.error(f"Sign up failed: {error}")
                    else:
                        st.success("Account created! 30 free scans added.")
                        st.rerun()

    with tab3:
        st.write("Sign in with Google.")
        google_auth_url = "https://pxvtvuwlpzwlkdoxjrep.supabase.co/auth/v1/authorize?provider=google&redirect_to=https://gaiagpt.streamlit.app"
        st.markdown(f'<a href="{google_auth_url}" target="_blank"><button style="padding:10px 20px;background:#4285f4;color:white;border:none;border-radius:5px;">Sign in with Google</button></a>', unsafe_allow_html=True)

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
    st.warning("You have no scans left.")
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

# ---------- Navigation ----------
dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard", icon="🏠")
crops_page     = st.Page("pages/2_Crops.py", title="Crop Disease", icon="🌿")
pests_page     = st.Page("pages/3_Pests.py", title="Pest Detection", icon="🐛")
soil_page      = st.Page("pages/4_Soil.py", title="Soil Analysis", icon="🏞️")
livestock_page = st.Page("pages/5_Livestock.py", title="Livestock Health", icon="🐄")
payment_history_page = st.Page("pages/6_Payment_History.py", title="Payment History", icon="💳")
admin_page = st.Page("pages/7_Admin.py", title="Admin Dashboard", icon="🔐")
profile_page = st.Page("pages/8_Profile.py", title="My Profile", icon="👤")

pg = st.navigation({
    "GAIA": [dashboard_page],
    "Diagnose": [crops_page, pests_page, soil_page, livestock_page],
    "Account": [payment_history_page, profile_page],
    "Admin": [admin_page],
})
pg.run()
