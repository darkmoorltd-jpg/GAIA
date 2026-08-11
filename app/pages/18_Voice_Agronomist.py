import streamlit as st
import requests
from datetime import datetime

DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

st.set_page_config(page_title="GAIA - Voice Agronomist", page_icon="🍅", layout="wide")

# ----- custom CSS for beautiful conversation cards -----
st.markdown("""
<style>
    .stApp { background: #0d1110; color: #e8f5e9; }
    header, footer { visibility: hidden; }
    .gaia-header { text-align: center; padding: 20px 0 10px 0; }
    .gaia-logo {
        font-size: 3rem; font-weight: 900;
        background: linear-gradient(135deg, #00c853, #69f0ae, #00c853);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .gaia-tagline { color: #6b7280; font-size: 0.95rem; }
    .answer-card {
        background: #111915; border: 1px solid #1a2a1f; border-radius: 20px;
        padding: 24px; margin: 16px 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .answer-card h3 { color: #00c853; margin-top: 16px; margin-bottom: 8px; }
    .answer-card p, .answer-card li { color: #d1d5db; line-height: 1.7; }
    .stButton button {
        background: linear-gradient(135deg, #00c853, #4caf50) !important;
        color: #fff !important; border: none !important;
        border-radius: 12px !important; padding: 12px 30px !important;
        font-weight: 600 !important;
    }
    .stButton button:hover { box-shadow: 0 0 20px rgba(0,200,83,0.4); }
</style>
""", unsafe_allow_html=True)

# ----- header -----
st.markdown('<div class="gaia-header"><div class="gaia-logo">🍅 GAIA Voice Agronomist</div><div class="gaia-tagline">Your AI farm assistant - powered by Darkmoor Ltd</div></div>', unsafe_allow_html=True)

if "voice_history" not in st.session_state:
    st.session_state.voice_history = []

GAIA_IDENTITY = "You are GAIA, an AI agronomist built by Darkmoor Ltd in Nigeria. Help African farmers with crop diseases, pests, soil, and livestock. Never mention any other AI company. You ARE GAIA."

def ask_gaia(question):
    headers = {"Authorization": "Bearer " + DEEPSEEK_API_KEY, "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "system", "content": GAIA_IDENTITY}, {"role": "user", "content": question}], "temperature": 0.7, "max_tokens": 1000}
    try:
        r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"], None
        return None, "Connection error. Please try again."
    except:
        return None, "I am temporarily unavailable."

question = st.text_area("Ask anything about your farm:", placeholder="e.g., My maize leaves have brown spots. What should I do?", height=80, key="q")

if st.button("🍅 Ask GAIA", type="primary") and question:
    with st.spinner("GAIA is thinking..."):
        answer, error = ask_gaia(question)
    if error:
        st.error(error)
    else:
        st.session_state.voice_history.append({"question": question, "answer": answer, "time": datetime.now().strftime("%H:%M")})
        st.rerun()

# ----- conversation history (beautiful cards) -----
if st.session_state.voice_history:
    st.markdown("---")
    st.markdown("### Conversation")
    for item in reversed(st.session_state.voice_history):
        with st.chat_message("user"):
            st.write(item["question"])
            st.caption(item["time"])
        with st.chat_message("assistant", avatar="🍅"):
            st.markdown('<div class="answer-card">' + item["answer"].replace("\n", "<br>") + '</div>', unsafe_allow_html=True)
            st.caption("GAIA - " + item["time"])

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