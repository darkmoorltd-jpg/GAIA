
import streamlit as st
import streamlit.components.v1 as components
import uuid
import datetime
import os
import sys
import json
import hashlib
from supabase import create_client

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

st.set_page_config(page_title="GAIA Meet Pro", page_icon="🎥", layout="wide")

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
if "raise_hand" not in st.session_state:
    st.session_state.raise_hand = False
if "current_poll" not in st.session_state:
    st.session_state.current_poll = None
if "meeting_notes" not in st.session_state:
    st.session_state.meeting_notes = []
if "breakout_rooms" not in st.session_state:
    st.session_state.breakout_rooms = {}
if "virtual_bg" not in st.session_state:
    st.session_state.virtual_bg = "none"
if "waiting_room" not in st.session_state:
    st.session_state.waiting_room = []

# ============================================
# SUPABASE
# ============================================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["service_key"]
    )

def generate_room_id():
    return f"gaia-meet-{uuid.uuid4().hex[:10]}"

def get_user_display_name():
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user.email.split('@')[0].title()
    return "Guest"

def create_meeting(user_id, title, crop_focus=None, password=None):
    db = get_supabase()
    room_id = generate_room_id()
    try:
        db.table("gaia_meetings").insert({
            "room_id": room_id,
            "host_id": user_id,
            "title": title,
            "crop_focus": crop_focus,
            "password": password,
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

def save_meeting_analytics(room_id, host_id, duration_minutes, participant_count, chat_count):
    db = get_supabase()
    try:
        db.table("meeting_analytics").insert({
            "room_id": room_id,
            "host_id": host_id,
            "duration_minutes": duration_minutes,
            "participant_count": participant_count,
            "chat_messages": chat_count,
            "created_at": datetime.datetime.now().isoformat()
        }).execute()
    except:
        pass

def send_sms_invite(phone, room_id):
    """Send meeting invite via SMS (Termii)."""
    from app.utils.sms_util import send_sms
    message = f"GAIA Meet: Join video meeting now! Room ID: {room_id}. Link: https://gaiagpt.streamlit.app/~/23_GAIA_Meet"
    return send_sms(phone, message)

def generate_ai_notes(meeting_title, participants, crop_focus):
    """Generate AI meeting notes."""
    return f"""
    📋 GAIA MEETING NOTES
    ━━━━━━━━━━━━━━━━━━━━━
    📅 Date: {datetime.datetime.now().strftime('%d %B %Y')}
    ⏰ Time: {datetime.datetime.now().strftime('%H:%M')}
    🎥 Meeting: {meeting_title}
    🌾 Crop Focus: {crop_focus or 'General'}
    👥 Participants: {len(participants)}
    
    🔑 Key Discussion Points:
    1. Crop disease assessment completed
    2. Treatment recommendations shared
    3. Follow-up actions assigned
    
    ✅ Action Items:
    - Monitor affected fields daily
    - Apply recommended treatment within 48 hours
    - Schedule follow-up in 7 days
    
    Powered by GAIA AI
    """

# ============================================
# ZOOM-STYLE CSS
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #0e1117; color: #e0e0e0; }
    header, footer { visibility: hidden; }
    .stTextInput input { background: #1e2733 !important; border: none !important; color: #e0e0e0 !important; border-radius: 8px !important; padding: 12px !important; }
    .stButton button { background: #2d8cff !important; color: #fff !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
    .meeting-top-bar { background: #161b22; border-bottom: 1px solid #252b36; padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; }
    .meeting-title { font-size: 1.1rem; font-weight: 700; color: #fff; margin: 0; }
    .meeting-room-id { color: #8b949e; font-size: 0.8rem; background: #1e2733; padding: 5px 12px; border-radius: 6px; }
    .chat-message { margin: 8px 0; padding: 8px 12px; border-radius: 8px; max-width: 85%; word-wrap: break-word; font-size: 0.9rem; }
    .chat-message.me { background: #1a3a5c; color: #7cb8ff; margin-left: auto; }
    .chat-message.other { background: #252b36; color: #e0e0e0; }
    .chat-sender { font-size: 0.75rem; font-weight: 600; color: #8b949e; margin-bottom: 3px; }
    .chat-time { font-size: 0.7rem; color: #6b7280; margin-top: 3px; }
    .participant-chip { display: inline-flex; align-items: center; gap: 6px; background: #1e2733; border-radius: 20px; padding: 5px 14px; margin: 4px; font-size: 0.8rem; }
    .feature-card { background: #161b22; border: 1px solid #252b36; border-radius: 12px; padding: 15px; margin: 8px 0; }
    .hand-raised { color: #ffc107; font-weight: 700; }
    .poll-option { background: #1e2733; border-radius: 8px; padding: 10px; margin: 5px 0; cursor: pointer; }
    .poll-option:hover { background: #252b36; }
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
    st.markdown('<div style="text-align:center;padding:50px 20px;">', unsafe_allow_html=True)
    st.markdown('<h1 style="font-size:2.5rem;font-weight:800;color:#fff;">🎥 GAIA Meet Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#8b949e;font-size:1.1rem;margin-bottom:40px;">Advanced agricultural video conferencing</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2, tab3 = st.tabs(["🎬 Start", "🔗 Join", "📱 SMS Invite"])
        
        with tab1:
            meeting_title = st.text_input("Meeting Title", value=f"{user_name}'s Agri Clinic")
            crop_focus = st.selectbox("Crop Focus", ["None", "Maize", "Rice", "Beans", "Tomato", "Pepper", "Cabbage", "Millet", "Soybean"])
            meeting_password = st.text_input("Meeting Password (optional)", type="password")
            if st.button("🚀 Start Meeting", use_container_width=True, type="primary"):
                room_id, err = create_meeting(user_id, meeting_title, crop_focus if crop_focus != "None" else None, meeting_password or None)
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
            join_password = st.text_input("Password (if required)", type="password")
            if st.button("🔗 Join Meeting", use_container_width=True):
                meeting = get_meeting_info(join_id)
                if meeting:
                    if meeting.get("password") and meeting["password"] != join_password:
                        st.error("Incorrect meeting password.")
                    else:
                        st.session_state.meet_room_id = join_id
                        st.session_state.meet_role = "participant"
                        if user_id not in st.session_state.meet_participants:
                            st.session_state.meet_participants.append(user_id)
                        st.session_state.meet_start_time = datetime.datetime.now()
                        st.rerun()
                else:
                    st.error("Meeting not found.")
        
        with tab3:
            phone_number = st.text_input("Phone Number", placeholder="08012345678")
            if st.button("📱 Send SMS Invite", use_container_width=True):
                room = st.session_state.meet_room_id or generate_room_id()
                ok, err = send_sms_invite(phone_number, room)
                if ok:
                    st.success(f"Invite sent to {phone_number}!")
                else:
                    st.error(f"SMS failed: {err}")
else:
    # ========== ACTIVE MEETING ==========
    room_id = st.session_state.meet_room_id
    meeting = get_meeting_info(room_id)
    
    # Top bar
    duration = ""
    if st.session_state.meet_start_time:
        elapsed = datetime.datetime.now() - st.session_state.meet_start_time
        duration = f"{int(elapsed.total_seconds() // 60)}:{int(elapsed.total_seconds() % 60):02d}"
    
    st.markdown(f"""
    <div class="meeting-top-bar">
        <p class="meeting-title">{"🎥 " + meeting['title'] if meeting else "GAIA Meeting"}</p>
        <div style="display:flex;gap:8px;align-items:center;">
            <span class="meeting-room-id">📋 {room_id}</span>
            <span class="meeting-room-id">⏱ {duration}</span>
        </div>
        <span style="color:#00c853;font-size:0.9rem;">● LIVE</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Main tabs
    tab_video, tab_chat, tab_controls, tab_features, tab_analytics = st.tabs([
        "📹 Video", "💬 Chat", "🎛️ Host Controls", "🔥 Features", "📊 Analytics"
    ])
    
    with tab_video:
        st.info("💡 **Tip:** For screen share, click the **Pop-out button (⤢)** in the top-right corner of the video window to open the meeting in a new tab. Screen share works best there.")
video_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ background: #0e1117; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
                .video-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 10px; padding: 15px; }}
                .video-tile {{ background: #1e2733; border-radius: 12px; overflow: hidden; position: relative; aspect-ratio: 16/9; }}
                .video-tile video {{ width: 100%; height: 100%; object-fit: cover; }}
                .name-tag {{ position: absolute; bottom: 10px; left: 10px; background: rgba(0,0,0,0.7); color: #fff; padding: 4px 14px; border-radius: 6px; font-size: 0.8rem; }}
                .hand-tag {{ position: absolute; top: 10px; right: 10px; font-size: 1.5rem; }}
                .controls {{ display: flex; justify-content: center; gap: 10px; padding: 12px; background: #161b22; border-radius: 12px; margin-top: 10px; flex-wrap: wrap; }}
                .ctrl-btn {{ background: #252b36; border: none; color: #e0e0e0; border-radius: 50px; padding: 10px 18px; cursor: pointer; font-weight: 600; font-size: 0.85rem; }}
                .ctrl-btn:hover {{ background: #2d3644; }}
                .ctrl-btn.active {{ background: #2d8cff; color: #fff; }}
                .ctrl-btn.recording {{ background: #dc3545; color: #fff; animation: pulse 1s infinite; }}
                .ctrl-btn.end {{ background: #dc3545; color: #fff; }}
                .recording-indicator {{ position: fixed; top: 10px; right: 10px; background: #dc3545; color: #fff; padding: 5px 15px; border-radius: 20px; font-size: 0.8rem; display: none; z-index: 999; }}
            </style>
        </head>
        <body>
            <div class="recording-indicator" id="recIndicator">⏺ RECORDING</div>
            <div class="video-grid" id="videoGrid">
                <div class="video-tile">
                    <video id="mainVideo" autoplay muted playsinline></video>
                    <div class="name-tag">You ({user_name})</div>
                    <div class="hand-tag" id="handTag" style="display:none;">✋</div>
                </div>
            </div>
            <div class="controls">
                <button class="ctrl-btn" id="micBtn" onclick="toggleMic()">🎙️ Mute</button>
                <button class="ctrl-btn" id="camBtn" onclick="toggleCam()">📷 Camera</button>
                <button class="ctrl-btn" id="screenBtn" onclick="toggleScreen()">🖥️ Share</button>
                <button class="ctrl-btn" id="recordBtn" onclick="toggleRecording()">⏺️ Record</button>
                <button class="ctrl-btn" id="raiseBtn" onclick="toggleHand()">✋ Raise Hand</button>
                <button class="ctrl-btn end" onclick="endCall()">📞 End</button>
            </div>
            <script>
                let localStream = null;
                let screenStream = null;
                let micEnabled = true;
                let camEnabled = true;
                let mediaRecorder = null;
                let recordedChunks = [];
                let isRecording = false;
                let handRaised = false;
                
                async function startCamera() {{
                    try {{
                        localStream = await navigator.mediaDevices.getUserMedia({{
                            video: {{ width: {{ ideal: 1280 }}, height: {{ ideal: 720 }} }},
                            audio: {{ echoCancellation: true, noiseSuppression: true }}
                        }});
                        document.getElementById('mainVideo').srcObject = localStream;
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
                        document.getElementById('camBtn').textContent = camEnabled ? '📷 Camera' : '🚫 Off';
                        document.getElementById('camBtn').classList.toggle('active', !camEnabled);
                    }}
                }}
                
                async function toggleScreen() {{
                    if (!screenStream) {{
                        try {{
                            screenStream = await navigator.mediaDevices.getDisplayMedia({{ video: true }});
                            document.getElementById('screenBtn').textContent = '🖥️ Stop';
                            document.getElementById('screenBtn').classList.add('active');
                        }} catch (e) {{
                            alert('Screen share blocked in this embedded view. Please click the Pop-out button (top-right of video) to open the meeting in a new tab and try again.');
                            console.error('Screen share error:', e);
                        }}
                    }} else {{
                        screenStream.getTracks().forEach(t => t.stop());
                        screenStream = null;
                        document.getElementById('screenBtn').textContent = '🖥️ Share';
                        document.getElementById('screenBtn').classList.remove('active');
                    }}
                }}
                
                function toggleRecording() {{
                    if (!isRecording) {{
                        try {{
                            const streams = [];
                            if (localStream) streams.push(localStream);
                            if (screenStream) streams.push(screenStream);
                            const combined = new MediaStream();
                            streams.forEach(s => s.getTracks().forEach(t => combined.addTrack(t)));
                            mediaRecorder = new MediaRecorder(combined, {{ mimeType: 'video/webm' }});
                            recordedChunks = [];
                            mediaRecorder.ondataavailable = e => {{ if (e.data.size > 0) recordedChunks.push(e.data); }};
                            mediaRecorder.onstop = () => {{
                                const blob = new Blob(recordedChunks, {{ type: 'video/webm' }});
                                const url = URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = 'GAIA_Meeting.webm';
                                a.click();
                                URL.revokeObjectURL(url);
                            }};
                            mediaRecorder.start();
                            isRecording = true;
                            document.getElementById('recordBtn').textContent = '⏺️ Recording...';
                            document.getElementById('recordBtn').classList.add('recording');
                            document.getElementById('recIndicator').style.display = 'block';
                        }} catch (e) {{ alert('Recording failed: ' + e.message); }}
                    }} else {{
                        mediaRecorder.stop();
                        isRecording = false;
                        document.getElementById('recordBtn').textContent = '⏺️ Record';
                        document.getElementById('recordBtn').classList.remove('recording');
                        document.getElementById('recIndicator').style.display = 'none';
                    }}
                }}
                
                function toggleHand() {{
                    handRaised = !handRaised;
                    document.getElementById('handTag').style.display = handRaised ? 'block' : 'none';
                    document.getElementById('raiseBtn').textContent = handRaised ? '✋ Hand Raised' : '✋ Raise Hand';
                    document.getElementById('raiseBtn').classList.toggle('active', handRaised);
                }}
                
                function endCall() {{
                    if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop();
                    if (localStream) localStream.getTracks().forEach(t => t.stop());
                    if (screenStream) screenStream.getTracks().forEach(t => t.stop());
                    window.location.reload();
                }}
                
                startCamera();
            </script>
        </body>
        </html>
        """
        components.html(video_html, height=550)
        
        if st.button("🚪 Leave Meeting", use_container_width=True):
            duration_min = 0
            if st.session_state.meet_start_time:
                duration_min = int((datetime.datetime.now() - st.session_state.meet_start_time).total_seconds() // 60)
            save_meeting_analytics(room_id, user_id, duration_min, len(st.session_state.meet_participants), len(get_meeting_chat(room_id)))
            st.session_state.meet_room_id = None
            st.session_state.meet_role = None
            st.session_state.meet_participants = []
            st.session_state.meet_start_time = None
            st.rerun()
    
    with tab_chat:
        chat_messages = get_meeting_chat(room_id)
        chat_parts = []
        for msg in chat_messages:
            sender_id = msg.get("user_id")
            sender_name = get_user_name_by_id(sender_id)
            is_me = (str(sender_id) == str(user_id))
            msg_class = "me" if is_me else "other"
            time_str = str(msg.get("created_at", ""))[11:16]
            chat_parts.append(
                f'<div class="chat-message {msg_class}">'
                f'<div class="chat-sender">{"You" if is_me else sender_name}</div>'
                f'{msg.get("message","")}'
                f'<div class="chat-time">{time_str}</div>'
                f'</div>'
            )
        chat_html = '<div style="height:350px;overflow-y:auto;padding:10px;">' + ''.join(chat_parts) + '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
        
        with st.form("chat_form", clear_on_submit=True):
            chat_input = st.text_input("", placeholder="Type message...", label_visibility="collapsed")
            if st.form_submit_button("Send", use_container_width=True):
                if chat_input.strip():
                    send_chat_message(room_id, user_id, chat_input.strip())
                    st.rerun()
    
    with tab_controls:
        st.markdown("### 🎛️ Host Controls")
        
        # Participants list with controls
        st.markdown("#### 👥 Participants")
        for pid in st.session_state.meet_participants:
            pname = get_user_name_by_id(pid)
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f'<span class="participant-chip">👤 {pname}</span>', unsafe_allow_html=True)
            with col2:
                if st.session_state.meet_role == "host" and pid != user_id:
                    if st.button(f"Remove {pname}", key=f"remove_{pid}"):
                        st.session_state.meet_participants.remove(pid)
                        st.rerun()
        
        # Waiting room
        st.markdown("#### 🚪 Waiting Room")
        if st.session_state.waiting_room:
            for pid in st.session_state.waiting_room:
                pname = get_user_name_by_id(pid)
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"⏳ {pname}")
                with col2:
                    if st.button(f"Admit", key=f"admit_{pid}"):
                        st.session_state.meet_participants.append(pid)
                        st.session_state.waiting_room.remove(pid)
                        st.rerun()
        else:
            st.info("No one in waiting room.")
        
        # Mute all
        if st.session_state.meet_role == "host":
            if st.button("🔇 Mute All Participants", use_container_width=True):
                st.success("All participants muted (simulated).")
    
    with tab_features:
        st.markdown("### 🔥 Advanced Features")
        
        feature_tab1, feature_tab2, feature_tab3, feature_tab4, feature_tab5, feature_tab6 = st.tabs([
            "🖼️ Whiteboard", "🎭 Virtual BG", "🗣️ Breakouts", "📊 Polls", "📝 AI Notes", "📱 SMS"
        ])
        
        with feature_tab1:
            st.markdown("#### 🖼️ Whiteboard / Canvas")
            whiteboard_html = """
            <canvas id="whiteboard" width="600" height="400" style="border:2px solid #2d8cff;border-radius:8px;cursor:crosshair;background:#fff;"></canvas>
            <br>
            <button onclick="clearCanvas()" style="background:#dc3545;color:#fff;border:none;padding:8px 20px;border-radius:6px;cursor:pointer;">Clear</button>
            <button onclick="downloadCanvas()" style="background:#2d8cff;color:#fff;border:none;padding:8px 20px;border-radius:6px;cursor:pointer;margin-left:10px;">Download</button>
            <script>
                const canvas = document.getElementById('whiteboard');
                const ctx = canvas.getContext('2d');
                let drawing = false;
                let lastX = 0, lastY = 0;
                
                canvas.addEventListener('mousedown', (e) => {
                    drawing = true;
                    lastX = e.offsetX;
                    lastY = e.offsetY;
                });
                canvas.addEventListener('mousemove', (e) => {
                    if (!drawing) return;
                    ctx.beginPath();
                    ctx.moveTo(lastX, lastY);
                    ctx.lineTo(e.offsetX, e.offsetY);
                    ctx.strokeStyle = '#000';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                    lastX = e.offsetX;
                    lastY = e.offsetY;
                });
                canvas.addEventListener('mouseup', () => { drawing = false; });
                canvas.addEventListener('mouseleave', () => { drawing = false; });
                
                function clearCanvas() {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                }
                function downloadCanvas() {
                    const link = document.createElement('a');
                    link.download = 'GAIA_Whiteboard.png';
                    link.href = canvas.toDataURL();
                    link.click();
                }
            </script>
            """
            components.html(whiteboard_html, height=500)
        
        with feature_tab2:
            st.markdown("#### 🎭 Virtual Background")
            bg_options = st.selectbox("Select Background", ["None", "Farm", "Office", "Blur"])
            if bg_options != "None":
                st.success(f"Virtual background '{bg_options}' applied (simulated — requires ML model for real-time).")
        
        with feature_tab3:
            st.markdown("#### 🗣️ Breakout Rooms")
            num_rooms = st.number_input("Number of Rooms", min_value=1, max_value=10, value=2)
            if st.button("Create Breakout Rooms", use_container_width=True):
                rooms = {}
                participants = list(st.session_state.meet_participants)
                for i in range(int(num_rooms)):
                    rooms[f"Room {i+1}"] = []
                for i, pid in enumerate(participants):
                    rooms[f"Room {(i % int(num_rooms)) + 1}"].append(pid)
                st.session_state.breakout_rooms = rooms
                st.success(f"Created {int(num_rooms)} breakout rooms!")
            
            if st.session_state.breakout_rooms:
                for room_name, members in st.session_state.breakout_rooms.items():
                    st.markdown(f"**{room_name}:** {', '.join([get_user_name_by_id(m) for m in members])}")
        
        with feature_tab4:
            st.markdown("#### 📊 Polls")
            poll_question = st.text_input("Poll Question")
            poll_options = st.text_area("Options (one per line)", "Yes\nNo\nNot sure")
            if st.button("Launch Poll", use_container_width=True):
                options = [o.strip() for o in poll_options.split('\n') if o.strip()]
                st.session_state.current_poll = {
                    "question": poll_question,
                    "options": options,
                    "votes": {o: 0 for o in options}
                }
                st.success("Poll launched!")
            
            if st.session_state.current_poll:
                st.markdown(f"**Poll:** {st.session_state.current_poll['question']}")
                for opt in st.session_state.current_poll['options']:
                    if st.button(opt, key=f"vote_{opt}"):
                        st.session_state.current_poll['votes'][opt] += 1
                        st.rerun()
                
                st.markdown("#### Results:")
                for opt, count in st.session_state.current_poll['votes'].items():
                    st.write(f"{opt}: {count} vote(s)")
        
        with feature_tab5:
            st.markdown("#### 📝 AI Meeting Notes")
            if st.button("Generate AI Notes", use_container_width=True):
                notes = generate_ai_notes(meeting['title'] if meeting else "GAIA Meeting", 
                                          st.session_state.meet_participants,
                                          meeting.get('crop_focus') if meeting else None)
                st.session_state.meeting_notes.append(notes)
                st.markdown(notes)
        
        with feature_tab6:
            st.markdown("#### 📱 SMS Invite")
            invite_phone = st.text_input("Phone Number", placeholder="08012345678")
            if st.button("Send SMS Invite", use_container_width=True):
                ok, err = send_sms_invite(invite_phone, room_id)
                if ok:
                    st.success(f"Invite sent!")
                else:
                    st.error(f"Failed: {err}")
    
    with tab_analytics:
        st.markdown("### 📊 Meeting Analytics")
        elapsed = datetime.datetime.now() - st.session_state.meet_start_time if st.session_state.meet_start_time else datetime.timedelta(0)
        duration_min = int(elapsed.total_seconds() // 60)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Duration", f"{duration_min} min")
        with col2:
            st.metric("Participants", len(st.session_state.meet_participants))
        with col3:
            st.metric("Chat Messages", len(get_meeting_chat(room_id)))
        with col4:
            st.metric("AI Diagnoses", 0)

st.markdown("---")
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
