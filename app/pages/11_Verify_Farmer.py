
import streamlit as st
from supabase import create_client, Client
import uuid
import requests as req
import re
from datetime import datetime

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

VERIFICATION_FEE = 200000      # in kobo (₦2,000)
VERIFICATION_FEE_NAIRA = 2000

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def init_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

def safe_crops(val):
    if not val: return "None"
    if isinstance(val, list): return ", ".join(val)
    return str(val).strip("{}").replace('"', '')

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

def is_unique(service, table, column, value, exclude_user_id=None):
    query = service.table(table).select("user_id").eq(column, value)
    if exclude_user_id:
        query = query.neq("user_id", exclude_user_id)
    res = query.execute()
    return len(res.data) == 0 if res.data else True

st.set_page_config(page_title="GAIA – Farmer Verification", page_icon="🛡️", layout="wide")

# ── Auto‑verify payment on return from Paystack ──
query_params = st.query_params
url_ref = query_params.get("reference", [None])[0]
if url_ref:
    supabase = init_supabase()
    existing = supabase.table("farmer_verifications").select("*").eq("payment_reference", url_ref).execute()
    if existing.data and len(existing.data) > 0:
        is_paid = verify_payment(url_ref)
        if is_paid:
            supabase.table("farmer_verifications").update({
                "payment_status": "paid", "status": "pending"
            }).eq("payment_reference", url_ref).execute()
            st.session_state.verification_paid = True
            st.success("✅ Payment confirmed! You can now submit your documents.")
            st.query_params.clear()
            st.rerun()

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = init_supabase()
service = init_service()

# Check existing verification
existing = supabase.table("farmer_verifications").select("*").eq("user_id", user.id).execute()
verification = existing.data[0] if existing.data and len(existing.data) > 0 else None

# Track payment status
if "verification_paid" not in st.session_state:
    st.session_state.verification_paid = (
        verification and verification.get("payment_status") == "paid"
    ) or False

if "verify_attempts" not in st.session_state:
    st.session_state.verify_attempts = 0

