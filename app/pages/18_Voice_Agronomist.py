
import streamlit as st
import requests
import os
from datetime import datetime
import uuid
from app.utils.scan_util import deduct_scans

DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
GROQ_API_KEY = st.secrets["groq"]["api_key"]


def detect_language(text):
    """Detect Nigerian language based on common words."""
    t = text.lower()
    if any(w in t for w in ["biko", "kedu", "ndewo", "imo", "igbo"]):
        return "ig"
    if any(w in t for w in ["sannu", "barka", "hausa", "zamu", "ya ya"]):
        return "ha"
    if any(w in t for w in ["e kaaro", "bawo", "yoruba", "se", "mo wa"]):
        return "yo"
    if any(w in t for w in ["wetin", "how far", "abi", "dey", "pidgin"]):
        return "pcm"
    return "en-GB"


st.set_page_config(page_title="GAIA - Chat & Voice Agronomist", page_icon="🍅", layout="wide")

# ===== THEME TOGGLE =====
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="voice_theme_toggle")
theme = "dark" if dark_mode else "light"

# ===== SESSION STATE =====
if "voice_history" not in st.session_state:
    st.session_state.voice_history = []
if "processing_audio" not in st.session_state:
    st.session_state.processing_audio = False
if "pending_transcription" not in st.session_state:
    st.session_state.pending_transcription = ""
if "farmer_memory" not in st.session_state:
    st.session_state.farmer_memory = {}
if "audio_to_play" not in st.session_state:
    st.session_state.audio_to_play = None

GAIA_IDENTITY = (
    "You are GAIA, an AI agronomist built by Darkmoor Ltd in Nigeria. "
    "Help African farmers with crop diseases, pests, soil, and livestock. "
    "NEVER mention any other AI company. You ARE GAIA. Be friendly and personal. "
    "IMPORTANT: Always reply in the same language the farmer uses. "
    "If the farmer speaks Hausa, reply in Hausa; Yoruba, reply in Yoruba; "
    "Igbo, reply in Igbo; Pidgin English, reply in Pidgin; English, reply in English. "
    "Speak naturally like a local agronomist, using local farming terms."
)

def build_memory_context():
    if not st.session_state.farmer_memory:
        return ""
    ctx = "You know this about the farmer: "
    for k, v in st.session_state.farmer_memory.items():
        ctx += k + ": " + str(v) + ". "
    return ctx

def update_farmer_memory(question, answer):
    q = question.lower()
    if "my name is" in q:
        st.session_state.farmer_memory["name"] = q.split("my name is")[-1].strip().split()[0].title()
    for crop in ["maize","rice","wheat","beans","cassava","yam","tomato"]:
        if crop in q:
            st.session_state.farmer_memory["crop"] = crop
            break
    for loc in ["kaduna","kano","lagos","abuja","ibadan","enugu"]:
        if loc in q:
            st.session_state.farmer_memory["location"] = loc.title()
            break

def ask_gaia(question):
    system_prompt = GAIA_IDENTITY + " " + build_memory_context()
    headers = {"Authorization": "Bearer " + DEEPSEEK_API_KEY, "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 3000
    }
    try:
        r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"], None
        return None, "Connection error"
    except Exception as e:
        return None, str(e)

def speak_answer(text, language="en-GB"):
    """Convert GAIA's answer to speech and return audio bytes."""
    try:
        from app.utils.deepseek_explainer import text_to_speech
        audio_bytes, err = text_to_speech(text, language)
        if audio_bytes:
            return audio_bytes, None
        return None, err or "Voice unavailable"
    except Exception as e:
        return None, str(e)

