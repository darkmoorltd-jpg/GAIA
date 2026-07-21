
import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

def bottom_nav():
    st.markdown("---")
    st.markdown("### 🚀 Quick Navigation")
    cols = st.columns(8)
    with cols[0]:
        if st.button("🌿 Crops", key="bn_crops"): st.switch_page("pages/2_Crops.py")
    with cols[1]:
        if st.button("🐛 Pests", key="bn_pests"): st.switch_page("pages/3_Pests.py")
    with cols[2]:
        if st.button("🏞️ Soil", key="bn_soil"): st.switch_page("pages/4_Soil.py")
    with cols[3]:
        if st.button("🐄 Livestock", key="bn_livestock"): st.switch_page("pages/5_Livestock.py")
    with cols[4]:
        if st.button("💳 Buy Scans", key="bn_buy"): st.switch_page("pages/9_Buy_Scans.py")
    with cols[5]:
        if st.button("📋 Payments", key="bn_payments"): st.switch_page("pages/6_Payment_History.py")
    with cols[6]:
        if st.button("🔐 Admin", key="bn_admin"): st.switch_page("pages/7_Admin.py")
    with cols[7]:
        if st.button("🚪 Logout", key="bn_logout"):
            from supabase import create_client
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
            supabase = create_client(url, key)
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()


SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
SUPABASE_KEY = st.secrets["supabase"]["key"]  # anon key for storage uploads

@st.cache_resource
def init_service_client():
    return create_client(SUPABASE_URL, SERVICE_KEY)

@st.cache_resource
def init_anon_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="GAIA – Admin", page_icon="🔐", layout="wide", initial_sidebar_state="expanded")

# Force sidebar visible on all pages
st.markdown("""

""", unsafe_allow_html=True)


ADMIN_EMAIL = "darkmoorltd@gmail.com"
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()
if st.session_state.user.email != ADMIN_EMAIL:
    st.error("Access denied.")
    st.stop()

st.title("🔐 GAIA Admin Dashboard")
supabase = init_service_client()
anon_client = init_anon_client()

# ---------- Helper functions ----------
@st.cache_data(ttl=30)
def get_all_users():
    try:
        resp = supabase.auth.admin.list_users()
        if hasattr(resp, 'users'):
            users = resp.users
        else:
            users = resp if isinstance(resp, list) else []
    except:
        return []
    
    profiles = supabase.table("user_profiles").select("*").execute()
    profile_map = {p["user_id"]: p for p in profiles.data} if profiles.data else {}
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
    current = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
    current_scans = current.data[0]["scans_remaining"] if current.data else 0
    supabase.table("user_scans").update({
        "scans_remaining": current_scans + amount
    }).eq("user_id", user_id).execute()
    return True

def change_user_password(user_id, new_password):
    try:
        supabase.auth.admin.update_user(user_id, {"password": new_password})
        return True, None
    except Exception as e:
        return False, str(e)

def create_new_user(email, password, first_name="", last_name=""):
    try:
        resp = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        if resp.user:
            supabase.table("user_profiles").insert({
                "user_id": resp.user.id,
                "first_name": first_name,
                "last_name": last_name
            }).execute()
            supabase.table("user_scans").insert({
                "user_id": resp.user.id,
                "scans_remaining": 30,
                "plan": "free"
            }).execute()
            return True, None
        return False, "User creation failed"
    except Exception as e:
        return False, str(e)

def get_messages():
    """Get all messages ordered by most recent."""
    resp = supabase.table("messages").select("*").order("created_at", desc=True).limit(100).execute()
    return resp.data if resp.data else []

def send_admin_reply(user_id, message_text):
    supabase.table("messages").insert({
        "user_id": user_id,
        "admin_id": ADMIN_EMAIL,
        "message": message_text,
        "is_from_admin": True,
        "read": True
    }).execute()

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "👤 Manage Users", "➕ Create User", "📨 Messages"])

with tab1:
    users = get_all_users()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Users", len(users))
    col2.metric("Total Scans Used", sum(30 - u["scans_remaining"] for u in users))
    col3.metric("Free Users", sum(1 for u in users if u["plan"] == "free"))
    col4.metric("Paid Users", sum(1 for u in users if u["plan"] != "free"))
    st.dataframe(pd.DataFrame(users), use_container_width=True)

