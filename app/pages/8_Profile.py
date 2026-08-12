import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
ADMIN_EMAIL = "darkmoorltd@gmail.com"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="GAIA – My Profile", page_icon="👤", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = init_supabase()
is_admin = (user.email == ADMIN_EMAIL)

# Fetch profile on every page load
res = supabase.table("user_profiles").select("*").eq("user_id", user.id).execute()
profile = res.data[0] if res.data and len(res.data) > 0 else None

has_saved_name = bool(profile and profile.get("first_name"))
profile_locked = has_saved_name and not is_admin

st.markdown("<style>.stApp{background:linear-gradient(135deg,#f5f7fa,#e8f5e9)}.title{font-size:2.5rem;font-weight:800;text-align:center;color:#2e7d32}</style>", unsafe_allow_html=True)
st.title("👤 My Profile")

if profile_locked:
    st.info("🔒 Your profile has been saved and is now locked. Contact the admin to make changes.")
elif has_saved_name and is_admin:
    st.info("🔧 Admin mode — you can edit any user's profile.")
elif not has_saved_name:
    st.info("📝 Fill in your details and save. Once saved, only the admin can edit it.")

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
    
    st.markdown("**Social Media**")
    social = profile.get("social_media", {}) if profile else {}
    col1, col2, col3 = st.columns(3)
    with col1:
        twitter = st.text_input("Twitter/X", value=social.get("twitter", ""), disabled=profile_locked)
    with col2:
        linkedin = st.text_input("LinkedIn", value=social.get("linkedin", ""), disabled=profile_locked)
    with col3:
        instagram = st.text_input("Instagram", value=social.get("instagram", ""), disabled=profile_locked)
    
    if not profile_locked or is_admin:
        if st.form_submit_button("💾 Save Profile"):
            update_data = {
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "phone": phone.strip(),
                "country": country.strip(),
                "social_media": {
                    "twitter": twitter.strip(),
                    "linkedin": linkedin.strip(),
                    "instagram": instagram.strip()
                }
            }
            try:
                supabase.table("user_profiles").update(update_data).eq("user_id", user.id).execute()
                st.success("✅ Profile updated!")
                st.rerun()
            except:
                update_data["user_id"] = user.id
                supabase.table("user_profiles").insert(update_data).execute()
                st.success("✅ Profile created!")
                st.rerun()

st.markdown("---")
st.markdown("


# ---------- Quick Navigation ----------
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(10)
with cols[0]:
    st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]:
    st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]:
    st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]:
    st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]:
    st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]:
    st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[6]:
    st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[7]:
    st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[8]:
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")