# ===== THEME CSS =====
if theme == "dark":
    st.markdown("""
    <style>
        @keyframes bounce { 0%,100%{transform:translateY(0) rotate(0deg)} 25%{transform:translateY(-20px) rotate(15deg)} 50%{transform:translateY(0) rotate(0deg)} 75%{transform:translateY(-10px) rotate(-15deg)} }
        @keyframes glow { 0%,100%{text-shadow:0 0 20px rgba(0,200,83,.6)} 50%{text-shadow:0 0 40px rgba(0,200,83,1),0 0 80px rgba(0,200,83,.8)} }
        @keyframes slideIn { from{opacity:0;transform:translateY(15px)} to{opacity:1;transform:translateY(0)} }
        .dancing-tomato { font-size:5rem;text-align:center;animation:bounce 1.5s infinite ease-in-out;display:inline-block }
        .gaia-title { font-size:2.5rem;font-weight:900;text-align:center;background:linear-gradient(135deg,#00c853,#69f0ae,#00c853);-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:glow 2s ease-in-out infinite alternate }
        .msg-bubble { padding:14px 18px;border-radius:16px;margin:10px 0;font-size:.92rem;line-height:1.6;animation:slideIn .4s ease }
        .msg-user { background:linear-gradient(135deg,#1a5c30,#0d3320);color:#e8f5e9;margin-left:60px;border-bottom-right-radius:4px }
        .msg-gaia { background:#151d18;color:#d1d5db;border:1px solid #1e2d23;margin-right:60px;border-bottom-left-radius:4px }
        .stApp { background:#0d1110 }
        header,footer { visibility:hidden }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @keyframes bounce { 0%,100%{transform:translateY(0) rotate(0deg)} 25%{transform:translateY(-20px) rotate(15deg)} 50%{transform:translateY(0) rotate(0deg)} 75%{transform:translateY(-10px) rotate(-15deg)} }
        @keyframes glowLight { 0%,100%{text-shadow:0 0 15px rgba(46,125,50,.5)} 50%{text-shadow:0 0 30px rgba(46,125,50,1),0 0 60px rgba(46,125,50,.7)} }
        @keyframes slideIn { from{opacity:0;transform:translateY(15px)} to{opacity:1;transform:translateY(0)} }
        .dancing-tomato { font-size:5rem;text-align:center;animation:bounce 1.5s infinite ease-in-out;display:inline-block }
        .gaia-title { font-size:2.5rem;font-weight:900;text-align:center;background:linear-gradient(135deg,#2e7d32,#66bb6a,#2e7d32);-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:glowLight 2s ease-in-out infinite alternate }
        .msg-bubble { padding:14px 18px;border-radius:16px;margin:10px 0;font-size:.92rem;line-height:1.6;animation:slideIn .4s ease }
        .msg-user { background:#2e7d32;color:#fff;margin-left:60px;border-bottom-right-radius:4px }
        .msg-gaia { background:#f1f5f9;color:#1e293b;border:1px solid #e2e8f0;margin-right:60px;border-bottom-left-radius:4px }
        .stApp { background:#f8fafc }
        header,footer { visibility:hidden }
    </style>
    """, unsafe_allow_html=True)

# ===== HEADER =====
st.markdown(f"""
<div style="text-align:center;padding:10px 0;">
    <span class="dancing-tomato">🍅</span>
</div>
<div class="gaia-title">GAIA Chat & Voice Agronomist</div>
<div style="text-align:center;color:#6b7280;margin-bottom:1.5rem;">Speak or type — GAIA listens and talks back</div>
""", unsafe_allow_html=True)

# ===== PLAY STORED AUDIO (after rerun) =====
if st.session_state.audio_to_play:
    st.audio(st.session_state.audio_to_play, format="audio/mp3")
    st.session_state.audio_to_play = None

# ===== PROCESS PENDING TRANSCRIPTION =====
if st.session_state.pending_transcription:
    text = st.session_state.pending_transcription
    st.session_state.pending_transcription = ""
    
    st.success("You said: " + text)
    with st.spinner("🍅 GAIA is thinking..."):
        answer, err = ask_gaia(text)
    if err:
        st.error(err)
    else:
        st.session_state.voice_history.append({
            "id": str(uuid.uuid4())[:8],
            "q": "🎤 " + text,
            "a": answer,
            "t": datetime.now().strftime("%H:%M"),
            "hidden": False
        })
        update_farmer_memory(text, answer)

        # Deduct scans ONCE
        if "user" in st.session_state and st.session_state.user is not None:
            deduct_scans(st.session_state.user.id, 3, "Voice Agronomist")

        # Generate voice response and store for next run
        lang = detect_language(text)
        audio_bytes, speech_err = speak_answer(answer, lang)
        if audio_bytes:
            st.session_state.audio_to_play = audio_bytes
        else:
            st.session_state.audio_to_play = None
            st.caption(f"🔇 Voice unavailable: {speech_err}")

    st.rerun()

