
import streamlit as st
import streamlit.components.v1 as components
import uuid
import datetime
import os
import sys
from supabase import create_client

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

st.set_page_config(page_title="GAIA Meet", page_icon="🎥", layout="wide")

# ============================================
# SESSION STATE
# ============================================
if "meet_room_id" not in st.session_state:
    st.session_state.meet_room_id = None
if "meet_role" not in st.session_state:
    st.session_state.meet_role = None
if "meet_participants" not in st.session_state:
    st.session_state.meet_participants = []
if "meet_start_time" not in st.session_state:
    st.session_state.meet_start_time = None

# ============================================
# SUPABASE
# ============================================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["service_key"]
    )

# ============================================
# FUNCTIONS
# ============================================
def generate_room_id():
    return f"gaia-meet-{uuid.uuid4().hex[:10]}"

def get_user_display_name():
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user.email.split('@')[0].title()
    return "Guest"

def create_meeting(user_id, title, crop_focus=None):
    db = get_supabase()
    room_id = generate_room_id()
    try:
        db.table("gaia_meetings").insert({
            "room_id": room_id,
            "host_id": user_id,
            "title": title,
            "crop_focus": crop_focus,
            "status": "active",
            "created_at": datetime.datetime.now().isoformat()
        }).execute()
        return room_id, None
    except Exception as e:
        return None, str(e)

def get_meeting_info(room_id):
    db = get_supabase()
    try:
        res = db.table("gaia_meetings").select("*").eq("room_id", room_id).execute()
        return res.data[0] if res.data else None
    except:
        return None

def get_meeting_chat(room_id):
    db = get_supabase()
    try:
        res = db.table("meeting_chat").select("*").eq("room_id", room_id).order("created_at").execute()
        return res.data if res.data else []
    except:
        return []

def send_chat_message(room_id, user_id, message):
    db = get_supabase()
    try:
        db.table("meeting_chat").insert({
            "room_id": room_id,
            "user_id": user_id,
            "message": message,
            "created_at": datetime.datetime.now().isoformat()
        }).execute()
        return True
    except:
        return False

def get_user_name_by_id(user_id):
    db = get_supabase()
    try:
        res = db.table("user_profiles").select("first_name,last_name").eq("user_id", user_id).execute()
        if res.data:
            p = res.data[0]
            name = f"{p.get('first_name','')} {p.get('last_name','')}".strip()
            if name:
                return name
    except:
        pass
    return f"Farmer-{str(user_id)[:6]}"

