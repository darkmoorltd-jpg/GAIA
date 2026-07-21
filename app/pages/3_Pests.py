
import streamlit as st
from PIL import Image
import torch, torch.nn.functional as F, numpy as np, os, sys, timm

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Pest Detection", page_icon="🐛", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .top-nav { display: flex; justify-content: center; gap: 2rem; padding: 0.8rem; background: rgba(255,255,255,0.9); backdrop-filter: blur(15px); border-radius: 15px; margin-bottom: 2rem; }
    .top-nav a { color: #2e7d32; text-decoration: none; font-weight: 600; font-size: 1rem; padding: 0.5rem 1.5rem; border-radius: 30px; }
</style>
<div class="top-nav"><a href="/" target="_self">🏠 Dashboard</a></div>
""", unsafe_allow_html=True)

if "theme" not in st.session_state: st.session_state.theme = "dark"
dark_mode = st.toggle("", value=(st.session_state.theme == "dark"), key="pests_theme_toggle")
st.session_state.theme = "dark" if dark_mode else "light"
theme = st.session_state.theme

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

class Pest102Classifier(nn.Module):
    def __init__(self): super().__init__(); self.backbone = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=0); self.head = nn.Sequential(nn.Linear(self.backbone.embed_dim, 2048), nn.GELU(), nn.Dropout(0.3), nn.Linear(2048, 1024), nn.GELU(), nn.Dropout(0.2), nn.Linear(1024, NUM_CLASSES))
    def forward(self, x): return self.head(self.backbone(x))

@st.cache_resource
def load_pest_model():
    checkpoint = "checkpoints/pests_102class/best_model.pt"
    if not os.path.exists(checkpoint): raise FileNotFoundError(f"Model not found at {checkpoint}")
    model = Pest102Classifier(); state_dict = torch.load(checkpoint, map_location="cpu", weights_only=False); model.load_state_dict(state_dict); model.eval()
    return model

def predict_image(model, image):
    transform = Compose([Resize((224, 224)), ToTensor(), Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    with torch.no_grad(): return F.softmax(model(transform(image).unsqueeze(0)), dim=1)[0].cpu().numpy()

def deduct_and_show(user_id):
    from supabase import create_client
    url = st.secrets["supabase"]["url"]; key = st.secrets["supabase"]["key"]; supabase = create_client(url, key)
    try: supabase.table("user_scans").insert({"user_id": user_id, "scans_remaining": 30, "plan": "free"}).execute()
    except: pass
    try:
        supabase.rpc("decrement_scan", {"uid": user_id}).execute()
        res = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
        if res.data: st.success(f"Scan deducted. Remaining: {res.data[0]['scans_remaining']}")
    except: pass

st.markdown('<h1 style="text-align:center;color:#e65100;">🐛 Pest Detection (102 Species)</h1>', unsafe_allow_html=True)
uploaded_files = st.file_uploader("📤 Upload insect photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file).convert("RGB")
        col1, col2 = st.columns([1, 2])
        with col1: st.image(image, caption=uploaded_file.name, width=200)
        with col2:
            try:
                model = load_pest_model(); probs = predict_image(model, image)
                top_idx = np.argmax(probs); st.success(f"**{PEST_CLASSES[top_idx]}** ({probs[top_idx]*100:.1f}%)")
                if st.session_state.get("user"): deduct_and_show(st.session_state.user.id)
            except Exception as e: st.error(str(e))
        st.markdown("---")
