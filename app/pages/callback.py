
import streamlit as st
import requests
from supabase import create_client, Client

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

st.set_page_config(page_title="Processing Payment", page_icon="⏳", layout="centered")

PLANS = {
    "10": 10, "25": 25, "60": 60, "250": 250, "unlimited": 9999
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

query_params = st.query_params
reference = query_params.get("reference", [None])[0]
plan = query_params.get("plan", [None])[0]

if not reference or not plan or plan not in PLANS:
    st.error("Invalid payment link.")
    st.stop()

txn = verify_transaction(reference)
if not txn:
    st.error("Payment verification failed. Contact darkmoorltd@gmail.com")
    st.stop()

# Extract customer email from Paystack
email = txn.get("customer", {}).get("email", "")
scans = PLANS[plan]
amount = txn.get("amount", 0) / 100

if email:
    # Store in pending_payments table using service key
    service = create_client(SUPABASE_URL, SERVICE_KEY)
    try:
        service.table("pending_payments").insert({
            "email": email,
            "reference": reference,
            "plan": plan,
            "scans": scans,
            "amount": amount,
            "claimed": False
        }).execute()
    except Exception as e:
        st.error(f"Failed to save payment: {e}")
        st.stop()

st.success("✅ Payment saved! Log in to GAIA to claim your scans.")
st.markdown("[Go to GAIA](https://gaiagpt.streamlit.app)")
