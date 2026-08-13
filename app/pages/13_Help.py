import streamlit as st
from supabase import create_client, Client
import uuid

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

def upload_file_to_supabase(file_bytes, filename):
    """Upload file to Supabase Storage and return URL."""
    supabase = get_service()
    clean_name = "attachment_" + uuid.uuid4().hex[:10] + ".bin"
    
    try:
        supabase.storage.from_("support_attachments").upload(clean_name, file_bytes)
        url = supabase.storage.from_("support_attachments").get_public_url(clean_name)
        return url, None
    except Exception as e:
        try:
            supabase.storage.create_bucket("support_attachments", {"public": True})
            supabase.storage.from_("support_attachments").upload(clean_name, file_bytes)
            url = supabase.storage.from_("support_attachments").get_public_url(clean_name)
            return url, None
        except Exception as e2:
            return None, f"Upload failed: {str(e2)[:200]}"

st.set_page_config(page_title="GAIA – Help & Support", page_icon="💬", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = get_service()

# ============================================
# FULL NAVIGATION
# ============================================
st.markdown("---")
st.markdown("### Quick Navigation")
cols = st.columns(10)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="Livestock")
with cols[5]: st.page_link("pages/17_Video_Scan.py", label="Video Scan")
with cols[6]: st.page_link("pages/19_Satellite.py", label="Satellite")
with cols[7]: st.page_link("pages/18_Voice_Agronomist.py", label="Voice AI")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="Buy Scans")
with cols[9]: st.page_link("pages/10_Early_Warning.py", label="Alerts")

st.markdown("### More Features")
cols2 = st.columns(10)
with cols2[0]: st.page_link("pages/11_Verify_Farmer.py", label="Verify")
with cols2[1]: st.page_link("pages/12_Verification_History.py", label="History")
with cols2[2]: st.page_link("pages/14_Wallet.py", label="Wallet")
with cols2[3]: st.page_link("pages/15_Badges.py", label="Badges")
with cols2[4]: st.page_link("pages/16_Chat.py", label="Chat")
with cols2[5]: st.page_link("pages/20_Marketplace.py", label="Market")
with cols2[6]: st.page_link("pages/21_Crop_Insurance.py", label="Insurance")
with cols2[7]: st.page_link("pages/6_Payment_History.py", label="Payments")
with cols2[8]: st.page_link("pages/8_Profile.py", label="Profile")
with cols2[9]: st.page_link("pages/13_Help.py", label="Help")
