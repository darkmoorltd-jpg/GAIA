
import streamlit as st
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os
import sys
import timm

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

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

dark_mode = st.toggle("", value=True, key="pest_theme_toggle")
theme = "dark" if dark_mode else "light"

# ---------- 102 pest classes ----------
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

# ---------- Helper ----------
def _get_recommendation(pest):
    recs = {
        'aphids': "Apply neem oil or insecticidal soap. Introduce ladybugs as natural predators.",
        'corn borer': "Use Bt (Bacillus thuringiensis) spray. Apply before larvae enter the stalk.",
        'mole cricket': "Apply parasitic nematodes to soil. Use bait traps at dusk.",
        'grub': "Apply milky spore bacteria to lawn. Beneficial nematodes are highly effective.",
        'wireworm': "Rotate crops with non‑host plants. Use soil insecticides if infestation is severe.",
        'rice leaf roller': "Spray neem oil at early infestation. Encourage natural enemies like spiders.",
        'brown plant hopper': "Apply systemic insecticides. Maintain field drainage and avoid excessive nitrogen.",
        'army worm': "Use Bt or spinosad spray. Hand‑pick caterpillars in small gardens.",
        'red spider': "Spray with water to dislodge mites. Apply horticultural oil or sulfur.",
        'blister beetle': "Hand‑pick beetles (wear gloves). Use spinosad for severe infestations.",
        'white margined moth': "Apply Bt or pyrethrin spray. Remove infested leaves.",
        'thrips': "Use blue sticky traps. Apply spinosad or insecticidal soap.",
    }
    return recs.get(pest, "Consult a local agronomist for targeted treatment options. Isolate affected plants and monitor daily.")

# ---------- Custom model class ----------
class Pest102Classifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=0)
        self.head = nn.Sequential(
            nn.Linear(self.backbone.embed_dim, 2048),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(2048, 1024),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(1024, NUM_CLASSES)
        )
    def forward(self, x):
        return self.head(self.backbone(x))

@st.cache_resource
def load_pest_model():
    checkpoint = "checkpoints/pests_102class/best_model.pt"
    if not os.path.exists(checkpoint):
        raise FileNotFoundError(f"Model not found at {checkpoint}")
    model = Pest102Classifier()
    state_dict = torch.load(checkpoint, map_location="cpu", weights_only=False)
    model.load_state_dict(state_dict)
    model.eval()
    return model

