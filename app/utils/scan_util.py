
import streamlit as st
from supabase import create_client, Client

def get_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["service_key"]
    return create_client(url, key)

def deduct_scans(user_id, amount, feature_name):
    """Deduct scans and show remaining."""
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
    current = res.data[0]["scans_remaining"] if res.data else 30
    
    if current < amount:
        st.error(f"⚠️ Not enough scans! Need {amount}, have {current}.")
        return False, current
    
    # Deduct
    new_total = current - amount
    supabase.table("user_scans").update({"scans_remaining": new_total}).eq("user_id", user_id).execute()
    
    # Show the deduction message
    st.markdown(f"""
    <div style="background:#fff3e0;border:2px solid #ff9800;border-radius:10px;padding:1rem;margin:0.5rem 0;text-align:center;">
        <strong>📉 Scan Deduction</strong><br>
        {amount} scans used for <strong>{feature_name}</strong><br>
        <strong>Remaining: {new_total} scans</strong>
    </div>
    """, unsafe_allow_html=True)
    
    return True, new_total
