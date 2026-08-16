
import streamlit as st
import hashlib
from datetime import datetime

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(page_title="GAIA University", page_icon="🎓", layout="wide")

# ============================================
# THEME TOGGLE
# ============================================
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="university_theme_toggle")
theme = "dark" if dark_mode else "light"

# ============================================
# CUSTOM CSS
# ============================================
if theme == "dark":
    st.markdown("""
    <style>
        @keyframes gradShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .stApp {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            background-size: 400% 400%;
            animation: gradShift 15s ease infinite;
            color: #fff;
        }
        header, footer { visibility: hidden; }
        .title {
            font-size: 3rem; font-weight: 900; text-align: center;
            background: linear-gradient(135deg, #00c853, #69f0ae);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 25px rgba(0,200,83,0.7);
        }
        .subtitle { text-align: center; color: #b0bec5; font-size: 1.2rem; margin-bottom: 2rem; }
        .lesson-card {
            background: rgba(255,255,255,0.05);
            border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0;
            backdrop-filter: blur(15px);
            border-left: 4px solid #00c853;
        }
        .badge-card {
            background: rgba(255,215,0,0.1);
            border: 2px solid #ffd700;
            border-radius: 20px; padding: 2rem; text-align: center;
        }
        .stButton button {
            background: linear-gradient(135deg, #00c853, #4caf50);
            color: #fff; border: none; border-radius: 10px;
            padding: 12px 30px; font-weight: 700;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @keyframes gradShiftLight {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .stApp {
            background: linear-gradient(135deg, #e8f5e9, #f1f8e9, #fffde7);
            background-size: 400% 400%;
            animation: gradShiftLight 15s ease infinite;
            color: #1b5e20;
        }
        header, footer { visibility: hidden; }
        .title {
            font-size: 3rem; font-weight: 900; text-align: center;
            background: linear-gradient(135deg, #2e7d32, #4caf50);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .subtitle { text-align: center; color: #33691e; font-size: 1.2rem; margin-bottom: 2rem; }
        .lesson-card {
            background: rgba(255,255,255,0.9);
            border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            border-left: 4px solid #2e7d32;
        }
        .badge-card {
            background: rgba(255,215,0,0.15);
            border: 2px solid #ffd700;
            border-radius: 20px; padding: 2rem; text-align: center;
        }
        .stButton button {
            background: linear-gradient(135deg, #2e7d32, #4caf50);
            color: #fff; border: none; border-radius: 10px;
            padding: 12px 30px; font-weight: 700;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.markdown('<div class="title">🎓 GAIA University</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Learn. Grow. Earn. — Start your Maize Masterclass</div>', unsafe_allow_html=True)

# ============================================
# COURSE DATA (for MVP)
# ============================================
LESSONS = [
    {
        "title": "Lesson 1: Seed Selection & Land Preparation",
        "content": """
        **Seed Selection**  
        Choose high‑yielding, disease‑resistant maize varieties like SAMMAZ 15, SAMMAZ 52, or Oba Super 2.  
        Check for:
        - Germination rate ≥ 90%
        - Uniform seed size and color
        - No cracks or insect damage

        **Land Preparation**  
        - Clear land and plough to a depth of 20‑25 cm.
        - Make ridges 75‑90 cm apart for good drainage.
        - Apply 10‑15 tonnes/ha of well‑decomposed manure or compost.
        - Test soil pH (ideal: 5.5‑7.0). GAIA Soil Analysis can help.
        """
    },
    {
        "title": "Lesson 2: Disease Identification & Treatment",
        "content": """
        **Common Maize Diseases**  
        1. **Northern Leaf Blight** — gray‑green cigar‑shaped lesions.
        2. **Common Rust** — small round brown pustules on leaves.
        3. **Gray Leaf Spot** — rectangular gray lesions.

        **How GAIA Helps**  
        - Upload a leaf photo in the Crops page to get instant diagnosis.
        - GAIA will provide organic and chemical treatments.
        - Always confirm with 2‑3 photos for consensus.
        """
    },
    {
        "title": "Lesson 3: Pest & Nutrient Management",
        "content": """
        **Major Pests**  
        - Fall armyworm: spray Emamectin benzoate at first sign.
        - Stem borers: use granules in whorls.

        **Nutrient Management**  
        - Apply NPK 15:15:15 at planting (200 kg/ha).
        - Top‑dress with Urea (100 kg/ha) at 6 weeks.
        - Use organic mulch to conserve moisture.
        """
    },
]

# ============================================
# SESSION STATE
# ============================================
if "current_lesson" not in st.session_state:
    st.session_state.current_lesson = 0
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = None

# ============================================
# LESSON NAVIGATION
# ============================================
col1, col2, col3 = st.columns([1, 3, 1])
with col1:
    if st.session_state.current_lesson > 0:
        if st.button("← Previous Lesson"):
            st.session_state.current_lesson -= 1
            st.rerun()
with col3:
    if st.session_state.current_lesson < len(LESSONS) - 1:
        if st.button("Next Lesson →"):
            st.session_state.current_lesson += 1
            st.rerun()

lesson = LESSONS[st.session_state.current_lesson]
st.markdown(f'<div class="lesson-card"><h2>{lesson["title"]}</h2></div>', unsafe_allow_html=True)
st.markdown(lesson["content"])

# Voice button
if st.button("🔊 Listen to this lesson"):
    try:
        from app.utils.deepseek_explainer import text_to_speech
        audio_bytes, err = text_to_speech(lesson["content"])
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")
        else:
            st.warning(f"Voice unavailable: {err}")
    except Exception as e:
        st.warning("Voice generation not available.")

# ============================================
# QUIZ
# ============================================
st.markdown("---")
st.subheader("📝 Lesson Quiz")

if st.button("Start Quiz", disabled=st.session_state.quiz_started):
    st.session_state.quiz_started = True
    st.rerun()

if st.session_state.quiz_started:
    # Simple fixed quiz (5 questions)
    quiz = [
        {"q": "Which maize variety is disease-resistant?", "opts": ["SAMMAZ 15", "Local dent", "Any variety"], "ans": 0},
        {"q": "What is the ideal soil pH for maize?", "opts": ["3.0-4.0", "5.5-7.0", "8.0-9.0"], "ans": 1},
        {"q": "What does Northern Leaf Blight look like?", "opts": ["Round brown pustules", "Cigar-shaped gray-green lesions", "Yellow mosaic"], "ans": 1},
        {"q": "When should NPK be applied?", "opts": ["After harvest", "At planting", "Never"], "ans": 1},
        {"q": "Which pest is controlled by Emamectin benzoate?", "opts": ["Aphids", "Fall armyworm", "Birds"], "ans": 1},
    ]
    score = 0
    for i, q in enumerate(quiz):
        user_ans = st.radio(f"Q{i+1}: {q['q']}", q['opts'], key=f"quiz_{i}")
        if user_ans == q['opts'][q['ans']]:
            score += 1
    if st.button("Submit Quiz"):
        st.session_state.quiz_score = score
        st.rerun()
    if st.session_state.quiz_score is not None:
        st.success(f"Your score: {st.session_state.quiz_score}/5")
        if st.session_state.quiz_score >= 4:
            st.markdown('<div class="badge-card"><h2>🏆 Badge Earned</h2><h3>🌽 GAIA Maize Specialist</h3><p>Congratulations! You completed the Maize Masterclass.</p></div>', unsafe_allow_html=True)
            # Optionally save badge to Supabase (if table exists)
            if "user" in st.session_state and st.session_state.user:
                try:
                    from supabase import create_client
                    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["service_key"])
                    supabase.table("badge_subscriptions").upsert({
                        "user_id": st.session_state.user.id,
                        "plan": "maize_specialist",
                        "status": "active",
                        "created_at": datetime.now().isoformat()
                    }).execute()
                except:
                    pass
        else:
            st.info("Score 80% or above to earn the badge. Review the lesson and try again.")

# ============================================
# NAVIGATION
# ============================================
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(10)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[6]: st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[7]: st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[9]: st.page_link("pages/22_University.py", label="🎓 University")
