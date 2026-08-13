
import streamlit as st
from supabase import create_client, Client

def get_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["service_key"]
    return create_client(url, key)

def deduct_scans(user_id, amount, feature_name):
    """Deduct a specific number of scans and show remaining."""
    supabase = get_supabase()
    
    # Ensure user_scans row exists
    try:
        supabase.table("user_scans").insert(
            {"user_id": user_id, "scans_remaining": 30, "plan": "free"}
        ).execute()
    except:
        pass
    
    # Fetch current scans
    res = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
    current = res.data[0]["scans_remaining"] if res.data else 0
    
    if current < amount:
        st.error(f"⚠️ Not enough scans! You need {amount} scans but only have {current} left.")
        st.info("💳 Go to Buy Scans to purchase more.")
        return False, current
    
    # Deduct
    new_total = current - amount
    supabase.table("user_scans").update({"scans_remaining": new_total}).eq("user_id", user_id).execute()
    
    st.success(f"📉 {amount} scans deducted for {feature_name}. Remaining: {new_total}")
    return True, new_total
