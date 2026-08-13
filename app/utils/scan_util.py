
import streamlit as st
from supabase import create_client, Client

def get_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["service_key"]
    return create_client(url, key)

def deduct_scans(user_id, amount, feature_name):
    """Deduct scans and show a HUGE visible banner."""
    supabase = get_supabase()
    
    # Ensure row exists
    try:
        supabase.table("user_scans").insert(
            {"user_id": user_id, "scans_remaining": 30, "plan": "free"}
        ).execute()
    except:
        pass
    
    # Fetch current
    res = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
    current = res.data[0]["scans_remaining"] if res.data else 30
    
    if current < amount:
        st.error(f"⚠️ NOT ENOUGH SCANS! You need {amount} scans but only have {current}. Go to Buy Scans.")
        return False, current
    
    new_total = current - amount
    supabase.table("user_scans").update({"scans_remaining": new_total}).eq("user_id", user_id).execute()
    
    # HUGE VISIBLE BANNER
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #ff9800, #f44336);
        color: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        text-align: center;
        box-shadow: 0 8px 30px rgba(255,152,0,0.5);
        font-size: 1.2rem;
        font-weight: bold;
    ">
        📉 SCAN DEDUCTION<br>
        <span style="font-size: 1.5rem;">-{amount} SCANS</span><br>
        Used for: {feature_name}<br>
        <span style="font-size: 1.3rem; color: #fff;">REMAINING: {new_total} SCANS</span>
    </div>
    """, unsafe_allow_html=True)
    
    return True, new_total
