import streamlit as st
import streamlit.components.v1 as components
import uuid
import datetime
import os
import sys
from supabase import create_client

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

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

# ============================================
# SUPABASE
# ============================================


@st.cache_resource
def get_service_client():
    return create_client(
        st.secrets["supabase"]["url"], st.secrets["supabase"]["service_key"]
    )


def generate_room_id():
    return f"gaia-meet-{uuid.uuid4().hex[:10]}"


def get_user_display_name():
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user.email.split("@")[0].title()
    return "Guest"


def create_meeting(user_id, title):
    db = get_service_client()
    room_id = generate_room_id()
    try:
        db.table("gaia_meetings").insert(
            {
                "room_id": room_id,
                "host_id": user_id,
                "title": title,
                "status": "active",
                "created_at": datetime.datetime.now().isoformat(),
            }
        ).execute()
        return room_id, None
    except Exception as e:
        return None, str(e)


def get_meeting_info(room_id):
    db = get_service_client()
    try:
        res = db.table("gaia_meetings").select("*").eq("room_id", room_id).execute()
        return res.data[0] if res.data else None
    except BaseException:
        return None


def get_user_name_by_id(user_id):
    db = get_service_client()
    try:
        res = (
            db.table("user_profiles")
            .select("first_name,last_name")
            .eq("user_id", user_id)
            .execute()
        )
        if res.data:
            p = res.data[0]
            name = f"{
                p.get(
                    'first_name',
                    '')} {
                p.get(
                    'last_name',
                    '')}".strip()
            if name:
                return name
    except BaseException:
        pass
    return f"Farmer-{str(user_id)[:6]}"


def get_participants(room_id):
    db = get_service_client()
    try:
        res = (
            db.table("meeting_participants")
            .select("user_id")
            .eq("room_id", room_id)
            .execute()
        )
        return res.data if res.data else []
    except BaseException:
        return []


# ============================================
# CSS
# ============================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #0e1117; color: #e0e0e0; }
    header, footer { visibility: hidden; }
    .stTextInput input { background: #1e2733 !important; border: none !important; color: #e0e0e0 !important; border-radius: 8px !important; padding: 12px !important; }
    .stButton button { background: #2d8cff !important; color: #fff !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
    .participant-chip { display: inline-block; background: #1e2733; border-radius: 20px; padding: 5px 14px; margin: 4px; font-size: 0.8rem; }
</style>
""",
    unsafe_allow_html=True,
)

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
    st.markdown(
        "<h1 style='text-align:center;color:#fff;'>🎥 GAIA Meet</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;color:#8b949e;'>Real-time agricultural video conferencing</p>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2 = st.tabs(["🎬 Start", "🔗 Join"])

        with tab1:
            meeting_title = st.text_input(
                "Meeting Title", value=f"{user_name}'s Agri Clinic"
            )
            if st.button("🚀 Start Meeting", use_container_width=True, type="primary"):
                room_id, err = create_meeting(user_id, meeting_title)
                if room_id:
                    st.session_state.meet_room_id = room_id
                    st.session_state.meet_role = "host"
                    st.session_state.meet_start_time = datetime.datetime.now()
                    st.rerun()
                else:
                    st.error(str(err)[:120])

        with tab2:
            join_id = st.text_input("Room ID", placeholder="gaia-meet-xxxx")
            if st.button("🔗 Join Meeting", use_container_width=True):
                meeting = get_meeting_info(join_id)
                if meeting:
                    st.session_state.meet_room_id = join_id
                    st.session_state.meet_role = "participant"
                    st.session_state.meet_start_time = datetime.datetime.now()
                    st.rerun()
                else:
                    st.error("Meeting not found.")
else:
    room_id = st.session_state.meet_room_id
    meeting = get_meeting_info(room_id)

    # Top bar
    elapsed = (
        datetime.datetime.now() - st.session_state.meet_start_time
        if st.session_state.meet_start_time
        else datetime.timedelta(0)
    )
    duration = f"{int(elapsed.total_seconds() //
                      60)}:{int(elapsed.total_seconds() %
                                60):02d}"

    st.markdown(
        f"""
    <div style="background:#161b22;padding:12px 24px;border-bottom:1px solid #252b36;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:1.1rem;font-weight:700;color:#fff;">🎥 {meeting['title'] if meeting else 'GAIA Meeting'}</span>
        <span style="color:#8b949e;font-size:0.8rem;">📋 {room_id} | ⏱ {duration}</span>
        <span style="color:#00c853;">● LIVE</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Jitsi Meet embed — real audio/video, screen share, chat, recording
    jitsi_html = f"""
    <iframe
        src="https://meet.jit.si/{room_id}"
        style="width:100%; height:600px; border:0; border-radius:12px;"
        allow="camera; microphone; fullscreen; display-capture; autoplay"
        allowfullscreen
    ></iframe>
    """
    components.html(jitsi_html, height=620)

    # Participants list (Supabase)
    participants = get_participants(room_id)
    st.markdown("### 👥 Participants")
    for p in participants:
        pname = get_user_name_by_id(p["user_id"])
        st.markdown(
            f'<span class="participant-chip">👤 {pname}</span>', unsafe_allow_html=True
        )

    if st.button("🚪 Leave Meeting", use_container_width=True):
        st.session_state.meet_room_id = None
        st.session_state.meet_start_time = None
        st.rerun()
