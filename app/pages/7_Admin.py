
from datetime import datetime
import pandas as pd
import streamlit as st
# Allow demo mode
from supabase import create_client

user = st.session_state.get("user", None)
if user is None:
    st.warning("Please log in first.")
    st.stop()
supabase = create_client(
    st.secrets["supabase"]["url"],
    st.secrets["supabase"]["key"])
try:
    session = supabase.auth.get_session()
    user = session.user if session else None
except BaseException:
    from supabase import create_client, Client

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
ADMIN_EMAIL = "darkmoorltd@gmail.com"

# Safe helper functions


def safe_str(val, default="N/A"):
    if val is None:
        return default
    return str(val)


def safe_date(val):
    if val is None:
        return "N/A"
    try:
        return str(val)[:10]
    except BaseException:
        return "N/A"


def safe_int(val, default=0):
    try:
        return int(val) if val is not None else default
    except BaseException:
        return default


def safe_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except BaseException:
        return default


@st.cache_resource
def init_service_client():
    return create_client(SUPABASE_URL, SERVICE_KEY)


st.set_page_config(page_title="GAIA – Admin", page_icon="🔐", layout="wide")

# Light mode default
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

st.session_state["user"] = None
if user.email != ADMIN_EMAIL:
    st.error("Access denied. Admin only.")
    st.stop()

st.markdown(
    '<div class="admin-title">🔐 GAIA Admin Dashboard</div>',
    unsafe_allow_html=True)

supabase = init_service_client()

# ===== FETCH ALL USERS =====


def get_all_users():
    users = []
    profiles = []
    scans = []
    wallets = []
    verifications = []

    # Get auth users
    try:
        resp = supabase.auth.admin.list_users()
        if hasattr(resp, 'users'):
            users = resp.users
        elif isinstance(resp, list):
            users = resp
    except BaseException:
        users = []

    # Get profiles
    try:
        p = supabase.table("user_profiles").select("*").execute()
        profiles = p.data if p.data else []
    except BaseException:
        profiles = []

    # Get scans
    try:
        s = supabase.table("user_scans").select("*").execute()
        scans = s.data if s.data else []
    except BaseException:
        scans = []

    # Get wallets
    try:
        w = supabase.table("farmer_wallets").select("*").execute()
        wallets = w.data if w.data else []
    except BaseException:
        wallets = []

    # Get verifications
    try:
        v = supabase.table("farmer_verifications").select("*").execute()
        verifications = v.data if v.data else []
    except BaseException:
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
        created = u.created_at if hasattr(
            u, 'created_at') else u.get(
            'created_at', '')

        p = profile_map.get(uid, {})
        s = scan_map.get(uid, {})
        w = wallet_map.get(uid, {})
        v = verify_map.get(uid, {})

        user_list.append(
            {
                "user_id": uid,
                "email": email or "N/A",
                "created_at": created or "",
                "scans_remaining": safe_int(
                    s.get("scans_remaining"),
                    0),
                "plan": safe_str(
                    s.get("plan"),
                    "free"),
                "wallet_balance": safe_float(
                    w.get("balance"),
                    0),
                "verification_status": safe_str(
                    v.get("status"),
                    safe_str(
                        p.get("verification_status"),
                        "pending")),
                **p})

    return user_list


def add_scans_to_user(user_id, amount):
    try:
        cur_res = supabase.table("user_scans").select(
            "scans_remaining").eq("user_id", user_id).execute()
        cur = safe_int(
            cur_res.data[0].get("scans_remaining"),
            0) if cur_res.data else 0
        supabase.table("user_scans").update(
            {"scans_remaining": cur + amount}).eq("user_id", user_id).execute()
        return True, None
    except Exception as e:
        return False, str(e)


def delete_user_fully(user_id):
    tables = [
        "payment_history",
        "messages",
        "farmer_verifications",
        "user_profiles",
        "user_scans",
        "marketplace_listings",
        "marketplace_orders",
        "insurance_policies",
        "insurance_claims",
        "field_monitoring",
        "seller_profiles",
        "badge_subscriptions",
        "farmer_wallets",
        "pending_payments",
        "posts",
        "friendships",
        "chat_members",
        "user_status",
        "user_feedback"]
    for table in tables:
        try:
            supabase.table(table).delete().eq("user_id", user_id).execute()
        except BaseException:
            pass
    try:
        supabase.auth.admin.delete_user(user_id)
        return True, None
    except Exception as e:
        return False, str(e)


