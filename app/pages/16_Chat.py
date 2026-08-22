import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import uuid
from app.utils.scan_util import deduct_scans

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]

@st.cache_resource
def get_db():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA – Community", page_icon="🌍", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
db = get_db()
service = get_service()

try:
    service.table("user_status").upsert({"user_id": user.id, "is_online": True, "last_seen": datetime.now().isoformat()}).execute()
except:
    pass

# ===== BUILD COMPLETE USER DATABASE =====
all_users = {}

# 1. Get all auth users (emails)
try:
    auth_users = service.auth.admin.list_users()
    if auth_users:
        for au in auth_users:
            all_users[au.id] = {
                "user_id": au.id,
                "email": au.email or '',
                "first_name": "",
                "last_name": "",
                "phone": "",
                "country": "",
                "state_city": "",
                "address": "",
            }
except:
    pass

# 2. Get all profiles and merge
try:
    res = service.table("user_profiles").select("*").execute()
    if res.data:
        for p in res.data:
            uid = p["user_id"]
            if uid not in all_users:
                all_users[uid] = {"user_id": uid, "email": ""}
            for key in ["first_name", "last_name", "phone", "country", "state_city", "address"]:
                all_users[uid][key] = p.get(key, "") or ""
except:
    pass

# Online users
online_users = set()
try:
    res = service.table("user_status").select("user_id").eq("is_online", True).execute()
    if res.data:
        for s in res.data:
            online_users.add(s["user_id"])
except:
    pass

# Friends
friend_ids = set()
try:
    res = db.table("friendships").select("*").eq("status", "accepted").or_(f"sender_id.eq.{user.id},receiver_id.eq.{user.id}").execute()
    if res.data:
        for f in res.data:
            fid = f["sender_id"] if f["receiver_id"] == user.id else f["receiver_id"]
            friend_ids.add(fid)
except:
    pass

# Pending requests
pending_requests = []
try:
    res = db.table("friendships").select("*").eq("receiver_id", user.id).eq("status", "pending").execute()
    if res.data:
        pending_requests = res.data
except:
    pass

# Chat rooms
my_rooms = []
try:
    res = db.table("chat_members").select("room_id").eq("user_id", user.id).execute()
    room_ids = [r["room_id"] for r in res.data] if res.data else []
    if room_ids:
        rooms = service.table("chat_rooms").select("*").in_("id", room_ids).execute()
        if rooms.data:
            for room in rooms.data:
                if room["is_group"]:
                    my_rooms.append({"id": room["id"], "name": room["name"], "is_group": True})
                else:
                    members = db.table("chat_members").select("user_id").eq("room_id", room["id"]).execute()
                    other_id = None
                    if members.data:
                        for m in members.data:
                            if m["user_id"] != user.id:
                                other_id = m["user_id"]
                                break
                    if other_id and other_id in all_users:
                        prof = all_users[other_id]
                        name = f"{prof.get('first_name','')} {prof.get('last_name','')}".strip()
                        if not name:
                            name = prof.get('email','Unknown')
                    else:
                        name = "Unknown"
                    my_rooms.append({"id": room["id"], "name": name, "other_id": other_id, "is_group": False})
except:
    pass

if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "active_chat_name" not in st.session_state:
    st.session_state.active_chat_name = ""

