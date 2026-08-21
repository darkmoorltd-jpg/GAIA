
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
    st.markdown('<div style="text-align:center;padding:50px 20px;">', unsafe_allow_html=True)
    st.markdown('<h1 style="font-size:2.5rem;font-weight:800;color:#fff;">🎥 GAIA Meet Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#8b949e;font-size:1.1rem;margin-bottom:40px;">Advanced agricultural video conferencing</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2 = st.tabs(["🎬 Start", "🔗 Join"])
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
else:
    room_id = st.session_state.meet_room_id
    meeting = get_meeting_info(room_id)
    
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
    
    tab_video, tab_chat, tab_features = st.tabs(["📹 Video", "💬 Chat", "🔥 Features"])
    
    with tab_video:
        # ============================================
        # REAL VIRTUAL BACKGROUND using MediaPipe
        # ============================================
        video_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/@mediapipe/selfie_segmentation/selfie_segmentation.js"></script>
            <style>
                body {{ background: #0e1117; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
                .video-container {{ position: relative; width: 100%; max-width: 800px; margin: 0 auto; }}
                .video-stack {{ position: relative; width: 100%; aspect-ratio: 16/9; }}
                video, canvas {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; border-radius: 12px; }}
                #bgCanvas {{ z-index: 1; }}
                #outputCanvas {{ z-index: 2; }}
                #webcam {{ z-index: 3; visibility: hidden; }}
                .controls {{ display: flex; justify-content: center; gap: 10px; padding: 15px; flex-wrap: wrap; }}
                .ctrl-btn {{ background: #252b36; border: none; color: #e0e0e0; border-radius: 50px; padding: 10px 20px; cursor: pointer; font-weight: 600; font-size: 0.85rem; font-family: 'Inter', sans-serif; }}
                .ctrl-btn:hover {{ background: #2d3644; }}
                .ctrl-btn.active {{ background: #2d8cff; color: #fff; }}
                .ctrl-btn.recording {{ background: #dc3545; color: #fff; }}
                .ctrl-btn.end {{ background: #dc3545; color: #fff; }}
                .bg-selector {{ display: flex; gap: 8px; padding: 10px; justify-content: center; }}
                .bg-option {{ width: 50px; height: 35px; border-radius: 6px; cursor: pointer; border: 2px solid transparent; }}
                .bg-option.active {{ border-color: #2d8cff; }}
            </style>
        </head>
        <body>
            <div class="video-container">
                <div class="video-stack">
                    <canvas id="bgCanvas"></canvas>
                    <canvas id="outputCanvas"></canvas>
                    <video id="webcam" autoplay playsinline></video>
                </div>
            </div>
            
            <div class="bg-selector">
                <div class="bg-option" style="background:#1a1a2e;" onclick="setBackground('none', this)" title="No Background"></div>
                <div class="bg-option" style="background:#0d3b0d;" onclick="setBackground('farm', this)" title="Farm"></div>
                <div class="bg-option" style="background:#1a3a5c;" onclick="setBackground('office', this)" title="Office"></div>
                <div class="bg-option" style="background:#333;" onclick="setBackground('blur', this)" title="Blur"></div>
            </div>
            
            <div class="controls">
                <button class="ctrl-btn" id="micBtn" onclick="toggleMic()">🎙️ Mute</button>
                <button class="ctrl-btn" id="camBtn" onclick="toggleCam()">📷 Camera</button>
                <button class="ctrl-btn" id="screenBtn" onclick="toggleScreen()">🖥️ Share</button>
                <button class="ctrl-btn" id="recordBtn" onclick="toggleRecording()">⏺️ Record</button>
                <button class="ctrl-btn end" onclick="endCall()">📞 End</button>
            </div>
            
            <script>
                const webcam = document.getElementById('webcam');
                const bgCanvas = document.getElementById('bgCanvas');
                const outputCanvas = document.getElementById('outputCanvas');
                const bgCtx = bgCanvas.getContext('2d');
                const outCtx = outputCanvas.getContext('2d');
                
                let currentBg = 'none';
                let localStream = null;
                let segModel = null;
                let micEnabled = true;
                let camEnabled = true;
                
                // Farm background gradient
                const farmBg = {{ image: null, draw: function(ctx, w, h) {{
                    const grad = ctx.createLinearGradient(0, 0, 0, h);
                    grad.addColorStop(0, '#4caf50');
                    grad.addColorStop(0.5, '#2e7d32');
                    grad.addColorStop(1, '#1b5e20');
                    ctx.fillStyle = grad;
                    ctx.fillRect(0, 0, w, h);
                    // Add some "crop" dots
                    ctx.fillStyle = '#8bc34a';
                    for (let i = 0; i < 50; i++) {{
                        ctx.fillRect(Math.random()*w, Math.random()*h, 3, 8);
                    }}
                }} }};
                
                const officeBg = {{ image: null, draw: function(ctx, w, h) {{
                    const grad = ctx.createLinearGradient(0, 0, 0, h);
                    grad.addColorStop(0, '#37474f');
                    grad.addColorStop(1, '#263238');
                    ctx.fillStyle = grad;
                    ctx.fillRect(0, 0, w, h);
                }} }};
                
                function setBackground(type, el) {{
                    currentBg = type;
                    document.querySelectorAll('.bg-option').forEach(o => o.classList.remove('active'));
                    if (el) el.classList.add('active');
                }}
                
                async function initCamera() {{
                    try {{
                        localStream = await navigator.mediaDevices.getUserMedia({{
                            video: {{ width: 640, height: 480 }},
                            audio: {{ echoCancellation: true, noiseSuppression: true }}
                        }});
                        webcam.srcObject = localStream;
                        await webcam.play();
                        
                        bgCanvas.width = 640;
                        bgCanvas.height = 480;
                        outputCanvas.width = 640;
                        outputCanvas.height = 480;
                        
                        // Load MediaPipe segmentation
                        const SelfieSegmentation = window.SelfieSegmentation;
                        segModel = new SelfieSegmentation({{
                            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/selfie_segmentation/${{file}}`
                        }});
                        
                        segModel.setOptions({{ modelSelection: 1 }}); // landscape model
                        segModel.onResults(onSegmentationResults);
                        
                        // Start processing loop
                        processFrame();
                    }} catch (e) {{ console.error('Camera error:', e); }}
                }}
                
                async function processFrame() {{
                    if (segModel && webcam.readyState === 4) {{
                        await segModel.send({{ image: webcam }});
                    }}
                    requestAnimationFrame(processFrame);
                }}
                
                function onSegmentationResults(results) {{
                    const w = webcam.videoWidth;
                    const h = webcam.videoHeight;
                    
                    bgCanvas.width = w;
                    bgCanvas.height = h;
                    outputCanvas.width = w;
                    outputCanvas.height = h;
                    
                    // Draw background
                    if (currentBg === 'farm') {{
                        farmBg.draw(bgCtx, w, h);
                    }} else if (currentBg === 'office') {{
                        officeBg.draw(bgCtx, w, h);
                    }} else if (currentBg === 'blur') {{
                        bgCtx.filter = 'blur(20px)';
                        bgCtx.drawImage(webcam, 0, 0, w, h);
                        bgCtx.filter = 'none';
                    }} else {{
                        bgCtx.clearRect(0, 0, w, h);
                    }}
                    
                    // Draw segmented person
                    if (results.segmentationMask) {{
                        outCtx.clearRect(0, 0, w, h);
                        outCtx.drawImage(results.segmentationMask, 0, 0, w, h);
                        
                        // Composite
                        const imageData = outCtx.getImageData(0, 0, w, h);
                        const bgData = bgCtx.getImageData(0, 0, w, h);
                        
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            // Alpha from segmentation mask
                            const alpha = imageData.data[i] / 255;
                            imageData.data[i] = bgData.data[i];
                            imageData.data[i+1] = bgData.data[i+1];
                            imageData.data[i+2] = bgData.data[i+2];
                            imageData.data[i+3] = 255;
                        }}
                        
                        // Now draw webcam with mask
                        const tempCanvas = document.createElement('canvas');
                        tempCanvas.width = w;
                        tempCanvas.height = h;
                        const tempCtx = tempCanvas.getContext('2d');
                        tempCtx.drawImage(webcam, 0, 0, w, h);
                        
                        outCtx.clearRect(0, 0, w, h);
                        outCtx.drawImage(results.segmentationMask, 0, 0, w, h);
                        outCtx.globalCompositeOperation = 'source-in';
                        outCtx.drawImage(tempCanvas, 0, 0, w, h);
                        outCtx.globalCompositeOperation = 'destination-over';
                        outCtx.drawImage(bgCanvas, 0, 0, w, h);
                        outCtx.globalCompositeOperation = 'source-over';
                    }}
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
                    try {{
                        const screenStream = await navigator.mediaDevices.getDisplayMedia({{ video: true }});
                        document.getElementById('screenBtn').textContent = '🖥️ Sharing...';
                    }} catch (e) {{ console.error('Screen error:', e); }}
                }}
                
                function toggleRecording() {{
                    document.getElementById('recordBtn').classList.toggle('recording');
                }}
                
                function endCall() {{
                    if (localStream) localStream.getTracks().forEach(t => t.stop());
                    window.location.reload();
                }}
                
                initCamera();
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
    
    with tab_features:
        st.markdown("### 🎭 Virtual Background (Real-Time)")
        st.markdown("Use the background selector **inside the video panel** to change your virtual background in real-time.")
        st.markdown("""
        - **None** — No background removal
        - **Farm** — Green farm background
        - **Office** — Professional office background
        - **Blur** — Blurred background (like Zoom)
        """)

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