def create_user(email, password, first_name, last_name, phone, state):
    try:
        resp = supabase.auth.admin.create_user({
            "email": email, "password": password, "email_confirm": True
        })
        if resp.user:
            uid = resp.user.id
            supabase.table("user_profiles").insert({
                "user_id": uid, "first_name": first_name, "last_name": last_name,
                "phone": phone, "state": state, "verification_status": "pending"
            }).execute()
            supabase.table("user_scans").insert({
                "user_id": uid, "scans_remaining": 30, "plan": "free"
            }).execute()
            return True, None
        return False, "Creation failed"
    except Exception as e:
        return False, str(e)


def approve_kyc(user_id):
    try:
        supabase.table("farmer_verifications").update(
            {"status": "approved"}).eq("user_id", user_id).execute()
    except BaseException:
        pass
    try:
        supabase.table("user_profiles").update(
            {"verification_status": "approved"}).eq("user_id", user_id).execute()
    except BaseException:
        pass


def reject_kyc(user_id):
    try:
        supabase.table("farmer_verifications").update(
            {"status": "rejected"}).eq("user_id", user_id).execute()
    except BaseException:
        pass
    try:
        supabase.table("user_profiles").update(
            {"verification_status": "rejected"}).eq("user_id", user_id).execute()
    except BaseException:
        pass


# ===== LOAD USERS =====
users = get_all_users()

# ===== TABS =====
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📊 Overview", "👤 All Users", "🛡️ KYC Queue", "✏️ Edit User", "➕ Create User", "📨 Support Tickets"])

# ===== TAB 1: OVERVIEW =====
with tab1:
    total = len(users)
    verified = sum(1 for u in users if u.get(
        "verification_status") == "approved")
    pending = sum(1 for u in users if u.get(
        "verification_status") == "pending")
    rejected = sum(1 for u in users if u.get(
        "verification_status") == "rejected")
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
            summary.append(
                {
                    "Email": safe_str(
                        u.get("email")), "Name": f"{
                        safe_str(
                            u.get(
                                'first_name', ''))} {
                        safe_str(
                            u.get(
                                'last_name', ''))}".strip(), "Phone": safe_str(
                        u.get("phone"), ""), "State": safe_str(
                        u.get("state"), ""), "KYC": safe_str(
                        u.get("verification_status"), "pending"), "Scans": safe_int(
                        u.get("scans_remaining"), 0), "Plan": safe_str(
                            u.get("plan"), "free"), "Wallet": f"₦{
                        safe_float(
                            u.get('wallet_balance')):,.2f}", "Joined": safe_date(
                        u.get("created_at")), })
        st.dataframe(pd.DataFrame(summary), use_container_width=True)
    else:
        st.info("No users found.")

