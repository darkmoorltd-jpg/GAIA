
import streamlit as st
# Allow demo mode
import requests
from supabase import create_client, Client
from datetime import datetime, timedelta

user = st.session_state.get("user", None)
if user is None:
    st.warning("Please log in first.")
    st.stop()

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

st.set_page_config(
    page_title="Processing Payment",
    page_icon="⏳",
    layout="centered")

# Scan plans (new)
SCAN_PLANS = {
    "starter": 150,
    "pro": 300,
    "business": 1000,
    "enterprise": 5000,
    # For backward compatibility
    "10": 10,
    "25": 25,
    "60": 60,
    "250": 250,
    "unlimited": 9999,
}

# Badge plans
BADGE_PLANS = {
    "badge_bronze": {"name": "Bronze", "duration_days": 30},
    "badge_silver": {"name": "Silver", "duration_days": 30},
    "badge_gold": {"name": "Gold", "duration_days": 30},
    "badge_platinum": {"name": "Platinum", "duration_days": 30},
}


def verify_transaction(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("data", {}).get("status") == "success":
                return data["data"]
    except BaseException:
        pass
    return None


query_params = st.query_params
reference = query_params.get("reference", [None])[0]
plan = query_params.get("plan", [None])[0]

if not reference:
    st.error("No payment reference found.")
    st.stop()

txn = verify_transaction(reference)
if not txn:
    st.error("Payment verification failed. Contact darkmoorltd@gmail.com")
    st.stop()

# Extract customer email
email = ""
try:
    email = txn.get("customer", {}).get("email", "")
except BaseException:
    pass
if not email:
    email = f"unknown_{reference[:10]}@paystack.pay"

amount_paid = txn.get("amount", 0) / 100  # in Naira
service = create_client(SUPABASE_URL, SERVICE_KEY)

# ============================================
# HANDLE BADGE SUBSCRIPTIONS
# ============================================
if plan in BADGE_PLANS:
    badge = BADGE_PLANS[plan]
    expiry = datetime.now() + timedelta(days=badge["duration_days"])
    # Find user by email (since callback may not have session state)
    auth_user = service.auth.admin.get_user_by_email(email)
    if not auth_user:
        st.error("Could not find user account for this payment.")
        st.stop()
    user_id = auth_user.id

    # Upsert badge subscription
    service.table("badge_subscriptions").upsert({
        "user_id": user_id,
        "plan": plan.replace("badge_", ""),  # bronze, silver, gold, platinum
        "start_date": datetime.now().isoformat(),
        "expiry": expiry.isoformat(),
        "status": "active",
    }).execute()

    # Record payment history
    service.table("payment_history").insert({
        "user_id": user_id,
        "amount": amount_paid,
        "scans_added": 0,
        "plan": plan,
        "reference": reference,
    }).execute()

    st.success(
        f"✅ Payment successful! You are now a {
            badge['name']} subscriber until {
            expiry.strftime('%d %b %Y')}.")
    st.markdown("[Go to Dashboard](/~/)")
    st.stop()

# ============================================
# HANDLE FARMER VERIFICATION
# ============================================
if plan == "verification":
    # Find user by email
    auth_user = service.auth.admin.get_user_by_email(email)
    if not auth_user:
        st.error("Could not find user account for this payment.")
        st.stop()
    user_id = auth_user.id

    # Update verification payment status
    service.table("farmer_verifications").update({
        "payment_status": "paid",
        "payment_reference": reference,
    }).eq("user_id", user_id).execute()

    st.success(
        "✅ Verification payment received! Your KYC is now pending admin review.")
    st.markdown("[Go to Dashboard](/~/)")
    st.stop()

# ============================================
# HANDLE SCAN PLANS (Starter, Pro, etc.)
# ============================================
if plan in SCAN_PLANS:
    scans_to_add = SCAN_PLANS[plan]
    # Find user by email
    auth_user = service.auth.admin.get_user_by_email(email)
    if not auth_user:
        st.error("Could not find user account for this payment.")
        st.stop()
    user_id = auth_user.id

    # Fetch current scans
    cur_res = service.table("user_scans").select(
        "scans_remaining").eq("user_id", user_id).execute()
    current_scans = cur_res.data[0]["scans_remaining"] if cur_res.data else 30
    new_total = current_scans + scans_to_add

    # Update scans and plan name
    service.table("user_scans").update({
        "scans_remaining": new_total,
        "plan": plan,
    }).eq("user_id", user_id).execute()

    # Record payment history
    service.table("payment_history").insert({
        "user_id": user_id,
        "amount": amount_paid,
        "scans_added": scans_to_add,
        "plan": plan,
        "reference": reference,
    }).execute()

    st.success(
        f"✅ Payment successful! {scans_to_add} scans added. Balance: {new_total}")
    st.markdown("[Go to Dashboard](/~/)")
    st.stop()

# If plan not recognised
st.warning("Payment processed but plan not recognised. Contact support.")