# Styling
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa, #e8f5e9); }
    .title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #2e7d32; }
    .subtitle { text-align: center; color: #555; margin-bottom: 2rem; }
    .verified-badge { background: linear-gradient(135deg, #2e7d32, #4caf50); color: #fff; padding: 10px 25px; border-radius: 30px; font-weight: 700; font-size: 1.2rem; }
    .pending-badge { background: linear-gradient(135deg, #f57f17, #ffb300); color: #fff; padding: 10px 25px; border-radius: 30px; font-weight: 700; font-size: 1.2rem; }
    .rejected-badge { background: linear-gradient(135deg, #c62828, #e53935); color: #fff; padding: 10px 25px; border-radius: 30px; font-weight: 700; font-size: 1.2rem; }
    .progress-container { display: flex; justify-content: center; gap: 2rem; margin-bottom: 2rem; }
    .progress-step { text-align: center; padding: 1rem 1.5rem; border-radius: 15px; background: rgba(255,255,255,0.8); }
    .progress-step.active { background: #2e7d32; color: #fff; }
    .progress-step.done { background: #c8e6c9; color: #2e7d32; }
    .progress-step.inactive { background: #f5f5f5; color: #999; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🛡️ Farmer Verification</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Complete your identity verification to unlock digital wallet and marketplace</div>', unsafe_allow_html=True)

# ============================================================
# PROGRESS INDICATOR
# ============================================================
st.markdown('<div class="progress-container">', unsafe_allow_html=True)

if verification and verification.get("status") == "approved":
    step1, step2, step3 = "done", "done", "done"
elif st.session_state.verification_paid:
    step1, step2, step3 = "done", "active", "inactive"
else:
    step1, step2, step3 = "active", "inactive", "inactive"

st.markdown(f'<div class="progress-step {step1}">💳 Payment</div>', unsafe_allow_html=True)
st.markdown(f'<div class="progress-step {step2}">📝 Profile</div>', unsafe_allow_html=True)
st.markdown(f'<div class="progress-step {step3}">✅ Done</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# SHOW CURRENT STATUS IF VERIFICATION EXISTS
# ============================================================
if verification:
    status = verification.get("status", "pending")
    
    if status == "approved":
        st.markdown(f'<div style="text-align:center;"><span class="verified-badge">✅ Verified Farmer</span></div>', unsafe_allow_html=True)
        st.success(f"**Name:** {verification.get('first_name','')} {verification.get('middle_name','')} {verification.get('last_name','')}\n\n**Phone:** {verification.get('phone')}\n\n**State:** {verification.get('state')} | **LGA:** {verification.get('lga')}\n\n**Crops:** {safe_crops(verification.get('crops'))}")
        st.info("🎉 You are verified! Your digital wallet is now active. Go to **💰 Digital Wallet** to view your account.")
        st.stop()
        
    elif status == "pending" and verification.get("payment_status") == "paid":
        st.markdown(f'<div style="text-align:center;"><span class="pending-badge">⏳ Under Review</span></div>', unsafe_allow_html=True)
        st.info("Your verification is under review. An admin will check within 24 hours.")
        st.stop()
        
    elif status == "rejected":
        st.markdown(f'<div style="text-align:center;"><span class="rejected-badge">❌ Rejected</span></div>', unsafe_allow_html=True)
        st.error(f"**Reason:** {verification.get('rejection_reason', 'No reason provided')}")
        if st.button("🔄 Resubmit Verification"):
            service.table("farmer_verifications").delete().eq("user_id", user.id).execute()
            st.session_state.verification_paid = False
            st.rerun()
        st.stop()

# ============================================================
# STEP 1: PAYMENT (₦2,000)
# ============================================================
if not st.session_state.verification_paid:
    st.markdown("### Step 1: Pay Verification Fee (₦2,000)")
    st.markdown("Payment is required before you can submit your documents.")
    
    ref = f"GAIA_VERIFY_{user.id[:8]}_{uuid.uuid4().hex[:8]}"
    
    service.table("farmer_verifications").upsert({
        "user_id": user.id,
        "payment_reference": ref,
        "payment_status": "pending",
        "status": "pending"
    }).execute()
    
    import streamlit.components.v1 as components
    paystack_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://js.paystack.co/v1/inline.js"></script>
        <style>
            body {{ margin:0; padding:0; display:flex; justify-content:center; }}
            .btn {{
                padding: 30px 80px; background: linear-gradient(135deg, #0d6efd, #6610f2); color: #fff;
                border: none; border-radius: 30px; font-size: 1.5rem;
                cursor: pointer; font-weight: 600;
            }}
            .btn:hover {{ background: #0b5ed7; }}
        </style>
    </head>
    <body>
        <button class="btn" onclick="payWithPaystack()">💳 Pay ₦{VERIFICATION_FEE_NAIRA:,} to Verify</button>
        <script>
            function payWithPaystack() {{
                PaystackPop.setup({{
                    key: 'pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057',
                    email: '{user.email}',
                    amount: {VERIFICATION_FEE},
                    currency: 'NGN',
                    ref: '{ref}',
                    label: 'GAIA Farmer Verification',
                    onClose: function() {{ window.location.reload(); }},
                    callback: function(response) {{
                        window.location.href = '/~/callback?reference=' + response.reference + '&plan=verify';
                    }}
                }}).openIframe();
            }}
        </script>
    </body>
    </html>
    """
    components.html(paystack_html, height=600)
    
    st.caption("⏳ A payment popup will appear. If blocked, allow popups for this site.")
    
    st.markdown("---")
    st.subheader("✅ Already Paid? Verify Your Payment to Continue")
    col1, col2 = st.columns([3, 1])
    with col1:
        manual_ref = st.text_input("Enter your Paystack reference", placeholder="e.g., GAIA_VERIFY_abc123", key="verify_ref")
    with col2:
        st.write("")
        if st.button("🔍 Verify Payment", use_container_width=True) and manual_ref:
            with st.spinner("Verifying..."):
                if verify_payment(manual_ref):
                    service.table("farmer_verifications").update({
                        "payment_status": "paid",
                        "payment_reference": manual_ref,
                        "status": "pending"
                    }).eq("user_id", user.id).execute()
                    st.session_state.verification_paid = True
                    st.session_state.verify_attempts = 0
                    st.success("✅ Payment verified! You can now submit your documents.")
                    st.rerun()
                else:
                    st.session_state.verify_attempts += 1
                    st.error("❌ Payment not found.")
                    if st.session_state.verify_attempts >= 3:
                        st.warning("Still having trouble? Contact support with your payment reference.")
                        st.markdown("[📧 Email Support](darkmoorltd@gmail.com)")
    
    st.stop()

# ============================================================
# STEP 2: UPLOAD DOCUMENTS (COMPREHENSIVE)
# ============================================================
if st.session_state.verification_paid:
    st.markdown("---")
    st.markdown("### Step 2: Complete Your Farmer Profile")
    st.markdown("All fields marked with * are **compulsory**.")
    
    with st.form("verify_form"):
        # ── PERSONAL INFORMATION ──
        st.markdown("#### 👤 Personal Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            first_name = st.text_input("First Name *", placeholder="Your legal first name")
        with col2:
            middle_name = st.text_input("Middle Name", placeholder="Optional")
        with col3:
            last_name = st.text_input("Last Name *", placeholder="Your legal last name")
        
        col1, col2 = st.columns(2)
        with col1:
            dob = st.date_input("Date of Birth *", min_value=datetime(1900,1,1), max_value=datetime.now())
        with col2:
            phone = st.text_input("Phone Number *", placeholder="+2348012345678")
        
        # ── ADDRESS ──
        st.markdown("#### 🏠 Home Address")
        home_address = st.text_input("Home Address *", placeholder="Street name, house number, landmark")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            city = st.text_input("City/Town *", placeholder="Your city or town")
        with col2:
            state = st.selectbox("State *", [
                "Select your state", "Abia","Adamawa","Akwa Ibom","Anambra","Bauchi","Bayelsa","Benue",
                "Borno","Cross River","Delta","Ebonyi","Edo","Ekiti","Enugu","FCT","Gombe","Imo",
                "Jigawa","Kaduna","Kano","Katsina","Kebbi","Kogi","Kwara","Lagos","Nasarawa",
                "Niger","Ogun","Ondo","Osun","Oyo","Plateau","Rivers","Sokoto","Taraba","Yobe","Zamfara"
            ])
        with col3:
            lga = st.text_input("Local Government Area *", placeholder="Your LGA")
        
        # ── FARM INFORMATION ──
        st.markdown("#### 🌾 Farm Information")
        col1, col2 = st.columns(2)
        with col1:
            farm_location = st.text_input("Farm Location *", placeholder="Where your farm is located")
            farm_size = st.selectbox("Farm Size *", [
                "Select size", "Less than 1 hectare", "1-2 hectares", "2-5 hectares",
                "5-10 hectares", "10-20 hectares", "20-50 hectares", "More than 50 hectares"
            ])
        with col2:
            crops_grown = st.multiselect("Crops Grown *", [
                "Maize","Rice","Millet","Beans","Soybean","Cassava","Yam",
                "Tomato","Pepper","Groundnut","Cotton","Sorghum","Vegetables","Fruits",
                "Livestock (Cattle)","Livestock (Poultry)","Livestock (Goats/Sheep)"
            ])
            association = st.text_input("Farmers Association", placeholder="e.g., AFAN, RIFAN, PAN (if applicable)")
        
        # ── GOVERNMENT ID ──
        st.markdown("#### 🛂 Government Identification")
        col1, col2 = st.columns(2)
        with col1:
            bvn = st.text_input("BVN (Bank Verification Number) *", max_chars=11, placeholder="11-digit BVN")
            id_type = st.selectbox("ID Type *", [
                "Select ID type", "National ID Card", "Voter's Card", "Driver's License",
                "International Passport", "NIN Slip"
            ])
        with col2:
            nin = st.text_input("NIN (National Identification Number) *", max_chars=11, placeholder="11-digit NIN")
            id_number = st.text_input("ID Number *", placeholder="Number on your ID card")
        
        # ── DOCUMENT UPLOADS ──
        st.markdown("#### 📷 Document Uploads")
        col1, col2, col3 = st.columns(3)
        with col1:
            nin_slip = st.file_uploader("Upload NIN Slip *", type=["jpg","jpeg","png","pdf"],
                help="Clear photo or scan of your NIN slip")
        with col2:
            id_card = st.file_uploader("Upload ID Card *", type=["jpg","jpeg","png"],
                help="National ID, Voter's Card, Driver's License, or Passport")
        with col3:
            selfie = st.file_uploader("Upload Selfie *", type=["jpg","jpeg","png"],
                help="Clear photo of your face holding your ID")
        
        submitted = st.form_submit_button("📤 Submit Verification", use_container_width=True)
        
        if submitted:
            errors = []
            
            # Validate personal info
            if not first_name or not first_name.strip():
                errors.append("First Name is required")
            if not last_name or not last_name.strip():
                errors.append("Last Name is required")
            if not dob:
                errors.append("Date of Birth is required")
            if not phone or not phone.strip():
                errors.append("Phone Number is required")
            elif not re.match(r'^\+?[\d\s\-\(\)]{10,15}$', phone.strip()):
                errors.append("Enter a valid phone number (e.g., +2348012345678)")
            
            # Validate address
            if not home_address or not home_address.strip():
                errors.append("Home Address is required")
            if not city or not city.strip():
                errors.append("City/Town is required")
            if not state or state == "Select your state":
                errors.append("State is required")
            if not lga or not lga.strip():
                errors.append("LGA is required")
            
            # Validate farm info
            if not farm_location or not farm_location.strip():
                errors.append("Farm Location is required")
            if not farm_size or farm_size == "Select size":
                errors.append("Farm Size is required")
            if not crops_grown:
                errors.append("At least one crop must be selected")
            
            # Validate government IDs
            if not bvn or not bvn.strip() or len(bvn.strip()) != 11 or not bvn.strip().isdigit():
                errors.append("Enter a valid 11-digit BVN")
            if not nin or not nin.strip() or len(nin.strip()) != 11 or not nin.strip().isdigit():
                errors.append("Enter a valid 11-digit NIN")
            if not id_type or id_type == "Select ID type":
                errors.append("ID Type is required")
            if not id_number or not id_number.strip():
                errors.append("ID Number is required")
            
            # Validate uploads
            if not nin_slip:
                errors.append("NIN Slip upload is required")
            if not id_card:
                errors.append("ID Card upload is required")
            if not selfie:
                errors.append("Selfie upload is required")
            
            # ── UNIQUENESS CHECKS ──
            if not errors:
                if not is_unique(service, "farmer_verifications", "email", user.email, user.id):
                    errors.append("❌ This email is already registered for verification.")
                if not is_unique(service, "farmer_verifications", "phone", phone.strip(), user.id):
                    errors.append("❌ This phone number is already registered by another farmer.")
                if not is_unique(service, "farmer_verifications", "bvn", bvn.strip(), user.id):
                    errors.append("❌ This BVN is already registered by another farmer.")
                if not is_unique(service, "farmer_verifications", "nin", nin.strip(), user.id):
                    errors.append("❌ This NIN is already registered by another farmer.")
            
            if errors:
                for err in errors:
                    st.error(f"❌ {err}")
            else:
                with st.spinner("Uploading documents..."):
                    try:
                        nin_fn = f"{user.id}/nin_{uuid.uuid4().hex[:8]}.jpg"
                        id_fn = f"{user.id}/id_{uuid.uuid4().hex[:8]}.jpg"
                        sf_fn = f"{user.id}/selfie_{uuid.uuid4().hex[:8]}.jpg"
                        
                        service.storage.from_("message_attachment").upload(nin_fn, nin_slip.getvalue())
                        service.storage.from_("message_attachment").upload(id_fn, id_card.getvalue())
                        service.storage.from_("message_attachment").upload(sf_fn, selfie.getvalue())
                        
                        service.table("farmer_verifications").upsert({
                            "user_id": user.id,
                            "email": user.email,
                            "first_name": first_name.strip(),
                            "middle_name": middle_name.strip() if middle_name else "",
                            "last_name": last_name.strip(),
                            "dob": dob.isoformat(),
                            "phone": phone.strip(),
                            "home_address": home_address.strip(),
                            "city": city.strip(),
                            "state": state,
                            "lga": lga.strip(),
                            "farm_location": farm_location.strip(),
                            "farm_size": farm_size,
                            "crops": crops_grown,
                            "association": association.strip() if association else "",
                            "bvn": bvn.strip(),
                            "nin": nin.strip(),
                            "id_type": id_type,
                            "id_number": id_number.strip(),
                            "nin_slip_url": nin_fn,
                            "id_url": id_fn,
                            "selfie_url": sf_fn,
                            "status": "pending",
                            "payment_status": "paid"
                        }).execute()
                        
                        st.success("✅ Verification submitted! An admin will review within 24 hours.")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Upload failed: {e}")

st.markdown("---")
cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
