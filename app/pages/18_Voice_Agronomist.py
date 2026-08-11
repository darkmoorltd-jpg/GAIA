
import streamlit as st
import requests
from datetime import datetime

# ===== CONFIG =====
DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

st.set_page_config(page_title="GAIA – Voice Agronomist", page_icon="🎙️", layout="wide")

# ===== THEME =====
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=True, key="voice_theme_toggle")
theme = "dark" if dark_mode else "light"

# ===== GAIA IDENTITY =====
GAIA_IDENTITY = """You are GAIA — the Global Agricultural Intelligence Assistant, built by Darkmoor Ltd in Nigeria. You are an expert AI agronomist dedicated to helping African smallholder farmers.

CRITICAL RULES:
1. NEVER mention DeepSeek, OpenAI, or any other AI company. You ARE GAIA.
2. If a user asks "Who built you?" respond: "I am GAIA, an AI agronomist built by Darkmoor Ltd in Nigeria to help farmers grow better crops."
3. If a user asks about any other AI, respond: "I am GAIA, focused on helping you with your farm!"
4. Always maintain the GAIA identity.

Your answers must be:
1. PRACTICAL — Specific dosages, timing, methods
2. LOCAL — African context, local product names
3. SIMPLE — Plain language any farmer understands
4. COMPLETE — Diagnosis, organic solution, chemical solution, prevention

Structure your response as:
**🔍 Diagnosis:** [What the problem likely is]
**🌿 Organic Solution:** [Natural treatment with exact recipe]
**⚗️ Chemical Solution:** [Specific product + dosage]
**⏰ When to Apply:** [Best time, frequency]
**🛡️ Prevention:** [How to prevent it next season]
**⚠️ Warning:** [Safety concerns]

If asked about non-farming topics, say: "I am GAIA, your farm assistant! I specialize in crops, pests, soil, and livestock. What farming question can I help with?"""

# ===== SESSION STATE =====
if "voice_history" not in st.session_state:
    st.session_state.voice_history = []
if "show_history" not in st.session_state:
    st.session_state.show_history = False

# ===== API CALL =====
def ask_gaia(question, crop_context=""):
    system_prompt = GAIA_IDENTITY
    if crop_context:
        system_prompt += " Crop context: " + crop_context
    
    headers = {
        "Authorization": "Bearer " + DEEPSEEK_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 1200
    }
    
    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"], None
        else:
            return None, "I am having trouble connecting. Please try again."
    except:
        return None, "I am temporarily unavailable. Please try again in a moment."

# ===== QUICK QUESTIONS =====
QUICK_QUESTIONS = [
    ("🌽 Maize", [
        "My maize leaves have brown spots with yellow edges. What is it?",
        "When is the best time to harvest maize?",
        "What is the best fertilizer for maize in sandy soil?",
        "How do I control fall armyworm in my maize field?",
    ]),
    ("🌾 Rice", [
        "My rice leaves are turning yellow. What is wrong?",
        "How do I control birds eating my rice?",
        "When should I apply fertilizer to my rice field?",
    ]),
    ("🐄 Livestock", [
        "My cow has sores on its mouth and is drooling. What disease?",
        "What vaccines does my cattle need?",
        "My chickens are sneezing and have swollen eyes. Help!",
    ]),
    ("🏞️ Soil and General", [
        "How do I test if my soil is acidic?",
        "What is the best crop rotation for maize farmers?",
        "How do I start vegetable farming with N50000?",
    ]),
]

