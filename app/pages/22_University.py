
import streamlit as st
user = st.session_state.get("user", None)
if user is None:
    user = None  # Allow demo mode
import json
import re
import random
from datetime import datetime

st.set_page_config(page_title="GAIA University", page_icon="🎓", layout="wide")

# Theme toggle
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="university_theme_toggle")
theme = "dark" if dark_mode else "light"

# Theme CSS
if theme == "dark":
    st.markdown("""
    <style>
        @keyframes gradShift { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
        .stApp { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); background-size: 400% 400%; animation: gradShift 15s ease infinite; color: #fff; }
        header, footer { visibility: hidden; }
        .title { font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(135deg, #00c853, #69f0ae); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 25px rgba(0,200,83,0.7); }
        .subtitle { text-align: center; color: #b0bec5; font-size: 1.2rem; margin-bottom: 2rem; }
        .module-card { background: rgba(255,255,255,0.05); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; border-left: 4px solid #00c853; }
        .lesson-card { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 1.2rem; margin: 0.5rem 0; }
        .badge-card { background: rgba(255,215,0,0.1); border: 2px solid #ffd700; border-radius: 20px; padding: 2rem; text-align: center; }
        .stButton button { background: linear-gradient(135deg, #00c853, #4caf50); color: #fff; border: none; border-radius: 10px; padding: 12px 30px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @keyframes gradShiftLight { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
        .stApp { background: linear-gradient(135deg, #e8f5e9, #f1f8e9, #fffde7); background-size: 400% 400%; animation: gradShiftLight 15s ease infinite; color: #1b5e20; }
        header, footer { visibility: hidden; }
        .title { font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(135deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; color: #33691e; font-size: 1.2rem; margin-bottom: 2rem; }
        .module-card { background: rgba(255,255,255,0.9); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; border-left: 4px solid #2e7d32; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .lesson-card { background: #fff; border-radius: 15px; padding: 1.2rem; margin: 0.5rem 0; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
        .badge-card { background: rgba(255,215,0,0.15); border: 2px solid #ffd700; border-radius: 20px; padding: 2rem; text-align: center; }
        .stButton button { background: linear-gradient(135deg, #2e7d32, #4caf50); color: #fff; border: none; border-radius: 10px; padding: 12px 30px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="title">🎓 GAIA University</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Maize Agronomist Course — University-Level Field Manual</div>', unsafe_allow_html=True)

# Complete course data with full lesson content
COURSE = {
    1: {
        "title": "Maize Identity, Botany and Plant Structure",
        "lessons": {
            "What is Maize?": "Maize is a cereal crop, Zea mays L., belonging to the grass family Gramineae/Poaceae. It is a C4 grass with high photosynthetic efficiency. Agronomists identify crop, age, uniformity, row arrangement, and environment before touching plants. Field task: identify five pieces of information before inspecting plants. Always document observation, measurement, calculation, interpretation, and next action.",
            "Why an Agronomist Studies the Whole Plant": "Maize performance depends on roots, stem, leaves, reproductive structures, soil, water, nutrients, pests, diseases, and management. Never diagnose from one leaf alone. Field task: dig up three plants and compare root systems. Record root colour, branching, depth, soil adhesion, lesions, insect damage, stem base, and leaves.",
            "Root System: What You Must Know in the Field": "Maize has no taproot. It has seminal roots and adventitious fibrous roots from lower stem nodes. Roots spread laterally and can penetrate about 2.5 m. Fertilizer is only useful if roots can access it. Field task: excavate soil block, observe fine and nodal roots, check for restricted growth, discoloration, rot, insect feeding, or hardpan layers.",
            "Stem, Nodes, Leaves and Brace Roots": "A normal maize stem is about 2–3 m high with roughly 14 internodes. Leaves average 12–18. Brace roots arise from above-ground nodes for stability. Field task: measure plant height for 10 plants and calculate mean. Example mean height calculation: (105+110+108+112+107+111+109+106+113+109) ÷ 10 = 109 cm.",
            "Leaves Are the Crop's Production Engine": "Leaves produce carbohydrates for growth and grain. Describe symptoms before naming them: which leaf, where on leaf, colour, shape, dead tissue, expanding or not, distribution pattern. Field task: assess 20 plants and calculate incidence: affected ÷ total × 100. Example: 7/20 × 100 = 35%.",
            "Tassels, Silks, Ears and Pollination": "Maize has separate male and female inflorescences on the same plant. Tassel is the terminal male inflorescence, ear is female. Each silk is associated with a potential kernel. Field task: inspect 20 plants at flowering and record tassel visible, pollen shed, silks visible, silk length, silk condition, insect feeding.",
            "Kernels, Ear Rows and Yield Components": "Grain yield ≈ plants/ha × ears/plant × kernels/ear × kernel weight. Example: 50,000 plants/ha × 1.0 ear × 450 kernels = 22,500,000 kernels. At 0.30 g/kernel, yield = 6,750 kg/ha. Field task: count rows on 10 ears and kernels in measured sections."
        }
    },
    2: {
        "title": "Environment, Soil and Field Assessment",
        "lessons": {
            "Maize Types and Production Objectives": "Distinguish crop type from production objective. Hybrids provide high yield but seed should not be saved for next crop. OPVs can be saved with isolation and selection. Field task: interview farmer on variety, seed source, seed class, purchase date, previous crop, target market, previous yield.",
            "Variety Selection: A Decision Matrix": "Build a matrix with criteria: adaptation, maturity, yield potential, disease resistance, pest tolerance, market, seed availability, seed cost, postharvest requirements. Score each variety 1–5, weight criteria 1–5, multiply and sum. This makes selection transparent.",
            "Seed Quality and Germination Testing": "Germination % = germinated seeds ÷ seeds tested × 100. Example: 94/100 = 94%. Field task: perform germination test and document daily emergence. Record seed lot, date, conditions, number tested, germinated, abnormal seedlings.",
            "Seed Treatment and Safety": "Seed treatment protects seed and young seedlings. Always read label, confirm crop registration, calculate rate, wear PPE, prevent treated seed entering food channels, clean equipment, record product details. Field task: conduct seed-treatment safety audit without applying chemicals.",
            "Environment: Rainfall and Planting Window": "Most Nigerian maize is rain-fed. Planting should begin at onset of reliable rainfall. Forest zone ~15 March–1 April, Derived Savannah ~1–30 April, Southern Guinea Savannah May–June depending on rainfall. Field task: create planting decision record with date, rainfall, soil moisture, forecast, variety maturity, field readiness."
        }
    },
    3: {
        "title": "Varieties, Seed Quality and Crop Establishment",
        "lessons": {
            "Soil Profile and Drainage": "Maize grows best on well-drained, slightly acid soils. Strongly acid soils may have aluminium and manganese toxicity. Field task: dig soil pit, describe surface and subsoil, feel moisture at depths, identify roots and hardpan layers. Record location of each observation.",
            "Soil Sampling for an Agronomist": "Soil test quality depends on sampling. Divide field into uniform units, avoid fertilizer bands and manure piles, collect multiple cores, mix representative subsamples, label with field, depth, date, history. Field task: design a soil sampling protocol for one field.",
            "Soil Organic Matter and Residues": "Crop residues are important organic matter sources. Retaining residues can protect soil and recycle nutrients. Field task: estimate residue mass using 1 m² quadrat. Example: 0.8 kg/m² × 10,000 = 8,000 kg/ha = 8 t/ha.",
            "Nutrient Requirement: The Numbers": "Approximate requirement per 100 kg grain: 2.43 kg N, 0.53 kg P, 1.8 kg K. For 5,000 kg/ha: N = 121.5 kg, P = 26.5 kg, K = 90 kg. This is crop uptake, not automatic fertilizer recommendation.",
            "Nitrogen: Function, Demand and Loss": "Nitrogen is central to maize growth. Losses occur through leaching, denitrification, and volatilization. Field task: ask farmer when and how nitrogen was applied. Product calculation: 92 kg N ÷ 0.46 = 200 kg urea/ha."
        }
    },
    4: {
        "title": "Plant Population, Planting Operations and Fertilizer Management",
        "lessons": {
            "Phosphorus: Early Roots and Placement": "Phosphorus is important early because young roots have limited capacity. Purple lower leaves can indicate deficiency but also low temperature or salinity. Field task: compare two areas with different placement history. Product calculation: 20 kg P ÷ 0.20 = 100 kg fertilizer/ha.",
            "Potassium and Crop Strength": "Potassium is important for photosynthesis. By silking, ~90% of total uptake may have occurred. Deficiency shows yellowing/drying of lower leaf margins. Field task: identify oldest affected leaves, check soil test K, record plant population and fertilizer history.",
            "Secondary and Micronutrients": "Sulphur, magnesium, calcium, and micronutrients like zinc can be deficient. Blindly applying micronutrients wastes money. Field task: create deficiency diagnostic card for N, P, K, S, and Zn with symptom location and look-alikes.",
            "Fertilizer Placement and Seedling Injury": "Fertilizer injury is usually right fertilizer placed too close to seed. Nitrogen and potassium salts are major contributors. Field task: measure seed depth, fertilizer depth, horizontal separation, product identity, rate per stand, seedling damage.",
            "Fertilizer Rate Conversion": "Product rate = required nutrient ÷ nutrient fraction. Example: 60 kg N ÷ 0.20 = 300 kg fertilizer/ha. 15-15-15 product at 200 kg/ha supplies 30 kg N, 30 kg P₂O₅, 30 kg K₂O. Field task: calculate product needed for 30, 60, 90 kg of labelled nutrient.",
            "Weed Competition": "Weeds compete for light, water, nutrients, space. Field task: count weeds in 0.25 m² quadrat. Example: 18 weeds ÷ 0.25 = 72 weeds/m² = 720,000 weeds/ha. Record species, growth stage, density, distribution, crop stage."
        }
    },
    5: {
        "title": "Crop Growth, Water, Weeds and Crop Management",
        "lessons": {
            "Herbicide Application as an Agronomic Operation": "Herbicide performance depends on product, weed species, weed stage, crop stage, rate, water volume, nozzle, pressure, weather, operator technique. Field task: conduct water-only calibration. 200 L/ha application with 15 L knapsack covers 750 m² per tank.",
            "Maize Growth Stages: VE to V5": "VE occurs 4–5 days after planting under ideal conditions. V1 = first leaf collar. V3 = increasing reliance on photosynthesis and nodal roots. V4 = weed control important. V5 = potential leaf and ear structures determined. Field task: stand count, height, leaf count, weed density, insect feeding, soil moisture.",
            "V6 to V15: Rapid Growth and Ear Determination": "Around V6–V8 growing point moves above soil surface. V7 begins rapid growth. Kernel-row number determined. V9–V11 rapid growth. V12–V15 high water and nutrient demand. Field task: compare V7 and V13 fields and write monitoring differences.",
            "VT, Silking and Pollination": "Tassel produces pollen, silks provide receptive surfaces. Assess synchrony. Field task: record 20 plants for tassel shed, visible silks, both. Silking incidence = silking ÷ total × 100. Water stress around flowering is critical.",
            "Grain Filling and Maturity": "Physiological maturity = maximum dry-matter accumulation, ~30% moisture. Field task: inspect kernel development, collect ears, check kernel consistency, measure moisture, assess lodging and insect damage.",
            "Water Management and Drought Diagnosis": "Maize is sensitive to water availability at establishment and reproduction. Field task: diagnose water stress by checking leaf rolling, soil moisture at root depth, symptoms on ridges vs low areas, recent rainfall, root inspection.",
            "Intercropping and Rotation": "Intercropping changes competition. Rotation prevents nutrient depletion and pest/disease buildup. Field task: map intercropped field and record previous two crops."
        }
    },
    6: {
        "title": "Pests, Diseases and Integrated Crop Protection",
        "lessons": {
            "Plant Population: The Core Calculation": "Plants/ha = 10,000 ÷ (row spacing × within-row spacing) × plants per position. Example: 0.75 m × 0.25 m, one plant = 53,333 plants/ha. Field task: measure actual spacing and calculate theoretical population, then count actual.",
            "Stand Count and Establishment Loss": "Target vs actual population. Example: target 50,000, actual 44,000 = 12% loss. Field task: count 10 row sections, calculate mean and range, mark unusual sections, identify cause of missing plants.",
            "Hand Planting and Thinning": "Plant three seeds per hole, thin to two 1–2 weeks after germination. Field task: select 20 stations, count seedlings, mark singles/doubles/triples/empty, calculate thinning requirement, repeat after thinning.",
            "Mechanical Planting and Calibration": "Calibrate planter each season. Example: 100 m test row at 20 cm spacing = 500 positions. If 460 seeds delivered = 8% deficit. Field task: conduct calibration test and record skips and doubles.",
            "Pest Scouting: From Walking to Data": "Scout using W pattern. Record crop stage, pest present/absent, pest stage, plant part affected, severity, natural enemies. Incidence = affected ÷ total × 100. Example: 12/40 = 30%. Field task: scout 50 plants in three zones and compare incidence."
        }
    },
    7: {
        "title": "Aflatoxin, Harvest, Drying and Grain Quality",
        "lessons": {
            "Stem Borers and Damage Signatures": "Stem borers cause window panes, dead hearts, tunnelling, frass, lodging. Field task: inspect whorl leaves, open suspect stems, look for tunnels/frass/larvae, record dead-heart incidence. Example: 8/40 = 20%.",
            "Fall Armyworm and Image-Based Diagnosis": "Fall armyworm attacks from seedling stage onward. Damage includes windowing, ragged feeding, frass in whorl. Field task: photograph whole plant, affected leaf, close detail. Submit to GAIA and compare with field evidence.",
            "Disease Diagnosis: Symptom ≠ Cause": "Leaf spots, blights, wilting, discoloration can arise from pathogens, nutrients, environment, or chemical injury. Field task: compare affected and unaffected plants, list three possible causes, identify evidence for each.",
            "Integrated Pest Management": "Combine prevention, monitoring, identification, severity assessment, justified intervention, safe application, follow-up. Field task: create IPM plan with Prevent/Detect/Respond columns for one major pest.",
            "Aflatoxin: Why Agronomy Continues After Flowering": "Aflatoxins are poisonous compounds produced by fungi. Contamination can occur without visible mould. Risk increases with drought, insect damage, high temperature, delayed drying. Field task: conduct aflatoxin-risk walk and identify moisture entry points."
        }
    },
    8: {
        "title": "Yield Forecasting, Farm Economics and GAIA Field Practice",
        "lessons": {
            "Aflasafe and Integrated Aflatoxin Management": "Aflasafe is a biocontrol product with atoxigenic Aspergillus flavus strains. Maize application rate ~10 kg/ha about 3 weeks before flowering. Field task: create calendar from 3 weeks before flowering to storage.",
            "Harvesting Maize": "Fresh maize: harvest when silk turns brown (~50–70 days). Grain: ~80–110 days depending on variety. Field task: sample ears, check kernel development, measure moisture, assess lodging, drying capacity.",
            "Drying, Respiration and Moisture": "Physiological maturity ~30% moisture. Storage target below 13%. Adjusted weight = observed weight × (100−observed moisture)/(100−target moisture). Example: 3,500 kg at 22% → 3,138 kg at 13%.",
            "Shelling, Cleaning, Storage and Transport": "Shelling methods: hand, ribbed tubes, hand-operated discs, engine-operated threshers. Field task: follow one bag from field to storage, record every handling step and quality risk.",
            "Yield Forecasting": "Sample-area method: yield = sample weight ÷ sample area × 10,000. Example: 400 kg from 1,000 m² = 4,000 kg/ha. Field task: sample multiple zones, measure moisture, calculate standardized yield.",
            "Farm Records and Economics": "Gross revenue = saleable quantity × selling price. Gross margin = gross revenue − variable costs. Example: 4,000 kg × ₦500 = ₦2,000,000. If costs = ₦1,250,000, margin = ₦750,000. Field task: calculate cost/ha for fertilizer products.",
            "The GAIA Agronomist Field Workflow": "8 steps: Establish context, Observe, Sample, Analyse (GAIA), Verify, Decide, Monitor, Document. GAIA is decision support, not magic. Field task: complete one GAIA case and write professional report with Observation, Evidence, Model Output, Verification, Diagnosis, Recommendation, Follow-up."
        }
    }
}

# Session state
if "selected_module_id" not in st.session_state:
    st.session_state.selected_module_id = None
if "selected_lesson" not in st.session_state:
    st.session_state.selected_lesson = None
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = None

# Module view
if st.session_state.selected_module_id is None:
    st.markdown("## 📚 Course Modules")
    for module_id, module in COURSE.items():
        st.markdown(f'<div class="module-card"><h3>Module {module_id}: {module["title"]}</h3><p>{len(module["lessons"])} lessons</p></div>', unsafe_allow_html=True)
        if st.button(f"Open Module {module_id}", key=f"mod_{module_id}"):
            st.session_state.selected_module_id = module_id
            st.rerun()
elif st.session_state.selected_lesson is None:
    module = COURSE[st.session_state.selected_module_id]
    st.markdown(f"## Module {st.session_state.selected_module_id}: {module['title']}")
    for lesson_title in module["lessons"].keys():
        if st.button(lesson_title, key=f"les_{st.session_state.selected_module_id}_{lesson_title}", use_container_width=True):
            st.session_state.selected_lesson = lesson_title
            st.rerun()
    if st.button("← Back to Modules"):
        st.session_state.selected_module_id = None
        st.rerun()
else:
    module = COURSE[st.session_state.selected_module_id]
    lesson_title = st.session_state.selected_lesson
    lesson_content = module["lessons"][lesson_title]
    
    st.markdown(f"## {lesson_title}")
    st.markdown(f"*Module {st.session_state.selected_module_id}: {module['title']}*")
    st.markdown(lesson_content)
    
    # Voice narration
    if st.button("🔊 Listen to this lesson"):
        try:
            from app.utils.deepseek_explainer import text_to_speech
            audio_bytes, err = text_to_speech(lesson_content)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
            else:
                st.warning(f"Voice unavailable: {err}")
        except:
            st.warning("Voice generation not available.")
    
    # Mark lesson complete button
    if st.button("✅ Mark Complete & Next Lesson"):
        # Find next lesson in module
        lessons = list(module["lessons"].keys())
        current_idx = lessons.index(lesson_title)
        if current_idx < len(lessons) - 1:
            st.session_state.selected_lesson = lessons[current_idx + 1]
            st.rerun()
        else:
            st.success("Module complete! Take the quiz to earn your badge.")
    
    if st.button("← Back to Lessons"):
        st.session_state.selected_lesson = None
        st.rerun()

# Navigation
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
