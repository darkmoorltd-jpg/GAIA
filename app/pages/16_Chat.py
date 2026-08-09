
import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# ---------- CONFIG ----------
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]

@st.cache_resource
def get_db():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIAchat", page_icon="💬", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
db = get_db()
service = get_service()

# Update online status
try:
    service.table("user_status").upsert({"user_id": user.id, "is_online": True, "last_seen": datetime.now().isoformat()}).execute()
except:
    pass

# ===== BUILD USER DATABASE =====
all_users = {}
try:
    auth_users = service.auth.admin.list_users()
    if auth_users:
        for au in auth_users:
            all_users[au.id] = {"user_id": au.id, "email": au.email or '', "first_name": "", "last_name": "", "phone": "", "country": "", "state_city": ""}
except:
    pass

try:
    res = service.table("user_profiles").select("*").execute()
    if res.data:
        for p in res.data:
            uid = p["user_id"]
            if uid not in all_users:
                all_users[uid] = {"user_id": uid, "email": ""}
            for key in ["first_name", "last_name", "phone", "country", "state_city"]:
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
                other_id = None
                members = db.table("chat_members").select("user_id").eq("room_id", room["id"]).execute()
                if members.data:
                    for m in members.data:
                        if m["user_id"] != user.id:
                            other_id = m["user_id"]
                            break
                if other_id and other_id in all_users:
                    prof = all_users[other_id]
                    name = f"{prof.get('first_name','')} {prof.get('last_name','')}".strip()
                    if not name:
                        name = prof.get('email', 'Unknown')
                else:
                    name = "Unknown"
                my_rooms.append({"id": room["id"], "name": name, "other_id": other_id})
except:
    pass

if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "active_chat_name" not in st.session_state:
    st.session_state.active_chat_name = ""
if "search_results" not in st.session_state:
    st.session_state.search_results = []

