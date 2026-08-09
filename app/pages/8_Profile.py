
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

# Fetch profile using service client to avoid RLS issues
res = service.table("user_profiles").select("*").eq("user_id", user.id).execute()
profile = res.data[0] if res.data and len(res.data) > 0 else None

# Determine locked status
profile_locked = bool(profile and profile.get("profile_locked", False))
if is_admin:
    profile_locked = False

st.markdown("<style>.stApp{background:linear-gradient(135deg,#f5f7fa,#e8f5e9)}</style>", unsafe_allow_html=True)
st.title("👤 My Profile")

if profile_locked:
    st.info("🔒 Your profile is locked. Contact admin to make changes.")
elif profile:
    st.info("📝 Profile saved. Admin can edit if needed.")
else:
    st.info("📝 Fill in your details and save.")

with st.form("profile_form"):
    col1, col2 = st.columns(2)
    with col1:
        first_name = st.text_input("First Name", value=profile.get("first_name", "") if profile else "", disabled=profile_locked)
    with col2:
        last_name = st.text_input("Last Name", value=profile.get("last_name", "") if profile else "", disabled=profile_locked)
    
    st.text_input("Email", value=user.email, disabled=True)
    
    col1, col2 = st.columns(2)
    with col1:
        country = st.text_input("Country", value=profile.get("country", "") if profile else "", disabled=profile_locked)
    with col2:
        phone = st.text_input("Phone", value=profile.get("phone", "") if profile else "", disabled=profile_locked)
    
    if not profile_locked:
        if st.form_submit_button("💾 Save Profile"):
            save_data = {
                "user_id": user.id,
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "phone": phone.strip(),
                "country": country.strip(),
                "profile_locked": True
            }
            
            # Use UPSERT with service client (bypasses ALL RLS)
            try:
                service.table("user_profiles").upsert(save_data).execute()
                st.success("✅ Profile saved!")
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
