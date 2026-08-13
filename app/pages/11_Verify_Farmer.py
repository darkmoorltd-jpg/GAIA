import streamlit as st
from supabase import create_client, Client
import uuid
import requests as req

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

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

st.set_page_config(page_title="GAIA – Farmer Verification", page_icon="🛡️", layout="wide")

# Check if returning from Paystack
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

# Styling
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa, #e8f5e9); }
    .title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #2e7d32; }
    .subtitle { text-align: center; color: #555; margin-bottom: 2rem; }
    .verified-badge { background: linear-gradient(135deg, #2e7d32, #4caf50); color: #fff; padding: 10px 25px; border-radius: 30px; font-weight: 700; font-size: 1.2rem; }
    .pending-badge { background: linear-gradient(135deg, #f57f17, #ffb300); color: #fff; padding: 10px 25px; border-radius: 30px; font-weight: 700; font-size: 1.2rem; }
    .rejected-badge { background: linear-gradient(135deg, #c62828, #e53935); color: #fff; padding: 10px 25px; border-radius: 30px; font-weight: 700; font-size: 1.2rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🛡️ Farmer Verification</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Verify your identity to unlock digital wallet and marketplace</div>', unsafe_allow_html=True)

# Show current status
if verification:
    status = verification.get("status", "pending")
    if status == "approved":
        st.markdown(f'<div style="text-align:center;"><span class="verified-badge">✅ Verified Farmer</span></div>', unsafe_allow_html=True)
        st.success(f"**Name:** {verification.get('full_name')}\n\n**Phone:** {verification.get('phone')}\n\n**State:** {verification.get('state')} | **LGA:** {verification.get('lga')}\n\n**Crops:** {safe_crops(verification.get('crops'))}")
        st.info("🎉 You are verified! Your digital wallet is now active. Go to **💰 Digital Wallet** to view your account.")
        
    elif status == "pending":
        st.markdown(f'<div style="text-align:center;"><span class="pending-badge">⏳ Under Review</span></div>', unsafe_allow_html=True)
        st.info(f"**Name:** {verification.get('full_name')}\n\n**Phone:** {verification.get('phone')}\n\n**State:** {verification.get('state')} | **LGA:** {verification.get('lga')}\n\n**Crops:** {safe_crops(verification.get('crops'))}")
        st.info("Your verification is under review. An admin will check within 24 hours.")
        
    elif status == "rejected":
        st.markdown(f'<div style="text-align:center;"><span class="rejected-badge">❌ Rejected</span></div>', unsafe_allow_html=True)
        st.error(f"**Reason:** {verification.get('rejection_reason', 'No reason provided')}")
        if st.button("🔄 Resubmit Verification"):
            service.table("farmer_verifications").delete().eq("user_id", user.id).execute()
            st.rerun()

else:
    # Step 1: Payment
    st.markdown("### Step 1: Pay Verification Fee (N500)")
    ref = f"GAIA_VERIFY_{user.id[:8]}_{uuid.uuid4().hex[:8]}"
    
    # Create pending verification record
    service.table("farmer_verifications").upsert({
        "user_id": user.id,
        "payment_reference": ref,
        "payment_status": "pending",
        "status": "pending"
    }).execute()
    
    # Inline Paystack popup (same pattern as Buy Scans)
    import streamlit.components.v1 as components
    paystack_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://js.paystack.co/v1/inline.js"></script>
        <style>
            body {{ margin:0; padding:0; display:flex; justify-content:center; }}
            .btn {{
                padding: 15px 40px; background: #0d6efd; color: #fff;
                border: none; border-radius: 30px; font-size: 1.2rem;
                cursor: pointer; font-weight: 600;
            }}
            .btn:hover {{ background: #0b5ed7; }}
        </style>
    </head>
    <body>
        <button class="btn" onclick="payWithPaystack()">💳 Pay N500 to Verify</button>
        <script>
            function payWithPaystack() {{
                PaystackPop.setup({{
                    key: 'pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057',
                    email: '{user.email}',
                    phone: '{user_phone}',
                    amount: 50000,
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
    components.html(paystack_html, height=100)
    
    st.caption("After payment, return to this page to upload your documents.")

    # Manual reference verification
    st.markdown("---")
    st.subheader("✅ Already Paid? Verify Your Payment")
    col1, col2 = st.columns([3, 1])
    with col1:
        manual_ref = st.text_input("Enter your Paystack reference", placeholder="e.g., GAIA_VERIFY_abc123", key="verify_ref")
    with col2:
        st.write("")
        if st.button("🔍 Verify Payment", use_container_width=True) and manual_ref:
            with st.spinner("Verifying..."):
                if verify_payment(manual_ref):
                    # Update the verification record
                    service.table("farmer_verifications").update({
                        "payment_status": "paid",
                        "payment_reference": manual_ref,
                        "status": "pending"
                    }).eq("user_id", user.id).execute()
                    st.success("✅ Payment verified! You can now submit your documents.")
                    st.rerun()
                else:
                    st.error("❌ Payment not found. Make sure you completed the payment and the reference is correct.")
    
    st.markdown("---")
    st.markdown("### Step 2: Upload Documents")
    
    with st.form("verify_form"):
        full_name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")
        
        col1, col2 = st.columns(2)
        with col1:
            state = st.selectbox("State", ["Delta","Lagos","Abuja","Kano","Rivers","Ogun","Oyo","Kaduna","Enugu","Edo","Anambra","Imo","Akwa Ibom","Benue","Plateau","Niger","Kwara","Osun","Ondo","Ekiti","Bayelsa","Cross River","Ebonyi","Abia","Adamawa","Bauchi","Borno","Gombe","Jigawa","Katsina","Kebbi","Kogi","Nasarawa","Sokoto","Taraba","Yobe","Zamfara"])
        with col2:
            lga = st.text_input("LGA")
        
        crops = st.multiselect("Crops Grown", ["Maize","Rice","Millet","Beans","Soybean","Cassava","Yam","Tomato","Pepper","Groundnut","Cotton","Sorghum","Vegetables","Fruits"])
        
        col1, col2 = st.columns(2)
        with col1:
            id_img = st.file_uploader("📷 Upload ID Card", type=["jpg","jpeg","png"], help="National ID, Voter's Card, Driver's License, or International Passport")
        with col2:
            selfie_img = st.file_uploader("🤳 Upload Selfie", type=["jpg","jpeg","png"], help="A clear photo of your face")
        
        if st.form_submit_button("📤 Submit Verification"):
            if not full_name or not phone or not state or not lga or not id_img:
                st.error("Please fill all required fields and upload your ID.")
            else:
                with st.spinner("Uploading documents..."):
                    try:
                        id_fn = f"{user.id}/id_{uuid.uuid4().hex[:8]}.jpg"
                        sf_fn = f"{user.id}/selfie_{uuid.uuid4().hex[:8]}.jpg" if selfie_img else None
                        
                        service.storage.from_("message_attachment").upload(id_fn, id_img.getvalue())
                        if sf_fn and selfie_img:
                            service.storage.from_("message_attachment").upload(sf_fn, selfie_img.getvalue())
                        
                        service.table("farmer_verifications").upsert({
                            "user_id": user.id,
                            "full_name": full_name,
                            "phone": phone,
                            "state": state,
                            "lga": lga,
                            "crops": crops,
                            "id_url": id_fn,
                            "selfie_url": sf_fn,
                            "status": "pending",
                            "payment_status": "pending"
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
with cols[5]: st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[?]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")


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