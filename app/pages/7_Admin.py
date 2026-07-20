
import streamlit as st
from supabase import create_client, Client
import pandas as pd

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]

@st.cache_resource
def init_service_client():
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA – Admin", page_icon="🔐", layout="wide")

ADMIN_EMAIL = "darkmoorltd@gmail.com"
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()
if st.session_state.user.email != ADMIN_EMAIL:
    st.error("Access denied.")
    st.stop()

st.title("🔐 GAIA Admin Dashboard")
supabase = init_service_client()

# ---------- Helper functions ----------
@st.cache_data(ttl=60)
def get_all_users():
    """Fetch all users from auth.users + their profiles."""
    try:
        # Get auth users via admin API – returns a list of User objects directly
        resp = supabase.auth.admin.list_users()
        # The response can be a list or have a 'users' attribute; handle both
        if hasattr(resp, 'users'):
            users = resp.users
        else:
            users = resp if isinstance(resp, list) else []
    except Exception as e:
        st.error(f"Failed to fetch users: {e}")
        return []
    
    # Get profiles
    profiles = supabase.table("user_profiles").select("*").execute()
    profile_map = {p["user_id"]: p for p in profiles.data} if profiles.data else {}
    # Get scans
    scans = supabase.table("user_scans").select("*").execute()
    scan_map = {s["user_id"]: s for s in scans.data} if scans.data else {}
    
    user_list = []
    for u in users:
        uid = u.id
        profile = profile_map.get(uid, {})
        scan = scan_map.get(uid, {})
        user_list.append({
            "user_id": uid,
            "email": u.email,
            "first_name": profile.get("first_name", ""),
            "last_name": profile.get("last_name", ""),
            "phone": profile.get("phone", ""),
            "country": profile.get("country", ""),
            "scans_remaining": scan.get("scans_remaining", 0),
            "plan": scan.get("plan", "free"),
            "created_at": u.created_at
        })
    return user_list

def add_scans_to_user(user_id, amount):
    """Add scans to a user's balance."""
    current = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
    current_scans = current.data[0]["scans_remaining"] if current.data else 0
    supabase.table("user_scans").update({
        "scans_remaining": current_scans + amount
    }).eq("user_id", user_id).execute()
    return True

def reset_user_password(user_id):
    """Generate a password reset link for the user."""
    resp = supabase.auth.admin.generate_link(user_id, type="recovery")
    return resp

# ---------- Display users ----------
users = get_all_users()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Users", len(users))
col2.metric("Total Scans Used", sum(30 - u["scans_remaining"] for u in users))
col3.metric("Free Users", sum(1 for u in users if u["plan"] == "free"))
col4.metric("Paid Users", sum(1 for u in users if u["plan"] != "free"))

st.markdown("---")
st.subheader("👥 All Users")

df = pd.DataFrame(users)
st.dataframe(df, use_container_width=True)

# ---------- User actions ----------
st.markdown("---")
st.subheader("⚙️ User Actions")
user_emails = [u["email"] for u in users]
selected_email = st.selectbox("Select User", user_emails)
selected_user = next((u for u in users if u["email"] == selected_email), None)

if selected_user:
    uid = selected_user["user_id"]
    st.write(f"**{selected_user['email']}** – {selected_user.get('first_name','')} {selected_user.get('last_name','')}")
    st.write(f"Country: {selected_user.get('country','')} | Phone: {selected_user.get('phone','')}")
    st.metric("Scans Remaining", selected_user["scans_remaining"])
    
    col1, col2 = st.columns(2)
    with col1:
        scans_to_add = st.number_input("Scans to add", min_value=1, max_value=9999, value=10)
        if st.button("➕ Add Scans"):
            if add_scans_to_user(uid, scans_to_add):
                st.success(f"Added {scans_to_add} scans to {selected_email}")
                st.cache_data.clear()
                st.rerun()
    with col2:
        if st.button("🔑 Send Password Reset"):
            try:
                result = reset_user_password(uid)
                st.success(f"Reset link sent to {selected_email}")
            except Exception as e:
                st.error(f"Failed: {e}")
