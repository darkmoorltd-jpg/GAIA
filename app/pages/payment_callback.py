
import streamlit as st
import requests
from supabase import create_client, Client
from datetime import datetime, timedelta

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
plan = query_params.get("plan", [None])[0]

if not reference:
    st.error("No payment reference found.")
    st.markdown("[Go to Dashboard](/~/)")
    st.stop()

service_client = get_service_client()

# Look up pending payment by reference
pending = service_client.table("pending_payments").select("*").eq("reference", reference).execute()
if not pending.data:
    st.error("Payment reference not found in our records.")
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

            # Determine action based on plan
            if plan in ["starter", "pro", "business", "enterprise", "10", "25", "60", "250", "unlimited"]:
                scans_to_add = {
                    "starter": 150, "pro": 300, "business": 1000, "enterprise": 5000,
                    "10": 10, "25": 25, "60": 60, "250": 250, "unlimited": 9999
                }.get(plan, 0)
                cur = service_client.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
                cur_scans = cur.data[0]["scans_remaining"] if cur.data else 0
                new_total = cur_scans + scans_to_add
                service_client.table("user_scans").update({
                    "scans_remaining": new_total,
                    "plan": plan
                }).eq("user_id", user_id).execute()
                service_client.table("payment_history").insert({
                    "user_id": user_id, "amount": amount_paid,
                    "scans_added": scans_to_add, "plan": plan, "reference": reference
                }).execute()
                st.success(f"✅ Payment successful! {scans_to_add} scans added.")
            elif plan.startswith("badge_"):
                badge_plan = plan.replace("badge_", "")
                expiry = datetime.now() + timedelta(days=30)
                service_client.table("badge_subscriptions").upsert({
                    "user_id": user_id, "plan": badge_plan,
                    "start_date": datetime.now().isoformat(),
                    "expiry": expiry.isoformat(),
                    "status": "active"
                }).execute()
                service_client.table("payment_history").insert({
                    "user_id": user_id, "amount": amount_paid,
                    "scans_added": 0, "plan": plan, "reference": reference
                }).execute()
                st.success(f"✅ Badge subscription activated!")
            elif plan == "verification":
                service_client.table("farmer_verifications").update({
                    "payment_status": "paid"
                }).eq("user_id", user_id).execute()
                st.success("✅ Verification payment received!")
            else:
                st.warning("Plan not recognised.")
            # Mark pending payment completed
            service_client.table("pending_payments").update({"status": "completed"}).eq("reference", reference).execute()
            st.markdown("[Go to Dashboard](/~/)")
except Exception as e:
    st.error(f"Payment verification failed: {e}")
