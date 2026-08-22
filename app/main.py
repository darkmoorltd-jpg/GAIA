
import streamlit as st
from supabase import create_client, Client
import requests
import time
import datetime
import uuid

# ---------- Secrets ----------
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

# ---------- Paystack plans ----------
PAYSTACK_PLANS = {
    "starter": 150, "pro": 300, "business": 1000, "enterprise": 5000
}

# ---------- Nigerian states ----------
NIGERIAN_STATES = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa",
    "Benue", "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti",
    "Enugu", "FCT Abuja", "Gombe", "Imo", "Jigawa", "Kaduna", "Kano",
    "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos", "Nasarawa", "Niger",
    "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto",
    "Taraba", "Yobe", "Zamfara"
]

CROPS = [
    "Maize", "Rice", "Beans", "Tomato", "Pepper", "Cabbage", "Cassava",
    "Yam", "Potato", "Sorghum", "Millet", "Groundnut", "Soybean",
    "Wheat", "Cotton", "Cocoa", "Oil Palm", "Other"
]

BANKS = [
    "Access Bank", "GTBank", "Zenith Bank", "UBA", "First Bank",
    "Kuda", "Opay", "Palmpay", "Moniepoint", "Sterling Bank",
    "Union Bank", "Fidelity Bank", "Wema Bank", "Jaiz Bank", "Other"
]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def init_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

def check_identifier_conflicts(data: dict):
    """Return an error message if email/phone/username/BVN/NIN already exists."""
    service = init_service()

    # Email is enforced by Supabase Auth, but check anyway for clearer message
    # We'll rely on sign_up error for email.

    # Phone
    phone = normalize_phone(data.get("phone", ""))
    if phone and phone != "234":
        res = service.table("user_profiles").select("user_id").eq("phone", phone).execute()
        if res.data:
            return "Phone number already registered."

    # Username
    username = data.get("username", "").strip().lower()
    if username:
        res = service.table("user_profiles").select("user_id").eq("username", username).execute()
        if res.data:
            return "Username already taken."

    # BVN
    bvn = data.get("bvn", "").strip()
    if bvn:
        res = service.table("user_profiles").select("user_id").eq("bvn", bvn).execute()
        if res.data:
            return "BVN already registered."

    # NIN
    nin = data.get("nin", "").strip()
    if nin:
        res = service.table("user_profiles").select("user_id").eq("nin", nin).execute()
        if res.data:
            return "NIN already registered."

    return None

def sign_up_comprehensive(data: dict):
    supabase = init_supabase()
    service = init_service()

    # Pre-check uniqueness
    conflict = check_identifier_conflicts(data)
    if conflict:
        return None, conflict

    # Normalize phone numbers
    normalized_phone = normalize_phone(data.get("phone", ""))
    normalized_whatsapp = normalize_phone(data.get("whatsapp", data.get("phone", "")))

    try:
        # 1. Create auth user
        auth_res = supabase.auth.sign_up({
            "email": data["email"],
            "password": data["password"]
        })
        if not auth_res.user:
            return None, "Email already registered."
        user_id = auth_res.user.id
    except Exception as e:
        err_str = str(e).lower()
        if "already" in err_str or "unique" in err_str or "duplicate" in err_str:
            return None, "Email already registered."
        return None, f"Signup failed: {err_str}"

        # 2. Create user_profiles row
        profile_data = {
            "user_id": user_id,
            "first_name": data.get("first_name", ""),
            "middle_name": data.get("middle_name", ""),
            "last_name": data.get("last_name", ""),
            "gender": data.get("gender", ""),
            "date_of_birth": data.get("dob", None),
            "marital_status": data.get("marital_status", ""),
            "username": data.get("username", "").lower(),
            "phone": normalized_phone,
            "whatsapp": normalized_whatsapp,
            "country": data.get("country", "Nigeria"),
            "state": data.get("state", ""),
            "lga": data.get("lga", ""),
            "city": data.get("city", ""),
            "street_address": data.get("street", ""),
            "landmark": data.get("landmark", ""),
            "postal_code": data.get("postal", ""),
            "bvn": data.get("bvn", ""),
            "nin": data.get("nin", ""),
            "govt_id_type": data.get("id_type", ""),
            "govt_id_number": data.get("id_number", ""),
            "farm_state": data.get("farm_state", ""),
            "farm_lga": data.get("farm_lga", ""),
            "farm_address": data.get("farm_address", ""),
            "farm_size_acres": data.get("farm_size", 0.0),
            "years_experience": data.get("years_exp", 0),
            "primary_crops": data.get("primary_crop", ""),
            "farming_type": data.get("farming_type", ""),
            "account_name": data.get("account_name", ""),
            "account_number": data.get("account_number", ""),
            "bank_name": data.get("bank_name", ""),
            "emergency_contact_name": data.get("emergency_name", ""),
            "emergency_contact_phone": data.get("emergency_phone", ""),
            "emergency_relationship": data.get("emergency_rel", ""),
            "notify_sms": data.get("notify_sms", True),
            "notify_whatsapp": data.get("notify_whatsapp", True),
            "notify_weather": data.get("notify_weather", True),
            "notify_disease": data.get("notify_disease", True),
            "notify_payment": data.get("notify_payment", True),
            "preferred_language": data.get("language", "English"),
            "verification_status": "pending"
        }
        try:
            service.table("user_profiles").insert(profile_data).execute()
        except:
            pass

        # 3. Create farmer_registry row
        farmer_data = {
            "user_id": user_id,
            "state": data.get("farm_state", ""),
            "lga": data.get("farm_lga", ""),
            "username": data.get("username", "").lower(),
            "phone": normalized_phone,
            "crop": data.get("primary_crop", ""),
            "farm_size_acres": data.get("farm_size", 0.0),
            "farmer_type": data.get("farming_type", "Smallholder"),
            "gender": data.get("gender", ""),
            "youth": data.get("youth", False),
            "gps_lat": data.get("gps_lat", None),
            "gps_lon": data.get("gps_lon", None),
            "unique_farmer_id": f"GAIA-{uuid.uuid4().hex[:8].upper()}"
        }
        try:
            service.table("farmer_registry").insert(farmer_data).execute()
        except:
            pass

        # 4. Create user_scans row (30 free)
        try:
            service.table("user_scans").insert({
                "user_id": user_id,
                "scans_remaining": 30,
                "plan": "free"
            }).execute()
        except:
            pass

        return auth_res.user, None
    except Exception as e:
        return None, str(e)


