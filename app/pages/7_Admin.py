
import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
ADMIN_EMAIL = "darkmoorltd@gmail.com"

def safe_str(val, default="N/A"):
    return str(val) if val is not None else default

def safe_date(val):
    if val is None:
        return "N/A"
    try:
        return str(val)[:10]
    except:
        return "N/A"

def safe_int(val, default=0):
    try:
        return int(val) if val is not None else default
    except:
        return default

def safe_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except:
        return default

@st.cache_resource
def init_service_client():
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA – Admin", page_icon="🔐", layout="wide")

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

def get_all_users():
    users = []
    profiles = []
    scans = []
    wallets = []
    verifications = []

    try:
        resp = supabase.auth.admin.list_users()
        if hasattr(resp, 'users'):
            users = resp.users
        elif isinstance(resp, list):
            users = resp
    except:
        users = []

    try:
        p = supabase.table("user_profiles").select("*").execute()
        profiles = p.data if p.data else []
    except:
        profiles = []

    try:
        s = supabase.table("user_scans").select("*").execute()
        scans = s.data if s.data else []
    except:
        scans = []

    try:
        w = supabase.table("farmer_wallets").select("*").execute()
        wallets = w.data if w.data else []
    except:
        wallets = []

    try:
        v = supabase.table("farmer_verifications").select("*").execute()
        verifications = v.data if v.data else []
    except:
        verifications = []

    profile_map = {}
    for p in profiles:
        uid = p.get("user_id")
        if uid:
            profile_map[uid] = p

    scan_map = {}
    for s in scans:
        uid = s.get("user_id")
        if uid:
            scan_map[uid] = s

    wallet_map = {}
    for w in wallets:
        uid = w.get("user_id")
        if uid:
            wallet_map[uid] = w

    verify_map = {}
    for v in verifications:
        uid = v.get("user_id")
        if uid:
            verify_map[uid] = v

    user_list = []
    for u in users:
        uid = u.id if hasattr(u, 'id') else u.get('id', '')
        if not uid:
            continue
        email = u.email if hasattr(u, 'email') else u.get('email', '')
        created = u.created_at if hasattr(u, 'created_at') else u.get('created_at', '')
        p = profile_map.get(uid, {})
        s = scan_map.get(uid, {})
        w = wallet_map.get(uid, {})
        v = verify_map.get(uid, {})

        user_list.append({
            "user_id": uid,
            "email": email or "N/A",
            "created_at": created or "",
            "scans_remaining": safe_int(s.get("scans_remaining"), 0),
            "plan": safe_str(s.get("plan"), "free"),
            "wallet_balance": safe_float(w.get("balance"), 0),
            "verification_status": safe_str(v.get("status"), safe_str(p.get("verification_status"), "pending")),
            **p
        })

    return user_list

def approve_kyc(user_id):
    try:
        supabase.table("farmer_verifications").update({"status": "approved"}).eq("user_id", user_id).execute()
    except:
        pass
    try:
        supabase.table("user_profiles").update({"verification_status": "approved"}).eq("user_id", user_id).execute()
    except:
        pass

def reject_kyc(user_id):
    try:
        supabase.table("farmer_verifications").update({"status": "rejected"}).eq("user_id", user_id).execute()
    except:
        pass
    try:
        supabase.table("user_profiles").update({"verification_status": "rejected"}).eq("user_id", user_id).execute()
    except:
        pass

def add_scans_to_user(user_id, amount):
    try:
        cur_res = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
        cur = safe_int(cur_res.data[0].get("scans_remaining"), 0) if cur_res.data else 0
        supabase.table("user_scans").update({"scans_remaining": cur + amount}).eq("user_id", user_id).execute()
        return True, None
    except Exception as e:
        return False, str(e)

users = get_all_users()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "👤 All Users", "🛡️ KYC Queue", "✏️ Edit User", "📨 Support Tickets"])

