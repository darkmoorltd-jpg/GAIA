
import streamlit as st
from supabase import create_client, Client
from datetime import datetime

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
ADMIN_EMAIL = "darkmoorltd@gmail.com"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def init_service():
    """Service role client — bypasses RLS for writes."""
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA – My Profile", page_icon="👤", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = init_supabase()
service = init_service()
is_admin = (user.email == ADMIN_EMAIL)

# Fetch profile using service role (always works)
try:
    res = service.table("user_profiles").select("*").eq("user_id", user.id).execute()
    profile = res.data[0] if res.data and len(res.data) > 0 else None
except:
    profile = None

has_saved_profile = bool(profile and profile.get("first_name") and profile.get("last_name"))
profile_locked = has_saved_profile and not is_admin

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa, #e8f5e9); color: #1b5e20; }
    header, footer { visibility: hidden; }
    .title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #2e7d32; }
    .locked-banner { background: #fff3e0; border: 2px solid #ff9800; border-radius: 12px; padding: 1rem; text-align: center; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">👤 My Profile</div>', unsafe_allow_html=True)

if profile_locked:
    st.markdown('<div class="locked-banner">🔒 Profile locked. Contact darkmoorltd@gmail.com to edit.</div>', unsafe_allow_html=True)

can_edit = not profile_locked or is_admin

with st.form("complete_profile_form"):
    st.markdown("## 📋 Personal Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        first_name = st.text_input("First Name *", value=profile.get("first_name", "") if profile else "", disabled=not can_edit)
        middle_name = st.text_input("Middle Name", value=profile.get("middle_name", "") if profile else "", disabled=not can_edit)
        gender = st.selectbox("Gender", ["", "Male", "Female"], disabled=not can_edit)
    with col2:
        last_name = st.text_input("Last Name *", value=profile.get("last_name", "") if profile else "", disabled=not can_edit)
        date_of_birth = st.date_input("Date of Birth", value=None, disabled=not can_edit, key="dob")
        marital_status = st.selectbox("Marital Status", ["", "Single", "Married", "Divorced", "Widowed"], disabled=not can_edit)
    with col3:
        phone = st.text_input("Phone * (for SMS receipts)", value=profile.get("phone", "") if profile else "", disabled=not can_edit)
        whatsapp = st.text_input("WhatsApp *", value=profile.get("whatsapp", "") if profile else "", disabled=not can_edit)
        email = st.text_input("Email", value=user.email, disabled=True)
    
    st.markdown("---")
    st.markdown("## 🏠 Address")
    col1, col2, col3 = st.columns(3)
    with col1:
        country = st.text_input("Country *", value=profile.get("country", "Nigeria") if profile else "Nigeria", disabled=not can_edit)
        state = st.text_input("State *", value=profile.get("state", "") if profile else "", disabled=not can_edit)
        lga = st.text_input("LGA", value=profile.get("lga", "") if profile else "", disabled=not can_edit)
    with col2:
        city = st.text_input("City/Town *", value=profile.get("city", "") if profile else "", disabled=not can_edit)
        street_address = st.text_input("Street Address", value=profile.get("street_address", "") if profile else "", disabled=not can_edit)
        landmark = st.text_input("Landmark", value=profile.get("landmark", "") if profile else "", disabled=not can_edit)
    with col3:
        postal_code = st.text_input("Postal Code", value=profile.get("postal_code", "") if profile else "", disabled=not can_edit)
    
    st.markdown("---")
    st.markdown("## 🛡️ KYC Information")
    col1, col2 = st.columns(2)
    with col1:
        bvn = st.text_input("BVN (11 digits)", value=profile.get("bvn", "") if profile else "", max_chars=11, disabled=not can_edit)
        nin = st.text_input("NIN (11 digits)", value=profile.get("nin", "") if profile else "", max_chars=11, disabled=not can_edit)
        govt_id_type = st.selectbox("Government ID Type", ["", "National ID Card", "Driver's License", "International Passport", "Voter's Card (PVC)", "NIN Slip"], disabled=not can_edit)
    with col2:
        govt_id_number = st.text_input("ID Number", value=profile.get("govt_id_number", "") if profile else "", disabled=not can_edit)
    
    st.markdown("---")
    st.markdown("## 🌾 Farm Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        farm_state = st.text_input("Farm State", value=profile.get("farm_state", "") if profile else "", disabled=not can_edit)
        farm_size = st.number_input("Farm Size (acres)", min_value=0.0, value=float(profile.get("farm_size_acres", 1.0) if profile else 1.0), disabled=not can_edit)
        farming_type = st.selectbox("Farming Type", ["", "Smallholder (< 1 acre)", "Medium (1-10 acres)", "Commercial (10-50 acres)", "Industrial (50+ acres)"], disabled=not can_edit)
    with col2:
        farm_lga = st.text_input("Farm LGA", value=profile.get("farm_lga", "") if profile else "", disabled=not can_edit)
        years_exp = st.number_input("Years of Experience", min_value=0, value=int(profile.get("years_experience", 0) if profile else 0), disabled=not can_edit)
        primary_crops = st.text_input("Primary Crops", value=profile.get("primary_crops", "") if profile else "", disabled=not can_edit)
    with col3:
        farm_address = st.text_input("Farm Address", value=profile.get("farm_address", "") if profile else "", disabled=not can_edit)
    
    st.markdown("---")
    st.markdown("## 🏦 Bank Information")
    col1, col2 = st.columns(2)
    with col1:
        account_name = st.text_input("Account Name", value=profile.get("account_name", "") if profile else "", disabled=not can_edit)
        bank_name = st.selectbox("Bank", ["", "Access Bank", "GTBank", "Zenith Bank", "UBA", "First Bank", "Kuda", "Opay", "Palmpay", "Moniepoint", "Sterling Bank", "Union Bank", "Fidelity Bank", "Wema Bank"], disabled=not can_edit)
    with col2:
        account_number = st.text_input("Account Number", value=profile.get("account_number", "") if profile else "", max_chars=10, disabled=not can_edit)
    
    st.markdown("---")
    st.markdown("## 🚨 Emergency Contact")
    col1, col2 = st.columns(2)
    with col1:
        emergency_name = st.text_input("Contact Name", value=profile.get("emergency_contact_name", "") if profile else "", disabled=not can_edit)
        emergency_relationship = st.text_input("Relationship", value=profile.get("emergency_relationship", "") if profile else "", disabled=not can_edit)
    with col2:
        emergency_phone = st.text_input("Contact Phone", value=profile.get("emergency_contact_phone", "") if profile else "", disabled=not can_edit)
    
    st.markdown("---")
    st.markdown("## 🔔 Notification Preferences")
    col1, col2 = st.columns(2)
    with col1:
        notify_sms = st.checkbox("SMS Notifications", value=True if not profile else profile.get("notify_sms", True), disabled=not can_edit)
        notify_whatsapp = st.checkbox("WhatsApp", value=True if not profile else profile.get("notify_whatsapp", True), disabled=not can_edit)
        notify_weather = st.checkbox("Weather Alerts", value=True if not profile else profile.get("notify_weather", True), disabled=not can_edit)
    with col2:
        notify_disease = st.checkbox("Disease Alerts", value=True if not profile else profile.get("notify_disease", True), disabled=not can_edit)
        notify_payment = st.checkbox("Payment Alerts", value=True if not profile else profile.get("notify_payment", True), disabled=not can_edit)
        preferred_language = st.selectbox("Language", ["English", "Hausa", "Yoruba", "Igbo", "Pidgin English"], disabled=not can_edit)
    
    if can_edit:
        submitted = st.form_submit_button("💾 Save Profile & Lock", type="primary", use_container_width=True)
    else:
        st.info("🔒 Profile is locked.")
        submitted = False

if submitted:
    if not first_name or not last_name or not phone:
        st.error("❌ First name, last name, and phone are required.")
    else:
        update_data = {
            "user_id": user.id,
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "middle_name": middle_name.strip() if middle_name else None,
            "phone": phone.strip(),
            "whatsapp": whatsapp.strip() if whatsapp else None,
            "gender": gender if gender else None,
            "marital_status": marital_status if marital_status else None,
            "country": country.strip() or "Nigeria",
            "state": state.strip() if state else None,
            "lga": lga.strip() if lga else None,
            "city": city.strip() if city else None,
            "street_address": street_address.strip() if street_address else None,
            "landmark": landmark.strip() if landmark else None,
            "postal_code": postal_code.strip() if postal_code else None,
            "bvn": bvn.strip() if bvn else None,
            "nin": nin.strip() if nin else None,
            "govt_id_type": govt_id_type if govt_id_type else None,
            "govt_id_number": govt_id_number.strip() if govt_id_number else None,
            "farm_state": farm_state.strip() if farm_state else None,
            "farm_lga": farm_lga.strip() if farm_lga else None,
            "farm_address": farm_address.strip() if farm_address else None,
            "farm_size_acres": farm_size,
            "years_experience": years_exp,
            "primary_crops": primary_crops.strip() if primary_crops else None,
            "farming_type": farming_type if farming_type else None,
            "account_name": account_name.strip() if account_name else None,
            "account_number": account_number.strip() if account_number else None,
            "bank_name": bank_name if bank_name else None,
            "emergency_contact_name": emergency_name.strip() if emergency_name else None,
            "emergency_contact_phone": emergency_phone.strip() if emergency_phone else None,
            "emergency_relationship": emergency_relationship.strip() if emergency_relationship else None,
            "notify_sms": notify_sms,
            "notify_whatsapp": notify_whatsapp,
            "notify_weather": notify_weather,
            "notify_disease": notify_disease,
            "notify_payment": notify_payment,
            "preferred_language": preferred_language,
            "verification_status": "pending",
        }
        
        try:
            if profile:
                # Update existing
                service.table("user_profiles").update(update_data).eq("user_id", user.id).execute()
            else:
                # Insert new
                service.table("user_profiles").insert(update_data).execute()
            st.success("✅ Profile saved! Phone number is now ready for Paystack SMS receipts.")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)[:200]}")

# ===== NAVIGATION =====
st.markdown("---")
cols = st.columns(9)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[6]: st.page_link("pages/20_Marketplace.py", label="🌍 Market")
with cols[7]: st.page_link("pages/21_Crop_Insurance.py", label="🏦 Insurance")
with cols[8]: st.page_link("pages/7_Admin.py", label="🔐 Admin")
