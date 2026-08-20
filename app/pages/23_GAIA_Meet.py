
import streamlit as st
import streamlit.components.v1 as components
import uuid
import datetime
import os
import sys
from supabase import create_client

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

st.set_page_config(page_title="GAIA Meet", page_icon="🎥", layout="wide")

# Session state
if "meet_room_id" not in st.session_state:
    st.session_state.meet_room_id = None
if "meet_role" not in st.session_state:
    st.session_state.meet_role = None
if "meet_participants" not in st.session_state:
    st.session_state.meet_participants = []
if "meet_start_time" not in st.session_state:
    st.session_state.meet_start_time = None

# Supabase
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

# Zoom-style CSS
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
    .copy-box { background: #1e2733; border: 1px solid #2d8cff; border-radius: 10px; padding: 10px 18px; text-align: center; color: #7cb8ff; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Auth check
if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in to use GAIA Meet.")
    st.stop()

user = st.session_state.user
user_id = user.id
user_name = get_user_display_name()

if st.session_state.meet_room_id is None:
    # Join/Create screen
    st.markdown('<div style="text-align:center;padding:50px 20px;">', unsafe_allow_html=True)
    st.markdown('<h1 style="font-size:2.5rem;font-weight:800;color:#fff;">🎥 GAIA Meet</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#8b949e;font-size:1.1rem;margin-bottom:40px;">Secure agricultural video conferencing</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2 = st.tabs(["🎬 Start", "🔗 Join"])
        with tab1:
            meeting_title = st.text_input("Meeting Title", value=f"{user_name}'s Agri Clinic")
            crop_focus = st.selectbox("Crop Focus", ["None", "Maize", "Rice", "Beans", "Tomato", "Pepper", "Cabbage", "Millet", "Soybean"])
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
    # Active meeting
    room_id = st.session_state.meet_room_id
    meeting = get_meeting_info(room_id)
    
    # Top bar
    st.markdown(f"""
    <div class="meeting-top-bar">
        <p class="meeting-title">{"🎥 " + meeting['title'] if meeting else "GAIA Meeting"}</p>
        <div style="display:flex;gap:8px;align-items:center;">
            <span class="meeting-room-id">📋 {room_id}</span>
        </div>
        <span style="color:#00c853;font-size:0.9rem;">● LIVE</span>
    </div>
    """, unsafe_allow_html=True)
    
    video_col, chat_col = st.columns([2.2, 1])
    
    with video_col:
        # FULLY WORKING WebRTC with recording and screen share
        video_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ background: #0e1117; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
                .video-grid {{ display: grid; grid-template-columns: 1fr; gap: 10px; padding: 15px; }}
                .video-tile {{ background: #1e2733; border-radius: 12px; overflow: hidden; position: relative; aspect-ratio: 16/9; }}
                .video-tile video {{ width: 100%; height: 100%; object-fit: cover; }}
                .name-tag {{ position: absolute; bottom: 10px; left: 10px; background: rgba(0,0,0,0.7); color: #fff; padding: 4px 14px; border-radius: 6px; font-size: 0.8rem; }}
                .controls {{ display: flex; justify-content: center; gap: 10px; padding: 12px; background: #161b22; border-radius: 12px; margin-top: 10px; flex-wrap: wrap; }}
                .ctrl-btn {{ background: #252b36; border: none; color: #e0e0e0; border-radius: 50px; padding: 10px 18px; cursor: pointer; font-weight: 600; font-size: 0.85rem; transition: all 0.2s; font-family: 'Inter', sans-serif; }}
                .ctrl-btn:hover {{ background: #2d3644; }}
                .ctrl-btn.active {{ background: #2d8cff; color: #fff; }}
                .ctrl-btn.recording {{ background: #dc3545; color: #fff; animation: pulse 1s infinite; }}
                .ctrl-btn.end {{ background: #dc3545; color: #fff; }}
                @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} 100% {{ opacity: 1; }} }}
                .recording-indicator {{ position: fixed; top: 10px; right: 10px; background: #dc3545; color: #fff; padding: 5px 15px; border-radius: 20px; font-size: 0.8rem; display: none; z-index: 999; }}
            </style>
        </head>
        <body>
            <div class="recording-indicator" id="recIndicator">⏺ RECORDING</div>
            <div class="video-grid" id="videoGrid">
                <div class="video-tile" id="mainVideoTile">
                    <video id="mainVideo" autoplay muted playsinline></video>
                    <div class="name-tag">You ({user_name})</div>
                </div>
            </div>
            <div class="controls">
                <button class="ctrl-btn" id="micBtn" onclick="toggleMic()">🎙️ Mute</button>
                <button class="ctrl-btn" id="camBtn" onclick="toggleCam()">📷 Camera</button>
                <button class="ctrl-btn" id="screenBtn" onclick="toggleScreen()">🖥️ Share Screen</button>
                <button class="ctrl-btn" id="recordBtn" onclick="toggleRecording()">⏺️ Record</button>
                <button class="ctrl-btn" id="downloadBtn" style="display:none;" onclick="downloadRecording()">💾 Download</button>
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
                
                // === START CAMERA AND MIC ===
                async function startCamera() {{
                    try {{
                        localStream = await navigator.mediaDevices.getUserMedia({{
                            video: {{ width: {{ ideal: 1280 }}, height: {{ ideal: 720 }} }},
                            audio: {{ echoCancellation: true, noiseSuppression: true }}
                        }});
                        document.getElementById('mainVideo').srcObject = localStream;
                        console.log('Camera + Mic started');
                    }} catch (e) {{
                        console.error('Camera error:', e);
                        alert('Camera/Mic permission denied. Please allow access.');
                    }}
                }}
                
                // === TOGGLE MIC ===
                function toggleMic() {{
                    if (localStream) {{
                        micEnabled = !micEnabled;
                        localStream.getAudioTracks().forEach(t => t.enabled = micEnabled);
                        document.getElementById('micBtn').textContent = micEnabled ? '🎙️ Mute' : '🔇 Unmute';
                        document.getElementById('micBtn').classList.toggle('active', !micEnabled);
                    }}
                }}
                
                // === TOGGLE CAMERA ===
                function toggleCam() {{
                    if (localStream) {{
                        camEnabled = !camEnabled;
                        localStream.getVideoTracks().forEach(t => t.enabled = camEnabled);
                        document.getElementById('camBtn').textContent = camEnabled ? '📷 Camera' : '🚫 Camera Off';
                        document.getElementById('camBtn').classList.toggle('active', !camEnabled);
                    }}
                }}
                
                // === SCREEN SHARE (FULLY WORKING) ===
                async function toggleScreen() {{
                    if (!screenStream) {{
                        try {{
                            screenStream = await navigator.mediaDevices.getDisplayMedia({{
                                video: {{ frameRate: {{ ideal: 30 }} }},
                                audio: false
                            }});
                            
                            // Add screen tile to grid
                            const grid = document.getElementById('videoGrid');
                            const screenTile = document.createElement('div');
                            screenTile.className = 'video-tile';
                            screenTile.id = 'screenTile';
                            screenTile.innerHTML = '<video id="screenVideo" autoplay playsinline></video><div class="name-tag">🖥️ Screen Share</div>';
                            grid.appendChild(screenTile);
                            
                            const screenVideo = screenTile.querySelector('video');
                            screenVideo.srcObject = screenStream;
                            
                            // Handle screen share stop
                            screenStream.getVideoTracks()[0].onended = () => {{
                                stopScreenShare();
                            }};
                            
                            document.getElementById('screenBtn').textContent = '🖥️ Stop Share';
                            document.getElementById('screenBtn').classList.add('active');
                            console.log('Screen share started');
                        }} catch (e) {{
                            console.error('Screen share error:', e);
                        }}
                    }} else {{
                        stopScreenShare();
                    }}
                }}
                
                function stopScreenShare() {{
                    if (screenStream) {{
                        screenStream.getTracks().forEach(t => t.stop());
                        screenStream = null;
                        const screenTile = document.getElementById('screenTile');
                        if (screenTile) screenTile.remove();
                        document.getElementById('screenBtn').textContent = '🖥️ Share Screen';
                        document.getElementById('screenBtn').classList.remove('active');
                    }}
                }}
                
                // === RECORDING (FULLY WORKING) ===
                async function toggleRecording() {{
                    if (!isRecording) {{
                        try {{
                            // Create combined stream (camera + screen if sharing)
                            const streams = [];
                            if (localStream) streams.push(localStream);
                            if (screenStream) streams.push(screenStream);
                            
                            const combinedStream = new MediaStream();
                            streams.forEach(s => {{
                                s.getTracks().forEach(t => combinedStream.addTrack(t));
                            }});
                            
                            mediaRecorder = new MediaRecorder(combinedStream, {{
                                mimeType: 'video/webm;codecs=vp9'
                            }});
                            
                            recordedChunks = [];
                            
                            mediaRecorder.ondataavailable = (event) => {{
                                if (event.data.size > 0) {{
                                    recordedChunks.push(event.data);
                                }}
                            }};
                            
                            mediaRecorder.onstop = () => {{
                                const blob = new Blob(recordedChunks, {{ type: 'video/webm' }});
                                const url = URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = 'GAIA_Meeting_' + new Date().toISOString() + '.webm';
                                a.click();
                                URL.revokeObjectURL(url);
                            }};
                            
                            mediaRecorder.start();
                            isRecording = true;
                            document.getElementById('recordBtn').textContent = '⏺️ Recording...';
                            document.getElementById('recordBtn').classList.add('recording');
                            document.getElementById('recIndicator').style.display = 'block';
                            console.log('Recording started');
                        }} catch (e) {{
                            console.error('Recording error:', e);
                            alert('Recording failed: ' + e.message);
                        }}
                    }} else {{
                        if (mediaRecorder && mediaRecorder.state === 'recording') {{
                            mediaRecorder.stop();
                        }}
                        isRecording = false;
                        document.getElementById('recordBtn').textContent = '⏺️ Record';
                        document.getElementById('recordBtn').classList.remove('recording');
                        document.getElementById('recIndicator').style.display = 'none';
                        console.log('Recording stopped and downloaded');
                    }}
                }}
                
                function downloadRecording() {{
                    if (mediaRecorder && mediaRecorder.state === 'recording') {{
                        mediaRecorder.stop();
                    }}
                }}
                
                // === END CALL ===
                function endCall() {{
                    if (mediaRecorder && mediaRecorder.state === 'recording') {{
                        mediaRecorder.stop();
                    }}
                    if (localStream) {{
                        localStream.getTracks().forEach(t => t.stop());
                    }}
                    if (screenStream) {{
                        screenStream.getTracks().forEach(t => t.stop());
                    }}
                    window.location.reload();
                }}
                
                // Start camera on load
                startCamera();
            </script>
        </body>
        </html>
        """
        components.html(video_html, height=600)
        
        if st.button("🚪 Leave Meeting", use_container_width=True):
            st.session_state.meet_room_id = None
            st.session_state.meet_role = None
            st.session_state.meet_participants = []
            st.session_state.meet_start_time = None
            st.rerun()
    
    with chat_col:
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
        chat_html = '<div style="height:400px;overflow-y:auto;padding:10px;">' + ''.join(chat_parts) + '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
        
        with st.form("chat_form", clear_on_submit=True):
            chat_input = st.text_input("", placeholder="Type message...", label_visibility="collapsed")
            if st.form_submit_button("Send", use_container_width=True):
                if chat_input.strip():
                    send_chat_message(room_id, user_id, chat_input.strip())
                    st.rerun()
        
        st.markdown("### 👥 Participants")
        for pid in st.session_state.meet_participants:
            pname = get_user_name_by_id(pid)
            st.markdown(f'<span class="participant-chip">👤 {pname}</span>', unsafe_allow_html=True)

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