with tab1:
    total = len(users)
    verified = sum(1 for u in users if u.get("verification_status") == "approved")
    pending = sum(1 for u in users if u.get("verification_status") == "pending")
    rejected = sum(1 for u in users if u.get("verification_status") == "rejected")
    paid = sum(1 for u in users if safe_str(u.get("plan"), "free") != "free")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Users", total)
    col2.metric("Verified", verified)
    col3.metric("Pending KYC", pending)
    col4.metric("Rejected", rejected)
    col5.metric("Paid Plans", paid)

    if users:
        summary = []
        for u in users:
            summary.append({
                "Email": safe_str(u.get("email")),
                "Name": f"{safe_str(u.get('first_name',''))} {safe_str(u.get('last_name',''))}".strip(),
                "Phone": safe_str(u.get("phone"), ""),
                "State": safe_str(u.get("state"), ""),
                "KYC": safe_str(u.get("verification_status"), "pending"),
                "Scans": safe_int(u.get("scans_remaining"), 0),
                "Plan": safe_str(u.get("plan"), "free"),
                "Wallet": f"₦{safe_float(u.get('wallet_balance')):,.2f}",
                "Joined": safe_date(u.get("created_at")),
            })
        st.dataframe(pd.DataFrame(summary), use_container_width=True)
    else:
        st.info("No users found.")

