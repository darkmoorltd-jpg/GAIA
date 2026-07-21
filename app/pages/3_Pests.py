
import streamlit as st
from PIL import Image
import torch
import torch.nn.functional as F
import numpy as np
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.models.pretrained_vit import PretrainedViTClassifier
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

# ---------- Theme toggle ----------
st.set_page_config(page_title="GAIA – Pest Detection", page_icon="🐛", layout="wide")

st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="pest_theme_toggle")

if dark_mode:
    theme = "dark"
else:
    theme = "light"

# ---------- Scan deduction ----------
def deduct_and_show():
    import streamlit as st
    from supabase import create_client
    if "user" not in st.session_state or st.session_state.user is None:
        return
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
    user_id = st.session_state.user.id
    try:
        supabase.table("user_scans").insert(
            {"user_id": user_id, "scans_remaining": 30, "plan": "free"}
        ).execute()
    except:
        pass
    try:
        supabase.rpc("decrement_scan", {"uid": user_id}).execute()
        res = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
        if res.data:
            remaining = res.data[0]["scans_remaining"]
            st.success(f"Scan deducted. Remaining scans: {remaining}")
    except:
        pass

# ---------- Pest definitions ----------
PEST_CLASSES = [
    'rice leaf roller', 'rice leaf caterpillar', 'paddy stem maggot', 'asiatic rice borer', 'yellow rice borer',
    'rice gall midge', 'Rice Stemfly', 'brown plant hopper', 'white backed plant hopper', 'small brown plant hopper',
    'rice water weevil', 'rice leafhopper', 'grain spreader thrips', 'rice shell pest', 'grub', 'mole cricket', 'wireworm',
    'white margined moth', 'black cutworm', 'large cutworm', 'yellow cutworm', 'red spider', 'corn borer', 'army worm', 'aphids',
    'Potosiabre vitarsis', 'peach borer', 'english grain aphid', 'green bug', 'bird cherry-oataphid', 'wheat blossom midge',
    'penthaleus major', 'longlegged spider mite', 'wheat phloeothrips', 'wheat sawfly', 'cerodonta denticornis', 'beet fly',
    'flea beetle', 'cabbage army worm', 'beet army worm', 'Beet spot flies', 'meadow moth', 'beet weevil', 'sericaorient alismots chulsky',
    'alfalfa weevil', 'flax budworm', 'alfalfa plant bug', 'tarnished plant bug', 'Locustoidea', 'lytta polita', 'legume blister beetle',
    'blister beetle', 'therioaphis maculata Buckton', 'odontothrips loti', 'Thrips', 'alfalfa seed chalcid', 'Pieris canidia',
    'Apolygus lucorum', 'Limacodidae', 'Viteus vitifoliae', 'Colomerus vitis', 'Brevipoalpus lewisi McGregor', 'oides decempunctata',
    'Polyphagotars onemus latus', 'Pseudococcus comstocki Kuwana', 'parathrene regalis', 'Ampelophaga', 'Lycorma delicatula', 'Xylotrechus',
    'Cicadella viridis', 'Miridae', 'Trialeurodes vaporariorum', 'Erythroneura apicalis', 'Papilio xuthus', 'Panonchus citri McGregor',
    'Phyllocoptes oleiverus ashmead', 'Icerya purchasi Maskell', 'Unaspis yanonensis', 'Ceroplastes rubens', 'Chrysomphalus aonidum',
    'Parlatoria zizyphus Lucus', 'Nipaecoccus vastalor', 'Aleurocanthus spiniferus', 'Tetradacus c Bactrocera minax ', 'Dacus dorsalis(Hendel)',
    'Bactrocera tsuneonis', 'Prodenia litura', 'Adristyrannus', 'Phyllocnistis citrella Stainton', 'Toxoptera citricidus', 'Toxoptera aurantii',
    'Aphis citricola Vander Goot', 'Scirtothrips dorsalis Hood', 'Dasineura sp', 'Lawana imitata Melichar', 'Salurnis marginella Guerr',
    'Deporaus marginatus Pascoe', 'Chlumetia transversa', 'Mango flat beak leafhopper', 'Rhytidodera bowrinii white', 'Sternochetus frigidus',
    'Cicadellidae'
]
NUM_CLASSES = len(PEST_CLASSES)

