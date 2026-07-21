
import streamlit as st
from supabase import create_client, Client
import requests

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

st.set_page_config(page_title="Processing Payment", page_icon="⏳", layout="centered")

PAYSTACK_PLANS = {
    "10": {"scans": 10},
    "25": {"scans": 25},
    "60": {"scans": 60},
    "250": {"scans": 250},
    "unlimited": {"scans": 9999}
}

def verify_transaction(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        if data["data"]["status"] == "success":
            return data["data"]
    return None

def get_service_client():
    return create_client(SUPABASE_URL, SERVICE_KEY)

query_params = st.query_params
reference = query_params.get("reference", [None])[0]
plan = query_params.get("plan", [None])[0]

if not reference or not plan or plan not in PAYSTACK_PLANS:
    st.error("Invalid payment link.")
    st.stop()

# Verify transaction
txn = verify_transaction(reference)
if not txn:
    st.error("Payment verification failed. Please contact darkmoorltd@gmail.com")
    st.stop()

# Try to get current user
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
user_id = None
try:
    session = supabase.auth.get_session()
    if session and session.user:
        user_id = session.user.id
except:
    pass

if user_id:
    # User IS logged in – credit immediately
    scans_to_add = PAYSTACK_PLANS[plan]["scans"]
    service = get_service_client()
    
    # Get current scans
    current = service.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
    current_scans = current.data[0]["scans_remaining"] if current.data else 0
    new_total = current_scans + scans_to_add
    
    # Update balance
    service.table("user_scans").update({
        "scans_remaining": new_total,
        "plan": plan
    }).eq("user_id", user_id).execute()
    
    # Record in payment history
    service.table("payment_history").insert({
        "user_id": user_id,
        "amount": txn["amount"] / 100,
        "scans_added": scans_to_add,
        "plan": plan,
        "reference": reference
    }).execute()
    
    st.success(f"✅ Payment successful! {scans_to_add} scans added.")
    st.markdown("[Go to Dashboard](https://gaiagpt.streamlit.app)")
else:
    # User NOT logged in – redirect to main app with payment details
    st.warning("You are not logged in. Redirecting to login page…")
    redirect_url = f"https://gaiagpt.streamlit.app/?pending_reference={reference}&pending_plan={plan}"
    st.markdown(f'<meta http-equiv="refresh" content="2; url={redirect_url}">', unsafe_allow_html=True)
    st.info("After logging in, your payment will be processed automatically.")
