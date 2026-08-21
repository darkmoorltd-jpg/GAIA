
import streamlit as st
import streamlit.components.v1 as components
import uuid
import datetime
import os
import sys
from supabase import create_client

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(page_title="GAIA Meet", page_icon="🎥", layout="wide")

# ============================================
# THEME TOGGLE
# ============================================
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=True, key="gaia_meet_theme")
theme = "dark" if dark_mode else "light"

# ============================================
# CUSTOM CSS
# ============================================
if theme == "dark":
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .stApp { background: linear-gradient(135deg, #0a0e1a, #1a1a2e, #16213e); color: #e0e0e0; }
        header, footer { visibility: hidden; }
        .meet-title {
            font-size: 3.5rem; font-weight: 900; text-align: center;
            background: linear-gradient(135deg, #00c853, #69f0ae, #00c853);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            animation: glow 2s ease-in-out infinite alternate;
            margin-bottom: 0.3rem;
        }
        @keyframes glow {
            from { text-shadow: 0 0 20px rgba(0,200,83,0.6); }
            to { text-shadow: 0 0 40px rgba(0,200,83,1), 0 0 80px rgba(0,200,83,0.8); }
        }
        .meet-subtitle { text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem; }
        .meet-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 1.5rem;
            backdrop-filter: blur(20px);
            margin-bottom: 1rem;
        }
        .room-id-box {
            background: rgba(0,200,83,0.1);
            border: 2px solid #00c853;
            border-radius: 15px;
            padding: 1rem;
            text-align: center;
            font-size: 1.1rem;
            color: #00c853;
        }
        .chat-container {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 15px;
            height: 400px;
            overflow-y: auto;
            padding: 15px;
            margin-bottom: 10px;
        }
        .chat-msg {
            padding: 10px 15px;
            border-radius: 12px;
            margin: 8px 0;
            max-width: 80%;
            word-wrap: break-word;
        }
        .chat-msg.me { background: #00c853; color: #000; margin-left: auto; border-bottom-right-radius: 4px; }
        .chat-msg.other { background: rgba(255,255,255,0.1); color: #e0e0e0; border-bottom-left-radius: 4px; }
        .chat-msg.system { background: rgba(255,152,0,0.2); color: #ff9800; text-align: center; margin: 8px auto; font-size: 0.85rem; }
        .chat-sender { font-size: 0.75rem; font-weight: 700; margin-bottom: 4px; opacity: 0.7; }
        .chat-time { font-size: 0.7rem; opacity: 0.5; margin-top: 4px; }
        .participant-badge {
            background: rgba(0,200,83,0.1);
            border: 1px solid #00c853;
            border-radius: 20px;
            padding: 5px 15px;
            margin: 5px;
            display: inline-block;
            font-size: 0.85rem;
            color: #00c853;
        }
        .stTextInput input {
            background: rgba(255,255,255,0.05) !important;
            border: 1px solid rgba(0,200,83,0.3) !important;
            color: #e0e0e0 !important;
            border-radius: 10px !important;
        }
        .stButton button {
            background: linear-gradient(135deg, #00c853, #4caf50) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
        }
        .stButton button:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,200,83,0.3); }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .stApp { background: linear-gradient(135deg, #f0fdf4, #e0f2fe); color: #0f172a; }
        header, footer { visibility: hidden; }
        .meet-title {
            font-size: 3.5rem; font-weight: 900; text-align: center;
            background: linear-gradient(135deg, #16a34a, #22c55e);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 0.3rem;
        }
        .meet-subtitle { text-align: center; color: #475569; font-size: 1.1rem; margin-bottom: 2rem; }
        .meet-card {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 20px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }
        .room-id-box {
            background: #f0fdf4;
            border: 2px solid #16a34a;
            border-radius: 15px;
            padding: 1rem;
            text-align: center;
            font-size: 1.1rem;
            color: #16a34a;
        }
        .chat-container {
            background: #f8fafc;
            border: 1px solid #e0e0e0;
            border-radius: 15px;
            height: 400px;
            overflow-y: auto;
            padding: 15px;
            margin-bottom: 10px;
        }
        .chat-msg {
            padding: 10px 15px;
            border-radius: 12px;
            margin: 8px 0;
            max-width: 80%;
            word-wrap: break-word;
        }
        .chat-msg.me { background: #16a34a; color: #fff; margin-left: auto; border-bottom-right-radius: 4px; }
        .chat-msg.other { background: #e2e8f0; color: #0f172a; border-bottom-left-radius: 4px; }
        .chat-msg.system { background: #fef3c7; color: #b45309; text-align: center; margin: 8px auto; font-size: 0.85rem; }
        .chat-sender { font-size: 0.75rem; font-weight: 700; margin-bottom: 4px; opacity: 0.7; }
        .chat-time { font-size: 0.7rem; opacity: 0.5; margin-top: 4px; }
        .participant-badge {
            background: #f0fdf4;
            border: 1px solid #16a34a;
            border-radius: 20px;
            padding: 5px 15px;
            margin: 5px;
            display: inline-block;
            font-size: 0.85rem;
            color: #16a34a;
        }
        .stTextInput input {
            background: #fff !important;
            border: 1px solid #e0e0e0 !important;
            color: #0f172a !important;
            border-radius: 10px !important;
        }
        .stButton button {
            background: linear-gradient(135deg, #16a34a, #22c55e) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# SESSION STATE
# ============================================
if "meet_room_id" not in st.session_state:
    st.session_state.meet_room_id = None
if "meet_role" not in st.session_state:
    st.session_state.meet_role = None
if "meet_participants" not in st.session_state:
    st.session_state.meet_participants = []
if "chat_refresh" not in st.session_state:
    st.session_state.chat_refresh = 0

# ============================================
# SUPABASE CLIENT
# ============================================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["service_key"]
    )

# ============================================
# MEETING FUNCTIONS
# ============================================
def generate_room_id():
    return f"gaia-meet-{uuid.uuid4().hex[:10]}"

def get_user_display_name():
    if "user" in st.session_state and st.session_state.user:
        email = st.session_state.user.email
        return email.split('@')[0].title()
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
    """Fetch all chat messages for a room."""
    db = get_supabase()
    try:
        res = db.table("meeting_chat").select("*").eq("room_id", room_id).order("created_at").execute()
        return res.data if res.data else []
    except:
        return []

def send_chat_message(room_id, user_id, message):
    """Send a chat message."""
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
    """Get display name from user ID."""
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
# HEADER
# ============================================
st.markdown('<div class="meet-title">🎥 GAIA Meet</div>', unsafe_allow_html=True)
st.markdown('<div class="meet-subtitle">Your own private agricultural video conferencing platform</div>', unsafe_allow_html=True)

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
# MAIN LAYOUT
# ============================================
if st.session_state.meet_room_id is None:
    # ========== CREATE OR JOIN ==========
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="meet-card">', unsafe_allow_html=True)
        st.subheader("🎬 Start New Meeting")
        meeting_title = st.text_input("Meeting Title", value=f"{user_name}'s Agri Clinic")
        crop_focus = st.selectbox("Crop Focus (optional)", 
                                 ["None", "Maize", "Rice", "Beans", "Tomato", "Pepper", "Cabbage", "Millet", "Soybean"])
        if st.button("🚀 Start Meeting", use_container_width=True, type="primary"):
            room_id, err = create_meeting(user_id, meeting_title, crop_focus if crop_focus != "None" else None)
            if room_id:
                st.session_state.meet_room_id = room_id
                st.session_state.meet_role = "host"
                st.session_state.meet_participants = [user_id]
                st.success(f"Meeting created! Room ID: {room_id}")
                st.rerun()
            else:
                st.error(f"Failed: {str(err)[:100]}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="meet-card">', unsafe_allow_html=True)
        st.subheader("🔗 Join Existing Meeting")
        join_id = st.text_input("Enter Room ID")
        if st.button("🔗 Join Meeting", use_container_width=True):
            meeting = get_meeting_info(join_id)
            if meeting:
                st.session_state.meet_room_id = join_id
                st.session_state.meet_role = "participant"
                if user_id not in st.session_state.meet_participants:
                    st.session_state.meet_participants.append(user_id)
                st.success("Joined meeting!")
                st.rerun()
            else:
                st.error("Meeting not found. Check the Room ID.")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    # ========== ACTIVE MEETING ==========
    room_id = st.session_state.meet_room_id
    meeting = get_meeting_info(room_id)
    
    # Meeting info bar
    st.markdown(f"""
    <div class="room-id-box">
        <strong>Room ID:</strong> {room_id}
        <br><span style="font-size:0.85rem;">Share this link: https://gaiagpt.streamlit.app/~/23_GAIA_Meet?room={room_id}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # ========== TWO COLUMN LAYOUT ==========
    video_col, chat_col = st.columns([2, 1])
    
    with video_col:
        st.markdown("### 📹 Video")
        
        video_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .video-card {{
                    background: #000;
                    border-radius: 15px;
                    overflow: hidden;
                    aspect-ratio: 16/9;
                    position: relative;
                }}
                .video-card video {{
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }}
                .participant-name {{
                    position: absolute;
                    bottom: 10px;
                    left: 10px;
                    background: rgba(0,0,0,0.7);
                    color: #fff;
                    padding: 4px 12px;
                    border-radius: 8px;
                    font-size: 0.85rem;
                }}
                .controls {{
                    display: flex;
                    justify-content: center;
                    gap: 12px;
                    padding: 15px;
                    flex-wrap: wrap;
                }}
                .control-btn {{
                    background: rgba(255,255,255,0.1);
                    border: 1px solid #00c853;
                    color: #00c853;
                    border-radius: 50px;
                    padding: 8px 20px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 0.85rem;
                    transition: all 0.3s;
                }}
                .control-btn:hover {{ background: rgba(0,200,83,0.2); }}
                .control-btn.end {{
                    background: #ef4444;
                    border-color: #ef4444;
                    color: #fff;
                }}
            </style>
        </head>
        <body>
            <div class="video-card">
                <video id="localVideo" autoplay muted playsinline></video>
                <div class="participant-name">You ({user_name})</div>
            </div>
            <div class="controls">
                <button class="control-btn" id="micBtn" onclick="toggleMic()">🎙️ Mute</button>
                <button class="control-btn" id="camBtn" onclick="toggleCam()">📷 Camera</button>
                <button class="control-btn" id="screenBtn" onclick="toggleScreen()">🖥️ Share</button>
                <button class="control-btn end" onclick="endCall()">📞 End</button>
            </div>
            <script>
                let localStream = null;
                let micEnabled = true;
                let camEnabled = true;
                let screenStream = null;
                
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
                    }}
                }}
                function toggleCam() {{
                    if (localStream) {{
                        camEnabled = !camEnabled;
                        localStream.getVideoTracks().forEach(t => t.enabled = camEnabled);
                        document.getElementById('camBtn').textContent = camEnabled ? '📷 Camera' : '🚫 Off';
                    }}
                }}
                async function toggleScreen() {{
                    if (!screenStream) {{
                        try {{
                            screenStream = await navigator.mediaDevices.getDisplayMedia({{ video: true }});
                            document.getElementById('screenBtn').textContent = '🖥️ Stop';
                        }} catch (e) {{ console.error('Screen error:', e); }}
                    }} else {{
                        screenStream.getTracks().forEach(t => t.stop());
                        screenStream = null;
                        document.getElementById('screenBtn').textContent = '🖥️ Share';
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
        components.html(video_html, height=450)
        
        if st.button("🚪 Leave Meeting", use_container_width=True):
            st.session_state.meet_room_id = None
            st.session_state.meet_role = None
            st.session_state.meet_participants = []
            st.rerun()
    
    with chat_col:
        st.markdown("### 💬 Live Chat")
        
        # Fetch chat messages from Supabase
        chat_messages = get_meeting_chat(room_id)
        
        # Build chat HTML
        chat_parts = []
        for msg in chat_messages:
            sender_id = msg.get("user_id")
            sender_name = get_user_name_by_id(sender_id)
            is_me = (str(sender_id) == str(user_id))
            msg_class = "me" if is_me else "other"
            time_str = str(msg.get("created_at", ""))[11:16]
            message_text = msg.get("message", "")
            
            chat_parts.append(
                f'<div class="chat-msg {msg_class}">'
                f'<div class="chat-sender">{"You" if is_me else sender_name}</div>'
                f'{message_text}'
                f'<div class="chat-time">{time_str}</div>'
                f'</div>'
            )
        
        chat_html = '<div class="chat-container">' + ''.join(chat_parts) + '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # Chat input
        with st.form("chat_form", clear_on_submit=True):
            chat_input = st.text_input("", placeholder="Type your message...", label_visibility="collapsed")
            if st.form_submit_button("📤 Send", use_container_width=True):
                if chat_input.strip():
                    send_chat_message(room_id, user_id, chat_input.strip())
                    st.rerun()
    
    # ========== PARTICIPANTS ==========
    st.markdown("### 👥 Participants")
    for pid in st.session_state.meet_participants:
        pname = get_user_name_by_id(pid)
        st.markdown(f'<span class="participant-badge">👤 {pname}</span>', unsafe_allow_html=True)

# ============================================
# NAVIGATION
# ============================================
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(10)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[6]: st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[7]: st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[9]: st.page_link("pages/23_GAIA_Meet.py", label="🎥 GAIA Meet")