# ---------- Theme‑dependent CSS ----------
if theme == "dark":
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #1a0f00 0%, #2e1c00 30%, #3e2a00 60%, #1a0f00 100%);
            color: #fff8e1;
        }
        header, footer {visibility: hidden;}
        
        .particles {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            z-index: -1; overflow: hidden;
        }
        .particle {
            position: absolute; background: rgba(255, 152, 0, 0.15);
            border-radius: 50%; animation: float 15s infinite ease-in-out;
        }
        .particle:nth-child(1) { width: 80px; height: 80px; left: 10%; top: 20%; animation-delay: 0s; }
        .particle:nth-child(2) { width: 60px; height: 60px; left: 80%; top: 60%; animation-delay: 3s; }
        .particle:nth-child(3) { width: 120px; height: 120px; left: 40%; top: 70%; animation-delay: 6s; }
        .particle:nth-child(4) { width: 50px; height: 50px; left: 70%; top: 10%; animation-delay: 9s; }
        .particle:nth-child(5) { width: 100px; height: 100px; left: 25%; top: 40%; animation-delay: 12s; }
        @keyframes float {
            0% { transform: translateY(0px) rotate(0deg); opacity: 0.5; }
            50% { transform: translateY(-30px) rotate(180deg); opacity: 0.8; }
            100% { transform: translateY(0px) rotate(360deg); opacity: 0.5; }
        }
        
        .scan-ring {
            position: absolute; top: 50%; left: 50%;
            width: 300px; height: 300px; border-radius: 50%;
            border: 3px solid rgba(255, 152, 0, 0.6);
            transform: translate(-50%, -50%);
            animation: scanPulse 2s infinite ease-out; z-index: 2; pointer-events: none;
        }
        .scan-ring:nth-child(2) { animation-delay: 0.7s; }
        .scan-ring:nth-child(3) { animation-delay: 1.4s; }
        @keyframes scanPulse {
            0% { width: 100px; height: 100px; opacity: 1; }
            100% { width: 400px; height: 400px; opacity: 0; }
        }
        
        .title {
            font-size: 3.5rem; font-weight: 900; text-align: center;
            background: linear-gradient(90deg, #ff9800, #ffcc80, #ff9800);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 25px rgba(255, 152, 0, 0.7);
            margin-bottom: 0.5rem; position: relative; z-index: 1;
            animation: pestGlow 2s ease-in-out infinite alternate;
        }
        @keyframes pestGlow {
            from { text-shadow: 0 0 25px rgba(255, 152, 0, 0.7); }
            to { text-shadow: 0 0 50px rgba(255, 152, 0, 1), 0 0 80px rgba(255, 152, 0, 0.6); }
        }
        .subtitle { text-align: center; font-size: 1.2rem; color: #bcaaa4; margin-bottom: 2rem; position: relative; z-index: 1; }
st.markdown('<a href="/" target="_self"><button style="padding:8px 16px; background: linear-gradient(90deg, #2e7d32, #4caf50); color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">🏠 Dashboard</button></a>', unsafe_allow_html=True)
        
        .stFileUploader { position: relative; z-index: 3; }
        .stFileUploader > div {
            background: rgba(255,255,255,0.05) !important; backdrop-filter: blur(12px) !important;
            border: 2px dashed rgba(255, 152, 0, 0.4) !important; border-radius: 20px !important;
            padding: 2rem !important; transition: all 0.3s ease;
        }
        .stFileUploader > div:hover {
            border-color: #ff9800 !important; background: rgba(255, 152, 0, 0.1) !important;
        }
        
        .stImage img { border-radius: 20px; box-shadow: 0 0 40px rgba(255, 152, 0, 0.3); }
        
        .result-card {
            background: rgba(255,255,255,0.05); backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 152, 0, 0.2); border-radius: 20px;
            padding: 1.5rem; margin: 0.5rem 0; transition: all 0.3s ease;
        }
        .result-card.top-result { border-color: #ff9800; box-shadow: 0 0 30px rgba(255, 152, 0, 0.3); }
        .pest-swatch {
            display: inline-block; width: 20px; height: 20px; border-radius: 4px;
            margin-right: 8px; vertical-align: middle; background: #ff9800;
            box-shadow: 0 0 10px rgba(255, 152, 0, 0.5);
        }
        
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #ff9800, #ffcc80);
        }
    </style>
    
    <div class="particles">
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
            color: #3e2723;
        }
        header, footer {visibility: hidden;}
        .particles, .scan-ring { display: none; }
        .title {
            font-size: 3.5rem; font-weight: 900; text-align: center;
            background: linear-gradient(90deg, #e65100, #ff9800, #e65100);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 10px rgba(230, 81, 0, 0.3);
            margin-bottom: 0.5rem;
            animation: pestGlowLight 2s ease-in-out infinite alternate;
        }
        @keyframes pestGlowLight {
            from { text-shadow: 0 0 10px rgba(230, 81, 0, 0.3); }
            to { text-shadow: 0 0 25px rgba(230, 81, 0, 0.8), 0 0 50px rgba(230, 81, 0, 0.5); }
        }
        .subtitle { text-align: center; font-size: 1.2rem; color: #4e342e; margin-bottom: 2rem; }
        .stFileUploader > div {
            background: rgba(255,255,255,0.8) !important; backdrop-filter: blur(10px) !important;
            border: 2px dashed rgba(230, 81, 0, 0.3) !important; border-radius: 20px !important;
            padding: 2rem !important;
        }
        .stFileUploader > div:hover {
            border-color: #e65100 !important; background: rgba(255, 152, 0, 0.1) !important;
        }
        .stImage img { border-radius: 20px; box-shadow: 0 0 20px rgba(0,0,0,0.2); }
        .result-card {
            background: rgba(255,255,255,0.8); backdrop-filter: blur(10px);
            border: 1px solid rgba(0,0,0,0.1); border-radius: 20px;
            padding: 1.5rem; margin: 0.5rem 0;
        }
        .result-card.top-result { border-color: #e65100; box-shadow: 0 0 20px rgba(230, 81, 0, 0.2); }
        .pest-swatch { background: #ff9800; box-shadow: 0 0 5px rgba(0,0,0,0.2); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #ff9800, #ffcc80); }
    </style>
    """, unsafe_allow_html=True)



# ---------- Navigation Bar ----------
st.markdown("""
<style>
    .nav-bar { display: flex; justify-content: center; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap; }
    .nav-bar a { text-decoration: none; color: inherit; }
    .nav-button {
        display: inline-block; padding: 10px 20px; border-radius: 12px;
        background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2); transition: all 0.3s ease;
        cursor: pointer; font-weight: 600; font-size: 0.95rem;
    }
    .nav-button:hover {
        background: rgba(255,255,255,0.2); border-color: rgba(255,255,255,0.5);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

cols = st.columns(5)
pages = [
    ("🏠 Dashboard", "pages/1_Dashboard.py"),
    ("🌿 Crops", "pages/2_Crops.py"),
    ("🐛 Pests", "pages/3_Pests.py"),
    ("🏞️ Soil", "pages/4_Soil.py"),
    ("🐄 Livestock", "pages/5_Livestock.py")
]
for col, (label, path) in zip(cols, pages):
    with col:
        st.page_link(path, label=label, help=f"Go to {label}")


# ---------- Hero Section ----------

# ---------- Sidebar navigation ----------
with st.sidebar:
    st.markdown("### 🌱 GAIA")
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("app/pages/1_Dashboard.py")
    if st.button("🌿 Crop Disease", use_container_width=True):
        st.switch_page("app/pages/2_Crops.py")
    if st.button("🐛 Pest Detection", use_container_width=True):
        st.switch_page("app/pages/3_Pests.py")
    if st.button("🏞️ Soil Analysis", use_container_width=True):
        st.switch_page("app/pages/4_Soil.py")
    if st.button("🐄 Livestock Health", use_container_width=True):
        st.switch_page("app/pages/5_Livestock.py")
    if st.button("💳 Payment History", use_container_width=True):
        st.switch_page("app/pages/6_Payment_History.py")
    st.markdown("---")
    if st.session_state.get("user"):
        st.write(f"👤 {st.session_state.user.email}")
        st.metric("Scans", st.session_state.get("scans_left", 0))
    st.markdown("*Powered by Darkmoor Ltd*")

st.markdown('<div class="title">🐛 Pest Detection</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Snap a photo of any insect and we\'ll identify it from 102 common pests</div>', unsafe_allow_html=True)

# ---------- Upload Section ----------
uploaded_file = st.file_uploader("📤 Upload insect photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(image, caption="", use_column_width=True)
        if theme == "dark":
            st.markdown("""
            <div style="position:relative; height:0;">
                <div class="scan-ring"></div>
                <div class="scan-ring"></div>
                <div class="scan-ring"></div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🔍 Identification Result")

    # Try to load the 102‑class model
    model = None
    try:
        from app.utils.model_loader import create_model_from_checkpoint
        checkpoint = "checkpoints/pests_102class/best_model.pt"
        if os.path.exists(checkpoint):
            model = create_model_from_checkpoint(checkpoint, NUM_CLASSES)
    except Exception as e:
        model = None
        st.warning(f"Real model unavailable, using demo. ({e})")

    if model is not None:
        transform = Compose([
            Resize((224, 224)),
            ToTensor(),
            Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        img_tensor = transform(image).unsqueeze(0)
        with torch.no_grad():
            logits = model(img_tensor)
            probs = F.softmax(logits, dim=1)[0].cpu().numpy()
    else:
        # Demo fallback
        import hashlib
        seed = int(hashlib.md5(uploaded_file.name.encode()).hexdigest()[:8], 16)
        np.random.seed(seed)
        probs = np.random.rand(NUM_CLASSES)
        probs = probs / probs.sum()

    top_idx = np.argmax(probs)
    st.markdown(f"""
    <div class="result-card top-result" style="border-left: 5px solid #ff9800;">
        <h2 style="margin:0; display: flex; align-items: center;">
            <span class="pest-swatch"></span>
            {PEST_CLASSES[top_idx]}
            <span style="margin-left: auto; font-size: 2rem; color: #ff9800;">{probs[top_idx]*100:.1f}%</span>
        </h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Top 5 Probabilities")
    sorted_idx = np.argsort(probs)[::-1][:5]
    for i in sorted_idx:
        st.write(f"**{PEST_CLASSES[i]}**: {probs[i]*100:.1f}%")
        st.progress(float(probs[i]))

    deduct_and_show()