# ---------- STYLES ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #111 0%, #1a1a2e 30%, #16213e 60%, #111 100%); color: #fff; }
    header, footer { visibility: hidden; }
    .stTabs [data-baseweb="tab-list"] { gap: 0; background: rgba(255,255,255,0.03); border-radius: 12px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 20px; font-weight: 600; font-size: 0.85rem; color: rgba(255,255,255,0.5); border-radius: 10px; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background: rgba(46,125,50,0.3); color: #fff; }
    .user-card {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px; padding: 15px; margin: 8px 0; display: flex; align-items: center; gap: 12px;
    }
    .avatar {
        width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, #2e7d32, #4caf50);
        display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fff; font-size: 1.2rem;
    }
    .empty-state { text-align: center; padding: 60px 20px; }
    .empty-state h3 { color: rgba(255,255,255,0.3); }
    .empty-state p { color: rgba(255,255,255,0.2); }
</style>
""", unsafe_allow_html=True)

# ---------- TABS ----------
tabs = st.tabs(["💬 Messages", "👥 Friends", "🌍 Discover", "📝 Feed"])

# ===== TAB 1: MESSAGES =====
with tabs[0]:
    col1, col2 = st.columns([1, 2.5])
    with col1:
        st.markdown("### 💬 Chats")
        for room in my_rooms:
            name = room["name"]
            is_online = room.get("other_id") in online_users if not room["is_group"] else False
            label = f"{'🟢' if is_online else '⚫'} {name}"
            if st.button(label, key=f"room_{room['id']}", use_container_width=True):
                st.session_state.active_chat = room["id"]
                st.session_state.active_chat_name = name
                st.rerun()
    with col2:
        if st.session_state.active_chat:
            room_id = st.session_state.active_chat
            st.markdown(f"### 💬 {st.session_state.active_chat_name}")
            try:
                msgs = db.table("messages").select("*").eq("room_id", room_id).order("created_at").execute()
            except:
                msgs = type('obj', (object,), {'data': []})()
            for msg in (msgs.data or []):
                is_mine = msg["sender_id"] == user.id
                with st.chat_message("user" if is_mine else "assistant"):
                    if msg.get("content"):
                        st.write(msg["content"])
                    st.caption(msg["created_at"][11:16] if msg.get("created_at") else "")
            ca, cb = st.columns([5, 1])
            with ca:
                msg_text = st.text_input("", placeholder="Type a message...", key=f"msg_{room_id}", label_visibility="collapsed")
            with cb:
                if st.button("📤", key=f"send_{room_id}"):
                    if msg_text:
                        service.table("messages").insert({"room_id": room_id, "sender_id": user.id, "content": msg_text}).execute()
                        # Deduct 2 scans for chat message
                        ok, remaining = deduct_scans(user.id, 2, "Chat with GAIA")
                        st.rerun()
        else:
            st.markdown('<div class="empty-state"><h3>💬 Your Messages</h3><p>Select a chat or find a farmer</p></div>', unsafe_allow_html=True)

# ===== TAB 2: FRIENDS =====
with tabs[1]:
    if pending_requests:
        st.markdown("### 📨 Friend Requests")
        for req in pending_requests:
            sender_id = req["sender_id"]
            sender = all_users.get(sender_id, {})
            name = f"{sender.get('first_name','')} {sender.get('last_name','')}".strip()
            if not name:
                name = sender.get('email', 'Unknown')
            st.markdown(f'<div class="user-card"><div class="avatar">{name[0].upper() if name else "?"}</div><div><strong>{name}</strong><br><span style="color:rgba(255,255,255,0.4);">wants to be your friend</span></div></div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("✅ Accept", key=f"acc_{sender_id}"):
                service.table("friendships").update({"status": "accepted"}).eq("sender_id", sender_id).eq("receiver_id", user.id).execute()
                st.rerun()
            if c2.button("❌ Decline", key=f"dec_{sender_id}"):
                service.table("friendships").delete().eq("sender_id", sender_id).eq("receiver_id", user.id).execute()
                st.rerun()
    st.markdown("### 👥 My Friends")
    found_friends = [f for f in friend_ids if f in all_users]
    if found_friends:
        for fid in found_friends:
            prof = all_users[fid]
            name = f"{prof.get('first_name','')} {prof.get('last_name','')}".strip()
            if not name:
                name = prof.get('email', 'Unknown')
            is_online = fid in online_users
            st.markdown(f"{'🟢' if is_online else '⚫'} **{name}** · {prof.get('state_city','')} · {prof.get('email','')} · {prof.get('phone','')}")
    else:
        st.info("No friends yet.")

# ===== TAB 3: DISCOVER =====
with tabs[2]:
    st.markdown("### 🌍 Discover Farmers")
    st.caption("Search by name, email, phone, state, or country")
    search = st.text_input("", placeholder="Search anything — name, email, phone, location...", key="disc_search")
    if search:
        s = search.lower().strip()
        found = False
        for uid, prof in all_users.items():
            if uid == user.id:
                continue
            name = f"{prof.get('first_name','')} {prof.get('last_name','')}".strip()
            email = prof.get('email', '') or ''
            phone = prof.get('phone', '') or ''
            state_city = prof.get('state_city', '') or ''
            country = prof.get('country', '') or ''
            address = prof.get('address', '') or ''
            searchable = f"{name} {email} {phone} {state_city} {country} {address}".lower()
            if s in searchable:
                found = True
                is_online = uid in online_users
                is_friend = uid in friend_ids
                display_name = name if name else (email or 'Unknown')
                st.markdown(f'<div class="user-card"><div class="avatar">{display_name[0].upper()}</div><div style="flex:1;"><strong>{display_name}</strong><div style="color:rgba(255,255,255,0.4);font-size:0.85rem;">{"🟢 Online · " if is_online else "⚫ Offline · "}{state_city or "Unknown"}</div><div style="color:rgba(255,255,255,0.25);font-size:0.75rem;">{email} · {phone}</div></div></div>', unsafe_allow_html=True)
                if not is_friend:
                    if st.button("➕ Add Friend", key=f"add_{uid}"):
                        try:
                            service.table("friendships").insert({"sender_id": user.id, "receiver_id": uid, "status": "pending"}).execute()
                            st.success("Request sent!")
                            st.rerun()
                        except:
                            st.warning("Already sent.")
                else:
                    st.caption("✅ Already friends")
                st.markdown("---")
        if not found:
            st.info(f"No farmers found matching '{search}'.")

# ===== TAB 4: FEED =====
with tabs[3]:
    st.markdown("### 📝 Community Feed")
    post_content = st.text_area("Share something...", max_chars=500)
    if st.button("📤 Post"):
        if post_content:
            service.table("posts").insert({"user_id": user.id, "content": post_content}).execute()
            st.rerun()
    try:
        posts = service.table("posts").select("*").order("created_at", desc=True).limit(20).execute()
        if posts.data:
            for post in posts.data:
                author = all_users.get(post["user_id"], {})
                author_name = f"{author.get('first_name','')} {author.get('last_name','')}".strip()
                if not author_name:
                    author_name = author.get('email', 'Unknown')
                st.markdown(f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:15px;margin:10px 0;"><strong>{author_name}</strong><div style="color:rgba(255,255,255,0.5);font-size:0.75rem;">{post.get("created_at","")[:16]}</div><p style="margin-top:8px;">{post.get("content","")}</p></div>', unsafe_allow_html=True)
    except:
        st.info("No posts yet.")

st.markdown("---")
cols = st.columns(6)
cols[0].page_link("pages/1_Dashboard.py", label="Dashboard")
cols[1].page_link("pages/2_Crops.py", label="Crops")
cols[2].page_link("pages/3_Pests.py", label="Pests")
cols[3].page_link("pages/4_Soil.py", label="Soil")
cols[4].page_link("pages/5_Livestock.py", label="Livestock")
cols[5].page_link("pages/9_Buy_Scans.py", label="Buy Scans")

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
#     st.page_link("pages/10_Early_Warning.py", label="⚠️ Alerts")

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
