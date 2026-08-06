import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import uuid

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA – Chat", page_icon="💬", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
db = get_supabase()
service = get_service()

# Mark user online
service.table("user_status").upsert({"user_id": user.id, "is_online": True, "last_seen": datetime.now().isoformat()}).execute()

# ---------- STYLES ----------
st.markdown("""
<style>
    .stApp { background: #f0f2f5; }
    header, footer { visibility: hidden; }
    .chat-container { display: flex; height: 85vh; gap: 1px; }
    .sidebar-chat { width: 320px; background: #fff; overflow-y: auto; padding: 10px; border-right: 1px solid #e0e0e0; }
    .main-chat { flex: 1; background: #fff; display: flex; flex-direction: column; }
    .chat-header { padding: 15px; border-bottom: 1px solid #e0e0e0; font-weight: 700; background: #f8f9fa; }
    .chat-messages { flex: 1; overflow-y: auto; padding: 15px; }
    .chat-input { padding: 15px; border-top: 1px solid #e0e0e0; display: flex; gap: 10px; background: #f8f9fa; }
    .msg-bubble {
        max-width: 70%; padding: 10px 15px; border-radius: 15px; margin: 5px 0;
        word-wrap: break-word; position: relative;
    }
    .msg-sent { background: #d4f1c4; margin-left: auto; border-bottom-right-radius: 5px; }
    .msg-received { background: #fff; border: 1px solid #e0e0e0; border-bottom-left-radius: 5px; }
    .msg-time { font-size: 0.7rem; color: #888; margin-top: 3px; }
    .user-item {
        padding: 10px; cursor: pointer; border-radius: 10px; margin: 3px 0;
        display: flex; align-items: center; gap: 10px; transition: background 0.2s;
    }
    .user-item:hover { background: #f0f2f5; }
    .user-item.active { background: #e3f2fd; }
    .online-dot { width: 10px; height: 10px; border-radius: 50%; background: #4caf50; display: inline-block; }
    .offline-dot { width: 10px; height: 10px; border-radius: 50%; background: #bbb; display: inline-block; }
    .avatar {
        width: 45px; height: 45px; border-radius: 50%; object-fit: cover;
        background: #e0e0e0; display: flex; align-items: center; justify-content: center;
        font-weight: 700; color: #666; font-size: 1.2rem;
    }
    .search-input { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 20px; margin-bottom: 10px; }
    .attachment-preview { max-width: 200px; border-radius: 10px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

# ---------- INITIALIZE STATE ----------
if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "active_chat_name" not in st.session_state:
    st.session_state.active_chat_name = ""

# ---------- FETCH DATA ----------
# Get all verified users (for search)
all_users = service.table("user_profiles").select("user_id,first_name,last_name,country,state_city").execute()
user_map = {}
if all_users.data:
    for u in all_users.data:
        user_map[u["user_id"]] = u

# Get online statuses
statuses = service.table("user_status").select("*").execute()
online_users = set()
if statuses.data:
    for s in statuses.data:
        if s.get("is_online"):
            online_users.add(s["user_id"])

# Get user's chat rooms
my_rooms = db.table("chat_members").select("room_id").eq("user_id", user.id).execute()
room_ids = [r["room_id"] for r in my_rooms.data] if my_rooms.data else []

# Get room details
rooms = []
if room_ids:
    room_data = service.table("chat_rooms").select("*").in_("id", room_ids).execute()
    if room_data.data:
        rooms = room_data.data

# Build room list with names
room_list = []
for room in rooms:
    if room["is_group"]:
        room_list.append({"id": room["id"], "name": room["name"], "is_group": True})
    else:
        # Find the other user
        members = db.table("chat_members").select("user_id").eq("room_id", room["id"]).execute()
        other_id = None
        if members.data:
            for m in members.data:
                if m["user_id"] != user.id:
                    other_id = m["user_id"]
                    break
        if other_id and other_id in user_map:
            name = f"{user_map[other_id].get('first_name','')} {user_map[other_id].get('last_name','')}"
        else:
            name = "Unknown User"
        room_list.append({"id": room["id"], "name": name, "other_id": other_id, "is_group": False})

# ---------- SIDEBAR ----------
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("### 💬 Chats")
    
    # Search users
    search = st.text_input("", placeholder="🔍 Search farmers...", key="search_users")
    
    if search:
        search_results = []
        for uid, prof in user_map.items():
            if uid == user.id:
                continue
            full_name = f"{prof.get('first_name','')} {prof.get('last_name','')}".lower()
            if search.lower() in full_name or search.lower() in prof.get('state_city','').lower():
                search_results.append((uid, prof))
        
        st.markdown("**Search Results:**")
        for uid, prof in search_results[:10]:
            full_name = f"{prof.get('first_name','')} {prof.get('last_name','')}"
            is_online = uid in online_users
            dot = "🟢" if is_online else "⚫"
            
            if st.button(f"{dot} {full_name}", key=f"search_{uid}", use_container_width=True):
                # Create or find 1-on-1 room
                existing = db.table("chat_members").select("room_id").eq("user_id", user.id).execute()
                my_room_ids = [r["room_id"] for r in existing.data] if existing.data else []
                
                found_room = None
                for rid in my_room_ids:
                    other_member = db.table("chat_members").select("user_id").eq("room_id", rid).neq("user_id", user.id).execute()
                    if other_member.data and other_member.data[0]["user_id"] == uid:
                        found_room = rid
                        break
                
                if found_room:
                    st.session_state.active_chat = found_room
                    st.session_state.active_chat_name = full_name
                else:
                    # Create new room
                    new_room = service.table("chat_rooms").insert({"is_group": False, "created_by": user.id}).execute()
                    if new_room.data:
                        rid = new_room.data[0]["id"]
                        service.table("chat_members").insert([
                            {"room_id": rid, "user_id": user.id},
                            {"room_id": rid, "user_id": uid}
                        ]).execute()
                        st.session_state.active_chat = rid
                        st.session_state.active_chat_name = full_name
                st.rerun()
    
    st.markdown("---")
    
    # Existing chats
    for room in room_list:
        is_online = room.get("other_id") in online_users if not room["is_group"] else False
        dot = "🟢" if is_online else "⚫"
        active = "active" if st.session_state.active_chat == room["id"] else ""
        
        if st.button(f"{dot} {room['name']}", key=f"room_{room['id']}", use_container_width=True):
            st.session_state.active_chat = room["id"]
            st.session_state.active_chat_name = room["name"]
            st.rerun()

# ---------- MAIN CHAT AREA ----------
with col2:
    if st.session_state.active_chat:
        room_id = st.session_state.active_chat
        
        # Chat header
        st.markdown(f"""
        <div class="chat-header">
            💬 {st.session_state.active_chat_name}
        </div>
        """, unsafe_allow_html=True)
        
        # Messages
        messages = db.table("messages").select("*").eq("room_id", room_id).order("created_at").execute()
        
        chat_html = '<div class="chat-messages">'
        if messages.data:
            for msg in messages.data:
                is_mine = msg["sender_id"] == user.id
                bubble_class = "msg-sent" if is_mine else "msg-received"
                sender_name = "You" if is_mine else st.session_state.active_chat_name
                time_str = msg["created_at"][11:16] if msg.get("created_at") else ""
                
                chat_html += f'<div class="msg-bubble {bubble_class}">'
                if not is_mine:
                    chat_html += f'<strong>{sender_name}</strong><br>'
                if msg.get("content"):
                    chat_html += f'{msg["content"]}<br>'
                if msg.get("attachment_url"):
                    if msg.get("attachment_type") == "image":
                        chat_html += f'<img src="{msg["attachment_url"]}" class="attachment-preview"><br>'
                    else:
                        chat_html += f'<a href="{msg["attachment_url"]}">📎 Attachment</a><br>'
                chat_html += f'<span class="msg-time">{time_str}</span>'
                chat_html += '</div>'
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # Input area
        col_a, col_b, col_c = st.columns([5, 1, 1])
        with col_a:
            msg_text = st.text_input("", placeholder="Type a message...", key=f"msg_{room_id}", label_visibility="collapsed")
        with col_b:
            uploaded_file = st.file_uploader("📎", type=["jpg","jpeg","png","pdf","doc","docx"], label_visibility="collapsed", key=f"file_{room_id}")
        with col_c:
            send_clicked = st.button("📤", use_container_width=True, key=f"send_{room_id}")
        
        if send_clicked:
            attachment_url = None
            attachment_type = None
            
            if uploaded_file:
                file_ext = uploaded_file.name.split('.')[-1].lower()
                if file_ext in ['jpg','jpeg','png']:
                    attachment_type = "image"
                elif file_ext == 'pdf':
                    attachment_type = "pdf"
                else:
                    attachment_type = "document"
                
                file_path = f"chat/{room_id}/{uuid.uuid4().hex[:8]}_{uploaded_file.name}"
                service.storage.from_("message_attachment").upload(file_path, uploaded_file.getvalue())
                attachment_url = service.storage.from_("message_attachment").get_public_url(file_path)
            
            if msg_text or attachment_url:
                service.table("messages").insert({
                    "room_id": room_id,
                    "sender_id": user.id,
                    "content": msg_text if msg_text else "",
                    "attachment_url": attachment_url,
                    "attachment_type": attachment_type
                }).execute()
                st.rerun()
    else:
        st.markdown("""
        <div style="display:flex;align-items:center;justify-content:center;height:100%;color:#888;">
            <div style="text-align:center;">
                <h2>💬 GAIA Chat</h2>
                <p>Search for a farmer on the left to start chatting</p>
                <p style="font-size:0.8rem;">Share photos, ask questions, help each other</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ---------- NAVIGATION ----------
st.markdown("---")
cols = st.columns(6)
cols[0].page_link("pages/1_Dashboard.py", label="Dashboard")
cols[1].page_link("pages/2_Crops.py", label="Crops")
cols[2].page_link("pages/3_Pests.py", label="Pests")
cols[3].page_link("pages/4_Soil.py", label="Soil")
cols[4].page_link("pages/5_Livestock.py", label="Livestock")
cols[5].page_link("pages/9_Buy_Scans.py", label="Buy Scans")
