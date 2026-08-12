
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
    """Service role client - bypasses RLS for admin operations."""
    return create_client(SUPABASE_URL, SERVICE_KEY)

@st.cache_resource
def init_anon_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="GAIA – Admin", page_icon="🔐", layout="wide", initial_sidebar_state="expanded")

# ===== LIGHT MODE DEFAULT =====
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa, #e8f5e9); color: #1b5e20; }
    header, footer { visibility: hidden; }
    .admin-title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #2e7d32; }
    .user-card { background: #fff; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .verified { color: #2e7d32; font-weight: 600; }
    .pending { color: #f57f17; font-weight: 600; }
    .rejected { color: #c62828; font-weight: 600; }
    .stButton button { background: #2e7d32 !important; color: #fff !important; border: none !important; border-radius: 8px !important; }
    .stButton button:hover { background: #1b5e20 !important; }
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

if st.session_state.user.email != ADMIN_EMAIL:
    st.error("Access denied. Admin only.")
    st.stop()

st.markdown('<div class="admin-title">🔐 GAIA Admin Dashboard</div>', unsafe_allow_html=True)

supabase = init_service_client()
anon = init_anon_client()

# ===== FETCH USERS DIRECTLY =====
def get_all_users():
    """Get all users using service role."""
    users = []
    profiles = []
    scans = []
    wallets = []
    verifications = []
    policies = []
    
    try:
        # Get all auth users
        resp = supabase.auth.admin.list_users()
        if hasattr(resp, 'users'):
            users = resp.users
        elif isinstance(resp, list):
            users = resp
        st.sidebar.success(f"✅ {len(users)} users found")
    except Exception as e:
        st.sidebar.error(f"Auth error: {str(e)[:100]}")
    
    try:
        p = supabase.table("user_profiles").select("*").execute()
        profiles = p.data if p.data else []
    except Exception as e:
        st.sidebar.warning(f"Profiles: {str(e)[:50]}")
    
    try:
        s = supabase.table("user_scans").select("*").execute()
        scans = s.data if s.data else []
    except:
        pass
    
    try:
        w = supabase.table("farmer_wallets").select("*").execute()
        wallets = w.data if w.data else []
    except:
        pass
    
    try:
        v = supabase.table("farmer_verifications").select("*").execute()
        verifications = v.data if v.data else []
    except:
        pass
    
    try:
        pol = supabase.table("insurance_policies").select("*").execute()
        policies = pol.data if pol.data else []
    except:
        pass
    
    profile_map = {p["user_id"]: p for p in profiles if p.get("user_id")}
    scan_map = {s["user_id"]: s for s in scans if s.get("user_id")}
    wallet_map = {w["user_id"]: w for w in wallets if w.get("user_id")}
    verify_map = {v["user_id"]: v for v in verifications if v.get("user_id")}
    policy_list = [p for p in policies if p.get("user_id")]
    
    user_list = []
    for u in users:
        uid = u.id if hasattr(u, 'id') else u.get('id', '')
        email = u.email if hasattr(u, 'email') else u.get('email', '')
        created = u.created_at if hasattr(u, 'created_at') else u.get('created_at', '')
        
        p = profile_map.get(uid, {})
        s = scan_map.get(uid, {})
        w = wallet_map.get(uid, {})
        v = verify_map.get(uid, {})
        user_policies = [pol for pol in policy_list if pol.get("user_id") == uid]
        
        user_list.append({
            "user_id": uid,
            "email": email or "N/A",
            "created_at": created or "",
            "scans_remaining": s.get("scans_remaining", 0),
            "plan": s.get("plan", "free"),
            "wallet_balance": w.get("balance", 0),
            "verification_status": v.get("status", p.get("verification_status", "pending")),
            **p
        })
    
    return user_list

def add_scans_to_user(user_id, amount):
    try:
        current = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
        cur = current.data[0]["scans_remaining"] if current.data else 0
        supabase.table("user_scans").update({"scans_remaining": cur + amount}).eq("user_id", user_id).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def delete_user_fully(user_id):
    tables = [
        "payment_history", "messages", "farmer_verifications", "user_profiles",
        "user_scans", "marketplace_listings", "marketplace_orders", "insurance_policies",
        "insurance_claims", "field_monitoring", "seller_profiles", "badge_subscriptions",
        "farmer_wallets", "pending_payments", "posts", "friendships", "chat_members",
        "chat_rooms", "user_status", "user_feedback"
    ]
    errors = []
    for table in tables:
        try:
            supabase.table(table).delete().eq("user_id", user_id).execute()
        except:
            pass  # Table might not have user_id column or doesn't exist
    try:
        supabase.auth.admin.delete_user(user_id)
        return True, None
    except Exception as e:
        return False, str(e)

def create_user(email, password, first_name, last_name, phone, state):
    try:
        resp = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        if resp.user:
            uid = resp.user.id
            supabase.table("user_profiles").insert({
                "user_id": uid,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "state": state,
                "verification_status": "pending"
            }).execute()
            supabase.table("user_scans").insert({
                "user_id": uid,
                "scans_remaining": 30,
                "plan": "free"
            }).execute()
            return True, None
        return False, "User creation failed"
    except Exception as e:
        return False, str(e)

def approve_kyc(user_id):
    supabase.table("farmer_verifications").update({"status": "approved"}).eq("user_id", user_id).execute()
    supabase.table("user_profiles").update({"verification_status": "approved", "kyc_level": 2}).eq("user_id", user_id).execute()

def reject_kyc(user_id):
    supabase.table("farmer_verifications").update({"status": "rejected"}).eq("user_id", user_id).execute()
    supabase.table("user_profiles").update({"verification_status": "rejected"}).eq("user_id", user_id).execute()

# ===== TABS =====
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "👤 All Users", "🛡️ KYC Queue", "✏️ Edit User", "➕ Create User"])

users = get_all_users()

# ===== TAB 1: OVERVIEW =====
with tab1:
    total = len(users)
    verified = sum(1 for u in users if u.get("verification_status") == "approved")
    pending = sum(1 for u in users if u.get("verification_status") == "pending")
    rejected = sum(1 for u in users if u.get("verification_status") == "rejected")
    paid = sum(1 for u in users if u.get("plan", "free") != "free")
    total_wallets = sum(float(u.get("wallet_balance", 0)) for u in users)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Users", total)
    col2.metric("Verified", verified)
    col3.metric("Pending KYC", pending)
    col4.metric("Rejected", rejected)
    col5.metric("Paid Plans", paid)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Wallet Balance", f"₦{total_wallets:,.2f}")
    col2.metric("Avg Scans/User", round(sum(u.get('scans_remaining', 0) for u in users) / max(total, 1), 1))
    
    st.markdown("---")
    st.markdown("### User Summary Table")
    
    if users:
        summary = []
        for u in users:
            summary.append({
                "Email": u.get("email", ""),
                "Name": f"{u.get('first_name','')} {u.get('last_name','')}".strip() or "N/A",
                "Phone": u.get("phone", ""),
                "State": u.get("state", ""),
                "KYC": u.get("verification_status", "pending"),
                "Scans": u.get("scans_remaining", 0),
                "Plan": u.get("plan", "free"),
                "Wallet": f"₦{float(u.get('wallet_balance', 0)):,.2f}",
                "Joined": (u.get("created_at") or "")[:10] if u.get("created_at") else "N/A",
            })
        st.dataframe(pd.DataFrame(summary), use_container_width=True)
    else:
        st.info("No users found. Check your service_key in Streamlit secrets.")

# ===== TAB 2: ALL USERS =====
with tab2:
    if not users:
        st.info("No users found.")
    else:
        user_emails = [u.get("email", "") for u in users]
        selected_email = st.selectbox("Select User", user_emails, key="view_user")
        selected = next((u for u in users if u.get("email") == selected_email), None)
        
        if selected:
            st.markdown('<div class="user-card">', unsafe_allow_html=True)
            st.markdown(f"### 👤 {selected.get('first_name','')} {selected.get('last_name','')}")
            st.markdown(f"**Email:** {selected.get('email','')}")
            st.markdown(f"**Joined:** {(selected.get('created_at') or '')[:16] if selected.get('created_at') else 'N/A'}")
            
            st.markdown("---")
            st.markdown("#### 📋 Personal")
            c1, c2, c3 = st.columns(3)
            c1.write(f"Phone: {selected.get('phone','N/A')}")
            c1.write(f"WhatsApp: {selected.get('whatsapp','N/A')}")
            c1.write(f"Gender: {selected.get('gender','N/A')}")
            c2.write(f"BVN: {selected.get('bvn','N/A')}")
            c2.write(f"NIN: {selected.get('nin','N/A')}")
            c2.write(f"ID Type: {selected.get('govt_id_type','N/A')}")
            c3.write(f"State: {selected.get('state','N/A')}")
            c3.write(f"LGA: {selected.get('lga','N/A')}")
            c3.write(f"City: {selected.get('city','N/A')}")
            
            st.markdown("---")
            st.markdown("#### 🌾 Farm")
            c1, c2 = st.columns(2)
            c1.write(f"Farm State: {selected.get('farm_state','N/A')}")
            c1.write(f"Farm Size: {selected.get('farm_size_acres','N/A')} acres")
            c1.write(f"Crops: {selected.get('primary_crops','N/A')}")
            c2.write(f"Experience: {selected.get('years_experience','N/A')} years")
            c2.write(f"Farming Type: {selected.get('farming_type','N/A')}")
            
            st.markdown("---")
            st.markdown("#### 🏦 Banking")
            c1, c2 = st.columns(2)
            c1.write(f"Account: {selected.get('account_name','N/A')} — {selected.get('account_number','N/A')}")
            c2.write(f"Bank: {selected.get('bank_name','N/A')}")
            
            st.markdown("---")
            st.markdown("#### 🚨 Emergency Contact")
            st.write(f"{selected.get('emergency_contact_name','N/A')} — {selected.get('emergency_contact_phone','N/A')} ({selected.get('emergency_relationship','N/A')})")
            
            st.markdown("---")
            st.markdown("#### 💰 Wallet & Plan")
            c1, c2 = st.columns(2)
            c1.metric("Scans", selected.get("scans_remaining", 0))
            c2.metric("Wallet", f"₦{float(selected.get('wallet_balance', 0)):,.2f}")
            st.write(f"Plan: **{selected.get('plan', 'free')}**")
            st.write(f"KYC: **{selected.get('verification_status', 'pending').upper()}**")
            
            st.markdown('</div>', unsafe_allow_html=True)

# ===== TAB 3: KYC QUEUE =====
with tab3:
    st.markdown("### 🛡️ Pending KYC Verifications")
    pending_users = [u for u in users if u.get("verification_status") == "pending"]
    
    if not pending_users:
        st.info("No pending KYC.")
    else:
        for u in pending_users:
            with st.expander(f"⏳ {u.get('first_name','')} {u.get('last_name','')} — {u.get('email','')}"):
                st.write(f"BVN: {u.get('bvn','N/A')}")
                st.write(f"NIN: {u.get('nin','N/A')}")
                st.write(f"ID Type: {u.get('govt_id_type','N/A')}")
                c1, c2 = st.columns(2)
                if c1.button("✅ Approve", key=f"app_{u['user_id']}"):
                    approve_kyc(u["user_id"])
                    st.success("Approved!")
                    st.rerun()
                if c2.button("❌ Reject", key=f"rej_{u['user_id']}"):
                    reject_kyc(u["user_id"])
                    st.error("Rejected.")
                    st.rerun()

# ===== TAB 4: EDIT USER =====
with tab4:
    st.markdown("### ✏️ Edit User")
    if not users:
        st.info("No users.")
    else:
        emails = [u.get("email","") for u in users]
        sel = st.selectbox("Select User to Edit", emails, key="edit_sel")
        u = next((x for x in users if x.get("email") == sel), None)
        if u:
            uid = u["user_id"]
            with st.form("edit_form"):
                c1, c2 = st.columns(2)
                with c1:
                    first = st.text_input("First Name", value=u.get("first_name",""))
                    last = st.text_input("Last Name", value=u.get("last_name",""))
                    phone = st.text_input("Phone", value=u.get("phone",""))
                    bvn = st.text_input("BVN", value=u.get("bvn",""))
                with c2:
                    nin = st.text_input("NIN", value=u.get("nin",""))
                    state = st.text_input("State", value=u.get("state",""))
                    status = st.selectbox("KYC Status", ["pending","approved","rejected"],
                                          index=["pending","approved","rejected"].index(u.get("verification_status","pending")))
                    plan = st.selectbox("Plan", ["free","10","25","60","250","unlimited"])
                
                add_scans = st.number_input("Scans to Add", min_value=0, value=0)
                
                if st.form_submit_button("💾 Save"):
                    updates = {}
                    if first != u.get("first_name",""): updates["first_name"] = first
                    if last != u.get("last_name",""): updates["last_name"] = last
                    if phone != u.get("phone",""): updates["phone"] = phone
                    if bvn != u.get("bvn",""): updates["bvn"] = bvn
                    if nin != u.get("nin",""): updates["nin"] = nin
                    if state != u.get("state",""): updates["state"] = state
                    if status != u.get("verification_status",""): updates["verification_status"] = status
                    if updates:
                        supabase.table("user_profiles").update(updates).eq("user_id", uid).execute()
                    if add_scans > 0:
                        add_scans_to_user(uid, add_scans)
                    supabase.table("user_scans").update({"plan": plan}).eq("user_id", uid).execute()
                    st.success("✅ Updated!")
                    st.rerun()
            
            # Delete
            st.markdown("---")
            st.markdown("### 🗑️ Danger Zone")
            if st.button("🗑️ Delete User Permanently", type="secondary"):
                st.warning("⚠️ This will delete ALL user data permanently.")
                confirm = st.checkbox("I understand. Delete this user.")
                if confirm:
                    ok, err = delete_user_fully(uid)
                    if ok:
                        st.success("User deleted.")
                        st.rerun()
                    else:
                        st.error(f"Failed: {err}")

# ===== TAB 5: CREATE USER =====
with tab5:
    st.markdown("### ➕ Create New User")
    with st.form("create_user"):
        c1, c2 = st.columns(2)
        with c1:
            em = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            fn = st.text_input("First Name")
        with c2:
            ln = st.text_input("Last Name")
            ph = st.text_input("Phone")
            stt = st.text_input("State")
        
        if st.form_submit_button("➕ Create"):
            if not em or not pw:
                st.error("Email and password required.")
            elif len(pw) < 6:
                st.error("Password must be 6+ characters.")
            else:
                ok, err = create_user(em, pw, fn, ln, ph, stt)
                if ok:
                    st.success(f"User {em} created with 30 free scans!")
                    st.rerun()
                else:
                    st.error(err)

# ===== NAVIGATION =====
st.markdown("---")
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
