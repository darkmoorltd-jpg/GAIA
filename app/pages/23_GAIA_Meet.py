import streamlit as st
import streamlit.components.v1 as components
import uuid
import datetime
import os
import sys
import json
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
if "meet_start_time" not in st.session_state:
    st.session_state.meet_start_time = None
if "my_peer_id" not in st.session_state:
    st.session_state.my_peer_id = None

# ============================================
# SUPABASE
# ============================================
@st.cache_resource
def get_service_client():
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

def create_meeting(user_id, title):
    db = get_service_client()
    room_id = generate_room_id()
    peer_id = f"{room_id}-{user_id[:8]}"
    try:
        db.table("gaia_meetings").insert({
            "room_id": room_id,
            "host_id": user_id,
            "title": title,
            "status": "active",
            "created_at": datetime.datetime.now().isoformat()
        }).execute()
        db.table("meeting_participants").insert({
            "room_id": room_id,
            "user_id": user_id,
            "peer_id": peer_id,
            "joined_at": datetime.datetime.now().isoformat()
        }).execute()
        return room_id, peer_id, None
    except Exception as e:
        return None, None, str(e)

def join_meeting(user_id, room_id):
    db = get_service_client()
    peer_id = f"{room_id}-{user_id[:8]}"
    try:
        db.table("meeting_participants").insert({
            "room_id": room_id,
            "user_id": user_id,
            "peer_id": peer_id,
            "joined_at": datetime.datetime.now().isoformat()
        }).execute()
    except:
        pass
    return peer_id

def get_meeting_info(room_id):
    db = get_service_client()
    try:
        res = db.table("gaia_meetings").select("*").eq("room_id", room_id).execute()
        return res.data[0] if res.data else None
    except:
        return None

def get_participants(room_id):
    db = get_service_client()
    try:
        res = db.table("meeting_participants").select("user_id,peer_id").eq("room_id", room_id).execute()
        return res.data if res.data else []
    except:
        return []