def predict_image(model, image: Image.Image):
    transform = Compose([
        Resize((224, 224)),
        ToTensor(),
        Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    img_tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        logits = model(img_tensor)
        probs = F.softmax(logits, dim=1)[0].cpu().numpy()
    return probs

# Scan deduction
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
        supabase.table("user_scans").insert({"user_id": user_id, "scans_remaining": 30, "plan": "free"}).execute()
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

# ---------- Theme CSS ----------
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(145deg, #0a0a0a 0%, #1a1a2e 50%, #0d0d0d 100%); color: #e0e0e0; }
        .scanlines { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,100,0.03) 2px, rgba(0,255,100,0.03) 4px); z-index: 0; pointer-events: none; }
        .particle { position: fixed; border-radius: 50%; background: radial-gradient(circle, rgba(0,255,100,0.4), transparent); animation: float 10s infinite ease-in-out; z-index: 0; pointer-events: none; }
        .particle:nth-child(1) { width: 200px; height: 200px; top: 5%; left: 5%; animation-delay: 0s; }
        .particle:nth-child(2) { width: 150px; height: 150px; top: 60%; left: 80%; animation-delay: 3s; }
        .particle:nth-child(3) { width: 250px; height: 250px; top: 70%; left: 10%; animation-delay: 6s; }
        @keyframes float { 0% { transform: translateY(0px) scale(1); opacity: 0.2; } 50% { transform: translateY(-50px) scale(1.1); opacity: 0.5; } 100% { transform: translateY(0px) scale(1); opacity: 0.2; } }
        .title { font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #00ff88, #00cc66, #00ff88); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 30px rgba(0,255,100,0.6); animation: titleGlow 2s ease-in-out infinite alternate; position: relative; z-index: 1; }
        @keyframes titleGlow { from { text-shadow: 0 0 30px rgba(0,255,100,0.6); } to { text-shadow: 0 0 60px rgba(0,255,100,0.9), 0 0 100px rgba(0,255,100,0.5); } }
        .subtitle { text-align: center; font-size: 1.1rem; color: #66ff99; margin-bottom: 2rem; position: relative; z-index: 1; }
        .stFileUploader > div { background: rgba(0,255,100,0.03) !important; backdrop-filter: blur(15px) !important; border: 2px dashed rgba(0,255,100,0.3) !important; border-radius: 20px !important; padding: 2rem !important; position: relative; z-index: 1; }
        .stFileUploader > div:hover { border-color: #00ff88 !important; box-shadow: 0 0 30px rgba(0,255,100,0.2); }
        .stImage img { border-radius: 20px; box-shadow: 0 0 40px rgba(0,255,100,0.3); border: 1px solid rgba(0,255,100,0.2); }
        .result-card { background: rgba(0,0,0,0.6); backdrop-filter: blur(25px); border: 1px solid rgba(0,255,100,0.2); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; position: relative; overflow: hidden; }
        .result-card::before { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: conic-gradient(transparent, rgba(0,255,100,0.1), transparent, transparent); animation: rotate 6s linear infinite; }
        @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .result-card > * { position: relative; z-index: 1; }
        .top-result { background: rgba(0,0,0,0.8); border: 2px solid #00ff88; box-shadow: 0 0 50px rgba(0,255,100,0.4), inset 0 0 30px rgba(0,255,100,0.05); }
        .top-result h3 { font-size: 1.2rem; text-transform: uppercase; letter-spacing: 2px; color: #00ff88; margin: 0.3rem 0; }
        .counter { font-size: 2rem; font-weight: 900; color: #00ff88; text-shadow: 0 0 30px rgba(0,255,100,0.8); animation: pulse 2s ease-in-out infinite; }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
        .progress-container { margin: 0.6rem 0; position: relative; }
        .progress-label { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem; }
        .progress-label span { font-weight: 600; color: #ddd; }
        .progress-label .percent { color: #00ff88; font-size: 1rem; font-weight: 700; }
        .progress-bar { height: 6px; background: rgba(255,255,255,0.05); border-radius: 8px; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 8px; background: linear-gradient(90deg, #00ff88, #00cc66, #00ff88); background-size: 200% 100%; animation: shimmer 2s ease infinite, grow 1.5s ease-out; box-shadow: 0 0 10px rgba(0,255,100,0.6); transition: width 1s ease; }
        @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
        @keyframes grow { from { width: 0% !important; } }
        .progress-fill.warning { background: linear-gradient(90deg, #ffaa00, #ff8800, #ffaa00); box-shadow: 0 0 10px rgba(255,170,0,0.6); }
        .progress-fill.danger { background: linear-gradient(90deg, #ff4444, #ff0000, #ff4444); box-shadow: 0 0 10px rgba(255,0,0,0.6); }
        .action-box { background: rgba(0,255,100,0.05); border: 1px solid rgba(0,255,100,0.3); border-radius: 15px; padding: 1rem; text-align: center; margin-top: 1rem; backdrop-filter: blur(10px); }
    </style>
    <div class="scanlines"></div>
    <div class="particle"></div><div class="particle"></div><div class="particle"></div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e8f5e9 100%); color: #1b5e20; }
        .title { font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #2e7d32, #66bb6a, #2e7d32); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 10px rgba(46,125,50,0.3); animation: titleGlowLight 2s ease-in-out infinite alternate; }
        @keyframes titleGlowLight { from { text-shadow: 0 0 10px rgba(46,125,50,0.3); } to { text-shadow: 0 0 25px rgba(46,125,50,0.8), 0 0 50px rgba(46,125,50,0.5); } }
        .subtitle { text-align: center; font-size: 1.1rem; color: #33691e; margin-bottom: 2rem; }
        .stFileUploader > div { background: rgba(255,255,255,0.8) !important; backdrop-filter: blur(10px) !important; border: 2px dashed rgba(46,125,50,0.3) !important; border-radius: 20px !important; padding: 2rem !important; }
        .stImage img { border-radius: 20px; box-shadow: 0 0 20px rgba(0,0,0,0.2); }
        .result-card { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.1); border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; }
        .top-result { border-color: #2e7d32; box-shadow: 0 0 20px rgba(46,125,50,0.2); }
        .top-result h3 { font-size: 1.2rem; color: #1b5e20; }
        .counter { font-size: 2rem; font-weight: 900; color: #2e7d32; }
        .progress-container { margin: 0.6rem 0; }
        .progress-label { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem; }
        .progress-label span { font-weight: 600; color: #1b5e20; }
        .progress-label .percent { color: #2e7d32; font-size: 1rem; font-weight: 700; }
        .progress-bar { height: 6px; background: rgba(0,0,0,0.05); border-radius: 8px; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 8px; background: linear-gradient(90deg, #4caf50, #81c784); animation: grow 1.5s ease-out; }
        @keyframes grow { from { width: 0% !important; } }
        .progress-fill.warning { background: linear-gradient(90deg, #ffa726, #ffb74d); }
        .progress-fill.danger { background: linear-gradient(90deg, #ef5350, #e57373); }
        .action-box { background: rgba(46,125,50,0.05); border: 1px solid rgba(46,125,50,0.2); border-radius: 15px; padding: 1rem; text-align: center; margin-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# ---------- UI ----------
st.markdown('<div class="title">🐛 PEST IDENTIFICATION</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a photo. Instant neural scan. 102 species detected.</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("📤 DROP YOUR INSECT PHOTO HERE", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="", width=300)
    st.markdown("---")

    try:
        model = load_pest_model()
        probs = predict_image(model, image)
    except FileNotFoundError as e:
        st.error(f"🚫 {e}")
        st.stop()
    except Exception as e:
        st.error(f"Scan failed: {e}")
        st.stop()

    top_idx = np.argmax(probs)
    top_prob = probs[top_idx] * 100

    st.markdown(f"""
    <div class="result-card top-result">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <p style="color: #66ff99; margin: 0; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px;">Identified Pest</p>
                <h3 style="margin: 0.3rem 0;">{PEST_CLASSES[top_idx]}</h3>
            </div>
            <div class="counter">{top_prob:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🧬 TOP 5 PROBABILITIES")
    sorted_idx = np.argsort(probs)[::-1][:5]
    for i in sorted_idx:
        pest_name = PEST_CLASSES[i]
        percent = probs[i] * 100
        bar_class = " warning" if percent < 40 else (" danger" if percent < 20 else "")
        st.markdown(f"""
        <div class="result-card">
            <div class="progress-container">
                <div class="progress-label">
                    <span>{pest_name.upper()}</span>
                    <span class="percent">{percent:.1f}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill{bar_class}" style="width: {percent}%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="action-box">
        <h3 style="color: #00ff88; margin: 0;">⚡ RECOMMENDATION</h3>
        <p style="margin-top: 0.5rem; color: #ddd;">{_get_recommendation(PEST_CLASSES[top_idx])}</p>
    </div>
    """, unsafe_allow_html=True)

    deduct_and_show()
