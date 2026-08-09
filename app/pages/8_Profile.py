
import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
ADMIN_EMAIL = "darkmoorltd@gmail.com"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def init_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA – My Profile", page_icon="👤", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = init_supabase()
service = init_service()
is_admin = (user.email == ADMIN_EMAIL)

res = service.table("user_profiles").select("*").eq("user_id", user.id).execute()
profile = res.data[0] if res.data and len(res.data) > 0 else None

profile_locked = True
if is_admin: profile_locked = False
if not profile: profile_locked = False

CROP_LIST = ["Maize","Rice","Millet","Beans","Soybean","Cassava","Yam","Tomato","Pepper","Groundnut","Cotton","Sorghum","Vegetables","Fruits","Wheat","Cocoa","Oil Palm","Rubber","Cashew","Coffee","Tea","Coconut","Sugarcane","Ginger","Garlic","Onion","Cabbage"]
NIGERIAN_STATES = ["Abia","Adamawa","Akwa Ibom","Anambra","Bauchi","Bayelsa","Benue","Borno","Cross River","Delta","Ebonyi","Edo","Ekiti","Enugu","FCT","Gombe","Imo","Jigawa","Kaduna","Kano","Katsina","Kebbi","Kogi","Kwara","Lagos","Nasarawa","Niger","Ogun","Ondo","Osun","Oyo","Plateau","Rivers","Sokoto","Taraba","Yobe","Zamfara"]

st.markdown("<style>.stApp{background:linear-gradient(135deg,#f5f7fa,#e8f5e9)}</style>", unsafe_allow_html=True)
st.title("👤 My Profile")

if profile and not is_admin:
    st.info("🔒 Your profile is permanently locked. Contact admin to make changes.")
elif not profile:
    st.info("📝 Fill in your details and save. After saving, your profile will be permanently locked.")

with st.form("profile_form"):
    st.markdown("### 👤 Personal Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        first_name = st.text_input("First Name *", value=profile.get("first_name", "") if profile else "", disabled=profile_locked)
    with col2:
        middle_name = st.text_input("Middle Name", value=profile.get("middle_name", "") if profile else "", disabled=profile_locked)
    with col3:
        last_name = st.text_input("Last Name *", value=profile.get("last_name", "") if profile else "", disabled=profile_locked)
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Email", value=user.email, disabled=True)
    with col2:
        phone = st.text_input("Phone *", value=profile.get("phone", "") if profile else "", disabled=profile_locked)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        dob = st.date_input("Date of Birth", value=None if not profile or not profile.get("date_of_birth") else profile["date_of_birth"], disabled=profile_locked)
    with col2:
        bvn = st.text_input("BVN (11 digits)", value=profile.get("bvn", "") if profile else "", max_chars=11, disabled=profile_locked)
    with col3:
        nin = st.text_input("NIN (11 digits)", value=profile.get("nin", "") if profile else "", max_chars=11, disabled=profile_locked)
    
    if not profile_locked:
        nin_slip = st.file_uploader("📄 Upload NIN Slip", type=["jpg","jpeg","png","pdf"])
    elif profile and profile.get("nin_slip_url"):
        st.markdown(f"[📄 View NIN Slip]({profile['nin_slip_url']})")
    
    st.markdown("---")
    st.markdown("### 🏠 Location Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        country = st.text_input("Country *", value=profile.get("country", "") if profile else "", disabled=profile_locked)
    with col2:
        state = st.selectbox("State *", options=[""] + NIGERIAN_STATES, index=0 if not profile else NIGERIAN_STATES.index(profile.get("state", ""))+1 if profile.get("state") in NIGERIAN_STATES else 0, disabled=profile_locked)
    with col3:
        lga = st.text_input("Local Government Area *", value=profile.get("lga", "") if profile else "", disabled=profile_locked)
    
    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("City *", value=profile.get("city", "") if profile else "", disabled=profile_locked)
    with col2:
        house_address = st.text_area("House Address *", value=profile.get("house_address", "") if profile else "", disabled=profile_locked)
    
    st.markdown("---")
    st.markdown("### 🌾 Farm Information")
    col1, col2 = st.columns(2)
    with col1:
        farm_location = st.text_input("Farm Location", value=profile.get("farm_location", "") if profile else "", disabled=profile_locked)
    with col2:
        farm_size = st.selectbox("Farm Size", options=["","Less than 1 hectare","1-5 hectares","5-10 hectares","10-50 hectares","More than 50 hectares"], index=0 if not profile else 0, disabled=profile_locked)
    
    farm_address = st.text_area("Farm Address", value=profile.get("farm_address", "") if profile else "", disabled=profile_locked)
    
    # Crops grown - handle array
    existing_crops = profile.get("crops_grown", []) if profile else []
    if isinstance(existing_crops, str):
        existing_crops = [c.strip() for c in existing_crops.split(",") if c.strip()]
    crops = st.multiselect("Crops Grown *", options=CROP_LIST, default=existing_crops, disabled=profile_locked)
    
    association = st.text_input("Association Belonging To", value=profile.get("association", "") if profile else "", disabled=profile_locked, placeholder="e.g., RIFAN, AFAN, PAN")
    
    if not profile_locked:
        if st.form_submit_button("💾 Save Profile", use_container_width=True):
            errors = []
            if not first_name.strip(): errors.append("First Name is required")
            if not last_name.strip(): errors.append("Last Name is required")
            if not phone.strip(): errors.append("Phone is required")
            if not country.strip(): errors.append("Country is required")
            if not state: errors.append("State is required")
            if not lga.strip(): errors.append("LGA is required")
            if not city.strip(): errors.append("City is required")
            if not house_address.strip(): errors.append("House Address is required")
            if not crops: errors.append("At least one crop is required")
            
            if errors:
                for e in errors: st.error(f"❌ {e}")
            else:
                save_data = {
                    "user_id": user.id,
                    "first_name": first_name.strip(),
                    "middle_name": middle_name.strip(),
                    "last_name": last_name.strip(),
                    "phone": phone.strip(),
                    "country": country.strip(),
                    "state": state,
                    "lga": lga.strip(),
                    "city": city.strip(),
                    "house_address": house_address.strip(),
                    "farm_location": farm_location.strip(),
                    "farm_size": farm_size,
                    "farm_address": farm_address.strip(),
                    "crops_grown": crops,
                    "association": association.strip(),
                    "date_of_birth": str(dob) if dob else None,
                    "bvn": bvn.strip() if bvn else None,
                    "nin": nin.strip() if nin else None,
                }
                
                if nin_slip:
                    try:
                        file_path = f"{user.id}/nin_slip_{user.id[:8]}.{nin_slip.name.split('.')[-1]}"
                        service.storage.from_("message_attachment").upload(file_path, nin_slip.getvalue())
                        save_data["nin_slip_url"] = service.storage.from_("message_attachment").get_public_url(file_path)
                    except:
                        pass
                
                try:
                    service.table("user_profiles").upsert(save_data).execute()
                    st.success("✅ Profile saved and locked!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Save failed: {str(e)[:200]}")

st.markdown("---")
cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
