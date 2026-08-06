import streamlit as st
from supabase import create_client, Client
import uuid

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]

@st.cache_resource
def init_supabase(): return create_client(SUPABASE_URL, SUPABASE_KEY)
@st.cache_resource
def init_service(): return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA – Farmer Verification", page_icon="🛡️", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = init_supabase()
service = init_service()

existing = supabase.table("farmer_verifications").select("*").eq("user_id", user.id).execute()
verification = existing.data[0] if existing.data and len(existing.data) > 0 else None

st.markdown('<style>.stApp{background:linear-gradient(135deg,#f5f7fa,#e8f5e9)}.title{font-size:2.5rem;font-weight:800;text-align:center;color:#2e7d32}</style>', unsafe_allow_html=True)
st.markdown('<div class="title">🛡️ Farmer Verification</div>', unsafe_allow_html=True)

if verification and verification.get("status") == "approved":
    st.success(f"✅ Verified Farmer — {verification.get('full_name')} | {verification.get('state')}")
elif verification and verification.get("status") == "pending":
    st.info(f"⏳ Under Review — {verification.get('full_name')} | {verification.get('state')}")
else:
    with st.form("verify_form"):
        full_name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")
        state = st.selectbox("State", ["Delta","Lagos","Abuja","Kano","Rivers","Ogun","Oyo","Kaduna","Enugu","Edo"])
        lga = st.text_input("LGA")
        crops = st.multiselect("Crops Grown", ["Maize","Rice","Millet","Beans","Soybean","Cassava","Yam","Tomato","Pepper","Groundnut","Cotton","Sorghum"])
        id_img = st.file_uploader("Upload ID Card", type=["jpg","jpeg","png"])
        sf = st.file_uploader("Upload Selfie", type=["jpg","jpeg","png"])
        if st.form_submit_button("Submit Verification"):
            if not full_name or not id_img:
                st.error("Fill all fields and upload ID.")
            else:
                id_fn = f"{user.id}/id_{uuid.uuid4().hex[:8]}.jpg"
                sf_fn = f"{user.id}/selfie_{uuid.uuid4().hex[:8]}.jpg" if sf else None
                service.storage.from_("message_attachment").upload(id_fn, id_img.getvalue())
                if sf: service.storage.from_("message_attachment").upload(sf_fn, sf.getvalue())
                service.table("farmer_verifications").upsert({"user_id":user.id,"full_name":full_name,"phone":phone,"state":state,"lga":lga,"crops":crops,"id_url":id_fn,"selfie_url":sf_fn,"status":"pending","payment_status":"pending"}).execute()
                st.success("Submitted!")
                st.rerun()
st.markdown("---")
cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
