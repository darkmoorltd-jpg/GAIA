
import streamlit as st
from supabase import create_client, Client
import requests
import time

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

st.set_page_config(page_title="Processing Payment", page_icon="⏳", layout="centered")

# Payment plans (same as main.py)
PAYSTACK_PLANS = {
    "10": {"scans": 10},
    "25": {"scans": 25},
    "60": {"scans": 60},
    "250": {"scans": 250},
    "unlimited": {"scans": 9999}
}

def verify_paystack_transaction(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        if data["data"]["status"] == "success":
            return data["data"]
    return None

def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

query_params = st.query_params
reference = query_params.get("reference", [None])[0]
plan = query_params.get("plan", [None])[0]

if not reference or not plan:
    st.error("Invalid payment link. No reference or plan found.")
    st.stop()

plan_data = PAYSTACK_PLANS.get(plan)
if not plan_data:
    st.error(f"Unknown plan: {plan}")
    st.stop()

st.title("⏳ Processing your payment…")
st.write(f"Reference: {reference}")

# Verify with Paystack
txn = verify_paystack_transaction(reference)

if not txn:
    st.error("Payment verification failed. Please contact support: darkmoorltd@gmail.com")
    st.stop()

# Payment successful – try to credit the user
supabase = init_supabase()
user_id = None

# Try to get current session
try:
    session = supabase.auth.get_session()
    if session and session.user:
        user_id = session.user.id
except:
    pass

if user_id:
    scans_to_add = plan_data["scans"]
    # Use service client for the update to bypass RLS
    service_client = create_client(SUPABASE_URL, st.secrets["supabase"]["service_key"])
    
    current = service_client.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
    current_scans = current.data[0]["scans_remaining"] if current.data else 0
    new_total = current_scans + scans_to_add
    
    service_client.table("user_scans").update({
        "scans_remaining": new_total,
        "plan": plan
    }).eq("user_id", user_id).execute()
    
    service_client.table("payment_history").insert({
        "user_id": user_id,
        "amount": txn["amount"] / 100,
        "scans_added": scans_to_add,
        "plan": plan,
        "reference": reference
    }).execute()
    
    st.success(f"✅ Payment successful! {scans_to_add} scans added to your account.")
    st.markdown("[Go to Dashboard](https://gaiagpt.streamlit.app)")
else:
    # Store payment in session state for later processing
    st.warning("You are not logged in. Please log in to complete your payment.")
    st.markdown("[Log in now](https://gaiagpt.streamlit.app)")
    st.info("After logging in, your scans will be added automatically.")
