
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

online_users = set()
try:
    res = service.table("user_status").select("user_id").eq("is_online", True).execute()
    if res.data:
        for s in res.data:
            online_users.add(s["user_id"])
except:
    pass

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
                if other_id and other_id in all_users:
                    prof = all_users[other_id]
                    name = f"{prof.get('first_name','')} {prof.get('last_name','')}".strip() or prof.get('email', 'Unknown')
                else:
                    name = "Unknown"
                my_rooms.append({"id": room["id"], "name": name, "other_id": other_id})
except:
    pass

if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "active_chat_name" not in st.session_state:
    st.session_state.active_chat_name = ""
if "active_chat_other" not in st.session_state:
    st.session_state.active_chat_other = None

if "accept_clicked" in st.session_state and st.session_state.accept_clicked:
    sid = st.session_state.accept_clicked
    try:
        service.table("friendships").update({"status": "accepted"}).eq("sender_id", sid).eq("receiver_id", user.id).execute()
        room_id = get_or_create_dm(sid)
        if room_id:
            st.session_state.active_chat = room_id
            prof = all_users.get(sid, {})
            name = f"{prof.get('first_name','')} {prof.get('last_name','')}".strip() or prof.get('email', 'Unknown')
            st.session_state.active_chat_name = name
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

# ---------- PERFECT WHATSAPP STYLE ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;500;600;700&display=swap');
    * { font-family: 'Segoe UI', system-ui, sans-serif; }
    .stApp { background: #efeae2; }
    header, footer { visibility: hidden; }
    
    .chat-item {
        display: flex; align-items: center; gap: 12px; padding: 12px 16px;
        cursor: pointer; background: white; border-bottom: 1px solid #f2f2f2;
    }
    .chat-item:hover { background: #f5f6f6; }
    .chat-item.active { background: #d9fdd3; }
    .avatar {
        width: 49px; height: 49px; border-radius: 50%; background: #25d366;
        display: flex; align-items: center; justify-content: center; font-weight: 600;
        color: #fff; font-size: 1.3rem; flex-shrink: 0;
    }
    .chat-name { font-weight: 500; font-size: 1rem; color: #111b21; }
    .chat-subtitle { font-size: 0.8rem; color: #667781; }
    
    .message-bubble {
        max-width: 60%; padding: 8px 12px; border-radius: 8px; margin: 2px 63px;
        font-size: 0.9rem; line-height: 1.4; position: relative;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1); word-wrap: break-word;
    }
    .message-mine { background: #d9fdd3; float: right; border-top-right-radius: 0; }
    .message-other { background: #fff; float: left; border-top-left-radius: 0; }
    .message-time { font-size: 0.65rem; color: #667781; float: right; margin-left: 8px; margin-top: 2px; }
    
    .chat-header {
        background: #f0f2f5; padding: 10px 16px; border-left: 1px solid #e0e0e0;
        display: flex; align-items: center; gap: 12px;
    }
    
    .stButton button {
        background: #00a884 !important; color: #fff !important; border: none !important;
        border-radius: 50% !important; width: 42px !important; height: 42px !important;
        padding: 0 !important; font-size: 1.2rem !important;
    }
    .stButton button:hover { background: #06cf9c !important; }
    
    .search-input input, .chat-input input {
        background: #fff !important; border: 1px solid #e0e0e0 !important;
        border-radius: 24px !important; padding: 10px 16px !important; font-size: 0.9rem !important;
    }
    
    [data-testid="stVerticalBlock"] { gap: 0 !important; }
    .st-emotion-cache-1cypcdb { background: white !important; }
</style>
""", unsafe_allow_html=True)

# ---------- HEADER BAR ----------
st.markdown('<div style="background:#00a884;padding:8px 16px;color:white;font-weight:500;font-size:1.1rem;text-align:center;">💬 GAIAchat</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1.2, 2.8])

# ===== LEFT PANEL =====
with col_left:
    search = st.text_input("", placeholder="🔍 Search or start new chat", key="chat_search", label_visibility="collapsed")
    
    if pending_requests:
        st.markdown('<div style="padding:10px 16px;background:white;font-weight:500;color:#111b21;border-bottom:1px solid #f0f0f0;">📨 Friend Requests</div>', unsafe_allow_html=True)
        for req in pending_requests:
            sender = all_users.get(req["sender_id"], {})
            name = f"{sender.get('first_name','')} {sender.get('last_name','')}".strip() or sender.get('email', 'Unknown')
            st.markdown(f'<div class="chat-item"><div class="avatar">{name[0].upper()}</div><div><div class="chat-name">{name}</div><div class="chat-subtitle">wants to connect</div></div></div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅", key=f"acc_{req['sender_id']}"):
                    st.session_state.accept_clicked = req["sender_id"]
                    st.rerun()
            with c2:
                if st.button("❌", key=f"dec_{req['sender_id']}"):
                    st.session_state.decline_clicked = req["sender_id"]
                    st.rerun()
    
    if search:
        s = search.lower().strip()
        st.markdown(f'<div style="padding:8px 16px;background:white;font-size:0.85rem;color:#667781;border-bottom:1px solid #f0f0f0;">Results for "{search}"</div>', unsafe_allow_html=True)
        found = False
        for uid, prof in all_users.items():
            if uid == user.id:
                continue
            name = f"{prof.get('first_name','')} {prof.get('last_name','')}".strip()
            email = prof.get('email', '') or ''
            phone = prof.get('phone', '') or ''
            searchable = f"{name} {email} {phone}".lower()
            if s in searchable:
                found = True
                display_name = name if name else (email or 'Unknown')
                is_online = uid in online_users
                is_friend = uid in friend_ids
                
                st.markdown(f'<div class="chat-item"><div class="avatar">{display_name[0].upper()}</div><div style="flex:1;"><div class="chat-name">{display_name}</div><div class="chat-subtitle">{"🟢 Online" if is_online else "Offline"}</div></div></div>', unsafe_allow_html=True)
                
                if is_friend:
                    if st.button("💬 Chat", key=f"chat_{uid}"):
                        room_id = get_or_create_dm(uid)
                        if room_id:
                            st.session_state.active_chat = room_id
                            st.session_state.active_chat_name = display_name
                            st.session_state.active_chat_other = uid
                            st.rerun()
                else:
                    if st.button("➕ Add", key=f"add_{uid}"):
                        try:
                            service.table("friendships").insert({"sender_id": user.id, "receiver_id": uid, "status": "accepted"}).execute()
                            room_id = get_or_create_dm(uid)
                            if room_id:
                                st.session_state.active_chat = room_id
                                st.session_state.active_chat_name = display_name
                                st.session_state.active_chat_other = uid
                                st.success(f"Connected with {display_name}!")
                                st.rerun()
                        except:
                            room_id = get_or_create_dm(uid)
                            if room_id:
                                st.session_state.active_chat = room_id
                                st.session_state.active_chat_name = display_name
                                st.session_state.active_chat_other = uid
                                st.rerun()
        if not found:
            st.info(f"No farmers found matching '{search}'.")
    else:
        if my_rooms:
            st.markdown('<div style="padding:10px 16px;background:white;font-weight:500;color:#111b21;border-bottom:1px solid #f0f0f0;">💬 Chats</div>', unsafe_allow_html=True)
            for room in my_rooms:
                is_online = room.get("other_id") in online_users
                is_active = st.session_state.active_chat == room["id"]
                active_class = " active" if is_active else ""
                st.markdown(f'<div class="chat-item{active_class}" onclick=""><div class="avatar">{room["name"][0].upper()}</div><div style="flex:1;"><div class="chat-name">{room["name"]}</div><div class="chat-subtitle">{"🟢 Online" if is_online else "Offline"}</div></div></div>', unsafe_allow_html=True)
                if st.button("💬", key=f"open_{room['id']}"):
                    st.session_state.active_chat = room["id"]
                    st.session_state.active_chat_name = room["name"]
                    st.session_state.active_chat_other = room.get("other_id")
                    st.rerun()
        else:
            st.markdown('<div style="padding:40px;text-align:center;color:#667781;">Search for a farmer to start chatting</div>', unsafe_allow_html=True)

# ===== RIGHT PANEL =====
with col_right:
    if st.session_state.active_chat:
        room_id = st.session_state.active_chat
        name = st.session_state.active_chat_name
        other_id = st.session_state.active_chat_other
        is_online = other_id in online_users if other_id else False
        
        st.markdown(f'<div class="chat-header"><div class="avatar">{name[0].upper()}</div><div><strong style="color:#111b21;">{name}</strong><br><span style="font-size:0.8rem;color:#667781;">{"🟢 online" if is_online else "offline"}</span></div></div>', unsafe_allow_html=True)
        
        try:
            msgs = db.table("messages").select("*").eq("room_id", room_id).order("created_at").execute()
            msgs_data = msgs.data if msgs.data else []
        except:
            msgs_data = []
        
        st.markdown('<div style="height:55vh;overflow-y:auto;padding:10px;background:#e5ddd5;">', unsafe_allow_html=True)
        for msg in msgs_data:
            is_mine = msg["sender_id"] == user.id
            bubble_class = "message-mine" if is_mine else "message-other"
            time_str = msg.get("created_at", "")[11:16] if msg.get("created_at") else ""
            align = "text-align:right;" if is_mine else "text-align:left;"
            st.markdown(f'<div style="{align}"><div class="message-bubble {bubble_class}">{msg.get("content","")}<span class="message-time">{time_str}</span></div></div><div style="clear:both;"></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div style="background:#f0f2f5;padding:10px 16px;display:flex;align-items:center;gap:8px;">', unsafe_allow_html=True)
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
        st.markdown(f'<div style="display:flex;align-items:center;justify-content:center;height:80vh;flex-direction:column;background:#f0f2f5;border-left:1px solid #e0e0e0;"><div style="font-size:5rem;margin-bottom:20px;">💬</div><h2 style="color:#41525d;font-weight:300;">GAIAchat</h2><p style="color:#667781;max-width:400px;text-align:center;">Connect with farmers across Africa.<br>Search by name or phone number to start chatting.</p></div>', unsafe_allow_html=True)

# ---------- NAVIGATION ----------
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