# ===== TAB 2: ALL USERS =====
with tab2:
    if not users:
        st.info("No users.")
    else:
        emails = [safe_str(u.get("email")) for u in users]
        sel = st.selectbox("Select User to View", emails, key="view_sel")
        u = next((x for x in users if safe_str(x.get("email")) == sel), None)

        if u:
            st.markdown('<div class="user-card">', unsafe_allow_html=True)
            st.markdown(
                f"### 👤 {
                    safe_str(
                        u.get('first_name'))} {
                    safe_str(
                        u.get('last_name'))}")
            st.markdown(f"**Email:** {safe_str(u.get('email'))}")
            st.markdown(f"**Joined:** {safe_date(u.get('created_at'))}")

            st.markdown("---")
            st.markdown("#### 📋 Personal Information")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"Phone: {safe_str(u.get('phone'))}")
                st.write(f"WhatsApp: {safe_str(u.get('whatsapp'))}")
                st.write(f"Gender: {safe_str(u.get('gender'))}")
                st.write(f"DOB: {safe_str(u.get('date_of_birth'))}")
            with c2:
                st.write(f"BVN: {safe_str(u.get('bvn'))}")
                st.write(f"NIN: {safe_str(u.get('nin'))}")
                st.write(f"ID Type: {safe_str(u.get('govt_id_type'))}")
                st.write(f"ID Number: {safe_str(u.get('govt_id_number'))}")
            with c3:
                st.write(f"Marital: {safe_str(u.get('marital_status'))}")
                st.write(f"Country: {safe_str(u.get('country'))}")
                st.write(f"State: {safe_str(u.get('state'))}")
                st.write(f"LGA: {safe_str(u.get('lga'))}")

            st.markdown("---")
            st.markdown("#### 🏠 Address")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"City: {safe_str(u.get('city'))}")
                st.write(f"Street: {safe_str(u.get('street_address'))}")
                st.write(f"Landmark: {safe_str(u.get('landmark'))}")
            with c2:
                st.write(f"Postal: {safe_str(u.get('postal_code'))}")

            st.markdown("---")
            st.markdown("#### 🌾 Farm Information")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"Farm State: {safe_str(u.get('farm_state'))}")
                st.write(f"Farm LGA: {safe_str(u.get('farm_lga'))}")
                st.write(
                    f"Farm Size: {
                        safe_str(
                            u.get('farm_size_acres'))} acres")
            with c2:
                st.write(
                    f"Experience: {
                        safe_str(
                            u.get('years_experience'))} years")
                st.write(f"Crops: {safe_str(u.get('primary_crops'))}")
                st.write(f"Type: {safe_str(u.get('farming_type'))}")

            st.markdown("---")
            st.markdown("#### 🏦 Bank Information")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"Account: {safe_str(u.get('account_name'))}")
                st.write(f"Number: {safe_str(u.get('account_number'))}")
            with c2:
                st.write(f"Bank: {safe_str(u.get('bank_name'))}")

            st.markdown("---")
            st.markdown("#### 🚨 Emergency Contact")
            st.write(
                f"{
                    safe_str(
                        u.get('emergency_contact_name'))} — {
                    safe_str(
                        u.get('emergency_contact_phone'))} ({
                    safe_str(
                        u.get('emergency_relationship'))})")

            st.markdown("---")
            st.markdown("#### 💰 Wallet & Plan")
            c1, c2 = st.columns(2)
            c1.metric("Scans", safe_int(u.get("scans_remaining")))
            c2.metric("Wallet", f"₦{safe_float(u.get('wallet_balance')):,.2f}")
            st.write(f"Plan: **{safe_str(u.get('plan'), 'free')}**")

            status = safe_str(u.get("verification_status"), "pending")
            if status == "approved":
                st.markdown(
                    f"KYC: **<span class='verified'>APPROVED</span>**",
                    unsafe_allow_html=True)
            elif status == "rejected":
                st.markdown(
                    f"KYC: **<span class='rejected'>REJECTED</span>**",
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f"KYC: **<span class='pending'>PENDING</span>**",
                    unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

# ===== TAB 3: KYC QUEUE =====
with tab3:
    st.markdown("### 🛡️ Pending KYC")
    pending_users = [u for u in users if u.get(
        "verification_status") == "pending"]
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
                    try:
                        approve_kyc(u["user_id"])
                        st.success("Approved!")
                        st.rerun()
                    except Exception as e:
                        st.warning(
                            f"Approved (partial update): {
                                str(e)[
                                    :100]}")
                if c2.button("❌ Reject", key=f"rej_{u['user_id']}"):
                    try:
                        reject_kyc(u["user_id"])
                        st.error("Rejected.")
                        st.rerun()
                    except Exception as e:
                        st.warning(
                            f"Rejected (partial update): {
                                str(e)[
                                    :100]}")

# ===== TAB 4: EDIT USER =====
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
                    first = st.text_input(
                        "First Name", value=safe_str(
                            u.get("first_name"), ""))
                    last = st.text_input(
                        "Last Name", value=safe_str(
                            u.get("last_name"), ""))
                    phone = st.text_input(
                        "Phone", value=safe_str(
                            u.get("phone"), ""))
                    bvn = st.text_input(
                        "BVN", value=safe_str(
                            u.get("bvn"), ""))
                with c2:
                    nin = st.text_input(
                        "NIN", value=safe_str(
                            u.get("nin"), ""))
                    state = st.text_input(
                        "State", value=safe_str(
                            u.get("state"), ""))
                    status_opts = ["pending", "approved", "rejected"]
                    status = st.selectbox(
                        "KYC Status",
                        status_opts,
                        index=status_opts.index(
                            safe_str(
                                u.get("verification_status"),
                                "pending")) if safe_str(
                            u.get("verification_status"),
                            "pending") in status_opts else 0)
                    plan_opts = ["free", "10", "25", "60", "250", "unlimited"]
                    plan = st.selectbox(
                        "Plan",
                        plan_opts,
                        index=plan_opts.index(
                            safe_str(
                                u.get("plan"),
                                "free")) if safe_str(
                            u.get("plan"),
                            "free") in plan_opts else 0)

                add_scans = st.number_input(
                    "Scans to Add", min_value=0, value=0)

                if st.form_submit_button("💾 Save Changes"):
                    updates = {}
                    if first != safe_str(u.get("first_name"), ""):
                        updates["first_name"] = first
                    if last != safe_str(u.get("last_name"), ""):
                       updates["last_name"] = last
                    if phone != safe_str(u.get("phone"), ""):
                        updates["phone"] = phone
                    if bvn != safe_str(u.get("bvn"), ""):
                       updates["bvn"] = bvn
                    if nin != safe_str(u.get("nin"), ""):
                        updates["nin"] = nin
                    if state != safe_str(u.get("state"), ""):
                       updates["state"] = state
                    try:
                        if updates:
                            supabase.table("user_profiles").update(
                                updates).eq("user_id", uid).execute()
                        if add_scans > 0:
                            add_scans_to_user(uid, add_scans)
                        supabase.table("user_profiles").update(
                            {"verification_status": status}).eq("user_id", uid).execute()
                        supabase.table("user_scans").update(
                            {"plan": plan}).eq("user_id", uid).execute()
                        st.success("✅ Updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Update failed: {str(e)[:200]}")

            st.markdown("---")
            st.markdown("### 🗑️ Danger Zone")
            if st.button("🗑️ Delete User Permanently", type="secondary"):
                st.warning("⚠️ This cannot be undone.")
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
    with st.form("create_user_form"):
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


# ===== TAB 6: SUPPORT TICKETS =====
with tab6:
    st.markdown("### 📨 User Support Tickets")

    # Ensure all_users is defined
    try:
        all_users = get_all_users()
    except BaseException:
        all_users = []

    try:
        tickets = supabase.table("support_tickets").select(
            "*").order("created_at", desc=True).execute()
        all_tickets = tickets.data if tickets.data else []
    except BaseException:
        all_tickets = []

    if not all_tickets:
        st.info("No support tickets yet.")
    else:
        for ticket in all_tickets:
            status = ticket.get("status", "open")
            status_emoji = {"open": "🟠", "closed": "✅"}.get(status, "⚪")

            # Get user info from all_users list
            user_info = {}
            for u in all_users:
                if isinstance(u, dict) and u.get(
                        "user_id") == ticket.get("user_id"):
                    user_info = u
                    break

            user_email = user_info.get("email", "N/A")
            user_name = f"{
                user_info.get(
                    'first_name',
                    '')} {
                user_info.get(
                    'last_name',
                    '')}".strip() or user_email

            with st.expander(f"{status_emoji} {ticket.get('subject', '')} — {user_email}"):
                # User details
                st.markdown("#### 👤 User Information")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Name:** {user_name}")
                    st.write(f"**Email:** {user_email}")
                with col2:
                    st.write(f"**Phone:** {user_info.get('phone', 'N/A')}")
                    st.write(
                        f"**User ID:** {str(ticket.get('user_id', 'N/A'))[:12]}...")
                with col3:
                    st.write(f"**State:** {user_info.get('state', 'N/A')}")
                    st.write(
                        f"**KYC:** {user_info.get('verification_status', 'N/A')}")

                st.markdown("---")
                st.markdown("#### 📝 Ticket Content")
                st.write(f"**Subject:** {ticket.get('subject', '')}")
                st.write(f"**Message:** {ticket.get('message', '')}")

                # Attachment
                attachment_url = ticket.get("attachment_url")
                if attachment_url:
                    attachment_type = ticket.get("attachment_type", "")
                    if attachment_type and attachment_type.startswith("image"):
                        st.image(attachment_url, width=300)
                    elif attachment_type and attachment_type.startswith("video"):
                        st.video(attachment_url)
                    else:
                        st.markdown(
                            f"[📎 Download Attachment]({attachment_url})")

                st.markdown("---")
                st.markdown("#### 💬 Conversation")

                # Get all replies
                try:
                    replies = supabase.table("support_replies").select(
                        "*").eq("ticket_id", ticket["id"]).order("created_at").execute()
                    reply_list = replies.data if replies.data else []
                except BaseException:
                    reply_list = []

                # Display all messages in chronological order
                if reply_list:
                    for reply in reply_list:
                        if reply.get("is_admin"):
                            st.markdown(
                                f'<div style="background:#e8f5e9;padding:8px 12px;border-radius:8px;margin:4px 0;"><strong>🔐 GAIA Team:</strong> {
                                    reply.get(
                                        "message",
                                        "")}</div>',
                                unsafe_allow_html=True)
                        else:
                            st.markdown(
                                f'<div style="background:#fff3e0;padding:8px 12px;border-radius:8px;margin:4px 0;"><strong>👤 User:</strong> {
                                    reply.get(
                                        "message",
                                        "")}</div>',
                                unsafe_allow_html=True)
                else:
                    st.info("No replies yet.")

                # Admin reply form
                st.markdown("#### ✍️ Reply to User")
                with st.form(f"admin_reply_form_{ticket['id']}"):
                    admin_reply = st.text_area(
                        "Your Reply", key=f"admin_reply_text_{
                            ticket['id']}", height=100)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        send_reply = st.form_submit_button(
                            "📤 Send Reply", use_container_width=True)
                    with col2:
                        close_ticket = st.form_submit_button(
                            "✅ Close Ticket", use_container_width=True)
                    with col3:
                        reopen_ticket = st.form_submit_button(
                            "🔄 Reopen", use_container_width=True)

                    if send_reply and admin_reply.strip():
                        try:
                            supabase.table("support_replies").insert({
                                "ticket_id": ticket["id"],
                                "sender_id": user.id,
                                "is_admin": True,
                                "message": admin_reply.strip()
                            }).execute()
                            st.success("✅ Reply sent!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to send reply: {e}")

                    if close_ticket:
                        supabase.table("support_tickets").update(
                            {"status": "closed"}).eq("id", ticket["id"]).execute()
                        st.success("Ticket closed.")
                        st.rerun()

                    if reopen_ticket:
                        supabase.table("support_tickets").update(
                            {"status": "open"}).eq("id", ticket["id"]).execute()
                        st.success("Ticket reopened.")
                        st.rerun()

