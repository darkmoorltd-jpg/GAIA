
import streamlit as st
import streamlit.components.v1 as components
import uuid
import datetime
import json
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

dark_mode = st.toggle("", value=False, key="gaia_meet_theme")
theme = "dark" if dark_mode else "light"

# ============================================
# CUSTOM CSS
# ============================================
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0a0e1a, #1a1a2e, #16213e); color: #e0e0e0; }
        header, footer { visibility: hidden; }
        .meet-title {
            font-size: 3rem; font-weight: 900; text-align: center;
            background: linear-gradient(135deg, #00c853, #69f0ae, #00c853);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            animation: glow 2s ease-in-out infinite alternate;
        }
        @keyframes glow {
            from { text-shadow: 0 0 20px rgba(0,200,83,0.6); }
            to { text-shadow: 0 0 40px rgba(0,200,83,1); }
        }
        .meet-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 1.5rem;
            backdrop-filter: blur(20px);
            margin-bottom: 1rem;
        }
        .control-btn {
            background: rgba(0,200,83,0.1);
            border: 1px solid #00c853;
            border-radius: 12px;
            padding: 10px 20px;
            color: #00c853;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            width: 100%;
            text-align: center;
        }
        .control-btn:hover {
            background: rgba(0,200,83,0.2);
            transform: translateY(-2px);
        }
        .chat-message {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 10px;
            margin: 5px 0;
        }
        .chat-message.user { border-left: 3px solid #00c853; }
        .chat-message.system { border-left: 3px solid #ff9800; }
        .participant-badge {
            background: rgba(0,200,83,0.1);
            border: 1px solid #00c853;
            border-radius: 20px;
            padding: 5px 15px;
            margin: 5px;
            display: inline-block;
            font-size: 0.85rem;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #f0fdf4, #e0f2fe); color: #0f172a; }
        header, footer { visibility: hidden; }
        .meet-title {
            font-size: 3rem; font-weight: 900; text-align: center;
            background: linear-gradient(135deg, #16a34a, #22c55e);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .meet-card {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 20px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }
        .control-btn {
            background: #16a34a;
            border-radius: 12px;
            padding: 10px 20px;
            color: #fff;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            text-align: center;
        }
        .chat-message {
            background: #f8fafc;
            border-radius: 12px;
            padding: 10px;
            margin: 5px 0;
        }
        .chat-message.user { border-left: 3px solid #16a34a; }
        .chat-message.system { border-left: 3px solid #f59e0b; }
        .participant-badge {
            background: #f0fdf4;
            border: 1px solid #16a34a;
            border-radius: 20px;
            padding: 5px 15px;
            margin: 5px;
            display: inline-block;
            font-size: 0.85rem;
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
if "meet_chat" not in st.session_state:
    st.session_state.meet_chat = []
if "meet_participants" not in st.session_state:
    st.session_state.meet_participants = []

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

def save_chat_message(room_id, user_id, message):
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

# ============================================
# HEADER
# ============================================
st.markdown('<div class="meet-title">🎥 GAIA Meet</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;font-size:1.1rem;">Your own private agricultural video conferencing platform</p>', unsafe_allow_html=True)

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
# TABS
# ============================================
tab1, tab2, tab3 = st.tabs(["🎥 Meeting Room", "💬 Chat", "👥 Participants"])

# ========== TAB 1: MEETING ROOM ==========
with tab1:
    if st.session_state.meet_room_id is None:
        st.markdown("### Create or Join a Meeting")
        
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
                    st.error(f"Failed to create meeting: {err}")
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
                    st.session_state.meet_participants.append(user_id)
                    st.success("Joined meeting!")
                    st.rerun()
                else:
                    st.error("Meeting not found. Check the Room ID.")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        room_id = st.session_state.meet_room_id
        meeting = get_meeting_info(room_id)
        
        st.markdown(f"### 🎥 Meeting: {meeting['title'] if meeting else 'Active Session'}")
        
        st.markdown(f"""
        <div class="meet-card">
            <p style="margin:0;"><strong>Room ID:</strong> {room_id}</p>
            <p style="margin:0.5rem 0 0 0;"><strong>Share this link:</strong> https://gaiagpt.streamlit.app/~/23_GAIA_Meet?room={room_id}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # WebRTC video area
        video_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .video-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 10px;
                    padding: 20px;
                }}
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
                    gap: 15px;
                    padding: 20px;
                    flex-wrap: wrap;
                }}
                .control-btn {{
                    background: rgba(255,255,255,0.1);
                    border: 1px solid #00c853;
                    color: #00c853;
                    border-radius: 50px;
                    padding: 10px 25px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: all 0.3s;
                }}
                .control-btn:hover {{
                    background: rgba(0,200,83,0.2);
                }}
                .control-btn.end {{
                    background: #ef4444;
                    border-color: #ef4444;
                    color: #fff;
                }}
            </style>
        </head>
        <body>
            <div class="video-grid" id="videoGrid">
                <div class="video-card">
                    <video id="localVideo" autoplay muted playsinline></video>
                    <div class="participant-name">You ({user_name})</div>
                </div>
            </div>
            <div class="controls">
                <button class="control-btn" id="micBtn" onclick="toggleMic()">🎙️ Mute</button>
                <button class="control-btn" id="camBtn" onclick="toggleCam()">📷 Camera</button>
                <button class="control-btn" id="screenBtn" onclick="toggleScreen()">🖥️ Share Screen</button>
                <button class="control-btn" id="recordBtn" onclick="toggleRecording()">⏺️ Record</button>
                <button class="control-btn end" onclick="endCall()">📞 End Call</button>
            </div>
            <script>
                let localStream = null;
                let micEnabled = true;
                let camEnabled = true;
                let screenStream = null;
                let isRecording = false;
                
                async function startCamera() {{
                    try {{
                        localStream = await navigator.mediaDevices.getUserMedia({{
                            video: true, audio: true
                        }});
                        document.getElementById('localVideo').srcObject = localStream;
                    }} catch (e) {{
                        console.error('Camera error:', e);
                    }}
                }}
                
                function toggleMic() {{
                    if (localStream) {{
                        micEnabled = !micEnabled;
                        localStream.getAudioTracks().forEach(track => track.enabled = micEnabled);
                        document.getElementById('micBtn').textContent = micEnabled ? '🎙️ Mute' : '🔇 Unmute';
                    }}
                }}
                
                function toggleCam() {{
                    if (localStream) {{
                        camEnabled = !camEnabled;
                        localStream.getVideoTracks().forEach(track => track.enabled = camEnabled);
                        document.getElementById('camBtn').textContent = camEnabled ? '📷 Camera' : '🚫 Camera Off';
                    }}
                }}
                
                async function toggleScreen() {{
                    if (!screenStream) {{
                        try {{
                            screenStream = await navigator.mediaDevices.getDisplayMedia({{
                                video: true
                            }});
                            const grid = document.getElementById('videoGrid');
                            const screenCard = document.createElement('div');
                            screenCard.className = 'video-card';
                            screenCard.id = 'screenCard';
                            screenCard.innerHTML = '<video autoplay playsinline></video><div class="participant-name">Screen Share</div>';
                            screenCard.querySelector('video').srcObject = screenStream;
                            grid.appendChild(screenCard);
                            document.getElementById('screenBtn').textContent = '🖥️ Stop Share';
                        }} catch (e) {{
                            console.error('Screen share error:', e);
                        }}
                    }} else {{
                        screenStream.getTracks().forEach(track => track.stop());
                        screenStream = null;
                        const screenCard = document.getElementById('screenCard');
                        if (screenCard) screenCard.remove();
                        document.getElementById('screenBtn').textContent = '🖥️ Share Screen';
                    }}
                }}
                
                function toggleRecording() {{
                    if (!isRecording) {{
                        isRecording = true;
                        document.getElementById('recordBtn').textContent = '⏺️ Recording...';
                    }} else {{
                        isRecording = false;
                        document.getElementById('recordBtn').textContent = '⏺️ Record';
                    }}
                }}
                
                function endCall() {{
                    if (localStream) localStream.getTracks().forEach(track => track.stop());
                    if (screenStream) screenStream.getTracks().forEach(track => track.stop());
                    window.location.reload();
                }}
                
                startCamera();
            </script>
        </body>
        </html>
        """
        
        components.html(video_html, height=700)
        
        if st.button("🚪 Leave Meeting", use_container_width=True):
            st.session_state.meet_room_id = None
            st.session_state.meet_role = None
            st.session_state.meet_participants = []
            st.rerun()

# ========== TAB 2: CHAT ==========
with tab2:
    st.markdown("### 💬 Meeting Chat")
    if st.session_state.meet_room_id:
        for msg in st.session_state.meet_chat:
            st.markdown(f'<div class="chat-message user"><strong>{msg["user"]}:</strong> {msg["text"]}</div>', unsafe_allow_html=True)
        
        with st.form("send_chat"):
            chat_input = st.text_input("Message")
            if st.form_submit_button("Send"):
                st.session_state.meet_chat.append({"user": user_name, "text": chat_input})
                save_chat_message(st.session_state.meet_room_id, user_id, chat_input)
                st.rerun()
    else:
        st.info("Join a meeting to chat.")

# ========== TAB 3: PARTICIPANTS ==========
with tab3:
    st.markdown("### 👥 Participants")
    if st.session_state.meet_participants:
        for pid in st.session_state.meet_participants:
            st.markdown(f'<span class="participant-badge">👤 {pid[:8]}</span>', unsafe_allow_html=True)
    else:
        st.info("No participants yet.")

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
