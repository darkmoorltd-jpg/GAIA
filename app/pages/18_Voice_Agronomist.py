import streamlit as st
import requests
import os
from datetime import datetime
import uuid

DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
GROQ_API_KEY = st.secrets["groq"]["api_key"]

st.set_page_config(page_title="GAIA - Voice Agronomist", page_icon="🍅", layout="wide")

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
<div style="text-align:center;padding:10px 0;"><span class="dancing-tomato">🍅</span></div>
<div class="gaia-title">GAIA Voice Agronomist</div>
<div style="text-align:center;color:#6b7280;margin-bottom:1.5rem;">Speak or type - GAIA listens and responds</div>
""", unsafe_allow_html=True)

# ===== SESSION STATE =====
if "voice_history" not in st.session_state:
    st.session_state.voice_history = []
if "processing_audio" not in st.session_state:
    st.session_state.processing_audio = False
if "pending_transcription" not in st.session_state:
    st.session_state.pending_transcription = ""

GAIA_IDENTITY = "You are GAIA, an AI agronomist built by Darkmoor Ltd in Nigeria. Help African farmers with crop diseases, pests, soil, and livestock. Never mention any other AI company. You ARE GAIA. Be friendly and personal."

def ask_gaia(question):
    headers = {"Authorization": "Bearer " + DEEPSEEK_API_KEY, "Content-Type": "application/json"}
    payload = {"model":"deepseek-chat","messages":[{"role":"system","content":GAIA_IDENTITY},{"role":"user","content":question}],"temperature":0.7,"max_tokens":1000}
    try:
        r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"], None
        return None, "Connection error"
    except:
        return None, "Temporarily unavailable"

# ===== PROCESS PENDING TRANSCRIPTION (prevents loop) =====
if st.session_state.pending_transcription:
    text = st.session_state.pending_transcription
    st.session_state.pending_transcription = ""  # Clear immediately to prevent loop
    
    st.success("You said: " + text)
    with st.spinner("🍅 GAIA is thinking..."):
        answer, err = ask_gaia(text)
    if err:
        st.error(err)
    else:
        st.session_state.voice_history.append({
            "q": "🎤 " + text,
            "a": answer,
            "t": datetime.now().strftime("%H:%M")
        })
    st.rerun()

# ===== VOICE INPUT =====
st.markdown("### 🎤 Speak to GAIA")

# Only show audio input if not currently processing
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
                else:
                    st.warning("No speech detected. Please try again.")
                    st.session_state.processing_audio = False
            else:
                st.error(f"Transcription failed (Error {resp.status_code}). Please type instead.")
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
            st.session_state.voice_history.append({"q":q,"a":answer,"t":datetime.now().strftime("%H:%M")})
            st.rerun()

# ===== CONVERSATION =====
st.markdown("---")
if st.session_state.voice_history:
    c1, c2 = st.columns([5,2])
    with c1: st.markdown("### 🍅 Conversation")
    with c2:
        if st.button("Clear All"): st.session_state.voice_history = []; st.rerun()
    for i, item in enumerate(reversed(st.session_state.voice_history)):
        st.markdown(f'<div style="text-align:right;font-size:.7rem;color:#6b7280;">You - {item["t"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="msg-bubble msg-user">{item["q"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="margin:4px 0;"><span>🍅</span><span style="font-size:.7rem;color:#6b7280;"> GAIA - {item["t"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="msg-bubble msg-gaia">{item["a"]}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center;padding:40px;color:#6b7280;"><div style="font-size:4rem;">🍅</div><h3>Start a Conversation</h3><p>Click the mic button above to speak, or type below</p></div>', unsafe_allow_html=True)

# ===== NAVIGATION =====
st.markdown("---")
cols = st.columns(9)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="Livestock")
with cols[5]: st.page_link("pages/18_Voice_Agronomist.py", label="Voice AI")
with cols[6]: st.page_link("pages/17_Video_Scan.py", label="Video Scan")
with cols[7]: st.page_link("pages/10_Early_Warning.py", label="Early Warning")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="Buy Scans")