def normalize_phone(phone):
    if not phone:
        return ""
    phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    if phone.startswith("0"):
        return "234" + phone[1:]
    elif phone.startswith("234"):
        return phone
    else:
        return "234" + phone

def find_email_by_identifier(identifier):
    """Resolve email from email, phone, or username using service role."""
    service = init_service()
    identifier = identifier.strip()

    # If it looks like an email, return as-is
    if "@" in identifier:
        return identifier

    # Try phone number (normalized)
    normalized = normalize_phone(identifier)
    if normalized and normalized != "234":
        try:
            res = service.table("user_profiles").select("user_id").eq("phone", normalized).execute()
            if res.data and res.data[0].get("user_id"):
                user_id = res.data[0]["user_id"]
                user = service.auth.admin.get_user_by_id(user_id)
                if user and user.email:
                    return user.email
        except:
            pass

    # Try username (case‑insensitive)
    try:
        res = service.table("user_profiles").select("user_id").eq("username", identifier.lower()).execute()
        if res.data and res.data[0].get("user_id"):
            user_id = res.data[0]["user_id"]
            user = service.auth.admin.get_user_by_id(user_id)
            if user and user.email:
                return user.email
    except:
        pass

    return None

def sign_in(identifier: str, password: str):
    supabase = init_supabase()
    email = find_email_by_identifier(identifier)
    if not email:
        return None, "No account found with that email, phone number, or username."
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        return res.user, None
    except Exception as e:
        return None, str(e)

def sign_out():
    supabase = init_supabase()
    supabase.auth.sign_out()
    st.session_state.user = None

def reset_password(email: str):
    supabase = init_supabase()
    try:
        supabase.auth.reset_password_for_email(email)
        return None
    except Exception as e:
        return str(e)

def get_user_scans(user_id: str):
    service = init_service()
    try:
        res = service.table("user_scans").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]
    except:
        pass
    return {"scans_remaining": 30, "plan": "free"}

def verify_paystack_transaction(reference: str):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code == 200:
        data = r.json()
        if data["data"]["status"] == "success":
            return data["data"]
    return None

