
import streamlit as st
import requests
from supabase import create_client, Client

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

@st.cache_resource
def get_service_client():
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA – Payment Callback", page_icon="💳", layout="centered")

st.title("⏳ Processing your payment...")

query_params = st.query_params
reference = query_params.get("reference", [None])[0]

if not reference:
    st.error("No payment reference found. If you completed a payment, please contact support with your payment reference.")
    st.markdown("[Go to Dashboard](/~/)")
    st.stop()

service_client = get_service_client()

# Look up the pending payment by reference (ours or Paystack's)
pending = service_client.table("pending_payments").select("*").eq("reference", reference).execute()
if not pending.data:
    # Try looking up by Paystack reference (trxref)
    trxref = query_params.get("trxref", [None])[0]
    if trxref:
        pending = service_client.table("pending_payments").select("*").eq("reference", trxref).execute()

if not pending.data:
    st.error("Payment reference not found in our records. Please contact support.")
    st.markdown("[Go to Dashboard](/~/)")
    st.stop()

pending_record = pending.data[0]
user_id = pending_record["user_id"]
plan = pending_record["plan"]

# Verify with Paystack
url = f"https://api.paystack.co/transaction/verify/{reference}"
headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
try:
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 200:
        data = r.json()
        if data["data"]["status"] == "success":
            txn = data["data"]
            amount_paid = txn["amount"] / 100
            scans_to_add = {"10": 10, "25": 25, "60": 60, "250": 250, "unlimited": 9999}.get(plan, 0)
            
            # Update user scans
            current = service_client.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
            current_scans = current.data[0]["scans_remaining"] if current.data else 0
            new_total = current_scans + scans_to_add
            service_client.table("user_scans").update({
                "scans_remaining": new_total,
                "plan": plan
            }).eq("user_id", user_id).execute()
            
            # Save payment history
            service_client.table("payment_history").insert({
                "user_id": user_id,
                "amount": amount_paid,
                "scans_added": scans_to_add,
                "plan": plan,
                "reference": reference
            }).execute()
            
            # Mark pending payment as completed
            service_client.table("pending_payments").update({"status": "completed"}).eq("reference", reference).execute()
            
            st.success(f"✅ Payment successful! {scans_to_add} scans added to your account.")
            st.markdown(f"Amount paid: ${amount_paid:.2f}")
            st.markdown(f"Reference: {reference}")
            st.markdown("[Go to Dashboard](/~/)")
        else:
            st.error(f"Payment not completed. Status: {data['data']['status']}")
    else:
        st.error("Could not verify payment. Please contact support with your reference.")
except Exception as e:
    st.error(f"Payment verification failed: {e}")