# ===== CSS =====
if theme == "dark":
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .stApp { background: #0d1110; }
        header, footer { visibility: hidden; }
        
        .gaia-header { text-align: center; padding: 20px 0 10px 0; }
        .gaia-logo {
            font-size: 3rem; font-weight: 900;
            background: linear-gradient(135deg, #00c853, #69f0ae, #00c853);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .gaia-tagline { color: #6b7280; font-size: 0.95rem; margin-top: 4px; }
        .powered-by { color: #3b82f6; font-size: 0.75rem; margin-top: 2px; opacity: 0.6; }
        
        .chat-area {
            max-width: 850px; margin: 0 auto;
            height: 55vh; overflow-y: auto; padding: 16px 20px;
            background: #111915; border-radius: 20px; border: 1px solid #1a2a1f;
        }
        
        .msg-row { display: flex; margin: 16px 0; animation: slideIn 0.3s ease; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        .msg-row.user { justify-content: flex-end; }
        .msg-row.gaia { justify-content: flex-start; }
        
        .msg-avatar {
            width: 36px; height: 36px; border-radius: 50%; margin: 0 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.1rem; flex-shrink: 0;
        }
        .msg-avatar.user { background: #1a1a2e; }
        .msg-avatar.gaia { background: linear-gradient(135deg, #0d3320, #1a5c30); }
        
        .msg-bubble {
            max-width: 72%; padding: 14px 18px; border-radius: 16px;
            font-size: 0.92rem; line-height: 1.6;
        }
        .msg-bubble.user { background: linear-gradient(135deg, #1a5c30, #0d3320); color: #e8f5e9; border-bottom-right-radius: 4px; }
        .msg-bubble.gaia { background: #151d18; color: #d1d5db; border: 1px solid #1e2d23; border-bottom-left-radius: 4px; }
        .msg-time { font-size: 0.68rem; color: #6b7280; margin-top: 6px; }
        
        .input-bar {
            max-width: 850px; margin: 16px auto;
            background: #111915; border: 1px solid #1a2a1f; border-radius: 16px;
            padding: 12px 16px; display: flex; gap: 10px; align-items: center;
        }
        .input-bar textarea {
            background: #0a0f0c !important; border: 1px solid #1a2a1f !important;
            border-radius: 12px !important; color: #e8f5e9 !important;
            padding: 10px 14px !important; font-size: 0.92rem !important;
        }
        .input-bar textarea::placeholder { color: #4b5563 !important; }
        
        .stButton button {
            background: linear-gradient(135deg, #00c853, #4caf50) !important;
            color: #fff !important; border: none !important;
            border-radius: 50% !important; width: 44px !important; height: 44px !important;
            padding: 0 !important; font-size: 1.2rem !important;
            transition: all 0.3s !important; flex-shrink: 0;
        }
        .stButton button:hover { transform: scale(1.08); box-shadow: 0 0 20px rgba(0,200,83,0.4); }
        
        .history-panel {
            background: #111915; border: 1px solid #1a2a1f; border-radius: 16px;
            padding: 16px; margin-top: 16px; max-height: 40vh; overflow-y: auto;
        }
        .history-item { padding: 10px; border-bottom: 1px solid #1a2a1f; cursor: pointer; transition: all 0.2s; }
        .history-item:hover { background: #1a2a1f; }
        .history-question { color: #e8f5e9; font-size: 0.85rem; font-weight: 500; }
        .history-time { color: #6b7280; font-size: 0.72rem; }
        
        .empty-state { text-align: center; padding: 60px 20px; }
        .empty-state-icon { font-size: 5rem; margin-bottom: 16px; }
        .empty-state h3 { color: #6b7280; font-weight: 400; }
        .empty-state p { color: #4b5563; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .stApp { background: #f8fafc; }
        header, footer { visibility: hidden; }
        
        .gaia-header { text-align: center; padding: 20px 0 10px 0; }
        .gaia-logo {
            font-size: 3rem; font-weight: 900;
            background: linear-gradient(135deg, #2e7d32, #4caf50, #2e7d32);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .gaia-tagline { color: #64748b; font-size: 0.95rem; margin-top: 4px; }
        .powered-by { color: #3b82f6; font-size: 0.75rem; margin-top: 2px; opacity: 0.6; }
        
        .chat-area {
            max-width: 850px; margin: 0 auto;
            height: 55vh; overflow-y: auto; padding: 16px 20px;
            background: #fff; border-radius: 20px; border: 1px solid #e2e8f0;
        }
        
        .msg-row { display: flex; margin: 16px 0; animation: slideIn 0.3s ease; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        .msg-row.user { justify-content: flex-end; }
        .msg-row.gaia { justify-content: flex-start; }
        
        .msg-avatar {
            width: 36px; height: 36px; border-radius: 50%; margin: 0 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.1rem; flex-shrink: 0;
        }
        .msg-avatar.user { background: #e2e8f0; }
        .msg-avatar.gaia { background: linear-gradient(135deg, #c8e6c9, #a5d6a7); }
        
        .msg-bubble {
            max-width: 72%; padding: 14px 18px; border-radius: 16px;
            font-size: 0.92rem; line-height: 1.6;
        }
        .msg-bubble.user { background: #2e7d32; color: #fff; border-bottom-right-radius: 4px; }
        .msg-bubble.gaia { background: #f1f5f9; color: #1e293b; border: 1px solid #e2e8f0; border-bottom-left-radius: 4px; }
        .msg-time { font-size: 0.68rem; color: #94a3b8; margin-top: 6px; }
        
        .input-bar {
            max-width: 850px; margin: 16px auto;
            background: #fff; border: 1px solid #e2e8f0; border-radius: 16px;
            padding: 12px 16px; display: flex; gap: 10px; align-items: center;
        }
        .input-bar textarea {
            background: #f8fafc !important; border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important; color: #1e293b !important;
            padding: 10px 14px !important; font-size: 0.92rem !important;
        }
        .input-bar textarea::placeholder { color: #94a3b8 !important; }
        
        .stButton button {
            background: #2e7d32 !important; color: #fff !important; border: none !important;
            border-radius: 50% !important; width: 44px !important; height: 44px !important;
            padding: 0 !important; font-size: 1.2rem !important;
            transition: all 0.3s !important; flex-shrink: 0;
        }
        .stButton button:hover { transform: scale(1.08); box-shadow: 0 0 20px rgba(46,125,50,0.3); }
        
        .history-panel {
            background: #fff; border: 1px solid #e2e8f0; border-radius: 16px;
            padding: 16px; margin-top: 16px; max-height: 40vh; overflow-y: auto;
        }
        .history-item { padding: 10px; border-bottom: 1px solid #e2e8f0; cursor: pointer; transition: all 0.2s; }
        .history-item:hover { background: #f1f5f9; }
        .history-question { color: #1e293b; font-size: 0.85rem; font-weight: 500; }
        .history-time { color: #94a3b8; font-size: 0.72rem; }
        
        .empty-state { text-align: center; padding: 60px 20px; }
        .empty-state-icon { font-size: 5rem; margin-bottom: 16px; }
        .empty-state h3 { color: #94a3b8; font-weight: 400; }
        .empty-state p { color: #64748b; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# ===== HEADER =====
st.markdown("""
<div class="gaia-header">
    <div class="gaia-logo">GAIA Voice Agronomist</div>
    <div class="gaia-tagline">Your AI farm assistant - ask anything, get expert answers instantly</div>
    <div class="powered-by">Powered by Darkmoor Ltd</div>
</div>
""", unsafe_allow_html=True)

# ===== CHAT AREA =====
st.markdown('<div class="chat-area">', unsafe_allow_html=True)

if not st.session_state.voice_history:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">🎙️</div>
        <h3>Your AI Agronomist is Ready</h3>
        <p>Ask any farming question below<br>Try: "My maize leaves have brown spots with yellow edges. Help!"</p>
    </div>
    """, unsafe_allow_html=True)

for item in st.session_state.voice_history:
    # User message
    user_html = '<div class="msg-row user"><div class="msg-bubble user">' + item['question'] + '<div class="msg-time">You - ' + item['time'] + '</div></div><div class="msg-avatar user">🧑‍🌾</div></div>'
    st.markdown(user_html, unsafe_allow_html=True)
    
    # GAIA message
    gaia_html = '<div class="msg-row gaia"><div class="msg-avatar gaia">🌱</div><div class="msg-bubble gaia">' + item['answer'].replace('
', '<br>') + '<div class="msg-time">GAIA - ' + item['time'] + '</div></div></div>'
    st.markdown(gaia_html, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ===== INPUT BAR =====
st.markdown('<div class="input-bar">', unsafe_allow_html=True)

col_text, col_send = st.columns([8, 1])

with col_text:
    question = st.text_area("", placeholder="Ask anything about your farm...", height=42, key="main_question", label_visibility="collapsed")

with col_send:
    ask_button = st.button("➤", key="ask_main", help="Send message")

st.markdown('</div>', unsafe_allow_html=True)

# Crop context
crop_context = st.selectbox("Crop context (optional)", ["None", "Maize", "Rice", "Wheat", "Beans", "Potato", "Tomato", "Pepper", "Cattle", "Poultry", "General Farming"], key="crop_select")

# Process question
if ask_button and question:
    with st.spinner("GAIA is thinking..."):
        ctx = crop_context if crop_context != "None" else ""
        answer, error = ask_gaia(question, ctx)
    
    if error:
        st.error(error)
    else:
        st.session_state.voice_history.append({
            "question": question,
            "answer": answer,
            "time": datetime.now().strftime("%H:%M")
        })
        st.rerun()

# ===== QUICK QUESTIONS =====
st.markdown("---")
for category, questions in QUICK_QUESTIONS:
    st.markdown(f'<div style="font-size:0.78rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;margin:12px 0 4px 0;">{category}</div>', unsafe_allow_html=True)
    cols = st.columns(len(questions))
    for i, q in enumerate(questions):
        with cols[i]:
            if st.button(q, key=f"quick_{category}_{i}", use_container_width=True):
                with st.spinner("Thinking..."):
                    answer, error = ask_gaia(q)
                if error:
                    st.error(error)
                else:
                    st.session_state.voice_history.append({
                        "question": q,
                        "answer": answer,
                        "time": datetime.now().strftime("%H:%M")
                    })
                    st.rerun()

# ===== HISTORY PANEL =====
if st.session_state.voice_history:
    st.markdown("---")
    if st.button("View Conversation History" if not st.session_state.show_history else "Hide History", use_container_width=True):
        st.session_state.show_history = not st.session_state.show_history
        st.rerun()
    
    if st.session_state.show_history:
        st.markdown('<div class="history-panel">', unsafe_allow_html=True)
        st.markdown("### Your Conversation History")
        for i, item in enumerate(reversed(st.session_state.voice_history)):
            st.markdown(f'<div class="history-item"><div class="history-question">Q: {item["question"][:100]}</div><div class="history-time">{item["time"]}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ===== NAVIGATION =====
st.markdown("---")
st.markdown("### Quick Navigation")
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

# ===== FOOTER =====
st.markdown("""
<div style="text-align:center;padding:20px;color:#6b7280;font-size:0.78rem;">
    GAIA Voice Agronomist · Powered by Darkmoor Ltd · Built in Nigeria
</div>
""", unsafe_allow_html=True)
