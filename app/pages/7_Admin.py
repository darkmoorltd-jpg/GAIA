import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

@st.cache_resource
def init_service_client():
    return create_client(SUPABASE_URL, SERVICE_KEY)

@st.cache_resource
def init_anon_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def safe_crops(val):
    if not val: return 'None'
    if isinstance(val, list): return ', '.join(val)
    return str(val).strip('{}').replace('"', '')

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
            "middle_name": profile.get("middle_name", ""),
            "last_name": profile.get("last_name", ""),
            "phone": profile.get("phone", ""),
            "country": profile.get("country", ""),
            "state": profile.get("state", ""),
            "city": profile.get("city", ""),
            "lga": profile.get("lga", ""),
            "bvn": profile.get("bvn", ""),
            "nin": profile.get("nin", ""),
            "crops_grown": profile.get("crops_grown", []),
            "association": profile.get("association", ""),
            "farm_location": profile.get("farm_location", ""),
            "farm_size": profile.get("farm_size", ""),
            "house_address": profile.get("house_address", ""),
            "date_of_birth": profile.get("date_of_birth", ""),
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

def delete_user(user_id):
    """Comprehensive user deletion — removes ALL related records then the auth user."""
    errors = []
    
    # Tables with 'user_id' column
    tables_with_user_id = [
        "payment_history",
        "pending_payments", 
        "messages",
        "farmer_verifications",
        "badge_subscriptions",
        "chat_members",
        "user_status",
        "user_profiles",
        "user_scans",
    ]
    
    for table in tables_with_user_id:
        try:
            supabase.table(table).delete().eq("user_id", user_id).execute()
        except Exception as e:
            if "does not exist" not in str(e).lower():
                errors.append(f"{table}: {str(e)[:80]}")
    
    # Friendships uses sender_id and receiver_id (not user_id)
    try:
        supabase.table("friendships").delete().eq("sender_id", user_id).execute()
    except:
        pass
    try:
        supabase.table("friendships").delete().eq("receiver_id", user_id).execute()
    except:
        pass
    
    # Posts may have user_id
    try:
        supabase.table("posts").delete().eq("user_id", user_id).execute()
    except:
        pass
    
    # Delete the auth user
    try:
        supabase.auth.admin.delete_user(user_id)
        return True, None
    except Exception as e:
        all_errors = errors + [f"auth.user: {str(e)[:100]}"]
        return False, " | ".join(all_errors) if all_errors else str(e)[:100]

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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "👤 Users", "➕ Create User", "🛡️ Verifications", "📨 Messages"])

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
        st.write(f"**{selected_user['email']}** — {selected_user.get('first_name','')} {selected_user.get('middle_name','')} {selected_user.get('last_name','')}")
        st.write(f"📞 {selected_user.get('phone','')} | 🎂 {selected_user.get('date_of_birth','N/A')}")
        st.write(f"🏠 {selected_user.get('house_address','')}, {selected_user.get('city','')}, {selected_user.get('state','')} {selected_user.get('country','')}")
        st.write(f"🏷️ BVN: {selected_user.get('bvn','N/A')} | NIN: {selected_user.get('nin','N/A')}")
        st.write(f"🌾 Farm: {selected_user.get('farm_location','N/A')} | Size: {selected_user.get('farm_size','N/A')}")
        st.write(f"🌱 Crops: {selected_user.get('crops_grown','N/A')}")
        st.write(f"🤝 Association: {selected_user.get('association','N/A')}")
        st.metric("Scans Remaining", selected_user["scans_remaining"])
        
        col1, col2, col3, col4 = st.columns(4)
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
        with col4:
            if "confirm_delete" not in st.session_state:
                st.session_state.confirm_delete = None
            
            if st.button("🗑️ Delete User", type="secondary"):
                st.session_state.confirm_delete = uid
            
            if st.session_state.confirm_delete == uid:
                st.error(f"⚠️ Are you sure? This will permanently delete {selected_user['email']} and ALL their data.")
                c1, c2 = st.columns(2)
                if c1.button("✅ Yes, Delete", key=f"confirm_del_{uid}"):
                    success, err = delete_user(uid)
                    if success:
                        st.success("User permanently deleted")
                        st.session_state.confirm_delete = None
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Delete failed: {err}")
                if c2.button("❌ Cancel", key=f"cancel_del_{uid}"):
                    st.session_state.confirm_delete = None
                    st.rerun()

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
    st.subheader("🛡️ Farmer Verifications")
    verifications = supabase.table("farmer_verifications").select("*").order("created_at", desc=True).limit(50).execute()
    if verifications.data:
        for idx, v in enumerate(verifications.data):
            status = v.get("status", "pending")
            emoji = "✅" if status == "approved" else ("⏳" if status == "pending" else "❌")
            with st.expander(f"{emoji} {v.get('full_name','N/A')} — {status.upper()}"):
                # User details
                st.markdown("### 📋 User Details")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Name:** {v.get('full_name','N/A')}")
                    st.write(f"**Phone:** {v.get('phone','N/A')}")
                    st.write(f"**Email:** {v.get('email','N/A')}")
                with col2:
                    st.write(f"**State:** {v.get('state','N/A')}")
                    st.write(f"**LGA:** {v.get('lga','N/A')}")
                    st.write(f"**Address:** {v.get('address','N/A')}")
                
                st.write(f"**Crops:** {safe_crops(v.get('crops'))}")
                st.write(f"**Payment Reference:** {v.get('payment_reference','N/A')}")
                st.write(f"**Payment Status:** {v.get('payment_status','N/A')}")
                
                # Show ID and selfie if available
                if v.get('id_url'):
                    st.markdown("**ID Card:**")
                    st.image(v['id_url'], width=300)
                if v.get('selfie_url'):
                    st.markdown("**Selfie:**")
                    st.image(v['selfie_url'], width=200)
                
                # Delete button for any verification
                if st.button("🗑️ Delete Verification", key=f"del_ver_{v['user_id']}_{idx}"):
                    supabase.table("farmer_verifications").delete().eq("user_id", v["user_id"]).execute()
                    st.success("Verification record deleted.")
                    st.rerun()

                if status == "approved":
                    c1, c2 = st.columns(2)
                    if c1.button("🔄 Revoke Approval", key=f"revoke_{v['user_id']}_{idx}"):
                        supabase.table("farmer_verifications").update({"status": "pending"}).eq("user_id", v["user_id"]).execute()
                        st.warning("Approval revoked — status set back to pending.")
                        st.rerun()
                    if c2.button("❌ Reject Farmer", key=f"rej_approved_{v['user_id']}_{idx}"):
                        reason = st.text_input("Rejection reason", key=f"reason_app_{v['user_id']}_{idx}")
                        if st.button("Confirm Reject", key=f"conf_app_{v['user_id']}_{idx}"):
                            supabase.table("farmer_verifications").update({"status": "rejected", "rejection_reason": reason}).eq("user_id", v["user_id"]).execute()
                            st.error("Farmer rejected")
                            st.rerun()

                if status == "pending":
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Approve", key=f"app_{v['user_id']}_{idx}"):
                        supabase.table("farmer_verifications").update({"status": "approved"}).eq("user_id", v["user_id"]).execute()
                        st.success("Approved!")
                        st.rerun()
                    if c2.button("❌ Reject", key=f"rej_{v['user_id']}_{idx}"):
                        reason = st.text_input("Rejection reason", key=f"reason_{v['user_id']}_{idx}")
                        if st.button("Confirm Reject", key=f"conf_{v['user_id']}_{idx}"):
                            supabase.table("farmer_verifications").update({"status": "rejected", "rejection_reason": reason}).eq("user_id", v["user_id"]).execute()
                            st.error("Rejected")
                            st.rerun()
    else:
        st.info("No verification requests yet.")

