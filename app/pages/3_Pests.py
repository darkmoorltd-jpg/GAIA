
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

# ---------- Page config & CSS ----------
st.set_page_config(page_title="GAIA – Pest Detection", page_icon="🐛", layout="wide", initial_sidebar_state="expanded")

# Force sidebar visible on all pages
st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
    }
</style>
""", unsafe_allow_html=True)


# ---------- Dashboard top nav ----------
st.markdown("""
<style>
    .top-nav {
        display: flex; justify-content: center; gap: 2rem;
        padding: 0.8rem; background: rgba(255,255,255,0.9); backdrop-filter: blur(15px);
        border-radius: 15px; margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .top-nav a {
        color: #2e7d32; text-decoration: none; font-weight: 600;
        font-size: 1rem; padding: 0.5rem 1.5rem; border-radius: 30px;
        transition: all 0.3s ease;
    }
    .top-nav a:hover {
        background: #e8f5e9; color: #1b5e20;
    }
</style>
<div class="top-nav">
    <a href="/" target="_self">🏠 Dashboard</a>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #fff3e0 100%); }
    .title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #e65100, #ff9800); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { font-size: 1.2rem; color: #555; margin-bottom: 2rem; }
    .pred-box { background: #fff8e1; border-left: 5px solid #ff9800; padding: 1rem 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
    .pred-box-high { border-left-color: #e65100; background: #ffe0b2; }
    .stProgress > div > div > div > div { background: linear-gradient(90deg, #ff9800, #ffb74d); }
    .counter { font-size: 2.5rem; font-weight: 900; color: #e65100; text-shadow: 0 0 20px rgba(230,81,0,0.5); animation: pulse 2s ease-in-out infinite; }
    @keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.05); } }
</style>
""", unsafe_allow_html=True)

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

# ---------- Custom model class ----------
class Pest102Classifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=0)
        self.head = nn.Sequential(
            nn.Linear(self.backbone.embed_dim, 2048), nn.GELU(), nn.Dropout(0.3),
            nn.Linear(2048, 1024), nn.GELU(), nn.Dropout(0.2),
            nn.Linear(1024, NUM_CLASSES)
        )
    def forward(self, x): return self.head(self.backbone(x))

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

# ---------- Scan deduction ----------
def deduct_and_show():
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

# ---------- UI ----------
st.markdown('<div class="title">🐛 Pest Detection</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload photos of insects to identify them</div>', unsafe_allow_html=True)

uploaded_files = st.file_uploader("📤 Upload insect photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    model = load_pest_model()
    for uploaded_file in uploaded_files:
        with st.expander(f"🐛 {uploaded_file.name}", expanded=(len(uploaded_files) == 1)):
            col1, col2 = st.columns([1, 2])
            with col1:
                image = Image.open(uploaded_file).convert("RGB")
                st.image(image, caption=uploaded_file.name, width=300)
            with col2:
                probs = predict_image(model, image)
                top_idx = np.argmax(probs)
                top_prob = probs[top_idx] * 100

                st.markdown(f"""
                <div class="pred-box-high">
                    <h3 style="margin:0">{PEST_CLASSES[top_idx]}</h3>
                    <span style="font-size:1.5rem; font-weight:bold;">{top_prob:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("#### Top 5 Probabilities")
                sorted_idx = np.argsort(probs)[::-1][:5]
                for i in sorted_idx:
                    st.write(f"**{PEST_CLASSES[i]}**: {probs[i]*100:.1f}%")
                    st.progress(float(probs[i]))

                deduct_and_show()


# ---------- Universal Bottom Navigation (safe) ----------
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(6)
with cols[0]:
    st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]:
    st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]:
    st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]:
    st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]:
    st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]:
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
