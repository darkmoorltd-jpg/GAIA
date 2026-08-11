import streamlit as st
import requests
from datetime import datetime
import uuid

DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

st.set_page_config(page_title="GAIA - Voice Agronomist", page_icon="🍅", layout="wide")

# ===== ANIMATED TOMATO + HEADER =====
st.markdown("""
<style>
    @keyframes bounce {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        25% { transform: translateY(-20px) rotate(15deg); }
        50% { transform: translateY(0) rotate(0deg); }
        75% { transform: translateY(-10px) rotate(-15deg); }
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    @keyframes glow {
        0%, 100% { text-shadow: 0 0 20px rgba(0,200,83,0.6); }
        50% { text-shadow: 0 0 40px rgba(0,200,83,1), 0 0 80px rgba(0,200,83,0.8); }
    }
    .dancing-tomato {
        font-size: 5rem;
        text-align: center;
        animation: bounce 1.5s infinite ease-in-out;
        display: inline-block;
    }
    .gaia-title {
        font-size: 2.8rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(135deg, #00c853, #69f0ae, #00c853);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: glow 2s ease-in-out infinite alternate;
    }
    .gaia-subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 1rem;
        animation: blink 3s ease-in-out infinite;
    }
    .msg-container {
        max-width: 850px;
        margin: 0 auto;
        padding: 10px;
    }
    .msg-bubble {
        padding: 14px 18px;
        border-radius: 16px;
        margin: 10px 0;
        font-size: 0.92rem;
        line-height: 1.6;
        animation: slideIn 0.4s ease;
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .msg-user {
        background: linear-gradient(135deg, #1a5c30, #0d3320);
        color: #e8f5e9;
        margin-left: 80px;
        border-bottom-right-radius: 4px;
    }
    .msg-gaia {
        background: #151d18;
        color: #d1d5db;
        border: 1px solid #1e2d23;
        margin-right: 80px;
        border-bottom-left-radius: 4px;
    }
    .msg-time {
        font-size: 0.68rem;
        color: #6b7280;
        margin-top: 6px;
    }
    .stApp {
        background: #0d1110;
    }
    header, footer { visibility: hidden; }
    .stButton button {
        background: linear-gradient(135deg, #00c853, #4caf50) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
    }
</style>
<div style="text-align:center;padding:20px;">
    <span class="dancing-tomato">🍅</span>
</div>
<div class="gaia-title">GAIA Voice Agronomist</div>
<div class="gaia-subtitle">Your AI farm assistant - ask anything, get expert answers</div>
<div class="gaia-subtitle" style="font-size:0.75rem;color:#3b82f6;">Powered by Darkmoor Ltd</div>
""", unsafe_allow_html=True)

# ===== SESSION STATE =====
if "voice_history" not in st.session_state:
    st.session_state.voice_history = []
if "hidden_messages" not in st.session_state:
    st.session_state.hidden_messages = set()
if "farmer_memory" not in st.session_state:
    st.session_state.farmer_memory = {}

# ===== GAIA IDENTITY WITH MEMORY =====
GAIA_BASE_IDENTITY = "You are GAIA, an AI agronomist built by Darkmoor Ltd in Nigeria. Help African farmers with crop diseases, pests, soil, and livestock. Never mention any other AI company. You ARE GAIA. Be friendly and personal - you know this farmer and care about their farm."

def build_memory_context():
    if not st.session_state.farmer_memory:
        return ""
    ctx = "You know the following about this farmer from previous conversations: "
    for key, value in st.session_state.farmer_memory.items():
        ctx += key + ": " + str(value) + ". "
    return ctx

def update_farmer_memory(question, answer):
    question_lower = question.lower()
    if "my name is" in question_lower:
        name = question_lower.split("my name is")[-1].strip().split()[0].title()
        st.session_state.farmer_memory["farmer_name"] = name
    if any(crop in question_lower for crop in ["maize", "rice", "wheat", "beans", "cassava", "yam"]):
        for crop in ["maize", "rice", "wheat", "beans", "cassava", "yam"]:
            if crop in question_lower:
                st.session_state.farmer_memory["main_crop"] = crop
    if any(loc in question_lower for loc in ["kaduna", "kano", "lagos", "abuja", "ibadan", "enugu"]):
        for loc in ["kaduna", "kano", "lagos", "abuja", "ibadan", "enugu"]:
            if loc in question_lower:
                st.session_state.farmer_memory["location"] = loc.title()

