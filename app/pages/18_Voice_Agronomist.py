
import streamlit as st
import requests
import time
from datetime import datetime

# ===== CONFIG =====
DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# ===== PAGE SETUP =====
st.set_page_config(page_title="GAIA – Voice Agronomist", page_icon="🎙️", layout="wide")

# ===== THEME TOGGLE (default DARK like DeepSeek) =====
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=True, key="voice_theme_toggle")
theme = "dark" if dark_mode else "light"

# ===== DEEPSEEK‑INSPIRED CSS =====
if theme == "dark":
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .stApp { background: #0f1117; color: #e8edf2; }
        header, footer { visibility: hidden; }
        
        .title { 
            font-size: 3.2rem; font-weight: 800; text-align: center;
            background: linear-gradient(135deg, #4f46e5, #818cf8, #4f46e5);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 0.3rem;
        }
        .subtitle { text-align: center; font-size: 1.1rem; color: #8b8fa3; margin-bottom: 2rem; }
        
        .chat-container {
            max-width: 900px; margin: 0 auto;
            height: 60vh; overflow-y: auto; padding: 20px;
            background: #16181d; border-radius: 20px; border: 1px solid #1e2030;
        }
        
        .msg-bubble {
            max-width: 80%; padding: 14px 20px; border-radius: 16px;
            margin: 12px 0; font-size: 0.95rem; line-height: 1.6;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        .msg-user {
            background: linear-gradient(135deg, #4f46e5, #6366f1);
            color: #fff; margin-left: auto; border-bottom-right-radius: 4px;
        }
        .msg-gaia {
            background: #1e2030; color: #e8edf2; border: 1px solid #2a2d3a;
            border-bottom-left-radius: 4px;
        }
        .msg-time { font-size: 0.7rem; color: #6b7085; margin-top: 6px; }
        
        .input-container {
            max-width: 900px; margin: 20px auto;
            background: #16181d; border: 1px solid #1e2030; border-radius: 16px;
            padding: 16px; display: flex; gap: 12px; align-items: center;
        }
        .input-container textarea {
            background: #0f1117 !important; border: 1px solid #2a2d3a !important;
            border-radius: 12px !important; color: #e8edf2 !important;
            padding: 12px !important; font-size: 0.95rem !important;
        }
        .input-container textarea::placeholder { color: #4a4d5e !important; }
        
        .stButton button {
            background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
            color: #fff !important; border: none !important;
            border-radius: 12px !important; padding: 12px 28px !important;
            font-weight: 600 !important; font-size: 0.95rem !important;
            transition: all 0.3s !important;
        }
        .stButton button:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 8px 25px rgba(79,70,229,0.4); 
        }
        
        .quick-chip {
            display: inline-block; padding: 8px 16px; margin: 4px;
            background: #16181d; border: 1px solid #2a2d3a; border-radius: 20px;
            cursor: pointer; font-size: 0.85rem; color: #8b8fa3;
            transition: all 0.2s; text-decoration: none;
        }
        .quick-chip:hover { background: #1e2030; border-color: #4f46e5; color: #818cf8; }
        
        .category-title { color: #6b7085; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 16px; margin-bottom: 8px; }
        
        .stSelectbox > div > div { background: #16181d !important; border: 1px solid #2a2d3a !important; border-radius: 12px !important; }
        .stSelectbox [data-baseweb="select"] { background: #16181d !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .stApp { background: #f8fafc; color: #1e293b; }
        header, footer { visibility: hidden; }
        
        .title { 
            font-size: 3.2rem; font-weight: 800; text-align: center;
            background: linear-gradient(135deg, #4f46e5, #818cf8, #4f46e5);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 0.3rem;
        }
        .subtitle { text-align: center; font-size: 1.1rem; color: #64748b; margin-bottom: 2rem; }
        
        .chat-container {
            max-width: 900px; margin: 0 auto;
            height: 60vh; overflow-y: auto; padding: 20px;
            background: #fff; border-radius: 20px; border: 1px solid #e2e8f0;
        }
        
        .msg-bubble {
            max-width: 80%; padding: 14px 20px; border-radius: 16px;
            margin: 12px 0; font-size: 0.95rem; line-height: 1.6;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        .msg-user { background: #4f46e5; color: #fff; margin-left: auto; border-bottom-right-radius: 4px; }
        .msg-gaia { background: #f1f5f9; color: #1e293b; border: 1px solid #e2e8f0; border-bottom-left-radius: 4px; }
        .msg-time { font-size: 0.7rem; color: #94a3b8; margin-top: 6px; }
        
        .input-container {
            max-width: 900px; margin: 20px auto;
            background: #fff; border: 1px solid #e2e8f0; border-radius: 16px;
            padding: 16px; display: flex; gap: 12px; align-items: center;
        }
        .input-container textarea {
            background: #f8fafc !important; border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important; color: #1e293b !important;
            padding: 12px !important; font-size: 0.95rem !important;
        }
        .input-container textarea::placeholder { color: #94a3b8 !important; }
        
        .stButton button {
            background: #4f46e5 !important; color: #fff !important; border: none !important;
            border-radius: 12px !important; padding: 12px 28px !important;
            font-weight: 600 !important; font-size: 0.95rem !important;
            transition: all 0.3s !important;
        }
        .stButton button:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 8px 25px rgba(79,70,229,0.3); 
        }
        
        .quick-chip {
            display: inline-block; padding: 8px 16px; margin: 4px;
            background: #fff; border: 1px solid #e2e8f0; border-radius: 20px;
            cursor: pointer; font-size: 0.85rem; color: #64748b;
            transition: all 0.2s; text-decoration: none;
        }
        .quick-chip:hover { background: #f1f5f9; border-color: #4f46e5; color: #4f46e5; }
        
        .category-title { color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 16px; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

# ===== DEEPSEEK API CALL =====
@st.cache_data(ttl=300)
def ask_deepseek(question, crop_context=""):
    system_prompt = """You are GAIA's AI Agronomist — an expert agricultural advisor for African smallholder farmers.

Your answers must be:
1. PRACTICAL — Give specific, actionable advice with exact dosages, timing, and methods
2. LOCAL — Use African farming context, local pesticide names when possible, and appropriate units (hectares, kg, liters)
3. SIMPLE — Explain in plain language a farmer can understand
4. COMPLETE — Cover the problem, cause, organic solution, chemical solution, and prevention
5. CONFIDENT — Don't hedge. Give your best recommendation.

Structure your response as:
**🔍 Diagnosis:** [What the problem likely is]
**🌿 Organic Solution:** [Natural treatment with exact recipe/method]
**⚗️ Chemical Solution:** [Specific product name + dosage per liter or per hectare]
**⏰ When to Apply:** [Best time of day, frequency, growth stage]
**🛡️ Prevention:** [How to prevent it next season]
**⚠️ Warning:** [Any safety concerns or things to avoid]

If the question is not about farming, crops, livestock, soil, or pests, politely redirect to agricultural topics.

Crop context: """ + (crop_context if crop_context else "General farming")
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"], None
        else:
            return None, f"API Error: {response.status_code}"
    except Exception as e:
        return None, str(e)

# ===== QUICK QUESTIONS =====
QUICK_QUESTIONS = {
    "🌽 Maize": [
        "My maize leaves have brown spots. What is it and how do I treat it?",
        "When should I harvest my maize? The cobs feel hard.",
        "What fertilizer should I use for maize in sandy soil?",
        "There are caterpillars eating my maize leaves. What pesticide works?",
    ],
    "🌾 Rice": [
        "My rice leaves are turning yellow. What's wrong?",
        "How do I control birds eating my rice?",
        "When is the best time to apply fertilizer to rice?",
    ],
    "🐄 Livestock": [
        "My cow has sores on its mouth and is drooling. What disease is this?",
        "What vaccines does my cattle need?",
        "My chickens are sneezing and have swollen eyes. What is it?",
    ],
    "🏞️ Soil": [
        "How do I know if my soil is acidic?",
        "What crops grow best in sandy soil?",
        "How much fertilizer per hectare for tomatoes?",
    ],
    "🛡️ General": [
        "How do I store my maize after harvest to prevent weevils?",
        "What's the best crop to rotate with maize?",
        "How do I start a small vegetable farm with N50,000?",
    ],
}

# ===== SESSION STATE =====
if "voice_history" not in st.session_state:
    st.session_state.voice_history = []

# ===== UI =====
st.markdown('<div class="title">🎙️ Voice Agronomist</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask anything about your farm — powered by DeepSeek AI</div>', unsafe_allow_html=True)

# ===== CHAT DISPLAY =====
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

if not st.session_state.voice_history:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;color:#6b7085;">
        <div style="font-size:4rem;margin-bottom:20px;">🎙️</div>
        <h3 style="color:#8b8fa3;font-weight:400;">Your AI Agronomist is Ready</h3>
        <p>Ask any farming question below — crop diseases, pests, soil, livestock, or general advice.</p>
        <p style="font-size:0.85rem;">Try: "My maize leaves have brown spots with yellow halos. Help!"</p>
    </div>
    """, unsafe_allow_html=True)

for i, item in enumerate(st.session_state.voice_history):
    st.markdown(f'<div class="msg-bubble msg-user">{item["question"]}<div class="msg-time">You · {item["time"]}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="msg-bubble msg-gaia">{item["answer"]}<div class="msg-time">GAIA · {item["time"]}</div></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ===== INPUT AREA =====
st.markdown('<div class="input-container">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 4, 1])

with col1:
    crop_context = st.selectbox("", ["None", "Maize", "Rice", "Wheat", "Beans", "Potato", "Tomato", "Pepper", "Cattle", "Poultry", "General"], label_visibility="collapsed", key="crop_select")

with col2:
    question = st.text_area("", placeholder="Ask anything about your farm... e.g., 'My tomato leaves have white spots. What should I do?'", height=68, key="main_question", label_visibility="collapsed")

with col3:
    st.write("")
    ask_button = st.button("🔍 Ask", type="primary", use_container_width=True, key="ask_main")

st.markdown('</div>', unsafe_allow_html=True)

if ask_button and question:
    with st.spinner("🧠 Consulting DeepSeek AI..."):
        ctx = crop_context if crop_context != "None" else ""
        answer, error = ask_deepseek(question, ctx)
    
    if error:
        st.error(f"❌ {error}")
    else:
        st.session_state.voice_history.append({
            "question": question,
            "answer": answer,
            "time": datetime.now().strftime("%H:%M")
        })
        st.rerun()

# ===== QUICK QUESTIONS =====
st.markdown("---")
st.markdown("### 💡 Quick Questions")

for category, questions in QUICK_QUESTIONS.items():
    st.markdown(f'<div class="category-title">{category}</div>', unsafe_allow_html=True)
    cols = st.columns(len(questions))
    for i, q in enumerate(questions):
        with cols[i]:
            if st.button(q[:60] + "…" if len(q) > 60 else q, key=f"quick_{category}_{i}", use_container_width=True):
                with st.spinner("🧠 Thinking..."):
                    answer, error = ask_deepseek(q)
                if error:
                    st.error(f"❌ {error}")
                else:
                    st.session_state.voice_history.append({
                        "question": q,
                        "answer": answer,
                        "time": datetime.now().strftime("%H:%M")
                    })
                    st.rerun()

# ===== NAVIGATION =====
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(9)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[6]: st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[7]: st.page_link("pages/10_Early_Warning.py", label="🛰️ Early Warning")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
