import streamlit as st
import streamlit.components.v1 as components
import requests
import base64
from datetime import datetime
import uuid
import tempfile

DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
GROQ_API_KEY = st.secrets["groq"]["api_key"]

st.set_page_config(page_title="GAIA - Voice Agronomist", page_icon="🍅", layout="wide")

st.markdown("""
<style>
    @keyframes bounce { 0%,100%{transform:translateY(0) rotate(0deg)} 25%{transform:translateY(-20px) rotate(15deg)} 50%{transform:translateY(0) rotate(0deg)} 75%{transform:translateY(-10px) rotate(-15deg)} }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
    @keyframes glow { 0%,100%{text-shadow:0 0 20px rgba(0,200,83,.6)} 50%{text-shadow:0 0 40px rgba(0,200,83,1),0 0 80px rgba(0,200,83,.8)} }
    @keyframes pulse { 0%,100%{transform:scale(1);box-shadow:0 0 30px rgba(255,0,0,.5)} 50%{transform:scale(1.08);box-shadow:0 0 60px rgba(255,0,0,.8)} }
    @keyframes slideIn { from{opacity:0;transform:translateY(15px)} to{opacity:1;transform:translateY(0)} }
    .dancing-tomato { font-size:5rem;text-align:center;animation:bounce 1.5s infinite ease-in-out;display:inline-block }
    .gaia-title { font-size:2.8rem;font-weight:900;text-align:center;background:linear-gradient(135deg,#00c853,#69f0ae,#00c853);-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:glow 2s ease-in-out infinite alternate }
    .gaia-subtitle { text-align:center;color:#6b7280;font-size:1rem;animation:blink 3s ease-in-out infinite }
    .msg-bubble { padding:14px 18px;border-radius:16px;margin:10px 0;font-size:.92rem;line-height:1.6;animation:slideIn .4s ease }
    .msg-user { background:linear-gradient(135deg,#1a5c30,#0d3320);color:#e8f5e9;margin-left:60px;border-bottom-right-radius:4px }
    .msg-gaia { background:#151d18;color:#d1d5db;border:1px solid #1e2d23;margin-right:60px;border-bottom-left-radius:4px }
    .msg-time { font-size:.68rem;color:#6b7280;margin-top:6px }
    .stApp { background:#0d1110 }
    header,footer { visibility:hidden }
    .stButton button { background:linear-gradient(135deg,#00c853,#4caf50)!important;color:#fff!important;border:none!important;border-radius:12px!important;padding:10px 24px!important;font-weight:600!important }
</style>
<div style="text-align:center;padding:10px 0;"><span class="dancing-tomato">🍅</span></div>
<div class="gaia-title">GAIA Voice Agronomist</div>
<div class="gaia-subtitle">Speak or type - GAIA listens and responds</div>
<div class="gaia-subtitle" style="font-size:.75rem;color:#3b82f6;">Powered by Darkmoor Ltd</div>
""", unsafe_allow_html=True)

if "voice_history" not in st.session_state: st.session_state.voice_history = []
if "farmer_memory" not in st.session_state: st.session_state.farmer_memory = {}

GAIA_BASE_IDENTITY = "You are GAIA, an AI agronomist built by Darkmoor Ltd in Nigeria. Help African farmers with crop diseases, pests, soil, and livestock. Never mention any other AI company. You ARE GAIA. Be friendly and personal."

def build_memory_context():
    if not st.session_state.farmer_memory: return ""
    ctx = "You know: "
    for k, v in st.session_state.farmer_memory.items(): ctx += k + ": " + str(v) + ". "
    return ctx

def update_farmer_memory(question, answer):
    q = question.lower()
    if "my name is" in q: st.session_state.farmer_memory["farmer_name"] = q.split("my name is")[-1].strip().split()[0].title()
    for crop in ["maize","rice","wheat","beans","cassava","yam","tomato"]:
        if crop in q: st.session_state.farmer_memory["main_crop"] = crop; break
    for loc in ["kaduna","kano","lagos","abuja","ibadan","enugu"]:
        if loc in q: st.session_state.farmer_memory["location"] = loc.title(); break

def ask_gaia(question):
    system_prompt = GAIA_BASE_IDENTITY + " " + build_memory_context()
    headers = {"Authorization": "Bearer " + DEEPSEEK_API_KEY, "Content-Type": "application/json"}
    payload = {"model":"deepseek-chat","messages":[{"role":"system","content":system_prompt},{"role":"user","content":question}],"temperature":0.7,"max_tokens":1000}
    try:
        r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        if r.status_code == 200: return r.json()["choices"][0]["message"]["content"], None
        return None, "Connection error."
    except: return None, "I am temporarily unavailable."

