
import streamlit as st
import requests
import base64
import json
import time
import os
from datetime import datetime

# ===== CONFIG =====
DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# ===== PAGE SETUP =====
st.set_page_config(page_title="GAIA – Voice Agronomist", page_icon="🎙️", layout="wide")

# ===== THEME TOGGLE =====
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
    .pulse {
        animation: pulse 2s infinite;
        width: 120px; height: 120px; border-radius: 50%;
        background: linear-gradient(135deg, #00c853, #4caf50);
        display: flex; align-items: center; justify-content: center;
        margin: 2rem auto; cursor: pointer;
        box-shadow: 0 0 40px rgba(0,200,83,0.5);
    }
    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 40px rgba(0,200,83,0.5); }
        50% { transform: scale(1.08); box-shadow: 0 0 80px rgba(0,200,83,0.8); }
        100% { transform: scale(1); box-shadow: 0 0 40px rgba(0,200,83,0.5); }
    }
    .answer-card {
        background: rgba(255,255,255,0.05); backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1); border-radius: 20px;
        padding: 2rem; margin: 1rem 0;
    }
    .quick-btn {
        background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
        border-radius: 12px; padding: 10px 16px; margin: 4px;
        cursor: pointer; font-size: 0.9rem; transition: all 0.2s;
        display: inline-block; color: inherit; text-decoration: none;
    }
    .quick-btn:hover { background: rgba(0,200,83,0.2); border-color: #00c853; }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="voice_theme_toggle")
theme = "dark" if dark_mode else "light"

if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #fff; }
        header, footer { visibility: hidden; }
        .title { font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #00c853, #69f0ae); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #b0bec5; margin-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); color: #1b5e20; }
        header, footer { visibility: hidden; }
        .title { font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #33691e; margin-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# ===== DEEPSEEK API CALL =====
def ask_deepseek(question, crop_context=""):
    """Send a question to DeepSeek and get a precise, farming‑specific answer."""
    
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
            return None, f"API Error: {response.status_code} - {response.text[:200]}"
    except Exception as e:
        return None, str(e)

# ===== QUICK QUESTION TEMPLATES =====
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
        "My rice field has standing water that smells bad. Help!",
    ],
    "🐄 Cattle": [
        "My cow has sores on its mouth and is drooling. What disease is this?",
        "What vaccine does my cattle need?",
        "My cow is not eating and has fever. What should I do?",
    ],
    "🐔 Poultry": [
        "My chickens are sneezing and have swollen eyes. What is it?",
        "How do I prevent Newcastle disease in my flock?",
        "What should I feed my layers for more eggs?",
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
st.markdown('<div class="subtitle">Ask anything about your farm — get instant expert answers powered by DeepSeek AI</div>', unsafe_allow_html=True)

# ===== INPUT METHODS =====
tab1, tab2 = st.tabs(["⌨️ Type Question", "🎤 Voice Input (Coming Soon)"])

with tab1:
    st.markdown("### Ask Your Question")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        question = st.text_area("", placeholder="e.g., 'My maize leaves have brown spots with yellow halos. What disease is this and how do I treat it?'", height=100, key="typed_question")
    with col2:
        crop_context = st.selectbox("Crop Context (optional)", ["None", "Maize", "Rice", "Wheat", "Beans", "Potato", "Tomato", "Pepper", "Cattle", "Poultry", "General Farming"])
        st.write("")
        st.write("")
        ask_button = st.button("🔍 Ask GAIA", type="primary", use_container_width=True)
    
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
            st.success("✅ Answer ready!")
    
    # Quick questions
    st.markdown("---")
    st.markdown("### 💡 Quick Questions")
    
    for category, questions in QUICK_QUESTIONS.items():
        with st.expander(category):
            for q in questions:
                if st.button(q, key=f"quick_{q[:30]}"):
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

with tab2:
    st.markdown("### 🎤 Voice Input")
    st.info("🎤 Voice input will use your phone's microphone. This feature is under development and will support English, Hausa, Yoruba, and Swahili.")
    st.markdown("**For now:** Type your question in the 'Type Question' tab above.")
    
    # Audio upload fallback
    audio_file = st.file_uploader("📤 Or upload a voice recording (mp3, wav)", type=["mp3", "wav", "ogg"])
    if audio_file:
        st.audio(audio_file)
        if st.button("🎤 Transcribe & Answer"):
            st.info("Voice transcription requires Whisper API. Coming in next update.")
            # Placeholder: In production, send to Whisper API, get text, then to DeepSeek

# ===== DISPLAY CONVERSATION HISTORY =====
if st.session_state.voice_history:
    st.markdown("---")
    st.markdown("### 📜 Conversation History")
    
    for i, item in enumerate(reversed(st.session_state.voice_history)):
        with st.expander(f"💬 {item['question'][:80]}... — {item['time']}", expanded=(i == 0)):
            st.markdown("**🧑‍🌾 You asked:**")
            st.info(item['question'])
            st.markdown("**🤖 GAIA answered:**")
            st.markdown(f'<div class="answer-card">{item["answer"]}</div>', unsafe_allow_html=True)

# ===== NAVIGATION =====
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(8)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[6]: st.page_link("pages/10_Early_Warning.py", label="🛰️ Early Warning")
with cols[7]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