def ask_gaia(question):
    memory_ctx = build_memory_context()
    system_prompt = GAIA_BASE_IDENTITY + " " + memory_ctx
    headers = {"Authorization": "Bearer " + DEEPSEEK_API_KEY, "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": question}], "temperature": 0.7, "max_tokens": 1000}
    try:
        r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"], None
        return None, "Connection error. Please try again."
    except:
        return None, "I am temporarily unavailable."

# ===== INPUT AREA =====
st.markdown('<div style="max-width:850px;margin:0 auto;">', unsafe_allow_html=True)
col1, col2 = st.columns([7, 1])
with col1:
    question = st.text_area("", placeholder="Ask anything about your farm... e.g., My maize leaves have brown spots with yellow edges", height=60, key="q", label_visibility="collapsed")
with col2:
    st.write("")
    ask_btn = st.button("Ask 🍅", type="primary", use_container_width=True)

if ask_btn and question:
    with st.spinner("🍅 GAIA is thinking..."):
        answer, error = ask_gaia(question)
    if error:
        st.error(error)
    else:
        msg_id = str(uuid.uuid4())[:8]
        st.session_state.voice_history.append({"id": msg_id, "question": question, "answer": answer, "time": datetime.now().strftime("%H:%M"), "hidden": False})
        update_farmer_memory(question, answer)
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ===== CONVERSATION DISPLAY =====
st.markdown("---")

if st.session_state.voice_history:
    col_title, col_actions = st.columns([5, 2])
    with col_title:
        st.markdown("### 🍅 Your Conversation")
    with col_actions:
        if st.button("🗑️ Clear All", key="clear_all"):
            st.session_state.voice_history = []
            st.rerun()
        if st.button("👁️ Show All" if any(item.get("hidden", False) for item in st.session_state.voice_history) else "All Visible", key="show_all"):
            for item in st.session_state.voice_history:
                item["hidden"] = False
            st.rerun()

    visible_count = 0
    for i, item in enumerate(reversed(st.session_state.voice_history)):
        if item.get("hidden", False):
            continue
        visible_count += 1
        msg_idx = len(st.session_state.voice_history) - 1 - i
        
        st.markdown('<div class="msg-container">', unsafe_allow_html=True)
        
        st.markdown('<div style="display:flex;justify-content:flex-end;"><div style="font-size:0.7rem;color:#6b7280;margin-bottom:2px;">You - ' + item["time"] + '</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="msg-bubble msg-user">' + item["question"] + '</div>', unsafe_allow_html=True)
        
        st.markdown('<div style="display:flex;align-items:center;gap:8px;margin:4px 0;"><span style="font-size:1.2rem;">🍅</span><span style="font-size:0.7rem;color:#6b7280;">GAIA - ' + item["time"] + '</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="msg-bubble msg-gaia">' + item["answer"].replace("\n", "<br>") + '</div>', unsafe_allow_html=True)
        
        col_del, col_hide, col_empty = st.columns([1, 1, 8])
        with col_del:
            if st.button("🗑️", key="del_" + str(msg_idx), help="Delete this message"):
                st.session_state.voice_history.pop(msg_idx)
                st.rerun()
        with col_hide:
            if st.button("👁️", key="hide_" + str(msg_idx), help="Hide this message"):
                st.session_state.voice_history[msg_idx]["hidden"] = True
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if visible_count == 0:
        st.info("All messages are hidden. Click Show All to see them.")
else:
    st.markdown("""
    <div style="text-align:center;padding:40px;color:#6b7280;">
        <div style="font-size:4rem;">🍅</div>
        <h3>Start a Conversation</h3>
        <p>Ask GAIA anything about your farm</p>
        <p style="font-size:0.85rem;">Try: "My name is Ibrahim. I grow maize in Kaduna. My leaves have brown spots."</p>
    </div>
    """, unsafe_allow_html=True)

# ===== FARMER MEMORY DISPLAY =====
if st.session_state.farmer_memory:
    with st.expander("🧠 What GAIA remembers about you", expanded=False):
        for key, value in st.session_state.farmer_memory.items():
            st.write(key.replace("_", " ").title() + ": **" + str(value) + "**")
        if st.button("Clear Memory"):
            st.session_state.farmer_memory = {}
            st.rerun()

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