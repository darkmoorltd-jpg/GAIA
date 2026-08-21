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
if "raise_hand" not in st.session_state:
    st.session_state.raise_hand = False
if "current_poll" not in st.session_state:
    st.session_state.current_poll = None
if "meeting_notes" not in st.session_state:
    st.session_state.meeting_notes = []
if "breakout_rooms" not in st.session_state:
    st.session_state.breakout_rooms = {}
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
    from app.utils.sms_util import send_sms
    message = f"GAIA Meet: Join video meeting now! Room ID: {room_id}"
    return send_sms(phone, message)

def generate_ai_notes(meeting_title, participants, crop_focus):
    return f"""📋 GAIA MEETING NOTES
    Date: {datetime.datetime.now().strftime('%d %B %Y')}
    Time: {datetime.datetime.now().strftime('%H:%M')}
    Meeting: {meeting_title}
    Crop: {crop_focus or 'General'}
    Participants: {len(participants)}
    
    ✅ Action Items:
    - Monitor affected fields
    - Apply treatment within 48 hours
    - Follow-up in 7 days
    """

# ============================================
# CSS
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #0e1117; color: #e0e0e0; }
    header, footer { visibility: hidden; }
    .stTextInput input { background: #1e2733 !important; border: none !important; color: #e0e0e0 !important; border-radius: 8px !important; padding: 12px !important; }
    .stButton button { background: #2d8cff !important; color: #fff !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
    .chat-message { margin: 8px 0; padding: 8px 12px; border-radius: 8px; max-width: 85%; word-wrap: break-word; font-size: 0.9rem; }
    .chat-message.me { background: #1a3a5c; color: #7cb8ff; margin-left: auto; }
    .chat-message.other { background: #252b36; color: #e0e0e0; }
    .participant-chip { display: inline-block; background: #1e2733; border-radius: 20px; padding: 5px 14px; margin: 4px; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# ============================================
# AUTH
# ============================================
if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in to use GAIA Meet.")
    st.stop()

user = st.session_state.user
user_id = user.id
user_name = get_user_display_name()

# ============================================
# JOIN / CREATE SCREEN
# ============================================
if st.session_state.meet_room_id is None:
    st.markdown("<h1 style='text-align:center;color:#fff;'>🎥 GAIA Meet</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#8b949e;'>Agricultural video conferencing</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2, tab3 = st.tabs(["🎬 Start", "🔗 Join", "📱 SMS Invite"])

        with tab1:
            meeting_title = st.text_input("Meeting Title", value=f"{user_name}'s Agri Clinic")
            crop_focus = st.selectbox("Crop Focus", ["None", "Maize", "Rice", "Beans", "Tomato"])
            meeting_password = st.text_input("Password (optional)", type="password")
            if st.button("🚀 Start Meeting", use_container_width=True, type="primary"):
                room_id, err = create_meeting(user_id, meeting_title, crop_focus, meeting_password or None)
                if room_id:
                    st.session_state.meet_room_id = room_id
                    st.session_state.meet_role = "host"
                    st.session_state.meet_participants = [user_id]
                    st.session_state.meet_start_time = datetime.datetime.now()
                    st.rerun()
                else:
                    st.error(str(err)[:120])

        with tab2:
            join_id = st.text_input("Room ID", placeholder="gaia-meet-xxxx")
            join_password = st.text_input("Password", type="password")
            if st.button("🔗 Join Meeting", use_container_width=True):
                meeting = get_meeting_info(join_id)
                if meeting:
                    if meeting.get("password") and meeting["password"] != join_password:
                        st.error("Incorrect password.")
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
                    st.success("Invite sent!")
                else:
                    st.error(str(err))
else:
    room_id = st.session_state.meet_room_id
    meeting = get_meeting_info(room_id)

    # Top bar
    elapsed = datetime.datetime.now() - st.session_state.meet_start_time if st.session_state.meet_start_time else datetime.timedelta(0)
    duration = f"{int(elapsed.total_seconds() // 60)}:{int(elapsed.total_seconds() % 60):02d}"

    st.markdown(f"""
    <div style="background:#161b22;padding:12px 24px;border-bottom:1px solid #252b36;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:1.1rem;font-weight:700;color:#fff;">🎥 {meeting['title'] if meeting else 'GAIA Meeting'}</span>
        <span style="color:#8b949e;font-size:0.8rem;">📋 {room_id} | ⏱ {duration}</span>
        <span style="color:#00c853;">● LIVE</span>
    </div>
    """, unsafe_allow_html=True)

    tab_video, tab_chat, tab_controls, tab_features = st.tabs(["📹 Video", "💬 Chat", "🎛️ Controls", "🔥 Features"])

    with tab_video:
        st.info("💡 For screen share, click the **Pop-out button (⤢)** in the top-right corner of the video to open in a new tab.")

        video_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ background:#0e1117; margin:0; padding:0; font-family:'Inter',sans-serif; }}
                .video-grid {{ display:grid; grid-template-columns:1fr; gap:10px; padding:15px; }}
                .video-tile {{ background:#1e2733; border-radius:12px; overflow:hidden; position:relative; aspect-ratio:16/9; }}
                .video-tile video {{ width:100%; height:100%; object-fit:cover; }}
                .name-tag {{ position:absolute; bottom:10px; left:10px; background:rgba(0,0,0,0.7); color:#fff; padding:4px 14px; border-radius:6px; font-size:0.8rem; }}
                .controls {{ display:flex; justify-content:center; gap:10px; padding:12px; background:#161b22; border-radius:12px; margin-top:10px; flex-wrap:wrap; }}
                .ctrl-btn {{ background:#252b36; border:none; color:#e0e0e0; border-radius:50px; padding:10px 18px; cursor:pointer; font-weight:600; font-size:0.85rem; }}
                .ctrl-btn:hover {{ background:#2d3644; }}
                .ctrl-btn.active {{ background:#2d8cff; color:#fff; }}
                .ctrl-btn.recording {{ background:#dc3545; color:#fff; }}
                .ctrl-btn.end {{ background:#dc3545; color:#fff; }}
                .recording-indicator {{ position:fixed; top:10px; right:10px; background:#dc3545; color:#fff; padding:5px 15px; border-radius:20px; font-size:0.8rem; display:none; z-index:999; }}
            </style>
        <script src="https://unpkg.com/peerjs@1.4.7/dist/peerjs.min.js"></script>
</head>
        <body>
            <div class="recording-indicator" id="recIndicator">⏺ RECORDING</div>
            <div class="video-grid">
                <div class="video-tile">
                    <video id="mainVideo" autoplay muted playsinline></video>
                    <div class="name-tag">You ({user_name})</div>
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
                
        // ========== PEERJS REAL-TIME AUDIO/VIDEO ==========
        const roomId = '{room_id}';
        const myUserId = '{user_id}';
        const myPeerId = roomId + '-' + myUserId.substring(0, 8);
        let myPeer = null;
        let localStream = null;
        let remoteStreams = new Map();

        // Initialize PeerJS
        function initPeerJS() {{
            myPeer = new Peer(myPeerId);
            myPeer.on('open', (id) => {{
                console.log('My peer ID:', id);
                // Register in Supabase via Streamlit (we'll do a postMessage or use a hidden input)
                window.parent.postMessage({{
                    type: 'peer_registered',
                    peer_id: id,
                    room_id: roomId
                }}, '*');
            }});

            myPeer.on('call', (call) => {{
                navigator.mediaDevices.getUserMedia({{
                    audio: true,
                    video: true
                }}).then((stream) => {{
                    call.answer(stream);
                    call.on('stream', (remoteStream) => {{
                        addRemoteVideo(call.peer, remoteStream);
                    }});
                }}).catch(err => console.error('Mic/cam error:', err));
            }});
        }}

        // Start local video and mic
        async function startCamera() {{
            try {{
                localStream = await navigator.mediaDevices.getUserMedia({{
                    audio: true,
                    video: {{ width: 640, height: 480 }}
                }});
                document.getElementById('mainVideo').srcObject = localStream;
            }} catch (e) {{
                console.error('Camera error:', e);
            }}
        }}

        // Call a peer
        function callPeer(remotePeerId) {{
            if (!localStream) {{
                // try to get stream if not already
                navigator.mediaDevices.getUserMedia({{
                    audio: true,
                    video: true
                }}).then(stream => {{
                    localStream = stream;
                    document.getElementById('mainVideo').srcObject = localStream;
                    doCall(remotePeerId, stream);
                }});
            }} else {{
                doCall(remotePeerId, localStream);
            }}
        }}

        function doCall(remotePeerId, stream) {{
            const call = myPeer.call(remotePeerId, stream);
            call.on('stream', (remoteStream) => {{
                addRemoteVideo(remotePeerId, remoteStream);
            }});
        }}

        // Add remote video tile
        function addRemoteVideo(peerId, stream) {{
            if (remoteStreams.has(peerId)) return;
            remoteStreams.set(peerId, stream);
            const grid = document.getElementById('videoGrid');
            const tile = document.createElement('div');
            tile.className = 'video-tile';
            tile.id = 'remote-' + peerId;
            tile.innerHTML = '<video autoplay playsinline></video><div class="name-tag">Participant</div>';
            grid.appendChild(tile);
            tile.querySelector('video').srcObject = stream;
        }}

        // Signal to Streamlit that we are ready
        window.parent.postMessage({{ type: 'meet_ready' }}, '*');

        // Start everything
        initPeerJS();
        startCamera();

        // ========== EXISTING CONTROLS (mic, cam, etc.) ==========
        // We'll keep the existing control functions but ensure they work on localStream
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
        function toggleRecording() {{
            if (!isRecording) {{
                try {{
                    const combined = new MediaStream();
                    if (localStream) localStream.getTracks().forEach(t => combined.addTrack(t));
                    remoteStreams.forEach(s => s.getTracks().forEach(t => combined.addTrack(t)));
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
        function endCall() {{
            if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop();
            if (localStream) localStream.getTracks().forEach(t => t.stop());
            remoteStreams.forEach(s => s.getTracks().forEach(t => t.stop()));
            if (myPeer) myPeer.destroy();
            window.location.reload();
        }}

            </script>
        </body>
        </html>
        """
        components.html(video_html, height=550)

        if st.button("🚪 Leave Meeting", use_container_width=True):
            dur_min = int((datetime.datetime.now() - st.session_state.meet_start_time).total_seconds() // 60) if st.session_state.meet_start_time else 0
            save_meeting_analytics(room_id, user_id, dur_min, len(st.session_state.meet_participants), len(get_meeting_chat(room_id)))
            st.session_state.meet_room_id = None
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
                f'<div style="font-size:0.7rem;color:#6b7280;">{time_str}</div>'
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
        st.markdown("### Host Controls")
        for pid in st.session_state.meet_participants:
            pname = get_user_name_by_id(pid)
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f'<span class="participant-chip">👤 {pname}</span>', unsafe_allow_html=True)
            with col2:
                if st.session_state.meet_role == "host" and pid != user_id:
                    if st.button(f"Remove", key=f"rm_{pid}"):
                        st.session_state.meet_participants.remove(pid)
                        st.rerun()
        if st.session_state.meet_role == "host":
            if st.button("🔇 Mute All (simulated)", use_container_width=True):
                st.success("Muted all.")

    with tab_features:
        feat1, feat2, feat3, feat4, feat5, feat6 = st.tabs(["🖼️ Whiteboard", "🎭 BG", "🗣️ Breakouts", "📊 Polls", "📝 Notes", "📱 SMS"])

        with feat1:
            st.markdown("#### Whiteboard")
            st.markdown("Draw on the canvas (pop-out for best experience):")
            components.html("""
            <canvas id="wb" width="600" height="400" style="border:2px solid #2d8cff;border-radius:8px;background:#fff;cursor:crosshair;"></canvas>
            <br><button onclick="clearWB()" style="background:#dc3545;color:#fff;border:none;padding:8px 20px;border-radius:6px;cursor:pointer;">Clear</button>
            <script>
                const c = document.getElementById('wb');
                const x = c.getContext('2d');
                let d = false, lx = 0, ly = 0;
                c.addEventListener('mousedown', e => { d = true; lx = e.offsetX; ly = e.offsetY; });
                c.addEventListener('mousemove', e => { if (!d) return; x.beginPath(); x.moveTo(lx, ly); x.lineTo(e.offsetX, e.offsetY); x.strokeStyle = '#000'; x.lineWidth = 2; x.stroke(); lx = e.offsetX; ly = e.offsetY; });
                c.addEventListener('mouseup', () => { d = false; });
                function clearWB() { x.clearRect(0, 0, c.width, c.height); }
            </script>
            """, height=500)

        with feat2:
            st.markdown("#### Virtual Background")
            bg = st.selectbox("Background", ["None", "Farm", "Office", "Blur"])
            if bg != "None":
                st.success(f"Background '{bg}' selected (simulated).")

        with feat3:
            st.markdown("#### Breakout Rooms")
            n = st.number_input("Rooms", min_value=1, max_value=10, value=2)
            if st.button("Create Breakout Rooms", use_container_width=True):
                parts = list(st.session_state.meet_participants)
                rooms = {f"Room {i+1}": [] for i in range(int(n))}
                for i, p in enumerate(parts):
                    rooms[f"Room {(i % int(n)) + 1}"].append(p)
                st.session_state.breakout_rooms = rooms
                st.success("Created!")
            for rname, members in st.session_state.breakout_rooms.items():
                st.markdown(f"**{rname}:** {', '.join([get_user_name_by_id(m) for m in members])}")

        with feat4:
            st.markdown("#### Polls")
            pq = st.text_input("Poll Question")
            po = st.text_area("Options (one per line)", "Yes\nNo\nNot sure")
            if st.button("Launch Poll", use_container_width=True):
                opts = [o.strip() for o in po.split('\n') if o.strip()]
                st.session_state.current_poll = {"q": pq, "opts": opts, "votes": {o: 0 for o in opts}}
                st.success("Poll launched!")
            if st.session_state.current_poll:
                st.markdown(f"**{st.session_state.current_poll['q']}**")
                for opt in st.session_state.current_poll['opts']:
                    if st.button(opt, key=f"vote_{opt}"):
                        st.session_state.current_poll['votes'][opt] += 1
                        st.rerun()
                st.markdown("#### Results")
                for opt, cnt in st.session_state.current_poll['votes'].items():
                    st.write(f"{opt}: {cnt}")

        with feat5:
            st.markdown("#### AI Meeting Notes")
            if st.button("Generate Notes", use_container_width=True):
                notes = generate_ai_notes(meeting['title'] if meeting else "GAIA Meeting", st.session_state.meet_participants, meeting.get('crop_focus') if meeting else None)
                st.markdown(notes)

        with feat6:
            st.markdown("#### SMS Invite")
            inv_phone = st.text_input("Phone", placeholder="08012345678")
            if st.button("Send Invite", use_container_width=True):
                ok, err = send_sms_invite(inv_phone, room_id)
                if ok:
                    st.success("Sent!")
                else:
                    st.error(str(err))

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