# ============================================
# ZOOM-STYLE CSS
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .stApp {
        background: #0e1117;
        color: #e0e0e0;
    }
    
    header, footer { visibility: hidden; }
    
    /* Hide Streamlit defaults */
    .stTextInput input {
        background: #1e2733 !important;
        border: none !important;
        color: #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }
    
    .stButton button {
        background: #2d8cff !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    
    .stButton button:hover {
        background: #1a75ff !important;
        transform: translateY(-1px);
    }
    
    /* Meeting title bar */
    .meeting-top-bar {
        background: #161b22;
        border-bottom: 1px solid #252b36;
        padding: 12px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: sticky;
        top: 0;
        z-index: 100;
    }
    
    .meeting-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #fff;
        margin: 0;
    }
    
    .meeting-room-id {
        color: #8b949e;
        font-size: 0.85rem;
        background: #1e2733;
        padding: 5px 15px;
        border-radius: 8px;
        cursor: pointer;
    }
    
    .meeting-timer {
        color: #8b949e;
        font-size: 0.9rem;
        background: #1e2733;
        padding: 5px 15px;
        border-radius: 8px;
    }
    
    /* Video grid */
    .video-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 10px;
        padding: 20px;
        max-width: 900px;
        margin: 0 auto;
    }
    
    .video-tile {
        background: #1e2733;
        border-radius: 12px;
        overflow: hidden;
        position: relative;
        aspect-ratio: 16/9;
    }
    
    .video-tile video {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    .video-tile .name-tag {
        position: absolute;
        bottom: 10px;
        left: 10px;
        background: rgba(0,0,0,0.7);
        color: #fff;
        padding: 4px 14px;
        border-radius: 6px;
        font-size: 0.8rem;
    }
    
    /* Bottom control bar */
    .control-bar {
        background: #161b22;
        border-top: 1px solid #252b36;
        padding: 14px 24px;
        display: flex;
        justify-content: center;
        gap: 15px;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 100;
    }
    
    .control-button {
        background: #252b36;
        border: none;
        color: #e0e0e0;
        border-radius: 50px;
        padding: 10px 22px;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.85rem;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .control-button:hover {
        background: #2d3644;
    }
    
    .control-button.active {
        background: #2d8cff;
        color: #fff;
    }
    
    .control-button.end-call {
        background: #dc3545;
        color: #fff;
    }
    
    .control-button.end-call:hover {
        background: #c82333;
    }
    
    /* Chat panel */
    .chat-panel {
        background: #161b22;
        border-left: 1px solid #252b36;
        border-radius: 12px;
        padding: 15px;
        height: 500px;
        display: flex;
        flex-direction: column;
    }
    
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 10px;
        margin-bottom: 10px;
    }
    
    .chat-message {
        margin: 8px 0;
        padding: 8px 12px;
        border-radius: 8px;
        max-width: 85%;
        word-wrap: break-word;
        font-size: 0.9rem;
    }
    
    .chat-message.me {
        background: #1a3a5c;
        color: #7cb8ff;
        margin-left: auto;
    }
    
    .chat-message.other {
        background: #252b36;
        color: #e0e0e0;
    }
    
    .chat-sender {
        font-size: 0.75rem;
        font-weight: 600;
        color: #8b949e;
        margin-bottom: 3px;
    }
    
    .chat-time {
        font-size: 0.7rem;
        color: #6b7280;
        margin-top: 3px;
    }
    
    /* Participant chips */
    .participant-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #1e2733;
        border-radius: 20px;
        padding: 5px 14px;
        margin: 4px;
        font-size: 0.8rem;
        color: #e0e0e0;
    }
    
    /* Meeting ID copy box */
    .copy-box {
        background: #1e2733;
        border: 1px solid #2d8cff;
        border-radius: 10px;
        padding: 10px 18px;
        text-align: center;
        color: #7cb8ff;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .copy-box:hover {
        background: #1a3a5c;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# AUTH CHECK
# ============================================
if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in to use GAIA Meet.")
    st.stop()

user = st.session_state.user
user_id = user.id
user_name = get_user_display_name()

# ============================================
# MAIN
# ============================================
if st.session_state.meet_room_id is None:
    # ========== JOIN/CREATE SCREEN ==========
    st.markdown('<div style="text-align:center;padding:60px 20px;">', unsafe_allow_html=True)
    st.markdown('<h1 style="font-size:2.5rem;font-weight:800;color:#fff;">🎥 GAIA Meet</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#8b949e;font-size:1.1rem;margin-bottom:40px;">Secure agricultural video conferencing</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="copy-box" style="margin-bottom:20px;">Start or join a meeting</div>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🎬 Start", "🔗 Join"])
        
        with tab1:
            meeting_title = st.text_input("Meeting Title", value=f"{user_name}'s Agri Clinic")
            crop_focus = st.selectbox("Crop Focus", 
                                     ["None", "Maize", "Rice", "Beans", "Tomato", "Pepper", "Cabbage", "Millet", "Soybean"])
            if st.button("🚀 Start Meeting", use_container_width=True, type="primary"):
                room_id, err = create_meeting(user_id, meeting_title, crop_focus if crop_focus != "None" else None)
                if room_id:
                    st.session_state.meet_room_id = room_id
                    st.session_state.meet_role = "host"
                    st.session_state.meet_participants = [user_id]
                    st.session_state.meet_start_time = datetime.datetime.now()
                    st.rerun()
                else:
                    st.error(f"Failed: {str(err)[:100]}")
        
        with tab2:
            join_id = st.text_input("Room ID", placeholder="gaia-meet-xxxx")
            if st.button("🔗 Join Meeting", use_container_width=True):
                meeting = get_meeting_info(join_id)
                if meeting:
                    st.session_state.meet_room_id = join_id
                    st.session_state.meet_role = "participant"
                    if user_id not in st.session_state.meet_participants:
                        st.session_state.meet_participants.append(user_id)
                    st.session_state.meet_start_time = datetime.datetime.now()
                    st.rerun()
                else:
                    st.error("Meeting not found.")
else:
    # ========== ACTIVE MEETING ==========
    room_id = st.session_state.meet_room_id
    meeting = get_meeting_info(room_id)
    
    # Top bar
    st.markdown(f"""
    <div class="meeting-top-bar">
        <div>
            <p class="meeting-title">{"🎥 " + meeting['title'] if meeting else "GAIA Meeting"}</p>
        </div>
        <div style="display:flex;gap:10px;align-items:center;">
            <span class="meeting-room-id">📋 {room_id}</span>
            <span class="meeting-timer">⏱ 00:00</span>
        </div>
        <div>
            <span style="color:#00c853;font-size:0.9rem;">● REC</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main layout
    video_col, chat_col = st.columns([2.2, 1])
    
    with video_col:
        # Video grid
        video_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    background: #0e1117;
                    margin: 0;
                    padding: 0;
                }}
                .video-grid {{
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: 10px;
                    padding: 15px;
                }}
                .video-tile {{
                    background: #1e2733;
                    border-radius: 12px;
                    overflow: hidden;
                    position: relative;
                    aspect-ratio: 16/9;
                }}
                .video-tile video {{
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }}
                .name-tag {{
                    position: absolute;
                    bottom: 10px;
                    left: 10px;
                    background: rgba(0,0,0,0.7);
                    color: #fff;
                    padding: 4px 14px;
                    border-radius: 6px;
                    font-size: 0.8rem;
                }}
                .controls {{
                    display: flex;
                    justify-content: center;
                    gap: 12px;
                    padding: 12px;
                    background: #161b22;
                    border-radius: 12px;
                    margin-top: 10px;
                }}
                .ctrl-btn {{
                    background: #252b36;
                    border: none;
                    color: #e0e0e0;
                    border-radius: 50px;
                    padding: 8px 18px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 0.85rem;
                    transition: all 0.2s;
                    font-family: 'Inter', sans-serif;
                }}
                .ctrl-btn:hover {{ background: #2d3644; }}
                .ctrl-btn.active {{ background: #2d8cff; color: #fff; }}
                .ctrl-btn.end {{ background: #dc3545; color: #fff; }}
                .ctrl-btn.end:hover {{ background: #c82333; }}
            </style>
        </head>
        <body>
            <div class="video-grid">
                <div class="video-tile">
                    <video id="localVideo" autoplay muted playsinline></video>
                    <div class="name-tag">You ({user_name})</div>
                </div>
            </div>
            <div class="controls">
                <button class="ctrl-btn" id="micBtn" onclick="toggleMic()">🎙️ Mute</button>
                <button class="ctrl-btn" id="camBtn" onclick="toggleCam()">📷 Camera</button>
                <button class="ctrl-btn" id="screenBtn" onclick="toggleScreen()">🖥️ Share Screen</button>
                <button class="ctrl-btn" id="chatBtn" onclick="toggleChat()">💬 Chat</button>
                <button class="ctrl-btn" id="recordBtn" onclick="toggleRecording()">⏺️ Record</button>
                <button class="ctrl-btn end" onclick="endCall()">📞 End</button>
            </div>
            <script>
                let localStream = null;
                let micEnabled = true;
                let camEnabled = true;
                let screenStream = null;
                let isRecording = false;
                
                async function startCamera() {{
                    try {{
                        localStream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                        document.getElementById('localVideo').srcObject = localStream;
                    }} catch (e) {{ console.error('Camera error:', e); }}
                }}
                
                function toggleMic() {{
                    if (localStream) {{
                        micEnabled = !micEnabled;
                        localStream.getAudioTracks().forEach(t => t.enabled = micEnabled);
                        document.getElementById('micBtn').textContent = micEnabled ? '🎙️ Mute' : '🔇 Unmute';
                        document.getElementById('micBtn').classList.toggle('active', !micEnabled);
                    }}
                }}
                
                function toggleCam() {{
                    if (localStream) {{
                        camEnabled = !camEnabled;
                        localStream.getVideoTracks().forEach(t => t.enabled = camEnabled);
                        document.getElementById('camBtn').textContent = camEnabled ? '📷 Camera' : '🚫 Camera Off';
                        document.getElementById('camBtn').classList.toggle('active', !camEnabled);
                    }}
                }}
                
                async function toggleScreen() {{
                    if (!screenStream) {{
                        try {{
                            screenStream = await navigator.mediaDevices.getDisplayMedia({{ video: true }});
                            document.getElementById('screenBtn').textContent = '🖥️ Stop Share';
                            document.getElementById('screenBtn').classList.add('active');
                        }} catch (e) {{ console.error('Screen error:', e); }}
                    }} else {{
                        screenStream.getTracks().forEach(t => t.stop());
                        screenStream = null;
                        document.getElementById('screenBtn').textContent = '🖥️ Share Screen';
                        document.getElementById('screenBtn').classList.remove('active');
                    }}
                }}
                
                function toggleChat() {{
                    document.getElementById('chatBtn').classList.toggle('active');
                }}
                
                function toggleRecording() {{
                    if (!isRecording) {{
                        isRecording = true;
                        document.getElementById('recordBtn').textContent = '⏺️ Recording...';
                        document.getElementById('recordBtn').classList.add('active');
                    }} else {{
                        isRecording = false;
                        document.getElementById('recordBtn').textContent = '⏺️ Record';
                        document.getElementById('recordBtn').classList.remove('active');
                    }}
                }}
                
                function endCall() {{
                    if (localStream) localStream.getTracks().forEach(t => t.stop());
                    if (screenStream) screenStream.getTracks().forEach(t => t.stop());
                    window.location.reload();
                }}
                
                startCamera();
            </script>
        </body>
        </html>
        """
        components.html(video_html, height=520)
        
        if st.button("🚪 Leave Meeting", use_container_width=True):
            st.session_state.meet_room_id = None
            st.session_state.meet_role = None
            st.session_state.meet_participants = []
            st.session_state.meet_start_time = None
            st.rerun()
    
    with chat_col:
        # Chat panel
        st.markdown("### 💬 Chat")
        
        chat_messages = get_meeting_chat(room_id)
        
        chat_parts = []
        for msg in chat_messages:
            sender_id = msg.get("user_id")
            sender_name = get_user_name_by_id(sender_id)
            is_me = (str(sender_id) == str(user_id))
            msg_class = "me" if is_me else "other"
            time_str = str(msg.get("created_at", ""))[11:16]
            message_text = msg.get("message", "")
            
            chat_parts.append(
                f'<div class="chat-message {msg_class}">'
                f'<div class="chat-sender">{"You" if is_me else sender_name}</div>'
                f'{message_text}'
                f'<div class="chat-time">{time_str}</div>'
                f'</div>'
            )
        
        chat_html = '<div class="chat-panel"><div class="chat-messages">' + ''.join(chat_parts) + '</div></div>'
        st.markdown(chat_html, unsafe_allow_html=True)
        
        with st.form("chat_form", clear_on_submit=True):
            chat_input = st.text_input("", placeholder="Type message...", label_visibility="collapsed")
            if st.form_submit_button("Send", use_container_width=True):
                if chat_input.strip():
                    send_chat_message(room_id, user_id, chat_input.strip())
                    st.rerun()
        
        # Participants
        st.markdown("### 👥 Participants")
        for pid in st.session_state.meet_participants:
            pname = get_user_name_by_id(pid)
            st.markdown(f'<span class="participant-chip">👤 {pname}</span>', unsafe_allow_html=True)