# ---------- STYLES ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #0a0f0c; color: #e8f5e9; }
    header, footer { visibility: hidden; }
    .chat-list { background: #111b15; border-right: 1px solid #1b2e1f; height: calc(100vh - 100px); overflow-y: auto; padding: 10px; }
    .chat-item {
        display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 10px;
        cursor: pointer; transition: all 0.2s; margin-bottom: 4px;
    }
    .chat-item:hover { background: rgba(46,125,50,0.1); }
    .chat-item.active { background: rgba(46,125,50,0.2); }
    .avatar {
        width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, #2e7d32, #4caf50);
        display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fff; font-size: 1.2rem;
        flex-shrink: 0;
    }
    .online-dot { width: 10px; height: 10px; border-radius: 50%; background: #4caf50; display: inline-block; margin-right: 4px; }
    .offline-dot { width: 10px; height: 10px; border-radius: 50%; background: #555; display: inline-block; margin-right: 4px; }
    .message-bubble {
        max-width: 70%; padding: 10px 15px; border-radius: 18px; margin: 4px 0;
        font-size: 0.95rem; line-height: 1.4;
    }
    .message-mine { background: linear-gradient(135deg, #2e7d32, #1b5e20); color: #fff; margin-left: auto; border-bottom-right-radius: 4px; }
    .message-other { background: #1e2d22; color: #e8f5e9; border-bottom-left-radius: 4px; }
    .search-input input { background: #1b2e1f !important; border: 1px solid #2e4a34 !important; color: #e8f5e9 !important; border-radius: 20px !important; padding: 10px 16px !important; }
    .search-input input::placeholder { color: rgba(255,255,255,0.3) !important; }
    .chat-input input { background: #1b2e1f !important; border: 1px solid #2e4a34 !important; color: #e8f5e9 !important; border-radius: 25px !important; padding: 12px 20px !important; }
    .chat-input input::placeholder { color: rgba(255,255,255,0.3) !important; }
    .stButton button {
        background: #2e7d32 !important; color: #fff !important; border: none !important;
        border-radius: 20px !important; padding: 8px 20px !important; font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    .stButton button:hover { background: #4caf50 !important; transform: scale(1.03); }
    .divider { border-top: 1px solid #1b2e1f; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)

# ---------- MAIN LAYOUT ----------
st.markdown('<div style="font-size:1.4rem;font-weight:700;padding:10px 0;color:#4caf50;">💬 GAIAchat</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 2.5])

# ===== LEFT PANEL =====
with col_left:
    st.markdown("### 📱 Chats")
    
    # Search bar
    search = st.text_input("", placeholder="🔍 Search by name or phone...", key="chat_search", label_visibility="collapsed")
    
    if search:
        s = search.lower().strip()
        search_results = []
        for uid, prof in all_users.items():
            if uid == user.id:
                continue
            name = f"{prof.get('first_name','')} {prof.get('last_name','')}".strip()
            email = prof.get('email', '') or ''
            phone = prof.get('phone', '') or ''
            searchable = f"{name} {email} {phone}".lower()
            if s in searchable:
                search_results.append({"uid": uid, "name": name or email, "is_friend": uid in friend_ids})
        
        st.markdown(f"**{len(search_results)} results for '{search}'**")
        for sr in search_results:
            is_online = sr["uid"] in online_users
            st.markdown(f'<div class="chat-item"><div class="avatar">{sr["name"][0].upper()}</div><div style="flex:1;"><strong>{sr["name"]}</strong><br><small style="color:rgba(255,255,255,0.4);">{"🟢 Online" if is_online else "⚫ Offline"}</small></div></div>', unsafe_allow_html=True)
            if not sr["is_friend"]:
                if st.button("➕ Add & Chat", key=f"add_{sr['uid']}"):
                    try:
                        # Create friendship
                        service.table("friendships").insert({"sender_id": user.id, "receiver_id": sr["uid"], "status": "accepted"}).execute()
                        # Create chat room
                        room = service.table("chat_rooms").insert({"name": f"DM: {user.id[:8]}-{sr['uid'][:8]}", "is_group": False}).execute()
                        room_id = room.data[0]["id"]
                        service.table("chat_members").insert([{"room_id": room_id, "user_id": user.id}, {"room_id": room_id, "user_id": sr["uid"]}]).execute()
                        st.success(f"Chat with {sr['name']} started!")
                        st.rerun()
                    except:
                        st.warning("Already connected.")
            else:
                if st.button("💬 Chat", key=f"chat_{sr['uid']}"):
                    # Find existing room
                    for room in my_rooms:
                        if room.get("other_id") == sr["uid"]:
                            st.session_state.active_chat = room["id"]
                            st.session_state.active_chat_name = sr["name"]
                            st.rerun()
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    else:
        # Show existing chats
        if pending_requests:
            st.markdown("### 📨 Requests")
            for req in pending_requests:
                sender = all_users.get(req["sender_id"], {})
                name = f"{sender.get('first_name','')} {sender.get('last_name','')}".strip() or sender.get('email', 'Unknown')
                st.markdown(f'<div class="chat-item"><div class="avatar">{name[0].upper()}</div><div><strong>{name}</strong><br><small>wants to chat</small></div></div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                c1.button("✅", key=f"acc_{req['sender_id']}", on_click=lambda rid=req["sender_id"]: accept_request(rid))
                c2.button("❌", key=f"dec_{req['sender_id']}", on_click=lambda rid=req["sender_id"]: decline_request(rid))
        
        st.markdown("### 💬 All Chats")
        if my_rooms:
            for room in my_rooms:
                is_online = room.get("other_id") in online_users
                is_active = st.session_state.active_chat == room["id"]
                active_class = " active" if is_active else ""
                st.markdown(f'<div class="chat-item{active_class}" onclick="document.getElementById(\'btn_{room["id"]}\').click()"><div class="avatar">{room["name"][0].upper()}</div><div style="flex:1;"><strong>{room["name"]}</strong><br><small>{"🟢 Online" if is_online else "⚫ Offline"}</small></div></div>', unsafe_allow_html=True)
                if st.button("💬", key=f"open_{room['id']}"):
                    st.session_state.active_chat = room["id"]
                    st.session_state.active_chat_name = room["name"]
                    st.rerun()
                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        else:
            st.info("No chats yet. Search for a farmer above!")

# ===== RIGHT PANEL =====
with col_right:
    if st.session_state.active_chat:
        room_id = st.session_state.active_chat
        name = st.session_state.active_chat_name
        is_online = False
        # Find if the other user is online
        for room in my_rooms:
            if room["id"] == room_id:
                is_online = room.get("other_id") in online_users
                break
        
        st.markdown(f'<div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #1b2e1f;"><div class="avatar">{name[0].upper()}</div><div><strong>{name}</strong><br><small>{"🟢 Online" if is_online else "⚫ Offline"}</small></div></div>', unsafe_allow_html=True)
        
        # Messages area
        try:
            msgs = db.table("messages").select("*").eq("room_id", room_id).order("created_at").execute()
            msgs_data = msgs.data if msgs.data else []
        except:
            msgs_data = []
        
        # Scrollable messages container
        st.markdown('<div style="height:60vh;overflow-y:auto;padding:10px;">', unsafe_allow_html=True)
        for msg in msgs_data:
            is_mine = msg["sender_id"] == user.id
            bubble_class = "message-mine" if is_mine else "message-other"
            time_str = msg.get("created_at", "")[11:16] if msg.get("created_at") else ""
            st.markdown(f'<div class="message-bubble {bubble_class}">{msg.get("content","")}<br><small style="opacity:0.5;">{time_str}</small></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Message input
        c1, c2 = st.columns([6, 1])
        with c1:
            new_msg = st.text_input("", placeholder="Type a message...", key=f"input_{room_id}", label_visibility="collapsed")
        with c2:
            if st.button("📤", key=f"send_{room_id}"):
                if new_msg:
                    service.table("messages").insert({
                        "room_id": room_id,
                        "sender_id": user.id,
                        "content": new_msg,
                        "created_at": datetime.now().isoformat()
                    }).execute()
                    st.rerun()
    else:
        st.markdown('<div style="display:flex;align-items:center;justify-content:center;height:70vh;flex-direction:column;"><div style="font-size:5rem;">💬</div><h2>Welcome to GAIAchat</h2><p style="color:rgba(255,255,255,0.4);">Search for a farmer by name or phone number to start chatting</p></div>', unsafe_allow_html=True)

# Helper functions
def accept_request(sender_id):
    service.table("friendships").update({"status": "accepted"}).eq("sender_id", sender_id).eq("receiver_id", user.id).execute()
    st.rerun()

def decline_request(sender_id):
    service.table("friendships").delete().eq("sender_id", sender_id).eq("receiver_id", user.id).execute()
    st.rerun()

# ---------- NAVIGATION BAR ----------
st.markdown("---")
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
