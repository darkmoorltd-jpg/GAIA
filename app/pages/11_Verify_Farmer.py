
import streamlit as st
from supabase import create_client, Client
import uuid
import requests as req
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_PUBLIC = "pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057"
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

def normalize_phone(phone):
    """Convert Nigerian phone to international format."""
    if not phone:
        return "08000000000"
    phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    if phone.startswith("0"):
        return "234" + phone[1:]
    elif phone.startswith("234"):
        return phone
    else:
        return "234" + phone

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def init_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

def verify_payment(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    try:
        r = req.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status"):
                tx_data = data.get("data", {})
                return tx_data.get("status") == "success"
    except:
        pass
    return False

st.set_page_config(page_title="GAIA – Farmer Verification", page_icon="🛡️", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = init_supabase()
service = init_service()

# ===== FETCH USER PHONE (MUST BE BEFORE PAYSTACK) =====
user_phone = ""
try:
    profile_res = service.table("user_profiles").select("phone").eq("user_id", user.id).execute()
    if profile_res.data and len(profile_res.data) > 0:
        user_phone = profile_res.data[0].get("phone", "") or ""
except:
    pass

phone_for_sms = normalize_phone(user_phone)

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa, #e8f5e9); color: #1b5e20; }
    header, footer { visibility: hidden; }
    .title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #2e7d32; }
    .subtitle { text-align: center; color: #607d8b; margin-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🛡️ Farmer Verification</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Verify your identity to unlock wallet, insurance, and marketplace features</div>', unsafe_allow_html=True)

# Check if already verified
try:
    existing = service.table("farmer_verifications").select("*").eq("user_id", user.id).execute()
    if existing.data and len(existing.data) > 0:
        status = existing.data[0].get("status", "pending")
        if status == "approved":
            st.success("✅ You are already verified! All features are unlocked.")
            st.stop()
        elif status == "pending":
            st.info("⏳ Your verification is pending review. Please wait for admin approval.")
            st.stop()
except:
    pass

with st.form("verification_form"):
    st.markdown("### 📋 Personal Information")
    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Full Name *", placeholder="e.g., Ibrahim Musa")
        phone = st.text_input("Phone Number *", value=user_phone, placeholder="e.g., 08031234567")
        state = st.text_input("State *", placeholder="e.g., Kaduna")
    with col2:
        lga = st.text_input("LGA", placeholder="e.g., Kaduna North")
        address = st.text_input("Address *", placeholder="e.g., 12 Main Street")
        crops = st.text_input("Primary Crops", placeholder="e.g., Maize, Rice, Beans")
    
    st.markdown("---")
    st.markdown("### 🪪 ID Upload")
    
    col1, col2 = st.columns(2)
    with col1:
        id_type = st.selectbox("ID Type *", ["National ID Card", "Driver's License", "International Passport", "Voter's Card (PVC)", "NIN Slip"])
        id_number = st.text_input("ID Number *", placeholder="e.g., 12345678901")
    with col2:
        id_upload = st.file_uploader("Upload ID *", type=["jpg", "jpeg", "png", "pdf"])
        selfie_upload = st.file_uploader("Upload Selfie with ID *", type=["jpg", "jpeg", "png"])
    
    st.markdown("---")
    
    # Verification fee
    st.markdown("### 💳 Verification Fee: ₦2,000")
    
    submit = st.form_submit_button("✅ Submit for Verification", type="primary", use_container_width=True)

if submit:
    if not full_name or not phone or not state or not address or not id_upload or not selfie_upload:
        st.error("❌ Please fill all required fields and upload ID + selfie.")
    else:
        # Create verification record (pending)
        verification_ref = f"GAIA_VERIFY_{user.id[:8]}_{uuid.uuid4().hex[:8]}"
        
        service.table("farmer_verifications").insert({
            "user_id": user.id,
            "full_name": full_name,
            "phone": phone,
            "state": state,
            "lga": lga,
            "address": address,
            "crops": crops,
            "payment_reference": verification_ref,
            "payment_status": "pending",
            "status": "pending"
        }).execute()
        
        # Paystack payment for verification
        components_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://js.paystack.co/v1/inline.js"></script>
        </head>
        <body>
            <button onclick="payForVerification()" style="background:#2e7d32;color:#fff;border:none;padding:15px 40px;border-radius:10px;font-weight:700;cursor:pointer;">Pay ₦2,000 to Verify</button>
            <script>
                function payForVerification() {{
                    PaystackPop.setup({{
                        key: '{PAYSTACK_PUBLIC}',
                        email: '{user.email}',
                        phone: '{phone_for_sms}',
                        amount: 200000,
                        currency: 'NGN',
                        ref: '{verification_ref}',
                        label: 'GAIA Farmer Verification',
                        onClose: function() {{ window.location.reload(); }},
                        callback: function(response) {{
                            window.location.href = '/~/callback?reference=' + response.reference + '&plan=verification';
                        }}
                    }}).openIframe();
                }}
            </script>
        </body>
        </html>
        """
        
        st.components.v1.html(components_html, height=120)
        st.info("👆 Click the green button above to pay the verification fee.")