# ---------- Streamlit page ----------
st.set_page_config(page_title="GAIA", page_icon="🌱", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None
if "signup_step" not in st.session_state:
    st.session_state.signup_step = 1

# ----- Google OAuth callback -----
query_params = st.query_params
auth_code = query_params.get("code", [None])[0]
if auth_code and st.session_state.user is None:
    supabase = init_supabase()
    try:
        supabase.auth.exchange_code_for_session({"auth_code": auth_code})
        st.rerun()
    except:
        pass

# ----- Paystack callback -----
reference = query_params.get("reference", [None])[0]
plan = query_params.get("plan", [None])[0]
if reference and plan:
    txn = verify_paystack_transaction(reference)
    if txn and st.session_state.user:
        user_id = st.session_state.user.id
        scans_to_add = PAYSTACK_PLANS.get(plan, 0)
        service = init_service()
        current = service.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
        cur = current.data[0]["scans_remaining"] if current.data else 30
        new_total = cur + scans_to_add
        service.table("user_scans").update({"scans_remaining": new_total, "plan": plan}).eq("user_id", user_id).execute()
        service.table("payment_history").insert({
            "user_id": user_id, "amount": txn["amount"]/100,
            "scans_added": scans_to_add, "plan": plan, "reference": reference
        }).execute()
        st.success(f"Payment successful! {scans_to_add} scans added.")
        st.query_params.clear()
        st.rerun()

# ----- Restore session -----
if st.session_state.user is None:
    supabase = init_supabase()
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
    except:
        pass

# ----- Authentication UI -----
if st.session_state.user is None:
    st.title("🌱 GAIA – Create Account")

    tab_login, tab_signup = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab_login:
        with st.form("login_form"):
            login_identifier = st.text_input("Email, Phone, or Username")
            password = st.text_input("Password", type="password")
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Login"):
                    user, err = sign_in(login_identifier, password)
                    if err:
                        st.error(f"Login failed: {err}")
                    else:
                        st.session_state.user = user
                        st.rerun()
            with col2:
                if st.form_submit_button("Forgot Password?"):
                    if login_identifier and "@" in login_identifier:
                        err = reset_password(login_identifier)
                        if err:
                            st.error(err)
                        else:
                            st.success("Reset email sent.")

    with tab_signup:
        # Multi-step signup
        step = st.session_state.signup_step

        if step == 1:
            st.subheader("Step 1 of 3: Account & Personal")
            with st.form("step1_form"):
                col1, col2 = st.columns(2)
                with col1:
                    first_name = st.text_input("First Name *")
                    middle_name = st.text_input("Middle Name")
                    gender = st.selectbox("Gender", ["", "Male", "Female", "Other"])
                with col2:
                    last_name = st.text_input("Last Name *")
                    date_of_birth = st.date_input(
        "Date of Birth",
        value=datetime.date(1956, 1, 1),
        min_value=datetime.date(1956, 1, 1),
        max_value=datetime.date.today()
    )
                    marital_status = st.selectbox("Marital Status", ["", "Single", "Married", "Divorced", "Widowed"])
                username = st.text_input("Username *")
                email = st.text_input("Email *")
                password = st.text_input("Password *", type="password")
                confirm = st.text_input("Confirm Password *", type="password")
                phone = st.text_input("Phone Number *")
                whatsapp = st.text_input("WhatsApp Number")
                if st.form_submit_button("Next →"):
                    if not first_name or not last_name or not email or not password or not phone:
                        st.error("Please fill required fields.")
                    elif password != confirm:
                        st.error("Passwords do not match.")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        st.session_state.step1_data = {
                            "first_name": first_name, "middle_name": middle_name,
                            "last_name": last_name, "gender": gender,
                            "date_of_birth": str(date_of_birth) if date_of_birth else None,
                            "marital_status": marital_status, "email": email,
                            "username": username,
                            "password": password, "phone": phone, "whatsapp": whatsapp or phone
                        }
                        st.session_state.signup_step = 2
                        st.rerun()

        elif step == 2:
            st.subheader("Step 2 of 3: Farm Information")
            with st.form("step2_form"):
                col1, col2 = st.columns(2)
                with col1:
                    country = st.text_input("Country", value="Nigeria")
                    state = st.selectbox("Residential State", [""] + NIGERIAN_STATES)
                    lga = st.text_input("LGA")
                with col2:
                    city = st.text_input("City/Town")
                    street = st.text_input("Street Address")
                    landmark = st.text_input("Landmark")
                farm_state = st.selectbox("Farm State", [""] + NIGERIAN_STATES)
                farm_lga = st.text_input("Farm LGA")
                farm_size = st.number_input("Farm Size (acres)", min_value=0.0, value=1.0)
                primary_crop = st.selectbox("Primary Crop", [""] + CROPS)
                farming_type = st.selectbox("Farming Type", ["", "Smallholder (< 1 acre)", "Medium (1-10 acres)", "Commercial (10-50 acres)", "Industrial (50+ acres)"])
                years_exp = st.number_input("Years of Experience", min_value=0, value=0)
                gps_lat = st.number_input("GPS Latitude (optional)", value=0.0)
                gps_lon = st.number_input("GPS Longitude (optional)", value=0.0)
                if st.form_submit_button("Next →"):
                    st.session_state.step2_data = {
                        "country": country, "state": state, "lga": lga,
                        "city": city, "street": street, "landmark": landmark,
                        "farm_state": farm_state, "farm_lga": farm_lga,
                        "farm_size": farm_size, "primary_crop": primary_crop,
                        "farming_type": farming_type, "years_exp": years_exp,
                        "gps_lat": gps_lat if gps_lat != 0 else None,
                        "gps_lon": gps_lon if gps_lon != 0 else None
                    }
                    st.session_state.signup_step = 3
                    st.rerun()

        elif step == 3:
            st.subheader("Step 3 of 3: KYC & Bank (Optional)")
            with st.form("step3_form"):
                col1, col2 = st.columns(2)
                with col1:
                    bvn = st.text_input("BVN (11 digits)", max_chars=11)
                    nin = st.text_input("NIN (11 digits)", max_chars=11)
                    govt_id_type = st.selectbox("Government ID Type", ["", "National ID Card", "Driver's License", "International Passport", "Voter's Card (PVC)", "NIN Slip"])
                with col2:
                    govt_id_number = st.text_input("ID Number")
                    account_name = st.text_input("Account Name")
                    bank_name = st.selectbox("Bank", [""] + BANKS)
                    account_number = st.text_input("Account Number", max_chars=10)
                emergency_name = st.text_input("Emergency Contact Name")
                emergency_phone = st.text_input("Emergency Contact Phone")
                emergency_rel = st.text_input("Relationship")
                notify_sms = st.checkbox("SMS Notifications", value=True)
                notify_whatsapp = st.checkbox("WhatsApp Notifications", value=True)
                notify_weather = st.checkbox("Weather Alerts", value=True)
                notify_disease = st.checkbox("Disease Alerts", value=True)
                notify_payment = st.checkbox("Payment Alerts", value=True)
                language = st.selectbox("Preferred Language", ["English", "Hausa", "Yoruba", "Igbo", "Pidgin English"])
                if st.form_submit_button("Create Account 🚀"):
                    final_data = {**st.session_state.step1_data, **st.session_state.step2_data, **{
                        "bvn": bvn, "nin": nin, "id_type": govt_id_type,
                        "id_number": govt_id_number, "account_name": account_name,
                        "bank_name": bank_name, "account_number": account_number,
                        "emergency_name": emergency_name,
                        "emergency_phone": emergency_phone,
                        "emergency_rel": emergency_rel,
                        "notify_sms": notify_sms,
                        "notify_whatsapp": notify_whatsapp,
                        "notify_weather": notify_weather,
                        "notify_disease": notify_disease,
                        "notify_payment": notify_payment,
                        "language": language
                    }}
                    user, err = sign_up_comprehensive(final_data)
                    if err:
                        st.error(f"Signup failed: {err}")
                    else:
                        st.session_state.user = user
                        st.success("Account created successfully! 30 free scans added.")
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

if scans_left <= 0:
    st.warning("You have no scans left. Choose a plan to continue.")
    st.markdown("### Choose a Plan")
    cols = st.columns(len(PAYSTACK_PLANS))
    for i, (plan_key, scans) in enumerate(PAYSTACK_PLANS.items()):
        with cols[i]:
            st.markdown(f"**{scans} scans**")
            st.markdown(f'<a href="https://paystack.com/pay/gaia_{plan_key}" target="_blank"><button style="width:100%;padding:10px;background:#0d6efd;color:white;border:none;border-radius:5px;">Select</button></a>', unsafe_allow_html=True)
    st.stop()

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
university_page = st.Page("pages/22_University.py", title="GAIA University", icon="🎓")
calendar_page = st.Page("pages/23_Farming_Calendar.py", title="Farming Calendar", icon="📅")
farmer_db_page = st.Page("pages/25_Farmer_Database.py", title="Farmer Database", icon="🌍")
loan_page = st.Page("pages/26_Loan_Management.py", title="Loan Management", icon="🏦")
extension_page = st.Page("pages/27_Extension_Dashboard.py", title="Extension Dashboard", icon="🧑‍🌾")

pg = st.navigation({
    "GAIA": [dashboard_page],
    "Diagnose": [crops_page, pests_page, soil_page, livestock_page, video_page, satellite_page, voice_page],
    "Services": [buy_scans_page, wallet_page, badges_page, insurance_page, loan_page, university_page, calendar_page],
    "Community": [chat_page, marketplace_page, farmer_db_page],
    "Account": [profile_page, payment_history_page, verify_farmer_page, verify_history_page, help_page],
    "Admin": [admin_page, extension_page],
})
pg.run()