# ===== NAVIGATION =====
st.markdown("---")
cols = st.columns(9)
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
   st.page_link("pages/8_Profile.py", label="👤 Profile")
with cols[6]:
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[7]:
   st.page_link("pages/20_Marketplace.py", label="🌍 Market")
with cols[8]:
    st.page_link("pages/21_Crop_Insurance.py", label="🏦 Insurance")

# ============================================
# FULL NAVIGATION — ALL PAGES
# ============================================
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(10)
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
    st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[6]:
    st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[7]:
    st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[8]:
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[9]:
    st.page_link("pages/10_Early_Warning.py", label="⚠️ Alerts")

st.markdown("### 📱 More Features")
cols2 = st.columns(10)
with cols2[0]:
    st.page_link("pages/11_Verify_Farmer.py", label="🛡️ Verify")
with cols2[1]:
    st.page_link("pages/12_Verification_History.py", label="📋 History")
with cols2[2]:
    st.page_link("pages/14_Wallet.py", label="💰 Wallet")
with cols2[3]:
    st.page_link("pages/15_Badges.py", label="🏅 Badges")
with cols2[4]:
    st.page_link("pages/16_Chat.py", label="💬 Chat")
with cols2[5]:
    st.page_link("pages/20_Marketplace.py", label="🌍 Market")
with cols2[6]:
    st.page_link("pages/21_Crop_Insurance.py", label="🏦 Insurance")
with cols2[7]:
    st.page_link("pages/6_Payment_History.py", label="💳 Payments")
with cols2[8]:
    st.page_link("pages/8_Profile.py", label="👤 Profile")
with cols2[9]:
    st.page_link("pages/13_Help.py", label="🆘 Help")
