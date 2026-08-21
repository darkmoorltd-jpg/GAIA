
import streamlit as st
user = st.session_state.get("user", None)
if user is None:
    st.warning("Please log in first.")
    st.stop()

if user is None:
    # Allow demo mode
    from supabase import create_client
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
try:
    session = supabase.auth.get_session()
    user = session.user if session else None
except:
    import requests
import os
from datetime import datetime
import uuid
import json
from app.utils.scan_util import deduct_scans
from supabase import create_client, Client

DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
GROQ_API_KEY = st.secrets["groq"]["api_key"]
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

st.set_page_config(page_title="GAIA - Chat & Voice Agronomist", page_icon="🍅", layout="wide")

# ===== THEME TOGGLE =====
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

st.markdown("""<style>.stApp{background: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('https://images.unsplash.com/photo-1523741543316-beb7fc7023d8?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80');background-size:cover;background-attachment:fixed;background-position:center;}</style>""", unsafe_allow_html=True)

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
if "recent_chats" not in st.session_state:
    st.session_state.recent_chats = []

# ===== DATABASE HELPERS =====
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def load_recent_chats(user_id, limit=50):
    """Load up to 50 recent chat messages for the user (only used for display, not context)."""
    if not user_id:
        return []
    supabase = init_supabase()
    try:
        res = supabase.table("gaia_chat_memory") \
            .select("question, answer, created_at") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        return list(reversed(res.data)) if res.data else []
    except Exception:
        return []

def save_chat(user_id, question, answer):
    if not user_id:
        return
    supabase = init_supabase()
    try:
        supabase.table("gaia_chat_memory").insert({
            "user_id": user_id,
            "question": question,
            "answer": answer[:2000],
            "created_at": datetime.now().isoformat()
        }).execute()
    except Exception:
        pass

def load_memory_from_db(user_id):
    if not user_id:
        return {}
    supabase = init_supabase()
    try:
        res = supabase.table("farmer_memory").select("key, value").eq("user_id", user_id).execute()
        if res.data:
            mem = {}
            for row in res.data:
                if row.get("key"):
                    mem[row["key"]] = row.get("value", "")
            return mem
    except Exception:
        pass
    return {}

def save_memory_to_db(user_id, key, value):
    if not user_id:
        return
    supabase = init_supabase()
    try:
        supabase.table("farmer_memory").upsert(
            {"user_id": user_id, "key": key, "value": str(value), "updated_at": datetime.now().isoformat()},
            on_conflict="user_id,key"
        ).execute()
    except Exception:
        pass

# ===== INITIAL MEMORY LOAD =====
if "user" in st.session_state and user is not None:
    user_id = user.id
    if not st.session_state.farmer_memory:
        st.session_state.farmer_memory.update(load_memory_from_db(user_id))
        try:
            profile_res = init_supabase().table("user_profiles").select("first_name, last_name, state, primary_crops").eq("user_id", user_id).execute()
            if profile_res.data:
                p = profile_res.data[0]
                if p.get("first_name") and p.get("last_name"):
                    st.session_state.farmer_memory["name"] = f"{p['first_name']} {p['last_name']}".strip()
                if p.get("state"):
                    st.session_state.farmer_memory["location"] = p["state"]
                if p.get("primary_crops"):
                    st.session_state.farmer_memory["crop"] = p["primary_crops"]
        except:
            pass
    if not st.session_state.recent_chats:
        st.session_state.recent_chats = load_recent_chats(user_id)

# ===== GAIA IDENTITY & CONDENSED MEMORY CONTEXT =====
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
    """Build a compact context to keep requests fast."""
    ctx_parts = []
    # Include only essential facts (name, crop, location, last question)
    essential_keys = ["name", "crop", "location"]
    facts = {k: st.session_state.farmer_memory[k] for k in essential_keys if k in st.session_state.farmer_memory}
    if facts:
        ctx_parts.append("Known facts: " + "; ".join(f"{k}: {v}" for k, v in facts.items()))
    # Include only last 5 chats, truncated to 120 chars each
    if st.session_state.recent_chats:
        recent = []
        for chat in st.session_state.recent_chats[-5:]:
            q = chat.get("question", "")[:120]
            a = chat.get("answer", "")[:120]
            recent.append(f"Q: {q}\nA: {a}")
        if recent:
            ctx_parts.append("Recent chat:\n" + "\n".join(recent))
    return "\n\n".join(ctx_parts)

