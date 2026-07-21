
import streamlit as st
from supabase import create_client, Client

def bottom_nav():
    st.markdown("---")
    st.markdown("### 🚀 Quick Navigation")
    cols = st.columns(8)
    with cols[0]:
        if st.button("🌿 Crops", key="bn_crops"): st.switch_page("pages/2_Crops.py")
    with cols[1]:
        if st.button("🐛 Pests", key="bn_pests"): st.switch_page("pages/3_Pests.py")
    with cols[2]:
        if st.button("🏞️ Soil", key="bn_soil"): st.switch_page("pages/4_Soil.py")
    with cols[3]:
        if st.button("🐄 Livestock", key="bn_livestock"): st.switch_page("pages/5_Livestock.py")
    with cols[4]:
        if st.button("💳 Buy Scans", key="bn_buy"): st.switch_page("pages/9_Buy_Scans.py")
    with cols[5]:
        if st.button("📋 Payments", key="bn_payments"): st.switch_page("pages/6_Payment_History.py")
    with cols[6]:
        if st.button("🔐 Admin", key="bn_admin"): st.switch_page("pages/7_Admin.py")
    with cols[7]:
        if st.button("🚪 Logout", key="bn_logout"):
            from supabase import create_client
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
            supabase = create_client(url, key)
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()


SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="GAIA – Profile", page_icon="👤", layout="wide", initial_sidebar_state="expanded")

# Force sidebar visible on all pages
st.markdown("""

""", unsafe_allow_html=True)


if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = init_supabase()

# Fetch profile
res = supabase.table("user_profiles").select("*").eq("user_id", user.id).execute()
profile = res.data[0] if res.data else {}

st.title("👤 My Profile")

with st.form("profile_form"):
    col1, col2 = st.columns(2)
    with col1:
        first_name = st.text_input("First Name", value=profile.get("first_name", ""))
    with col2:
        last_name = st.text_input("Last Name", value=profile.get("last_name", ""))
    
    st.text_input("Email", value=user.email, disabled=True)
    
    col1, col2 = st.columns(2)
    with col1:
        country = st.selectbox(
            "Country",
            options=[""] + [
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
            ],
            index=0 if not profile.get("country") else None
        )
    with col2:
        phone = st.text_input("Phone", value=profile.get("phone", ""))
    
    st.markdown("**Social Media**")
    social = profile.get("social_media", {}) or {}
    col1, col2, col3 = st.columns(3)
    with col1:
        twitter = st.text_input("Twitter/X", value=social.get("twitter", ""))
    with col2:
        linkedin = st.text_input("LinkedIn", value=social.get("linkedin", ""))
    with col3:
        instagram = st.text_input("Instagram", value=social.get("instagram", ""))
    
    if st.form_submit_button("Update Profile"):
        update_data = {
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "phone": phone.strip(),
            "country": country,
            "social_media": {
                "twitter": twitter.strip(),
                "linkedin": linkedin.strip(),
                "instagram": instagram.strip()
            }
        }
        # Try update first, if it fails (row doesn't exist), insert
        try:
            supabase.table("user_profiles").update(update_data).eq("user_id", user.id).execute()
        except:
            update_data["user_id"] = user.id
            supabase.table("user_profiles").insert(update_data).execute()
        st.success("Profile updated!")
        st.rerun()


# ---------- Universal Bottom Navigation (safe) ----------
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(6)
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
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
