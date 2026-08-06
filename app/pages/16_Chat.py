import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import uuid

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

# Mark online
try:
    service.table("user_status").upsert({"user_id": user.id, "is_online": True, "last_seen": datetime.now().isoformat()}).execute()
except:
    pass

# Get current user profile
my_profile = None
try:
    res = db.table("user_profiles").select("*").eq("user_id", user.id).execute()
    my_profile = res.data[0] if res.data else None
except:
    pass

# ---------- STYLES ----------
st.markdown("""
<style>
    .stApp { background: #f0f2f5; }
    header, footer { visibility: hidden; }
    .community-container { display: flex; height: 85vh; gap: 1px; }
    
    /* LEFT SIDEBAR */
    .left-sidebar { width: 300px; background: #fff; overflow-y: auto; padding: 10px; border-right: 1px solid #e0e0e0; }
    .left-sidebar h3 { font-size: 1.1rem; margin-bottom: 10px; }
    
    /* MAIN CHAT */
    .main-chat { flex: 1; background: #fff; display: flex; flex-direction: column; }
    .chat-header { padding: 12px 15px; border-bottom: 1px solid #e0e0e0; font-weight: 700; background: #f8f9fa; display: flex; align-items: center; gap: 10px; }
    .chat-messages { flex: 1; overflow-y: auto; padding: 15px; background: #e5ddd5; }
    .chat-input { padding: 10px 15px; border-top: 1px solid #e0e0e0; display: flex; gap: 10px; background: #f0f0f0; }
    
    /* RIGHT SIDEBAR */
    .right-sidebar { width: 280px; background: #fff; overflow-y: auto; padding: 10px; border-left: 1px solid #e0e0e0; }
    
    /* MESSAGE BUBBLES */
    .msg-bubble {
        max-width: 70%; padding: 8px 12px; border-radius: 8px; margin: 2px 0;
        word-wrap: break-word; position: relative; font-size: 0.9rem; line-height: 1.4;
    }
    .msg-sent { background: #d4f1c4; margin-left: auto; }
    .msg-received { background: #fff; }
    .msg-time { font-size: 0.65rem; color: #888; margin-top: 2px; text-align: right; }
    
    /* USER LIST ITEMS */
    .user-item {
        padding: 10px; cursor: pointer; border-radius: 10px; margin: 2px 0;
        display: flex; align-items: center; gap: 10px; transition: background 0.2s;
    }
    .user-item:hover { background: #f0f2f5; }
    .user-item.active { background: #e3f2fd; }
    
    /* AVATARS */
    .avatar-sm { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; background: #e0e0e0; }
    .avatar-lg { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; background: #e0e0e0; }
    
    /* ONLINE DOT */
    .online-dot { width: 10px; height: 10px; border-radius: 50%; background: #4caf50; display: inline-block; position: absolute; bottom: 2px; right: 2px; border: 2px solid #fff; }
    .offline-dot { width: 10px; height: 10px; border-radius: 50%; background: #bbb; display: inline-block; position: absolute; bottom: 2px; right: 2px; border: 2px solid #fff; }
    
    /* BUTTONS */
    .btn-friend { padding: 5px 15px; border-radius: 20px; border: 1px solid #2e7d32; background: #fff; color: #2e7d32; cursor: pointer; font-weight: 600; font-size: 0.8rem; }
    .btn-friend:hover { background: #e8f5e9; }
    .btn-friend.active { background: #2e7d32; color: #fff; }
    
    /* POSTS */
    .post-card { background: #fff; border-radius: 10px; padding: 15px; margin: 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .post-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
    .post-image { max-width: 100%; border-radius: 10px; margin: 10px 0; }
    .post-actions { display: flex; gap: 20px; margin-top: 10px; color: #666; font-size: 0.9rem; }
    
    /* SEARCH */
    .search-input { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 20px; margin-bottom: 10px; font-size: 0.9rem; }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 5px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 15px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ---------- FETCH DATA ----------
# All users
all_users = {}
try:
    res = service.table("user_profiles").select("*").execute()
    if res.data:
        for u in res.data:
            all_users[u["user_id"]] = u
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
friends = []
friend_ids = set()
try:
    res = db.table("friendships").select("*").eq("status", "accepted").or_(f"sender_id.eq.{user.id},receiver_id.eq.{user.id}").execute()
    if res.data:
        for f in res.data:
            friend_id = f["sender_id"] if f["receiver_id"] == user.id else f["receiver_id"]
            friends.append(friend_id)
            friend_ids.add(friend_id)
except:
    pass

# Friend requests received
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
                        name = f"{prof.get('first_name','')} {prof.get('last_name','')}"
                    else:
                        name = "Unknown"
                    my_rooms.append({"id": room["id"], "name": name, "other_id": other_id, "is_group": False})
except:
    pass

# ---------- INITIALIZE STATE ----------
if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "active_chat_name" not in st.session_state:
    st.session_state.active_chat_name = ""
if "community_tab" not in st.session_state:
    st.session_state.community_tab = "Chats"

# ---------- LAYOUT ----------
tabs = st.tabs(["💬 Chats", "👥 Friends", "📝 Posts"])

# ==================== TAB 1: CHATS ====================
with tabs[0]:
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        st.markdown("### 💬 Chats")
        search = st.text_input("", placeholder="🔍 Search...", key="chat_search")
        
        for room in my_rooms:
            is_online = room.get("other_id") in online_users if not room["is_group"] else False
            dot = "🟢" if is_online else ""
            active = "active" if st.session_state.active_chat == room["id"] else ""
            
            if st.button(f"{dot} {room['name']}", key=f"room_{room['id']}", use_container_width=True):
                st.session_state.active_chat = room["id"]
                st.session_state.active_chat_name = room["name"]
                st.rerun()
    
    with col2:
        if st.session_state.active_chat:
            room_id = st.session_state.active_chat
            
            # Header
            st.markdown(f'<div class="chat-header">💬 {st.session_state.active_chat_name}</div>', unsafe_allow_html=True)
            
            # Messages
            try:
                msgs = db.table("messages").select("*").eq("room_id", room_id).order("created_at").execute()
            except:
                msgs = type('obj', (object,), {'data': []})()
            
            chat_html = '<div class="chat-messages">'
            if msgs.data:
                for msg in msgs.data:
                    is_mine = msg["sender_id"] == user.id
                    bubble = "msg-sent" if is_mine else "msg-received"
                    time_str = msg["created_at"][11:16] if msg.get("created_at") else ""
                    
                    chat_html += f'<div class="msg-bubble {bubble}">'
                    if msg.get("content"):
                        chat_html += msg["content"]
                    if msg.get("attachment_url"):
                        if msg.get("attachment_type") == "image":
                            chat_html += f'<br><img src="{msg["attachment_url"]}" style="max-width:200px;border-radius:10px;">'
                        else:
                            chat_html += f'<br><a href="{msg["attachment_url"]}">📎 Attachment</a>'
                    chat_html += f'<div class="msg-time">{time_str}</div>'
                    chat_html += '</div>'
            chat_html += '</div>'
            st.markdown(chat_html, unsafe_allow_html=True)
            
            # Input
            ca, cb, cc = st.columns([5, 1, 1])
            with ca:
                msg_text = st.text_input("", placeholder="Type a message...", key=f"msg_{room_id}", label_visibility="collapsed")
            with cb:
                uploaded_file = st.file_uploader("📎", type=["jpg","jpeg","png","pdf"], label_visibility="collapsed", key=f"file_{room_id}")
            with cc:
                if st.button("📤", key=f"send_{room_id}", use_container_width=True):
                    attachment_url = None
                    attachment_type = None
                    
                    if uploaded_file:
                        ext = uploaded_file.name.split('.')[-1].lower()
                        attachment_type = "image" if ext in ['jpg','jpeg','png'] else "document"
                        path = f"chat/{room_id}/{uuid.uuid4().hex[:8]}_{uploaded_file.name}"
                        try:
                            service.storage.from_("message_attachment").upload(path, uploaded_file.getvalue())
                            attachment_url = service.storage.from_("message_attachment").get_public_url(path)
                        except:
                            pass
                    
                    if msg_text or attachment_url:
                        try:
                            service.table("messages").insert({
                                "room_id": room_id, "sender_id": user.id,
                                "content": msg_text or "", "attachment_url": attachment_url,
                                "attachment_type": attachment_type
                            }).execute()
                            st.rerun()
                        except:
                            st.error("Message failed. Try again.")
        else:
            st.markdown("""
            <div style="display:flex;align-items:center;justify-content:center;height:100%;color:#888;">
                <div style="text-align:center;">
                    <h2>💬 Welcome to GAIA Community</h2>
                    <p>Select a chat from the left or search for a farmer to start messaging</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("### 🔍 Find Farmers")
        search2 = st.text_input("", placeholder="Search by name or location...", key="search_farmers")
        
        if search2:
            for uid, prof in all_users.items():
                if uid == user.id:
                    continue
                full = f"{prof.get('first_name','')} {prof.get('last_name','')} {prof.get('state_city','')}".lower()
                if search2.lower() in full:
                    is_online = uid in online_users
                    dot = "🟢" if is_online else "⚫"
                    is_friend = uid in friend_ids
                    
                    with st.container():
                        st.markdown(f"**{dot} {prof.get('first_name','')} {prof.get('last_name','')}**")
                        st.caption(f"{prof.get('state_city','')} · {prof.get('country','')}")
                        
                        c1, c2 = st.columns(2)
                        if is_friend:
                            # Start chat
                            if c1.button("💬 Chat", key=f"chat_{uid}"):
                                existing = None
                                for room in my_rooms:
                                    if room.get("other_id") == uid:
                                        existing = room["id"]
                                        break
                                if existing:
                                    st.session_state.active_chat = existing
                                    st.session_state.active_chat_name = full
                                else:
                                    try:
                                        new_room = service.table("chat_rooms").insert({"is_group": False, "created_by": user.id}).execute()
                                        rid = new_room.data[0]["id"]
                                        service.table("chat_members").insert([{"room_id": rid, "user_id": user.id}, {"room_id": rid, "user_id": uid}]).execute()
                                        st.session_state.active_chat = rid
                                        st.session_state.active_chat_name = f"{prof.get('first_name','')} {prof.get('last_name','')}"
                                    except:
                                        pass
                                st.rerun()
                        else:
                            if c1.button("➕ Add Friend", key=f"add_{uid}"):
                                try:
                                    service.table("friendships").insert({"sender_id": user.id, "receiver_id": uid, "status": "pending"}).execute()
                                    st.success("Friend request sent!")
                                    st.rerun()
                                except:
                                    st.warning("Already sent or error.")
                        
                        st.markdown("---")

# ==================== TAB 2: FRIENDS ====================
with tabs[1]:
    st.markdown("### 👥 My Friends")
    
    # Friend requests
    if pending_requests:
        st.markdown("**Friend Requests:**")
        for req in pending_requests:
            sender_id = req["sender_id"]
            sender = all_users.get(sender_id, {})
            name = f"{sender.get('first_name','')} {sender.get('last_name','')}"
            
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.write(f"**{name}** wants to be your friend")
            with c2:
                if st.button("✅ Accept", key=f"accept_{sender_id}"):
                    service.table("friendships").update({"status": "accepted"}).eq("sender_id", sender_id).eq("receiver_id", user.id).execute()
                    st.rerun()
            with c3:
                if st.button("❌ Decline", key=f"decline_{sender_id}"):
                    service.table("friendships").delete().eq("sender_id", sender_id).eq("receiver_id", user.id).execute()
                    st.rerun()
        st.markdown("---")
    
    # Friend list
    if friends:
        for fid in friends:
            prof = all_users.get(fid, {})
            is_online = fid in online_users
            dot = "🟢" if is_online else "⚫"
            name = f"{prof.get('first_name','')} {prof.get('last_name','')}"
            pic = prof.get('profile_pic_url', '')
            
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                avatar_html = f'<img src="{pic}" class="avatar-sm">' if pic else f'<div class="avatar-sm" style="display:inline-flex;align-items:center;justify-content:center;font-weight:700;color:#666;">{name[0].upper()}</div>'
                st.markdown(f'{avatar_html} <span style="position:relative;display:inline-block;"><span class="{"online-dot" if is_online else "offline-dot"}"></span></span> **{name}**', unsafe_allow_html=True)
            with c2:
                if st.button("💬 Chat", key=f"friend_chat_{fid}"):
                    existing = None
                    for room in my_rooms:
                        if room.get("other_id") == fid:
                            existing = room["id"]
                            break
                    if existing:
                        st.session_state.active_chat = existing
                        st.session_state.active_chat_name = name
                        st.rerun()
            with c3:
                if st.button("❌ Remove", key=f"remove_{fid}"):
                    service.table("friendships").delete().or_(f"sender_id.eq.{user.id},receiver_id.eq.{user.id}").or_(f"sender_id.eq.{fid},receiver_id.eq.{fid}").execute()
                    st.rerun()
    else:
        st.info("No friends yet. Search for farmers in the Chats tab and add them!")

# ==================== TAB 3: POSTS ====================
with tabs[2]:
    st.markdown("### 📝 Community Posts")
    
    # Create post
    with st.form("new_post"):
        post_content = st.text_area("Share something with the community...", max_chars=500)
        post_image = st.file_uploader("Add photo", type=["jpg","jpeg","png"])
        if st.form_submit_button("Post"):
            img_url = None
            if post_image:
                path = f"posts/{uuid.uuid4().hex[:8]}_{post_image.name}"
                try:
                    service.storage.from_("message_attachment").upload(path, post_image.getvalue())
                    img_url = service.storage.from_("message_attachment").get_public_url(path)
                except:
                    pass
            if post_content or img_url:
                service.table("posts").insert({"user_id": user.id, "content": post_content, "image_url": img_url}).execute()
                st.rerun()
    
    # Show posts
    try:
        posts = service.table("posts").select("*").order("created_at", desc=True).limit(20).execute()
        if posts.data:
            for post in posts.data:
                author = all_users.get(post["user_id"], {})
                author_name = f"{author.get('first_name','')} {author.get('last_name','')}"
                author_pic = author.get('profile_pic_url', '')
                
                # Likes count
                likes_res = db.table("post_likes").select("*").eq("post_id", post["id"]).execute()
                likes_count = len(likes_res.data) if likes_res.data else 0
                
                # Comments count
                comments_res = db.table("post_comments").select("*").eq("post_id", post["id"]).execute()
                comments_count = len(comments_res.data) if comments_res.data else 0
                
                st.markdown(f"""
                <div class="post-card">
                    <div class="post-header">
                        <img src="{author_pic}" class="avatar-sm" onerror="this.style.display='none'">
                        <div>
                            <strong>{author_name}</strong>
                            <div style="font-size:0.7rem;color:#888;">{post['created_at'][:16] if post.get('created_at') else ''}</div>
                        </div>
                    </div>
                    <p>{post.get('content','')}</p>
                """, unsafe_allow_html=True)
                
                if post.get('image_url'):
                    st.image(post['image_url'], use_container_width=True)
                
                c1, c2 = st.columns([1, 4])
                with c1:
                    if st.button(f"❤️ {likes_count}", key=f"like_{post['id']}"):
                        try:
                            service.table("post_likes").upsert({"post_id": post["id"], "user_id": user.id}).execute()
                            st.rerun()
                        except:
                            pass
                with c2:
                    if st.button(f"💬 {comments_count} Comments", key=f"comments_{post['id']}"):
                        st.session_state[f"show_comments_{post['id']}"] = not st.session_state.get(f"show_comments_{post['id']}", False)
                
                # Show comments
                if st.session_state.get(f"show_comments_{post['id']}", False):
                    if comments_res.data:
                        for comment in comments_res.data:
                            commenter = all_users.get(comment["user_id"], {})
                            cname = f"{commenter.get('first_name','')} {commenter.get('last_name','')}"
                            st.markdown(f"**{cname}**: {comment.get('content','')}")
                    
                    with st.form(key=f"comment_form_{post['id']}"):
                        comment_text = st.text_input("Add a comment...")
                        if st.form_submit_button("Comment"):
                            service.table("post_comments").insert({"post_id": post["id"], "user_id": user.id, "content": comment_text}).execute()
                            st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("---")
    except:
        st.info("No posts yet. Be the first to share!")

# ---------- NAVIGATION ----------
st.markdown("---")
cols = st.columns(6)
cols[0].page_link("pages/1_Dashboard.py", label="Dashboard")
cols[1].page_link("pages/2_Crops.py", label="Crops")
cols[2].page_link("pages/3_Pests.py", label="Pests")
cols[3].page_link("pages/4_Soil.py", label="Soil")
cols[4].page_link("pages/5_Livestock.py", label="Livestock")
cols[5].page_link("pages/9_Buy_Scans.py", label="Buy Scans")