def update_farmer_memory(question, answer):
    q = question.lower()
    user_id = user.id if "user" in st.session_state and user else None

    if "my name is" in q:
        name = q.split("my name is")[-1].strip().split()[0].title()
        st.session_state.farmer_memory["name"] = name
        save_memory_to_db(user_id, "name", name)
    for crop in ["maize","rice","wheat","beans","cassava","yam","tomato"]:
        if crop in q:
            st.session_state.farmer_memory["crop"] = crop
            save_memory_to_db(user_id, "crop", crop)
            break
    for loc in ["kaduna","kano","lagos","abuja","ibadan","enugu"]:
        if loc in q:
            st.session_state.farmer_memory["location"] = loc.title()
            save_memory_to_db(user_id, "location", loc.title())
            break

    save_chat(user_id, question, answer)

    st.session_state.recent_chats.append({
        "question": question,
        "answer": answer,
        "created_at": datetime.now().isoformat()
    })
    st.session_state.recent_chats = st.session_state.recent_chats[-50:]

def ask_gaia_stream(question):
    """Stream response from DeepSeek and update placeholder in real time."""
    system_prompt = GAIA_IDENTITY + "\n\n" + build_memory_context()
    headers = {"Authorization": "Bearer " + DEEPSEEK_API_KEY, "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 3000,
        "stream": True
    }

    full_answer = ""
    placeholder = st.empty()

    try:
        r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, stream=True, timeout=60)
        if r.status_code != 200:
            return None, f"API error: {r.status_code}"

        for line in r.iter_lines():
            if not line:
                continue
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk['choices'][0].get('delta', {}).get('content', '')
                    if delta:
                        full_answer += delta
                        placeholder.markdown(full_answer + "▌")
                except:
                    continue

        placeholder.markdown(full_answer)
        return full_answer, None
    except Exception as e:
        return None, str(e)

def detect_language(text):
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

def speak_answer(text, language="en-GB"):
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
        .stApp { background: linear-gradient(rgba(13,17,16,0.4), rgba(13,17,16,0.4)), url("https://images.unsplash.com/photo-1523741543316-beb7fc7023d8?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80") center/cover fixed; }
        header,footer { visibility:hidden }
        .msg-user, .msg-gaia, .gaia-title, .subtitle, .dancing-tomato, .stMarkdown, .stMarkdown p { text-shadow: 1px 1px 4px rgba(0,0,0,0.3); }
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
        .stApp { background: linear-gradient(rgba(248,250,252,0.5), rgba(248,250,252,0.5)), url("https://images.unsplash.com/photo-1523741543316-beb7fc7023d8?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80") center/cover fixed; }
        header,footer { visibility:hidden }
        .msg-user, .msg-gaia, .gaia-title, .subtitle, .dancing-tomato, .stMarkdown, .stMarkdown p { text-shadow: 1px 1px 4px rgba(0,0,0,0.3); }
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

# ===== PLAY STORED AUDIO =====
if st.session_state.audio_to_play:
    st.audio(st.session_state.audio_to_play, format="audio/mp3")
    st.session_state.audio_to_play = None

# ===== PROCESS PENDING TRANSCRIPTION =====
if st.session_state.pending_transcription:
    text = st.session_state.pending_transcription
    st.session_state.pending_transcription = ""

    st.success("You said: " + text)
    with st.spinner("🍅 GAIA is thinking..."):
        answer, err = ask_gaia_stream(text)
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

        if "user" in st.session_state and user is not None:
            deduct_scans(user.id, 3, "Voice Agronomist")

        lang = detect_language(text)
        audio_bytes, speech_err = speak_answer(answer, lang)
        if audio_bytes:
            st.session_state.audio_to_play = audio_bytes
        else:
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
                else:
                    st.warning("No speech detected. Please try again.")
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
        answer, err = ask_gaia_stream(q)
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
            if "user" in st.session_state and user is not None:
                deduct_scans(user.id, 3, "Voice Agronomist (Text)")
            lang = detect_language(q)
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
            if "user" in st.session_state and user is not None:
                try:
                    init_supabase().table("farmer_memory").delete().eq("user_id", user.id).execute()
                except:
                    pass
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
