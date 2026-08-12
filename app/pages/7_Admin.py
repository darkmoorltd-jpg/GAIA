
import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
ADMIN_EMAIL = "darkmoorltd@gmail.com"

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

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()
if st.session_state.user.email != ADMIN_EMAIL:
    st.error("Access denied.")
    st.stop()

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa, #e8f5e9); }
    header, footer { visibility: hidden; }
    .admin-title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #2e7d32; }
    .user-card { background: #fff; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .verified { color: #2e7d32; font-weight: 600; }
    .pending { color: #f57f17; font-weight: 600; }
    .rejected { color: #c62828; font-weight: 600; }
    .section { background: #f9f9f9; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="admin-title">🔐 GAIA Admin Dashboard</div>', unsafe_allow_html=True)

supabase = init_service_client()
anon_client = init_anon_client()

# ===== Helper Functions =====
@st.cache_data(ttl=15)
def get_all_users_with_profiles():
    """Fetch all auth users and their complete profiles."""
    try:
        resp = supabase.auth.admin.list_users()
        users = resp.users if hasattr(resp, 'users') else []
    except:
        users = []
    
    profiles = supabase.table("user_profiles").select("*").execute()
    profile_map = {p["user_id"]: p for p in profiles.data} if profiles.data else {}
    
    scans = supabase.table("user_scans").select("*").execute()
    scan_map = {s["user_id"]: s for s in scans.data} if scans.data else {}
    
    user_list = []
    for u in users:
        uid = u.id
        p = profile_map.get(uid, {})
        s = scan_map.get(uid, {})
        user_list.append({
            "user_id": uid,
            "email": u.email,
            "created_at": u.created_at,
            "scans_remaining": s.get("scans_remaining", 0),
            "plan": s.get("plan", "free"),
            **p
        })
    return user_list

def update_profile_field(user_id, field, value):
    """Update a single field in user profile."""
    try:
        supabase.table("user_profiles").update({field: value}).eq("user_id", user_id).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def add_scans(user_id, amount):
    current = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
    cur = current.data[0]["scans_remaining"] if current.data else 0
    supabase.table("user_scans").update({"scans_remaining": cur + amount}).eq("user_id", user_id).execute()
    return True

def change_password(user_id, new_password):
    try:
        supabase.auth.admin.update_user(user_id, {"password": new_password})
        return True, None
    except Exception as e:
        return False, str(e)

def delete_user(user_id):
    try:
        for table in ["payment_history", "messages", "farmer_verifications", "user_profiles", "user_scans", "marketplace_listings", "insurance_policies", "insurance_claims", "field_monitoring", "seller_profiles", "badge_subscriptions", "farmer_wallets"]:
            try:
                supabase.table(table).delete().eq("user_id", user_id).execute()
            except:
                pass
        supabase.auth.admin.delete_user(user_id)
        return True, None
    except Exception as e:
        return False, str(e)

# ===== TABS =====
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "👤 User Profiles", "🛡️ KYC Verification", "✏️ Edit User", "➕ Create User"])

# ===== TAB 1: OVERVIEW =====
with tab1:
    users = get_all_users_with_profiles()
    total = len(users)
    verified = sum(1 for u in users if u.get("verification_status") == "approved")
    pending = sum(1 for u in users if u.get("verification_status") == "pending")
    paid_plans = sum(1 for u in users if u.get("plan", "free") != "free")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Users", total)
    col2.metric("Verified", verified)
    col3.metric("Pending KYC", pending)
    col4.metric("Paid Plans", paid_plans)
    
    st.markdown("---")
    st.markdown("### All Users Summary")
    
    if users:
        summary_data = []
        for u in users:
            summary_data.append({
                "Email": u.get("email", ""),
                "Name": f"{u.get('first_name','')} {u.get('last_name','')}".strip(),
                "Phone": u.get("phone", ""),
                "State": u.get("state", ""),
                "KYC": u.get("verification_status", "pending"),
                "Scans": u.get("scans_remaining", 0),
                "Plan": u.get("plan", "free"),
            })
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

# ===== TAB 2: USER PROFILES =====
with tab2:
    users = get_all_users_with_profiles()
    
    if not users:
        st.info("No users yet.")
    else:
        user_emails = [u.get("email", "") for u in users]
        selected_email = st.selectbox("Select User to View Full Profile", user_emails, key="profile_select")
        selected = next((u for u in users if u.get("email") == selected_email), None)
        
        if selected:
            st.markdown(f'<div class="user-card">', unsafe_allow_html=True)
            
            # Personal Info
            st.markdown("### 📋 Personal Information")
            col1, col2, col3 = st.columns(3)
            col1.write(f"**First Name:** {selected.get('first_name','N/A')}")
            col1.write(f"**Middle Name:** {selected.get('middle_name','N/A')}")
            col1.write(f"**Gender:** {selected.get('gender','N/A')}")
            col2.write(f"**Last Name:** {selected.get('last_name','N/A')}")
            col2.write(f"**Date of Birth:** {selected.get('date_of_birth','N/A')}")
            col2.write(f"**Marital Status:** {selected.get('marital_status','N/A')}")
            col3.write(f"**Email:** {selected.get('email','N/A')}")
            col3.write(f"**Phone:** {selected.get('phone','N/A')}")
            col3.write(f"**WhatsApp:** {selected.get('whatsapp','N/A')}")
            
            st.markdown("---")
            
            # Address
            st.markdown("### 🏠 Address")
            col1, col2 = st.columns(2)
            col1.write(f"**Country:** {selected.get('country','N/A')}")
            col1.write(f"**State:** {selected.get('state','N/A')}")
            col1.write(f"**LGA:** {selected.get('lga','N/A')}")
            col1.write(f"**City:** {selected.get('city','N/A')}")
            col2.write(f"**Street:** {selected.get('street_address','N/A')}")
            col2.write(f"**Landmark:** {selected.get('landmark','N/A')}")
            col2.write(f"**Postal Code:** {selected.get('postal_code','N/A')}")
            
            st.markdown("---")
            
            # KYC
            st.markdown("### 🛡️ KYC Information")
            status = selected.get("verification_status", "pending")
            status_class = {"approved": "verified", "pending": "pending", "rejected": "rejected"}.get(status, "pending")
            st.markdown(f"**Verification Status:** <span class='{status_class}'>{status.upper()}</span>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            col1.write(f"**BVN:** {selected.get('bvn','N/A')}")
            col1.write(f"**NIN:** {selected.get('nin','N/A')}")
            col1.write(f"**ID Type:** {selected.get('govt_id_type','N/A')}")
            col1.write(f"**ID Number:** {selected.get('govt_id_number','N/A')}")
            col2.write(f"**NIN Slip:** {'✅ Uploaded' if selected.get('nin_slip_url') else '❌ Not uploaded'}")
            col2.write(f"**Govt ID:** {'✅ Uploaded' if selected.get('govt_id_url') else '❌ Not uploaded'}")
            col2.write(f"**Selfie:** {'✅ Uploaded' if selected.get('selfie_with_id_url') else '❌ Not uploaded'}")
            
            st.markdown("---")
            
            # Farm Info
            st.markdown("### 🌾 Farm Information")
            col1, col2 = st.columns(2)
            col1.write(f"**Farm State:** {selected.get('farm_state','N/A')}")
            col1.write(f"**Farm LGA:** {selected.get('farm_lga','N/A')}")
            col1.write(f"**Farm Address:** {selected.get('farm_address','N/A')}")
            col1.write(f"**Farm Size:** {selected.get('farm_size_acres','N/A')} acres")
            col2.write(f"**Years Experience:** {selected.get('years_experience','N/A')}")
            col2.write(f"**Primary Crops:** {selected.get('primary_crops','N/A')}")
            col2.write(f"**Farming Type:** {selected.get('farming_type','N/A')}")
            
            st.markdown("---")
            
            # Banking
            st.markdown("### 🏦 Bank Information")
            col1, col2 = st.columns(2)
            col1.write(f"**Account Name:** {selected.get('account_name','N/A')}")
            col1.write(f"**Account Number:** {selected.get('account_number','N/A')}")
            col2.write(f"**Bank:** {selected.get('bank_name','N/A')}")
            
            st.markdown("---")
            
            # Emergency Contact
            st.markdown("### 🚨 Emergency Contact")
            col1, col2 = st.columns(2)
            col1.write(f"**Name:** {selected.get('emergency_contact_name','N/A')}")
            col1.write(f"**Relationship:** {selected.get('emergency_relationship','N/A')}")
            col2.write(f"**Phone:** {selected.get('emergency_contact_phone','N/A')}")
            
            st.markdown("---")
            
            # Notifications
            st.markdown("### 🔔 Notification Preferences")
            col1, col2, col3 = st.columns(3)
            col1.write(f"SMS: {'✅' if selected.get('notify_sms') else '❌'}")
            col1.write(f"WhatsApp: {'✅' if selected.get('notify_whatsapp') else '❌'}")
            col1.write(f"Email: {'✅' if selected.get('notify_email') else '❌'}")
            col2.write(f"Weather: {'✅' if selected.get('notify_weather') else '❌'}")
            col2.write(f"Disease: {'✅' if selected.get('notify_disease') else '❌'}")
            col2.write(f"Payment: {'✅' if selected.get('notify_payment') else '❌'}")
            col3.write(f"**Language:** {selected.get('preferred_language','English')}")
            col3.write(f"**Wallet PIN Set:** {'✅' if selected.get('wallet_pin') else '❌'}")
            
            st.markdown("---")
            
            # Activity
            st.markdown("### 📊 Activity Statistics")
            col1, col2, col3 = st.columns(3)
            col1.write(f"**Scans Remaining:** {selected.get('scans_remaining', 0)}")
            col1.write(f"**Plan:** {selected.get('plan', 'free')}")
            col1.write(f"**Account Created:** {selected.get('created_at','N/A')[:16]}")
            col2.write(f"**Crops Diagnosed:** {selected.get('crops_diagnosed', 0)}")
            col2.write(f"**Pests Identified:** {selected.get('pests_identified', 0)}")
            col2.write(f"**Soil Tests:** {selected.get('soil_tests', 0)}")
            col3.write(f"**Claims Filed:** {selected.get('claims_filed', 0)}")
            col3.write(f"**Listings Created:** {selected.get('listings_created', 0)}")
            col3.write(f"**Purchases Made:** {selected.get('purchases_made', 0)}")
            
            st.markdown('</div>', unsafe_allow_html=True)

# ===== TAB 3: KYC VERIFICATION =====
with tab3:
    st.markdown("### 🛡️ KYC Verification Queue")
    
    users = get_all_users_with_profiles()
    pending_users = [u for u in users if u.get("verification_status") == "pending" and u.get("bvn")]
    
    if not pending_users:
        st.info("No pending KYC verifications.")
    else:
        for u in pending_users:
            with st.expander(f"⏳ {u.get('first_name','')} {u.get('last_name','')} — {u.get('email','')}"):
                st.write(f"**BVN:** {u.get('bvn','N/A')}")
                st.write(f"**NIN:** {u.get('nin','N/A')}")
                st.write(f"**ID Type:** {u.get('govt_id_type','N/A')}")
                st.write(f"**ID Number:** {u.get('govt_id_number','N/A')}")
                st.write(f"**State:** {u.get('state','N/A')}")
                
                col1, col2 = st.columns(2)
                if col1.button("✅ Approve", key=f"approve_{u['user_id']}"):
                    supabase.table("user_profiles").update({"verification_status": "approved", "kyc_level": 2}).eq("user_id", u["user_id"]).execute()
                    st.success("Approved!")
                    st.rerun()
                if col2.button("❌ Reject", key=f"reject_{u['user_id']}"):
                    supabase.table("user_profiles").update({"verification_status": "rejected"}).eq("user_id", u["user_id"]).execute()
                    st.error("Rejected.")
                    st.rerun()

# ===== TAB 4: EDIT USER =====
with tab4:
    st.markdown("### ✏️ Edit User Profile")
    
    users = get_all_users_with_profiles()
    user_emails = [u.get("email", "") for u in users]
    selected_email = st.selectbox("Select User to Edit", user_emails, key="edit_select")
    selected = next((u for u in users if u.get("email") == selected_email), None)
    
    if selected:
        uid = selected["user_id"]
        
        with st.form("edit_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_first = st.text_input("First Name", value=selected.get("first_name", ""))
                new_last = st.text_input("Last Name", value=selected.get("last_name", ""))
                new_phone = st.text_input("Phone", value=selected.get("phone", ""))
                new_state = st.text_input("State", value=selected.get("state", ""))
            with col2:
                new_bvn = st.text_input("BVN", value=selected.get("bvn", ""))
                new_nin = st.text_input("NIN", value=selected.get("nin", ""))
                new_status = st.selectbox("Verification Status", 
                                          ["pending", "approved", "rejected"],
                                          index=["pending", "approved", "rejected"].index(selected.get("verification_status", "pending")))
                new_plan = st.selectbox("Plan", ["free", "10", "25", "60", "250", "unlimited"])
            
            scans_add = st.number_input("Scans to Add", min_value=0, value=0)
            
            if st.form_submit_button("💾 Save Changes"):
                updates = {}
                if new_first != selected.get("first_name", ""): updates["first_name"] = new_first
                if new_last != selected.get("last_name", ""): updates["last_name"] = new_last
                if new_phone != selected.get("phone", ""): updates["phone"] = new_phone
                if new_state != selected.get("state", ""): updates["state"] = new_state
                if new_bvn != selected.get("bvn", ""): updates["bvn"] = new_bvn
                if new_nin != selected.get("nin", ""): updates["nin"] = new_nin
                if new_status != selected.get("verification_status", ""): updates["verification_status"] = new_status
                
                if updates:
                    supabase.table("user_profiles").update(updates).eq("user_id", uid).execute()
                
                if scans_add > 0:
                    add_scans(uid, scans_add)
                
                if new_plan != selected.get("plan", "free"):
                    supabase.table("user_scans").update({"plan": new_plan}).eq("user_id", uid).execute()
                
                st.success("✅ User updated!")
                st.rerun()
        
        # Delete user
        if st.button("🗑️ Delete User", type="secondary"):
            confirm = st.checkbox("Are you sure? This cannot be undone.")
            if confirm:
                success, err = delete_user(uid)
                if success:
                    st.success("User deleted.")
                    st.rerun()
                else:
                    st.error(f"Failed: {err}")

# ===== TAB 5: CREATE USER =====
with tab5:
    st.markdown("### ➕ Create New User")
    
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            new_first = st.text_input("First Name")
        with col2:
            new_last = st.text_input("Last Name")
            new_phone = st.text_input("Phone")
            new_state = st.text_input("State")
        
        if st.form_submit_button("➕ Create User"):
            if not new_email or not new_password:
                st.error("Email and password required.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                try:
                    resp = supabase.auth.admin.create_user({
                        "email": new_email,
                        "password": new_password,
                        "email_confirm": True
                    })
                    if resp.user:
                        supabase.table("user_profiles").insert({
                            "user_id": resp.user.id,
                            "first_name": new_first.strip() or None,
                            "last_name": new_last.strip() or None,
                            "phone": new_phone.strip() or None,
                            "state": new_state.strip() or None,
                            "verification_status": "pending"
                        }).execute()
                        supabase.table("user_scans").insert({
                            "user_id": resp.user.id,
                            "scans_remaining": 30,
                            "plan": "free"
                        }).execute()
                        st.success(f"User {new_email} created!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ===== NAVIGATION =====
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(9)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/8_Profile.py", label="👤 Profile")
with cols[6]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[7]: st.page_link("pages/20_Marketplace.py", label="🌍 Market")
with cols[8]: st.page_link("pages/21_Crop_Insurance.py", label="🏦 Insurance")
