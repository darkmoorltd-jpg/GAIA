
import streamlit as st
from supabase import create_client, Client
from datetime import datetime

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

try:
    service.table("user_status").upsert({"user_id": user.id, "is_online": True, "last_seen": datetime.now().isoformat()}).execute()
except:
    pass

# ===== BUILD USER DATABASE PROPERLY =====
all_users = {}

# Method 1: Get all profiles from user_profiles table
try:
    res = service.table("user_profiles").select("*").execute()
    if res.data:
        for p in res.data:
            uid = p["user_id"]
            all_users[uid] = {
                "user_id": uid,
                "email": "",
                "first_name": p.get("first_name", "") or "",
                "last_name": p.get("last_name", "") or "",
                "phone": p.get("phone", "") or "",
                "country": p.get("country", "") or "",
                "state_city": p.get("state_city", "") or ""
            }
except:
    pass

# Method 2: Get all auth users (for emails)
try:
    auth_users = service.auth.admin.list_users()
    if auth_users:
        for au in auth_users:
            if au.id not in all_users:
                all_users[au.id] = {"user_id": au.id, "email": au.email or '', "first_name": "", "last_name": "", "phone": "", "country": "", "state_city": ""}
            else:
                # Merge email
                all_users[au.id]["email"] = au.email or all_users[au.id].get("email", "")
except:
    pass

# Method 3: Try to get users from auth schema directly
if len(all_users) < 2:
    try:
        res = service.table("users").select("id,email").execute()
        if res.data:
            for u in res.data:
                uid = u["id"]
                if uid not in all_users:
                    all_users[uid] = {"user_id": uid, "email": u.get("email", ""), "first_name": "", "last_name": "", "phone": "", "country": "", "state_city": ""}
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

# ===== HELPER FUNCTIONS =====
def get_or_create_dm(other_user_id):
    try:
        my_rooms_res = db.table("chat_members").select("room_id").eq("user_id", user.id).execute()
        if my_rooms_res.data:
            my_room_ids = set(r["room_id"] for r in my_rooms_res.data)
            for rid in my_room_ids:
                members_res = db.table("chat_members").select("user_id").eq("room_id", rid).execute()
                if members_res.data:
                    member_ids = set(m["user_id"] for m in members_res.data)
                    if other_user_id in member_ids and len(member_ids) == 2:
                        return rid
    except:
        pass
    try:
        room = service.table("chat_rooms").insert({"name": f"DM-{user.id[:6]}-{other_user_id[:6]}", "is_group": False}).execute()
        room_id = room.data[0]["id"]
        service.table("chat_members").insert([
            {"room_id": room_id, "user_id": user.id},
            {"room_id": room_id, "user_id": other_user_id}
        ]).execute()
        return room_id
    except:
        return None

def get_display_name(uid):
    prof = all_users.get(uid, {})
    name = f"{prof.get('first_name','')} {prof.get('last_name','')}".strip()
    if not name:
        name = prof.get('email', '').split('@')[0] if prof.get('email') else 'Unknown'
    return name

# ===== FRIENDS & ROOMS =====
friend_ids = set()
try:
    res = db.table("friendships").select("*").eq("status", "accepted").or_(f"sender_id.eq.{user.id},receiver_id.eq.{user.id}").execute()
    if res.data:
        for f in res.data:
            fid = f["sender_id"] if f["receiver_id"] == user.id else f["receiver_id"]
            friend_ids.add(fid)
except:
    pass

pending_requests = []
try:
    res = db.table("friendships").select("*").eq("receiver_id", user.id).eq("status", "pending").execute()
    if res.data:
        pending_requests = res.data
except:
    pass

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
                name = get_display_name(other_id) if other_id else "Unknown"
                my_rooms.append({"id": room["id"], "name": name, "other_id": other_id})
except:
    pass

if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "active_chat_name" not in st.session_state:
    st.session_state.active_chat_name = ""
if "active_chat_other" not in st.session_state:
    st.session_state.active_chat_other = None