with tab2:
    if not users:
        st.info("No users.")
    else:
        emails = [safe_str(u.get("email")) for u in users]
        sel = st.selectbox("Select User to View", emails, key="view_sel")
        u = next((x for x in users if safe_str(x.get("email")) == sel), None)

        if u:
            st.markdown('<div class="user-card">', unsafe_allow_html=True)
            st.markdown(f"### 👤 {safe_str(u.get('first_name'))} {safe_str(u.get('last_name'))}")
            st.markdown(f"**Email:** {safe_str(u.get('email'))}")
            st.markdown(f"**Joined:** {safe_date(u.get('created_at'))}")

            st.markdown("---")
            st.markdown("#### 📋 Personal Information")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"Phone: {safe_str(u.get('phone'))}")
                st.write(f"WhatsApp: {safe_str(u.get('whatsapp'))}")
                st.write(f"Gender: {safe_str(u.get('gender'))}")
            with c2:
                st.write(f"BVN: {safe_str(u.get('bvn'))}")
                st.write(f"NIN: {safe_str(u.get('nin'))}")
                st.write(f"ID Type: {safe_str(u.get('govt_id_type'))}")
            with c3:
                st.write(f"Country: {safe_str(u.get('country'))}")
                st.write(f"State: {safe_str(u.get('state'))}")
                st.write(f"LGA: {safe_str(u.get('lga'))}")

            st.markdown("---")
            st.markdown("#### 🌾 Farm Information")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"Farm State: {safe_str(u.get('farm_state'))}")
                st.write(f"Farm LGA: {safe_str(u.get('farm_lga'))}")
                st.write(f"Farm Size: {safe_str(u.get('farm_size_acres'))} acres")
            with c2:
                st.write(f"Experience: {safe_str(u.get('years_experience'))} years")
                st.write(f"Crops: {safe_str(u.get('primary_crops'))}")
                st.write(f"Type: {safe_str(u.get('farming_type'))}")

            st.markdown("---")
            st.markdown("#### 💰 Wallet & Plan")
            c1, c2 = st.columns(2)
            c1.metric("Scans", safe_int(u.get("scans_remaining")))
            c2.metric("Wallet", f"₦{safe_float(u.get('wallet_balance')):,.2f}")
            st.write(f"Plan: **{safe_str(u.get('plan'), 'free')}**")

            status = safe_str(u.get("verification_status"), "pending")
            if status == "approved":
                st.markdown(f"KYC: **<span class='verified'>APPROVED</span>**", unsafe_allow_html=True)
            elif status == "rejected":
                st.markdown(f"KYC: **<span class='rejected'>REJECTED</span>**", unsafe_allow_html=True)
            else:
                st.markdown(f"KYC: **<span class='pending'>PENDING</span>**", unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown("### 🛡️ Pending KYC")
    pending_users = [u for u in users if u.get("verification_status") == "pending"]
    if not pending_users:
        st.info("No pending KYC.")
    else:
        for u in pending_users:
            with st.expander(f"⏳ {safe_str(u.get('first_name'))} {safe_str(u.get('last_name'))} — {safe_str(u.get('email'))}"):
                st.write(f"BVN: {safe_str(u.get('bvn'))}")
                st.write(f"NIN: {safe_str(u.get('nin'))}")
                st.write(f"ID Type: {safe_str(u.get('govt_id_type'))}")
                c1, c2 = st.columns(2)
                if c1.button("✅ Approve", key=f"app_{u['user_id']}"):
                    approve_kyc(u["user_id"])
                    st.success("Approved!")
                    st.rerun()
                if c2.button("❌ Reject", key=f"rej_{u['user_id']}"):
                    reject_kyc(u["user_id"])
                    st.error("Rejected.")
                    st.rerun()

with tab4:
    st.markdown("### ✏️ Edit User")
    if not users:
        st.info("No users.")
    else:
        emails = [safe_str(u.get("email")) for u in users]
        sel = st.selectbox("Select User", emails, key="edit_sel")
        u = next((x for x in users if safe_str(x.get("email")) == sel), None)
        if u:
            uid = u["user_id"]
            with st.form("edit_form"):
                c1, c2 = st.columns(2)
                with c1:
                    first = st.text_input("First Name", value=safe_str(u.get("first_name"), ""))
                    last = st.text_input("Last Name", value=safe_str(u.get("last_name"), ""))
                    phone = st.text_input("Phone", value=safe_str(u.get("phone"), ""))
                with c2:
                    state = st.text_input("State", value=safe_str(u.get("state"), ""))
                    status_opts = ["pending", "approved", "rejected"]
                    status = st.selectbox("KYC Status", status_opts,
                                          index=status_opts.index(safe_str(u.get("verification_status"), "pending")) if safe_str(u.get("verification_status"), "pending") in status_opts else 0)
                    plan_opts = ["free", "starter", "pro", "business", "enterprise"]
                    plan = st.selectbox("Plan", plan_opts,
                                        index=plan_opts.index(safe_str(u.get("plan"), "free")) if safe_str(u.get("plan"), "free") in plan_opts else 0)
                add_scans = st.number_input("Scans to Add", min_value=0, value=0)

                if st.form_submit_button("💾 Save Changes"):
                    updates = {}
                    if first != safe_str(u.get("first_name"), ""): updates["first_name"] = first
                    if last != safe_str(u.get("last_name"), ""): updates["last_name"] = last
                    if phone != safe_str(u.get("phone"), ""): updates["phone"] = phone
                    if state != safe_str(u.get("state"), ""): updates["state"] = state
                    try:
                        if updates:
                            supabase.table("user_profiles").update(updates).eq("user_id", uid).execute()
                        if add_scans > 0:
                            add_scans_to_user(uid, add_scans)
                        supabase.table("user_profiles").update({"verification_status": status}).eq("user_id", uid).execute()
                        supabase.table("user_scans").update({"plan": plan}).eq("user_id", uid).execute()
                        st.success("✅ Updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Update failed: {str(e)[:200]}")

with tab5:
    st.markdown("### 📨 User Support Tickets")
    try:
        tickets = supabase.table("support_tickets").select("*").order("created_at", desc=True).execute()
        all_tickets = tickets.data if tickets.data else []
    except:
        all_tickets = []

    if not all_tickets:
        st.info("No support tickets yet.")
    else:
        for ticket in all_tickets:
            status = ticket.get("status", "open")
            status_emoji = {"open": "🟠", "closed": "✅"}.get(status, "⚪")
            user_email = "N/A"
            for u in users:
                if u.get("user_id") == ticket.get("user_id"):
                    user_email = u.get("email", "N/A")
                    break
            with st.expander(f"{status_emoji} {ticket.get('subject','')} — {user_email}"):
                st.write(f"**Subject:** {ticket.get('subject','')}")
                st.write(f"**Message:** {ticket.get('message','')}")
                with st.form(f"admin_reply_{ticket['id']}"):
                    admin_reply = st.text_area("Your Reply", height=80)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("📤 Send Reply"):
                            if admin_reply.strip():
                                supabase.table("support_replies").insert({
                                    "ticket_id": ticket["id"],
                                    "sender_id": st.session_state.user.id,
                                    "is_admin": True,
                                    "message": admin_reply.strip()
                                }).execute()
                                st.success("Reply sent!")
                                st.rerun()
                    with col2:
                        if st.form_submit_button("✅ Close Ticket"):
                            supabase.table("support_tickets").update({"status": "closed"}).eq("id", ticket["id"]).execute()
                            st.success("Ticket closed.")
                            st.rerun()

# Navigation
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
