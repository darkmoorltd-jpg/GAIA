
import streamlit as st
import hashlib
import json
import re
import random
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
        .quiz-option {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 10px 15px;
            margin: 5px 0;
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
        .quiz-option {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 10px 15px;
            margin: 5px 0;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.markdown('<div class="title">🎓 GAIA University</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Maize Masterclass — Deep, Practical, Visual</div>', unsafe_allow_html=True)

# ============================================
# LESSON DATA (Rich & Detailed)
# ============================================
LESSONS = [
    {
        "id": 1,
        "title": "Lesson 1: Seed Selection & Land Preparation",
        "image": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
        "content": """
### 🌱 Choosing the Right Seed

**Key Factors:**
- **Yield Potential:** Select hybrids like SAMMAZ 15, SAMMAZ 52, or Oba Super 2 for higher yields (5–8 t/ha).
- **Disease Resistance:** Look for varieties resistant to Maize Lethal Necrosis (MLN), rust, and leaf blight.
- **Maturity Period:** Early‑maturing varieties (90–110 days) fit shorter rainy seasons; late varieties (120–150 days) for long rains.
- **Adaptability:** Choose seeds bred for your region (e.g., drought‑tolerant for savanna, water‑tolerant for forest).

**Seed Quality Check:**
1. **Germination test:** Soak 100 seeds in water for 24 hours, then keep in moist cloth for 3 days. Count sprouted seeds — if ≥ 90 sprout, good quality.
2. **Physical inspection:** Reject seeds that are cracked, discolored, or have holes (insect damage).
3. **Buy from certified dealers:** Look for NASC (National Agricultural Seeds Council) seal.

### 🚜 Land Preparation

**Steps:**
1. **Clear vegetation** and remove stumps.
2. **Plough** to a depth of 20–25 cm to loosen soil and improve root penetration.
3. **Harrow** to break clods and level the field.
4. **Make ridges** 75–90 cm apart (for maize) to improve drainage and root aeration.
5. **Apply organic matter:** 10–15 t/ha of well‑decomposed manure or compost before final ridging.

**Soil pH:** Ideal pH is 5.5–7.0. Use GAIA Soil Analysis to check your soil type and get liming recommendations.
"""
    },
    {
        "id": 2,
        "title": "Lesson 2: Disease Identification & Management",
        "image": "https://images.unsplash.com/photo-1591546230271-9b1e1f7d2c2b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
        "content": """
### 🦠 Major Maize Diseases

**1. Northern Leaf Blight (Exserohilum turcicum)**
- **Symptoms:** Long, elliptical gray‑green lesions that later turn brown. Lesions may coalesce and blight entire leaves.
- **Damage:** Reduces photosynthetic area, leading to yield loss up to 50% if severe.
- **Control:** Use resistant hybrids. Apply Mancozeb 80 WP at 2.5 g/L water when first symptoms appear. Rotate crops with legumes.

**2. Common Rust (Puccinia sorghi)**
- **Symptoms:** Small, round, brown pustules on both leaf surfaces. Pustules may burst releasing brown spores.
- **Damage:** Early infection reduces plant vigor and kernel fill.
- **Control:** Plant rust‑resistant varieties. Spray Propiconazole 25 EC at 1 ml/L at early disease onset.

**3. Gray Leaf Spot (Cercospora zeae-maydis)**
- **Symptoms:** Rectangular gray‑brown lesions, limited by veins. Lesions may merge causing leaf blight.
- **Damage:** Common in high‑humidity areas; severe infections reduce yield by 20–40%.
- **Control:** Avoid continuous maize cropping. Apply Azoxystrobin 25 SC at 0.5 ml/L.

**🧪 How GAIA Helps:**  
Upload a clear leaf photo to the Crops page. GAIA will identify the disease and give a complete treatment guide (organic + chemical) with local product names.
"""
    },
    {
        "id": 3,
        "title": "Lesson 3: Pest & Nutrient Management",
        "image": "https://images.unsplash.com/photo-1592982537447-7440770cbfc9?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
        "content": """
### 🐛 Major Pests

**1. Fall Armyworm (Spodoptera frugiperda)**
- **Damage:** Larvae feed on leaves, whorls, and ears, causing window‑pane damage and frass.
- **Control:** Spray Emamectin benzoate 5% SG at 0.4 g/L. Use Bt maize varieties. Hand‑pick and destroy egg masses.

**2. Stem Borers (Busseola fusca, Chilo partellus)**
- **Damage:** Larvae bore into stalks, causing dead hearts, reduced plant vigor, and stem breakage.
- **Control:** Apply Carbofuran 3G granules into whorls at 8 kg/ha, 3–4 weeks after planting.

**3. Aphids (Rhopalosiphum maidis)**
- **Damage:** Sap‑sucking causes leaf curling and honeydew; also transmit Maize Dwarf Mosaic Virus.
- **Control:** Spray neem oil 5 ml/L + 1 ml liquid soap, or use Imidacloprid 17.8 SL at 0.5 ml/L.

### 🌿 Nutrient Management

**Fertilizer Schedule (per hectare):**
- **At planting:** Apply NPK 15:15:15 at 200 kg/ha in bands 5 cm away from seed.
- **Top‑dress (6 weeks):** Apply Urea 100 kg/ha near the root zone, especially after rain.
- **Micronutrients:** If leaves show interveinal chlorosis, apply Zinc sulphate 10 kg/ha.

**Organic Alternatives:**
- Use compost (10 t/ha) before planting.
- Apply poultry manure (5 t/ha) as basal dressing.
- Use legume intercropping (cowpea, groundnut) to fix nitrogen.

**💡 Pro Tip:** Use the GAIA Soil Analysis to get a personalized fertilizer recommendation.
"""
    },
]

# ============================================
# SESSION STATE
# ============================================
if "current_lesson" not in st.session_state:
    st.session_state.current_lesson = 0
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = None
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
            st.session_state.quiz_started = False
            st.session_state.quiz_questions = None
            st.session_state.quiz_score = None
            st.rerun()
with col3:
    if st.session_state.current_lesson < len(LESSONS) - 1:
        if st.button("Next Lesson →"):
            st.session_state.current_lesson += 1
            st.session_state.quiz_started = False
            st.session_state.quiz_questions = None
            st.session_state.quiz_score = None
            st.rerun()

lesson = LESSONS[st.session_state.current_lesson]
st.markdown(f'<div class="lesson-card"><h2>{lesson["title"]}</h2></div>', unsafe_allow_html=True)
st.image(lesson["image"], use_container_width=True, caption="Visual guide")
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
# AI‑GENERATED QUIZ
# ============================================
st.markdown("---")
st.subheader("📝 Lesson Quiz")

def generate_quiz_questions(lesson_content):
    """Use DeepSeek to generate 5 multiple choice questions."""
    try:
        from app.utils.deepseek_explainer import DEEPSEEK_API_KEY, DEEPSEEK_URL
        import requests
        prompt = f"""
        You are an agricultural exam generator for maize farmers in Nigeria.
        Based on the following lesson content, create exactly 5 multiple-choice questions.
        Each question must have 4 options (A-D) and one correct answer.
        Return ONLY a JSON array with fields: question, options (array of 4 strings), correct_index (0-3).

        Lesson Content:
        {lesson_content[:2000]}

        Return JSON.
        """
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are GAIA, an expert agricultural examiner. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 1000
        }
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            # Extract JSON from the response
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                quiz_data = json.loads(match.group())
                if len(quiz_data) == 5:
                    return quiz_data
    except:
        pass
    return None

if st.button("Start Quiz", disabled=st.session_state.quiz_started):
    st.session_state.quiz_started = True
    # Try to generate AI quiz
    with st.spinner("🧠 Generating unique quiz questions..."):
        st.session_state.quiz_questions = generate_quiz_questions(lesson["content"])
        if st.session_state.quiz_questions is None:
            # Fallback static questions varied by random seed
            random.seed(datetime.now().timestamp())
            st.session_state.quiz_questions = [
                {
                    "question": "What is the ideal soil pH for maize?",
                    "options": ["3.0-4.0", "5.5-7.0", "8.0-9.0", "6.5-8.5"],
                    "correct_index": 1
                },
                {
                    "question": "Which pest is controlled by Emamectin benzoate?",
                    "options": ["Aphids", "Fall armyworm", "Stem borers", "Termites"],
                    "correct_index": 1
                },
                {
                    "question": "What is the recommended NPK rate at planting?",
                    "options": ["50 kg/ha", "200 kg/ha", "500 kg/ha", "1000 kg/ha"],
                    "correct_index": 1
                },
                {
                    "question": "Which disease shows cigar-shaped lesions?",
                    "options": ["Common rust", "Northern leaf blight", "Gray leaf spot", "Downy mildew"],
                    "correct_index": 1
                },
                {
                    "question": "What is a sign of quality seed?",
                    "options": ["Any color", "Germination rate ≥90%", "Large size only", "Cheap price"],
                    "correct_index": 1
                }
            ]
    st.rerun()

if st.session_state.quiz_started and st.session_state.quiz_questions:
    quiz = st.session_state.quiz_questions
    score = 0
    for i, q in enumerate(quiz):
        user_ans = st.radio(f"Q{i+1}: {q['question']}", q['options'], key=f"quiz_{i}")
        if user_ans == q['options'][q['correct_index']]:
            score += 1

    if st.button("Submit Quiz"):
        st.session_state.quiz_score = score
        st.rerun()

    if st.session_state.quiz_score is not None:
        st.success(f"Your score: {st.session_state.quiz_score}/{len(quiz)}")
        if st.session_state.quiz_score >= 4:
            st.markdown('<div class="badge-card"><h2>🏆 Badge Earned</h2><h3>🌽 GAIA Maize Specialist</h3><p>Congratulations! You completed the Maize Masterclass.</p></div>', unsafe_allow_html=True)
            # Save badge to Supabase if possible
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
        # Button to retake quiz with new questions
        if st.button("🔄 Retake Quiz with New Questions"):
            st.session_state.quiz_started = False
            st.session_state.quiz_questions = None
            st.session_state.quiz_score = None
            st.rerun()

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