with tab2:
    users = get_all_users()
    user_emails = [u["email"] for u in users]
    selected_email = st.selectbox("Select User", user_emails)
    selected_user = next((u for u in users if u["email"] == selected_email), None)
    
    if selected_user:
        uid = selected_user["user_id"]
        st.write(f"**{selected_user['email']}** – {selected_user.get('first_name','')} {selected_user.get('last_name','')}")
        st.write(f"Country: {selected_user.get('country','')} | Phone: {selected_user.get('phone','')}")
        st.metric("Scans Remaining", selected_user["scans_remaining"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            scans_to_add = st.number_input("Scans to add", min_value=1, max_value=9999, value=10)
            if st.button("➕ Add Scans"):
                add_scans_to_user(uid, scans_to_add)
                st.success(f"Added {scans_to_add} scans")
                st.cache_data.clear()
                st.rerun()
        with col2:
            new_password = st.text_input("New password", type="password")
            if st.button("🔑 Update Password"):
                if len(new_password) < 6:
                    st.error("Min 6 characters")
                else:
                    success, err = change_user_password(uid, new_password)
                    if success:
                        st.success("Password updated")
                    else:
                        st.error(f"Failed: {err}")
        with col3:
            if st.button("📧 Send Reset Link"):
                try:
                    supabase.auth.admin.generate_link(uid, type="recovery")
                    st.success("Reset link sent")
                except Exception as e:
                    st.error(f"Failed: {e}")

with tab3:
    st.subheader("➕ Create New User")
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_email = st.text_input("Email")
            new_first = st.text_input("First Name")
        with col2:
            new_pass = st.text_input("Password", type="password")
            new_last = st.text_input("Last Name")
        if st.form_submit_button("Create User"):
            if not new_email or not new_pass:
                st.error("Email and password required")
            elif len(new_pass) < 6:
                st.error("Password must be at least 6 characters")
            else:
                success, msg = create_new_user(new_email, new_pass, new_first, new_last)
                if success:
                    st.success(f"User {new_email} created with 30 free scans!")
                    st.cache_data.clear()
                else:
                    st.error(msg)

with tab4:
    st.subheader("📨 User Messages")
    messages = get_messages()
    
    # Group messages by user
    from collections import defaultdict
    threads = defaultdict(list)
    for msg in messages:
        threads[msg["user_id"]].append(msg)
    
    if not threads:
        st.info("No messages yet.")
    else:
        for user_id, msgs in threads.items():
            # Get user email
            user_email = "Unknown"
            for m in msgs:
                if m.get("user_email"):
                    user_email = m["user_email"]
                    break
            if user_email == "Unknown":
                # Try to get from profiles
                profile = supabase.table("user_profiles").select("first_name,last_name").eq("user_id", user_id).execute()
                if profile.data:
                    p = profile.data[0]
                    user_email = f"{p.get('first_name','')} {p.get('last_name','')}".strip() or "User"
            
            latest = msgs[0]  # most recent
            unread = sum(1 for m in msgs if not m["read"] and not m["is_from_admin"])
            
            with st.expander(f"{'🔴 ' if unread else ''}{user_email} – {len(msgs)} messages (last: {latest['created_at'][:16]})"):
                for msg in reversed(msgs):  # show oldest first
                    sender = "👤 User" if not msg["is_from_admin"] else "🔐 You"
                    timestamp = msg["created_at"][:16] if msg.get("created_at") else ""
                    st.markdown(f"**{sender}** – {timestamp}")
                    if msg.get("message"):
                        st.write(msg["message"])
                    if msg.get("attachment_url"):
                        if msg.get("attachment_type") in ["image"]:
                            st.image(msg["attachment_url"], width=200)
                        else:
                            st.markdown(f"[📎 Download attachment]({msg['attachment_url']})")
                    st.markdown("---")
                
                # Reply box
                reply = st.text_input(f"Reply to {user_email}", key=f"reply_{user_id}")
                if st.button(f"Send reply", key=f"send_{user_id}"):
                    if reply.strip():
                        send_admin_reply(user_id, reply.strip())
                        st.success("Reply sent!")
                        st.cache_data.clear()
                        st.rerun()


# ---------- Universal Bottom Navigation (safe) ----------
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(6)
with cols[0]:
    st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]:
    st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]:
    st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]:
    st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]:
    st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]:
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