# ===== VOICE RECORDING =====
st.markdown("### 🎤 Speak to GAIA")
components.html("""
<!DOCTYPE html><html><head><style>
body{margin:0;padding:0;background:#0d1110;display:flex;justify-content:center;align-items:center;min-height:150px}
.mic-btn{width:70px;height:70px;border-radius:50%;border:none;background:linear-gradient(135deg,#f00,#c00);color:#fff;font-size:28px;cursor:pointer;transition:all .3s;box-shadow:0 0 30px rgba(255,0,0,.5)}
.mic-btn:hover{transform:scale(1.1)}
.mic-btn.recording{animation:pulse 1s infinite;background:#333;box-shadow:0 0 50px rgba(255,0,0,.9)}
@keyframes pulse{0%,100%{transform:scale(1);box-shadow:0 0 30px rgba(255,0,0,.5)}50%{transform:scale(1.1);box-shadow:0 0 60px rgba(255,0,0,1)}}
.status{color:#6b7280;margin-top:10px;font-family:sans-serif;text-align:center}
</style></head><body><div style="text-align:center">
<button id="micBtn" class="mic-btn" title="Click to record">🎤</button>
<div class="status" id="status">Click the mic to speak</div></div>
<script>
let mediaRecorder,audioChunks=[],isRecording=false;
const micBtn=document.getElementById("micBtn"),statusDiv=document.getElementById("status");
micBtn.addEventListener("click",async()=>{
if(!isRecording){try{const stream=await navigator.mediaDevices.getUserMedia({audio:true});mediaRecorder=new MediaRecorder(stream);audioChunks=[];
mediaRecorder.ondataavailable=(e)=>audioChunks.push(e.data);
mediaRecorder.onstop=()=>{const blob=new Blob(audioChunks,{type:"audio/webm"});const reader=new FileReader();reader.readAsDataURL(blob);reader.onloadend=()=>{const b64=reader.result.split(",")[1];window.location.href=window.location.href.split("?")[0]+"?audio="+encodeURIComponent(b64)}};
mediaRecorder.start();isRecording=true;micBtn.classList.add("recording");micBtn.textContent="⏹️";statusDiv.textContent="Recording... Click to stop"}
catch(err){statusDiv.textContent="Microphone access denied. Please allow mic access."}}
else{mediaRecorder.stop();isRecording=false;micBtn.classList.remove("recording");micBtn.textContent="🎤";statusDiv.textContent="Processing..."}})
</script></body></html>
""", height=200)

# ===== HANDLE AUDIO =====
query_params = st.query_params
audio_base64 = query_params.get("audio", [None])[0]

if audio_base64:
    with st.spinner("🍅 GAIA is listening..."):
        try:
            audio_bytes = base64.b64decode(audio_base64)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            groq_url = "https://api.groq.com/openai/v1/audio/transcriptions"
            groq_headers = {"Authorization": "Bearer " + GROQ_API_KEY}
            with open(tmp_path, "rb") as f:
                groq_resp = requests.post(groq_url, headers=groq_headers, files={"file":("recording.webm",f,"audio/webm")}, data={"model":"whisper-large-v3","language":"en","temperature":0})
            os.unlink(tmp_path)
            if groq_resp.status_code == 200:
                transcribed = groq_resp.json().get("text","")
                if transcribed:
                    with st.spinner("🍅 GAIA is thinking..."):
                        answer, error = ask_gaia(transcribed)
                    if error: st.error(error)
                    else:
                        st.session_state.voice_history.append({"id":str(uuid.uuid4())[:8],"question":"🎤 "+transcribed,"answer":answer,"time":datetime.now().strftime("%H:%M"),"hidden":False})
                        update_farmer_memory(transcribed, answer)
                else: st.warning("No speech detected.")
            else: st.warning("Transcription failed. Please type instead.")
            st.query_params.clear(); st.rerun()
        except Exception as e: st.warning("Voice unavailable. Please type. (" + str(e)[:80] + ")")

# ===== TEXT INPUT =====
st.markdown("---")
st.markdown("### ⌨️ Or Type")
col1, col2 = st.columns([7, 1])
with col1: question = st.text_area("", placeholder="Ask anything about your farm...", height=60, key="q", label_visibility="collapsed")
with col2: st.write(""); ask_btn = st.button("Ask 🍅", type="primary", use_container_width=True)
if ask_btn and question:
    with st.spinner("🍅 GAIA is thinking..."): answer, error = ask_gaia(question)
    if error: st.error(error)
    else: st.session_state.voice_history.append({"id":str(uuid.uuid4())[:8],"question":question,"answer":answer,"time":datetime.now().strftime("%H:%M"),"hidden":False}); update_farmer_memory(question, answer); st.rerun()

# ===== CONVERSATION =====
st.markdown("---")
if st.session_state.voice_history:
    c1, c2 = st.columns([5, 2])
    with c1: st.markdown("### 🍅 Conversation")
    with c2:
        if st.button("🗑️ Clear All"): st.session_state.voice_history = []; st.rerun()
    for i, item in enumerate(reversed(st.session_state.voice_history)):
        if item.get("hidden"): continue
        idx = len(st.session_state.voice_history) - 1 - i
        st.markdown('<div style="text-align:right;font-size:.7rem;color:#6b7280;">You - '+item["time"]+'</div>', unsafe_allow_html=True)
        st.markdown('<div class="msg-bubble msg-user">'+item["question"]+'</div>', unsafe_allow_html=True)
        st.markdown('<div style="margin:4px 0;"><span>🍅</span><span style="font-size:.7rem;color:#6b7280;"> GAIA - '+item["time"]+'</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="msg-bubble msg-gaia">'+item["answer"].replace("\n","<br>")+'</div>', unsafe_allow_html=True)
        cd, ch, ce = st.columns([1,1,8])
        with cd:
            if st.button("🗑️", key="d"+str(idx)): st.session_state.voice_history.pop(idx); st.rerun()
        with ch:
            if st.button("👁️", key="h"+str(idx)): st.session_state.voice_history[idx]["hidden"] = True; st.rerun()
else:
    st.markdown('<div style="text-align:center;padding:40px;color:#6b7280;"><div style="font-size:4rem;">🍅</div><h3>Start a Conversation</h3><p>Click the microphone to speak, or type below</p></div>', unsafe_allow_html=True)

# ===== MEMORY =====
if st.session_state.farmer_memory:
    with st.expander("🧠 What GAIA remembers about you", expanded=False):
        for k, v in st.session_state.farmer_memory.items(): st.write(k.replace("_"," ").title()+": **"+str(v)+"**")
        if st.button("Clear Memory"): st.session_state.farmer_memory = {}; st.rerun()

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