# ===== ACCEPT/DECLINE =====
if "accept_clicked" in st.session_state and st.session_state.accept_clicked:
    sid = st.session_state.accept_clicked
    try:
        service.table("friendships").update({"status": "accepted"}).eq("sender_id", sid).eq("receiver_id", user.id).execute()
        room_id = get_or_create_dm(sid)
        if room_id:
            st.session_state.active_chat = room_id
            st.session_state.active_chat_name = get_display_name(sid)
            st.session_state.active_chat_other = sid
    except:
        pass
    st.session_state.accept_clicked = None

if "decline_clicked" in st.session_state and st.session_state.decline_clicked:
    sid = st.session_state.decline_clicked
    try:
        service.table("friendships").delete().eq("sender_id", sid).eq("receiver_id", user.id).execute()
    except:
        pass
    st.session_state.decline_clicked = None

# ---------- PREMIUM STYLING ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #0a0e0a; }
    header, footer { visibility: hidden; }
    
    .chat-item {
        display: flex; align-items: center; gap: 14px; padding: 14px 18px;
        cursor: pointer; background: rgba(255,255,255,0.02); border-bottom: 1px solid rgba(255,255,255,0.04);
        transition: all 0.2s;
    }
    .chat-item:hover { background: rgba(255,255,255,0.05); }
    .chat-item.active { background: rgba(37, 211, 102, 0.15); border-left: 3px solid #25d366; }
    .avatar {
        width: 52px; height: 52px; border-radius: 50%; 
        background: linear-gradient(135deg, #25d366, #128c7e);
        display: flex; align-items: center; justify-content: center; 
        font-weight: 700; color: #fff; font-size: 1.3rem; flex-shrink: 0;
    }
    .chat-name { font-weight: 600; font-size: 1rem; color: #e9edef; }
    .chat-subtitle { font-size: 0.82rem; color: #8696a0; margin-top: 2px; }
    
    .message-bubble {
        max-width: 55%; padding: 10px 14px; border-radius: 12px; margin: 3px 20px;
        font-size: 0.9rem; line-height: 1.45; position: relative;
        box-shadow: 0 1px 2px rgba(0,0,0,0.2); word-wrap: break-word;
    }
    .message-mine { background: #005c4b; color: #e9edef; float: right; border-top-right-radius: 4px; }
    .message-other { background: #202c33; color: #e9edef; float: left; border-top-left-radius: 4px; }
    .message-time { font-size: 0.68rem; color: rgba(255,255,255,0.45); float: right; margin-left: 10px; margin-top: 4px; }
    
    .chat-header {
        background: #202c33; padding: 12px 20px; border-bottom: 1px solid rgba(255,255,255,0.06);
        display: flex; align-items: center; gap: 14px;
    }
    
    .stButton button {
        background: #00a884 !important; color: #fff !important; border: none !important;
        border-radius: 50% !important; width: 46px !important; height: 46px !important;
        padding: 0 !important; font-size: 1.3rem !important; transition: all 0.2s !important;
    }
    .stButton button:hover { background: #06cf9c !important; transform: scale(1.05); }
    
    .search-input input {
        background: #202c33 !important; border: none !important;
        border-radius: 10px !important; padding: 12px 18px !important; 
        font-size: 0.9rem !important; color: #e9edef !important;
    }
    .search-input input::placeholder { color: #8696a0 !important; }
    
    .chat-input input {
        background: #2a3942 !important; border: none !important;
        border-radius: 10px !important; padding: 12px 18px !important;
        font-size: 0.95rem !important; color: #e9edef !important;
    }
    .chat-input input::placeholder { color: #8696a0 !important; }
    
    .welcome-screen {
        background: #222e35; display: flex; align-items: center; justify-content: center;
        flex-direction: column; height: 100%; border-left: 1px solid rgba(255,255,255,0.06);
    }
    
    .online-badge { color: #25d366; font-weight: 500; }
    .offline-badge { color: #8696a0; }
    
    [data-testid="stVerticalBlock"] { gap: 0 !important; }
    .stTabs [data-baseweb="tab-list"] { background: #111b21; border-radius: 0; }
    .stTabs [data-baseweb="tab"] { color: #8696a0; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #25d366; }
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown('<div style="background:#111b21;padding:12px 20px;color:#e9edef;font-weight:600;font-size:1.1rem;display:flex;align-items:center;gap:10px;border-bottom:1px solid rgba(255,255,255,0.06);"><span style="color:#25d366;">💬</span> GAIAchat</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1.2, 2.8])

# ===== LEFT PANEL =====
with col_left:
    search = st.text_input("", placeholder="🔍 Search farmers by name or phone", key="chat_search", label_visibility="collapsed")
    
    # Friend Requests
    if pending_requests:
        st.markdown('<div style="padding:10px 18px;background:rgba(255,255,255,0.02);font-weight:600;color:#25d366;border-bottom:1px solid rgba(255,255,255,0.04);font-size:0.9rem;">📨 FRIEND REQUESTS</div>', unsafe_allow_html=True)
        for req in pending_requests:
            sender_name = get_display_name(req["sender_id"])
            st.markdown(f'<div class="chat-item"><div class="avatar">{sender_name[0].upper()}</div><div style="flex:1;"><div class="chat-name">{sender_name}</div><div class="chat-subtitle">wants to connect</div></div></div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Accept", key=f"acc_{req['sender_id']}"):
                    st.session_state.accept_clicked = req["sender_id"]
                    st.rerun()
            with c2:
                if st.button("❌ Decline", key=f"dec_{req['sender_id']}"):
                    st.session_state.decline_clicked = req["sender_id"]
                    st.rerun()
    
    if search:
        s = search.lower().strip()
        st.markdown(f'<div style="padding:8px 18px;background:rgba(255,255,255,0.02);font-size:0.85rem;color:#8696a0;border-bottom:1px solid rgba(255,255,255,0.04);">Results for "{search}"</div>', unsafe_allow_html=True)
        found = False
        for uid, prof in all_users.items():
            if uid == user.id:
                continue
            name = get_display_name(uid)
            phone = prof.get('phone', '') or ''
            email = prof.get('email', '') or ''
            searchable = f"{name} {phone} {email}".lower()
            if s in searchable:
                found = True
                is_online = uid in online_users
                is_friend = uid in friend_ids
                
                st.markdown(f'<div class="chat-item"><div class="avatar">{name[0].upper()}</div><div style="flex:1;"><div class="chat-name">{name}</div><div class="chat-subtitle"><span class="{"online-badge" if is_online else "offline-badge"}">{"🟢 Online" if is_online else "⚫ Offline"}</span>{" · " + phone if phone else ""}</div></div></div>', unsafe_allow_html=True)
                
                if is_friend:
                    if st.button("💬 Chat", key=f"chat_{uid}"):
                        room_id = get_or_create_dm(uid)
                        if room_id:
                            st.session_state.active_chat = room_id
                            st.session_state.active_chat_name = name
                            st.session_state.active_chat_other = uid
                            st.rerun()
                else:
                    if st.button("➕ Add", key=f"add_{uid}"):
                        try:
                            service.table("friendships").insert({"sender_id": user.id, "receiver_id": uid, "status": "accepted"}).execute()
                            room_id = get_or_create_dm(uid)
                            if room_id:
                                st.session_state.active_chat = room_id
                                st.session_state.active_chat_name = name
                                st.session_state.active_chat_other = uid
                                st.success(f"Connected with {name}!")
                                st.rerun()
                        except:
                            room_id = get_or_create_dm(uid)
                            if room_id:
                                st.session_state.active_chat = room_id
                                st.session_state.active_chat_name = name
                                st.session_state.active_chat_other = uid
                                st.rerun()
        if not found:
            st.info(f"No farmers found matching '{search}'.")
    else:
        if my_rooms:
            st.markdown('<div style="padding:10px 18px;background:rgba(255,255,255,0.02);font-weight:600;color:#25d366;border-bottom:1px solid rgba(255,255,255,0.04);font-size:0.9rem;">💬 CHATS</div>', unsafe_allow_html=True)
            for room in my_rooms:
                is_online = room.get("other_id") in online_users
                is_active = st.session_state.active_chat == room["id"]
                active_class = " active" if is_active else ""
                st.markdown(f'<div class="chat-item{active_class}"><div class="avatar">{room["name"][0].upper()}</div><div style="flex:1;"><div class="chat-name">{room["name"]}</div><div class="chat-subtitle"><span class="{"online-badge" if is_online else "offline-badge"}">{"🟢 Online" if is_online else "⚫ Offline"}</span></div></div></div>', unsafe_allow_html=True)
                if st.button("💬", key=f"open_{room['id']}"):
                    st.session_state.active_chat = room["id"]
                    st.session_state.active_chat_name = room["name"]
                    st.session_state.active_chat_other = room.get("other_id")
                    st.rerun()
        else:
            st.markdown(f'<div style="padding:60px 20px;text-align:center;color:#8696a0;"><p style="font-size:3rem;">💬</p><p>Search for a farmer to start chatting</p></div>', unsafe_allow_html=True)

# ===== RIGHT PANEL =====
with col_right:
    if st.session_state.active_chat:
        room_id = st.session_state.active_chat
        name = st.session_state.active_chat_name
        other_id = st.session_state.active_chat_other
        is_online = other_id in online_users if other_id else False
        
        st.markdown(f'<div class="chat-header"><div class="avatar">{name[0].upper()}</div><div><strong style="color:#e9edef;font-size:1.05rem;">{name}</strong><br><span style="font-size:0.8rem;" class="{"online-badge" if is_online else "offline-badge"}">{"🟢 online" if is_online else "offline"}</span></div></div>', unsafe_allow_html=True)
        
        try:
            msgs = db.table("messages").select("*").eq("room_id", room_id).order("created_at").execute()
            msgs_data = msgs.data if msgs.data else []
        except:
            msgs_data = []
        
        st.markdown('<div style="height:55vh;overflow-y:auto;padding:12px 0;background:#0b141a;">', unsafe_allow_html=True)
        for msg in msgs_data:
            is_mine = msg["sender_id"] == user.id
            bubble_class = "message-mine" if is_mine else "message-other"
            time_str = msg.get("created_at", "")[11:16] if msg.get("created_at") else ""
            align = "text-align:right;" if is_mine else "text-align:left;"
            st.markdown(f'<div style="{align}"><div class="message-bubble {bubble_class}">{msg.get("content","")}<span class="message-time">{time_str}</span></div></div><div style="clear:both;"></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div style="background:#202c33;padding:10px 18px;display:flex;align-items:center;gap:10px;">', unsafe_allow_html=True)
        c1, c2 = st.columns([9, 1])
        with c1:
            new_msg = st.text_input("", placeholder="Type a message", key=f"input_{room_id}", label_visibility="collapsed")
        with c2:
            if st.button("📤", key=f"send_{room_id}"):
                if new_msg.strip():
                    try:
                        service.table("messages").insert({
                            "room_id": room_id,
                            "sender_id": user.id,
                            "content": new_msg.strip()
                        }).execute()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Send failed: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="welcome-screen"><div style="font-size:6rem;margin-bottom:20px;">💬</div><h2 style="color:#e9edef;font-weight:300;">GAIAchat</h2><p style="color:#8696a0;max-width:400px;text-align:center;">Connect with farmers across Africa.<br>Search by name or phone number to start chatting.</p></div>', unsafe_allow_html=True)

# ---------- NAVIGATION ----------
st.markdown("---")
st.markdown('<div style="display:flex;justify-content:center;gap:10px;flex-wrap:wrap;">', unsafe_allow_html=True)
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
st.markdown('</div>', unsafe_allow_html=True)