def get_user_name_by_id(user_id):
    db = get_service_client()
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
# JOIN / CREATE
# ============================================
if st.session_state.meet_room_id is None:
    st.markdown("<h1 style='text-align:center;color:#fff;'>🎥 GAIA Meet</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#8b949e;'>Real-time agricultural video conferencing</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2 = st.tabs(["🎬 Start", "🔗 Join"])

        with tab1:
            meeting_title = st.text_input("Meeting Title", value=f"{user_name}'s Agri Clinic")
            if st.button("🚀 Start Meeting", use_container_width=True, type="primary"):
                room_id, peer_id, err = create_meeting(user_id, meeting_title)
                if room_id:
                    st.session_state.meet_room_id = room_id
                    st.session_state.meet_role = "host"
                    st.session_state.my_peer_id = peer_id
                    st.session_state.meet_start_time = datetime.datetime.now()
                    st.rerun()
                else:
                    st.error(str(err)[:120])

        with tab2:
            join_id = st.text_input("Room ID", placeholder="gaia-meet-xxxx")
            if st.button("🔗 Join Meeting", use_container_width=True):
                meeting = get_meeting_info(join_id)
                if meeting:
                    peer_id = join_meeting(user_id, join_id)
                    st.session_state.meet_room_id = join_id
                    st.session_state.meet_role = "participant"
                    st.session_state.my_peer_id = peer_id
                    st.session_state.meet_start_time = datetime.datetime.now()
                    st.rerun()
                else:
                    st.error("Meeting not found.")
else:
    room_id = st.session_state.meet_room_id
    my_peer_id = st.session_state.my_peer_id
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

    st.info("💡 **For screen share:** Use the Pop-out button (⤢) in the top-right corner of the video to open in a new tab. Screen share works best there.")

    # Build the entire meeting UI as one components.html
    meeting_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/peerjs@1.4.7/dist/peerjs.min.js"></script>
        <style>
            body {{ background:#0e1117; margin:0; padding:0; font-family:'Inter',sans-serif; }}
            .meet-container {{ display:flex; flex-direction:column; height:100vh; }}
            .video-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(250px, 1fr)); gap:10px; padding:15px; flex:1; overflow-y:auto; }}
            .video-tile {{ background:#1e2733; border-radius:12px; overflow:hidden; position:relative; aspect-ratio:16/9; }}
            .video-tile video {{ width:100%; height:100%; object-fit:cover; }}
            .name-tag {{ position:absolute; bottom:10px; left:10px; background:rgba(0,0,0,0.7); color:#fff; padding:4px 14px; border-radius:6px; font-size:0.8rem; }}
            .controls {{ display:flex; justify-content:center; gap:10px; padding:12px; background:#161b22; }}
            .ctrl-btn {{ background:#252b36; border:none; color:#e0e0e0; border-radius:50px; padding:10px 18px; cursor:pointer; font-weight:600; font-size:0.85rem; }}
            .ctrl-btn:hover {{ background:#2d3644; }}
            .ctrl-btn.active {{ background:#2d8cff; color:#fff; }}
            .ctrl-btn.recording {{ background:#dc3545; color:#fff; }}
            .ctrl-btn.end {{ background:#dc3545; color:#fff; }}
            .status {{ color:#8b949e; font-size:0.8rem; padding:0 15px; }}
            .chat-panel {{ background:#161b22; border-top:1px solid #252b36; padding:10px; display:flex; flex-direction:column; height:200px; }}
            .chat-messages {{ flex:1; overflow-y:auto; padding:5px; }}
            .chat-msg {{ margin:5px 0; padding:5px 10px; border-radius:6px; max-width:80%; word-wrap:break-word; }}
            .chat-msg.me {{ background:#1a3a5c; color:#7cb8ff; margin-left:auto; }}
            .chat-msg.other {{ background:#252b36; color:#e0e0e0; }}
            .chat-input {{ display:flex; gap:5px; }}
            .chat-input input {{ flex:1; background:#1e2733; border:none; color:#e0e0e0; padding:8px; border-radius:5px; }}
            .chat-input button {{ background:#2d8cff; border:none; color:#fff; padding:8px 15px; border-radius:5px; cursor:pointer; }}
            .participants-section {{ background:#161b22; border-top:1px solid #252b36; padding:10px; }}
            .participant-item {{ display:flex; align-items:center; justify-content:space-between; padding:5px 10px; background:#1e2733; border-radius:8px; margin:4px 0; }}
            .participant-name {{ color:#e0e0e0; font-size:0.9rem; }}
            .call-btn {{ background:#00c853; border:none; color:#000; padding:4px 12px; border-radius:5px; cursor:pointer; font-weight:600; }}
        </style>
    </head>
    <body>
        <div class="meet-container">
            <div class="video-grid" id="videoGrid">
                <div class="video-tile">
                    <video id="localVideo" autoplay muted playsinline></video>
                    <div class="name-tag">You ({user_name})</div>
                </div>
            </div>
            <div class="controls">
                <button class="ctrl-btn" id="micBtn" onclick="toggleMic()">🎙️ Mute</button>
                <button class="ctrl-btn" id="camBtn" onclick="toggleCam()">📷 Camera</button>
                <button class="ctrl-btn" id="screenBtn" onclick="toggleScreen()">🖥️ Share</button>
                <button class="ctrl-btn" id="recordBtn" onclick="toggleRecording()">⏺️ Record</button>
                <button class="ctrl-btn end" onclick="endCall()">📞 End</button>
            </div>
            <div class="status" id="status">Starting...</div>
            <div class="chat-panel">
                <div style="color:#8b949e;font-weight:600;">💬 Chat</div>
                <div class="chat-messages" id="chatMessages"></div>
                <div class="chat-input">
                    <input type="text" id="chatInput" placeholder="Type message..." />
                    <button onclick="sendChat()">Send</button>
                </div>
            </div>
            <div class="participants-section">
                <div style="color:#8b949e;font-weight:600;">👥 Participants</div>
                <div id="participantsList"></div>
            </div>
        </div>
        <script>
            const config = {json.dumps({
                "room_id": room_id,
                "my_peer_id": my_peer_id,
                "supabase_url": st.secrets["supabase"]["url"],
                "supabase_anon_key": st.secrets["supabase"]["key"],
                "user_id": user_id,
                "user_name": user_name
            })};
            const SUPABASE_URL = config.supabase_url;
            const SUPABASE_ANON_KEY = config.supabase_anon_key;
            const ROOM_ID = config.room_id;
            const MY_PEER_ID = config.my_peer_id;
            const USER_ID = config.user_id;
            const USER_NAME = config.user_name;

            let myPeer = null;
            let localStream = null;
            let screenStream = null;
            let mediaRecorder = null;
            let recordedChunks = [];
            let isRecording = false;
            let remoteStreams = new Map();
            let allParticipants = [];

            function updateStatus(msg) { document.getElementById('status').textContent = msg; }

            function getLocalStream() {
                if (localStream) return Promise.resolve(localStream);
                return navigator.mediaDevices.getUserMedia({
                    audio: true,
                    video: { width: 640, height: 480 }
                }).then(stream => {
                    localStream = stream;
                    document.getElementById('localVideo').srcObject = stream;
                    updateStatus('Camera ready');
                    return stream;
                }).catch(err => {
                    updateStatus('Camera/mic error: ' + err.message);
                    throw err;
                });
            }

            function initPeerJS() {
                myPeer = new Peer(MY_PEER_ID);
                myPeer.on('open', (id) => {
                    updateStatus('Connected as ' + id);
                    fetchParticipants();   // Fetch and call existing
                });
                myPeer.on('call', (call) => {
                    getLocalStream().then(stream => {
                        call.answer(stream);
                        call.on('stream', remoteStream => addRemoteVideo(call.peer, remoteStream));
                    }).catch(err => console.error('Failed to answer call', err));
                });
                myPeer.on('error', (err) => {
                    updateStatus('Error: ' + err.type);
                });
            }

            function callPeer(peerId) {
                if (remoteStreams.has(peerId)) return;
                getLocalStream().then(stream => {
                    const call = myPeer.call(peerId, stream);
                    call.on('stream', remoteStream => addRemoteVideo(peerId, remoteStream));
                }).catch(err => console.error('Failed to call peer', err));
            }

            function addRemoteVideo(peerId, stream) {
                if (remoteStreams.has(peerId)) return;
                remoteStreams.set(peerId, stream);
                const grid = document.getElementById('videoGrid');
                const tile = document.createElement('div');
                tile.className = 'video-tile';
                tile.id = 'remote-' + peerId;
                const video = document.createElement('video');
                video.autoplay = true;
                video.playsinline = true;
                video.srcObject = stream;
                video.onloadedmetadata = () => {
                    video.play().catch(() => {
                        video.muted = true;
                        video.play().catch(e => console.log('Autoplay blocked even muted', e));
                    });
                };
                const name = document.createElement('div');
                name.className = 'name-tag';
                name.textContent = 'Participant';
                tile.appendChild(video);
                tile.appendChild(name);
                grid.appendChild(tile);
                updateStatus('Participant video added');
            }

            function fetchParticipants() {
                fetch(`${SUPABASE_URL}/rest/v1/meeting_participants?room_id=eq.${ROOM_ID}&select=user_id,peer_id`, {
                    headers: {
                        'apikey': SUPABASE_ANON_KEY,
                        'Authorization': 'Bearer ' + SUPABASE_ANON_KEY
                    }
                })
                .then(res => res.json())
                .then(data => {
                    allParticipants = data;
                    // Call all other peers
                    data.forEach(p => {
                        if (p.peer_id && p.peer_id !== MY_PEER_ID) {
                            callPeer(p.peer_id);
                        }
                    });
                    renderParticipants(data);
                })
                .catch(err => {
                    updateStatus('Fetch participants error: ' + err.message);
                });
            }

            function renderParticipants(data) {
                const list = document.getElementById('participantsList');
                list.innerHTML = '';
                data.forEach(p => {
                    const item = document.createElement('div');
                    item.className = 'participant-item';
                    const nameSpan = document.createElement('span');
                    nameSpan.className = 'participant-name';
                    nameSpan.textContent = p.user_id === USER_ID ? 'You (' + USER_NAME + ')' : p.user_id;
                    item.appendChild(nameSpan);
                    if (p.peer_id && p.peer_id !== MY_PEER_ID) {
                        const callBtn = document.createElement('button');
                        callBtn.className = 'call-btn';
                        callBtn.textContent = '📞 Call';
                        callBtn.onclick = () => callPeer(p.peer_id);
                        item.appendChild(callBtn);
                    }
                    list.appendChild(item);
                });
            }

            // Poll for participants every 5 seconds
            setInterval(fetchParticipants, 5000);

            // Chat
            function sendChat() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                if (!message) return;
                fetch(`${SUPABASE_URL}/rest/v1/meeting_chat`, {
                    method: 'POST',
                    headers: {
                        'apikey': SUPABASE_ANON_KEY,
                        'Authorization': 'Bearer ' + SUPABASE_ANON_KEY,
                        'Content-Type': 'application/json',
                        'Prefer': 'return=representation'
                    },
                    body: JSON.stringify({
                        room_id: ROOM_ID,
                        user_id: USER_ID,
                        message: message,
                        created_at: new Date().toISOString()
                    })
                }).then(res => {
                    input.value = '';
                    loadChat();
                });
            }

            function loadChat() {
                fetch(`${SUPABASE_URL}/rest/v1/meeting_chat?room_id=eq.${ROOM_ID}&select=user_id,message,created_at&order=created_at.asc`, {
                    headers: {
                        'apikey': SUPABASE_ANON_KEY,
                        'Authorization': 'Bearer ' + SUPABASE_ANON_KEY
                    }
                })
                .then(res => res.json())
                .then(messages => {
                    const container = document.getElementById('chatMessages');
                    container.innerHTML = '';
                    messages.forEach(msg => {
                        const div = document.createElement('div');
                        div.className = 'chat-msg ' + (msg.user_id === USER_ID ? 'me' : 'other');
                        div.innerHTML = '<strong>' + (msg.user_id === USER_ID ? 'You' : 'Other') + ':</strong> ' + msg.message;
                        container.appendChild(div);
                    });
                    container.scrollTop = container.scrollHeight;
                });
            }

            // Controls
            function toggleMic() {
                if (localStream) {
                    const track = localStream.getAudioTracks()[0];
                    if (track) {
                        track.enabled = !track.enabled;
                        document.getElementById('micBtn').textContent = track.enabled ? '🎙️ Mute' : '🔇 Unmute';
                    }
                }
            }
            function toggleCam() {
                if (localStream) {
                    const track = localStream.getVideoTracks()[0];
                    if (track) {
                        track.enabled = !track.enabled;
                        document.getElementById('camBtn').textContent = track.enabled ? '📷 Camera' : '🚫 Off';
                    }
                }
            }
            async function toggleScreen() {
                if (!screenStream) {
                    try {
                        screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
                        document.getElementById('screenBtn').textContent = '🖥️ Stop';
                        screenStream.getVideoTracks()[0].onended = () => {
                            screenStream = null;
                            document.getElementById('screenBtn').textContent = '🖥️ Share';
                        };
                    } catch (e) {
                        alert('Screen share blocked. Use Pop-out button.');
                    }
                } else {
                    screenStream.getTracks().forEach(t => t.stop());
                    screenStream = null;
                    document.getElementById('screenBtn').textContent = '🖥️ Share';
                }
            }
            function toggleRecording() {
                if (!isRecording) {
                    const combined = new MediaStream();
                    if (localStream) localStream.getTracks().forEach(t => combined.addTrack(t));
                    if (screenStream) screenStream.getTracks().forEach(t => combined.addTrack(t));
                    remoteStreams.forEach(s => s.getTracks().forEach(t => combined.addTrack(t)));
                    mediaRecorder = new MediaRecorder(combined, { mimeType: 'video/webm' });
                    recordedChunks = [];
                    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) recordedChunks.push(e.data); };
                    mediaRecorder.onstop = () => {
                        const blob = new Blob(recordedChunks, { type: 'video/webm' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'GAIA_Meeting.webm';
                        a.click();
                        URL.revokeObjectURL(url);
                    };
                    mediaRecorder.start();
                    isRecording = true;
                    document.getElementById('recordBtn').textContent = '⏺️ Recording...';
                    document.getElementById('recordBtn').classList.add('recording');
                } else {
                    mediaRecorder.stop();
                    isRecording = false;
                    document.getElementById('recordBtn').textContent = '⏺️ Record';
                    document.getElementById('recordBtn').classList.remove('recording');
                }
            }
            function endCall() {
                if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop();
                if (localStream) localStream.getTracks().forEach(t => t.stop());
                remoteStreams.forEach(s => s.getTracks().forEach(t => t.stop()));
                if (screenStream) screenStream.getTracks().forEach(t => t.stop());
                if (myPeer) myPeer.destroy();
                window.location.reload();
            }

            // Initialize
            getLocalStream().then(() => {
                initPeerJS();
                loadChat();
            });
        </script>
    </body>
    </html>
    """
    components.html(meeting_html, height=800)

    if st.button("🚪 Leave Meeting", use_container_width=True):
        st.session_state.meet_room_id = None
        st.session_state.my_peer_id = None
        st.session_state.meet_start_time = None
        st.rerun()