with tab5:
    st.subheader("📨 User Messages")
    messages = get_messages()
    from collections import defaultdict
    threads = defaultdict(list)
    for msg in messages:
        threads[msg["user_id"]].append(msg)
    
    if not threads:
        st.info("No messages yet.")
    else:
        for user_id, msgs in threads.items():
            unread = sum(1 for m in msgs if not m.get("read") and not m.get("is_from_admin"))
            latest = msgs[0]
            with st.expander(f"{'🔴 ' if unread else ''}User: {user_id[:12]}... — {len(msgs)} messages"):
                for msg in reversed(msgs):
                    sender = "🔐 Admin" if msg.get("is_from_admin") else "👤 User"
                    st.markdown(f"**{sender}** — {msg.get('created_at','')[:16]}")
                    if msg.get("message"):
                        st.write(msg["message"])
                    if msg.get("attachment_url"):
                        st.markdown(f"[📎 Attachment]({msg['attachment_url']})")
                    st.markdown("---")
                
                reply = st.text_input(f"Reply", key=f"reply_{user_id}")
                if st.button(f"Send reply", key=f"send_{user_id}"):
                    if reply.strip():
                        send_admin_reply(user_id, reply.strip())
                        st.success("Reply sent!")
                        st.rerun()

# Quick Navigation
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