# ===== VOICE INPUT =====
st.markdown("### 🎤 Speak to GAIA")

if not st.session_state.processing_audio:
    audio = st.audio_input("Record your question")
    
    if audio is not None:
        st.session_state.processing_audio = True
        
        with st.spinner("🧠 Transcribing your voice..."):
            tmp = "/tmp/gaia_voice.wav"
            with open(tmp, "wb") as f:
                f.write(audio.getvalue() if hasattr(audio, 'getvalue') else audio.read())
            
            headers = {"Authorization": "Bearer " + GROQ_API_KEY}
            with open(tmp, "rb") as f:
                resp = requests.post("https://api.groq.com/openai/v1/audio/transcriptions",
                                   headers=headers, files={"file":("audio.wav",f,"audio/wav")},
                                   data={"model":"whisper-large-v3","language":"en"})
            os.remove(tmp)
            
            if resp.status_code == 200:
                text = resp.json().get("text","").strip()
                if text:
                    st.session_state.pending_transcription = text
                    st.session_state.processing_audio = False
                else:
                    st.warning("No speech detected. Please try again.")
                    st.session_state.processing_audio = False
            else:
                st.error(f"Transcription failed (Error {resp.status_code}). Please type instead.")
            
            # Ensure we can record again after this run
            st.session_state.processing_audio = False
            st.rerun()
else:
    st.info("Processing your previous recording...")
    st.session_state.processing_audio = False

# ===== TEXT INPUT =====
st.markdown("---")
st.markdown("### ⌨️ Or Type")
c1, c2 = st.columns([7,1])
with c1:
    q = st.text_area("", placeholder="Ask anything about your farm...", height=60, label_visibility="collapsed")
with c2:
    st.write("")
    if st.button("Ask 🍅", type="primary", use_container_width=True) and q:
        answer, err = ask_gaia(q)
        if err:
            st.error(err)
        else:
            st.session_state.voice_history.append({
                "id": str(uuid.uuid4())[:8],
                "q": q,
                "a": answer,
                "t": datetime.now().strftime("%H:%M"),
                "hidden": False
            })
            update_farmer_memory(q, answer)
            if "user" in st.session_state and st.session_state.user is not None:
                deduct_scans(st.session_state.user.id, 3, "Voice Agronomist (Text)")
            # Voice reply for typed text too
            lang = detect_language(text)
        audio_bytes, speech_err = speak_answer(answer, lang)
            if audio_bytes:
                st.session_state.audio_to_play = audio_bytes
            st.rerun()

# ===== CONVERSATION =====
st.markdown("---")
if st.session_state.voice_history:
    c1, c2 = st.columns([5,2])
    with c1:
        st.markdown("### 🍅 Conversation")
    with c2:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.voice_history = []
            st.rerun()
    
    for item in reversed(st.session_state.voice_history):
        st.markdown(f'<div style="text-align:right;font-size:.7rem;color:#6b7280;">You - {item["t"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="msg-bubble msg-user">{item["q"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="margin:4px 0;"><span>🍅</span><span style="font-size:.7rem;color:#6b7280;"> GAIA - {item["t"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="msg-bubble msg-gaia">{item["a"]}</div>', unsafe_allow_html=True)

# ===== FARMER MEMORY =====
if st.session_state.farmer_memory:
    st.markdown("---")
    with st.expander("🧠 What GAIA remembers about you", expanded=False):
        for k, v in st.session_state.farmer_memory.items():
            st.write(k.replace("_", " ").title() + ": **" + str(v) + "**")
        if st.button("Clear Memory"):
            st.session_state.farmer_memory = {}
            st.rerun()

# ===== NAVIGATION =====
st.markdown("---")
cols = st.columns(10)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="Livestock")
with cols[5]: st.page_link("pages/18_Voice_Agronomist.py", label="Voice AI")
with cols[6]: st.page_link("pages/17_Video_Scan.py", label="Video Scan")
with cols[7]: st.page_link("pages/10_Early_Warning.py", label="Early Warning")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="Buy Scans")
