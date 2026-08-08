
import streamlit as st
from PIL import Image
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from timm.models.vision_transformer import VisionTransformer
import os, requests, hashlib

st.set_page_config(page_title="GAIA – GaiaLens™", page_icon="🔍", layout="wide")

# ── DOWNLOAD MODELS FROM GITHUB RELEASES ──
BASE = "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0"
MODEL_URLS = {
    "crop": f"{BASE}/gaia_millet_3class.pt",
    "pest": f"{BASE}/pests_102class_best_model.pt",
    "soil": f"{BASE}/soil_11class_best_model.pt",
    "livestock": f"{BASE}/poultry_best_model.pt",
}

def ensure_model(model_type):
    os.makedirs("models", exist_ok=True)
    dest = f"models/{model_type}.pt"
    if not os.path.exists(dest) or os.path.getsize(dest) < 10000:
        url = MODEL_URLS.get(model_type)
        if url:
            with st.spinner(f"⬇️ Downloading {model_type} model..."):
                r = requests.get(url, stream=True, timeout=300)
                if r.status_code == 200:
                    with open(dest, "wb") as f:
                        for chunk in r.iter_content(32768):
                            f.write(chunk)
    return dest

# ── MODEL REBUILDER (same as your working model_loader.py) ──
def rebuild_vit(checkpoint_path, num_classes):
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    prefix = "backbone." if any(k.startswith("backbone.") for k in state) else "encoder."
    embed_dim = state[f"{prefix}cls_token"].shape[-1]
    pos = state[f"{prefix}pos_embed"]
    patches = pos.shape[1] - 1
    grid = int(patches ** 0.5)
    img_size = grid * 16
    depth = len([k for k in state if k.startswith(f"{prefix}blocks") and k.endswith(".norm1.weight")])
    heads = 6 if embed_dim == 384 else 3

    class ViT(nn.Module):
        def __init__(self):
            super().__init__()
            self.backbone = VisionTransformer(img_size=img_size, patch_size=16, embed_dim=embed_dim, depth=depth, num_heads=heads, num_classes=0, global_pool='token')
            self.head = nn.Linear(embed_dim, num_classes)
        def forward(self, x): return self.head(self.backbone(x))

    model = ViT()
    new_state = {}
    for k, v in state.items():
        if k.startswith("head."): new_state[k] = v
        elif k.startswith(prefix): new_state[k.replace(prefix, "backbone.", 1)] = v
        else: new_state[k] = v
    model.load_state_dict(new_state, strict=False)
    model.eval()
    return model, img_size

# ── CLASS NAMES ──
CLASS_NAMES = {
    "crop": ["Blast", "Rust", "Healthy"],
    "pest": [
        "rice leaf roller","rice leaf caterpillar","paddy stem maggot","asiatic rice borer","yellow rice borer",
        "rice gall midge","Rice Stemfly","brown plant hopper","white backed plant hopper","small brown plant hopper",
        "rice water weevil","rice leafhopper","grain spreader thrips","rice shell pest","grub","mole cricket","wireworm",
        "white margined moth","black cutworm","large cutworm","yellow cutworm","red spider","corn borer","army worm","aphids",
        "Potosiabre vitarsis","peach borer","english grain aphid","green bug","bird cherry-oataphid","wheat blossom midge",
        "penthaleus major","longlegged spider mite","wheat phloeothrips","wheat sawfly","cerodonta denticornis","beet fly",
        "flea beetle","cabbage army worm","beet army worm","Beet spot flies","meadow moth","beet weevil","sericaorient alismots chulsky",
        "alfalfa weevil","flax budworm","alfalfa plant bug","tarnished plant bug","Locustoidea","lytta polita","legume blister beetle",
        "blister beetle","therioaphis maculata Buckton","odontothrips loti","Thrips","alfalfa seed chalcid","Pieris canidia",
        "Apolygus lucorum","Limacodidae","Viteus vitifoliae","Colomerus vitis","Brevipoalpus lewisi McGregor","oides decempunctata",
        "Polyphagotars onemus latus","Pseudococcus comstocki Kuwana","parathrene regalis","Ampelophaga","Lycorma delicatula","Xylotrechus",
        "Cicadella viridis","Miridae","Trialeurodes vaporariorum","Erythroneura apicalis","Papilio xuthus","Panonchus citri McGregor",
        "Phyllocoptes oleiverus ashmead","Icerya purchasi Maskell","Unaspis yanonensis","Ceroplastes rubens","Chrysomphalus aonidum",
        "Parlatoria zizyphus Lucus","Nipaecoccus vastalor","Aleurocanthus spiniferus","Tetradacus c Bactrocera minax ","Dacus dorsalis(Hendel)",
        "Bactrocera tsuneonis","Prodenia litura","Adristyrannus","Phyllocnistis citrella Stainton","Toxoptera citricidus","Toxoptera aurantii",
        "Aphis citricola Vander Goot","Scirtothrips dorsalis Hood","Dasineura sp","Lawana imitata Melichar","Salurnis marginella Guerr",
        "Deporaus marginatus Pascoe","Chlumetia transversa","Mango flat beak leafhopper","Rhytidodera bowrinii white","Sternochetus frigidus",
        "Cicadellidae"
    ],
    "soil": ["Alluvial","Sandy","Clay","Loamy","Laterite","Black","Red","Peat","Cinder","Sandy Loam","Yellow"],
    "livestock": ["Coccidiosis","Healthy","Newcastle Disease","Salmonella"],
}

MODEL_CLASSES = {"crop": 3, "pest": 102, "soil": 11, "livestock": 4}

# ── LOAD MODELS ──
@st.cache_resource
def load_all_models():
    models = {}
    sizes = {}
    for m in ["crop","pest","soil","livestock"]:
        cp = ensure_model(m)
        if os.path.exists(cp):
            models[m], sizes[m] = rebuild_vit(cp, MODEL_CLASSES[m])
    return models, sizes

def predict(model, img, img_size):
    t = Compose([Resize((img_size, img_size)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
    with torch.no_grad():
        probs = F.softmax(model(t(img).unsqueeze(0)), dim=1)[0].detach().cpu().numpy()
    return probs

# ── UI ──
st.title("🔍 GaiaLens™ — Multi‑AI Farm Scanner")
st.markdown("All 4 GAIA models analyze your farm photo simultaneously — crops, pests, soil, livestock.")

scan_crop = st.sidebar.checkbox("🌿 Crop Disease", value=True)
scan_pest = st.sidebar.checkbox("🐛 Pest Detection", value=True)
scan_soil = st.sidebar.checkbox("🏞️ Soil Analysis", value=True)
scan_livestock = st.sidebar.checkbox("🐄 Livestock Health", value=True)

uploaded_file = st.file_uploader("📤 Upload a farm photo", type=["jpg","jpeg","png"])

if uploaded_file:
    models, sizes = load_all_models()
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="📸 Your Farm Photo", use_container_width=True)
    st.markdown("---")
    st.markdown("## 🔬 GAIA Multi‑Model Analysis")

    active = []
    if scan_crop: active.append(("crop","🌿 Crop Disease"))
    if scan_pest: active.append(("pest","🐛 Pest Detection"))
    if scan_soil: active.append(("soil","🏞️ Soil Analysis"))
    if scan_livestock: active.append(("livestock","🐄 Livestock Health"))

    if not active:
        st.warning("Select at least one model.")
        st.stop()

    cols = st.columns(len(active))
    for i, (key, label) in enumerate(active):
        with cols[i]:
            st.markdown(f"### {label}")
            if key in models:
                with st.spinner("Analyzing..."):
                    probs = predict(models[key], image, sizes[key])
                top_idx = np.argmax(probs)
                top_label = CLASS_NAMES[key][top_idx]
                top_conf = probs[top_idx] * 100
                is_healthy = "healthy" in top_label.lower()
                emoji = "✅" if is_healthy else "⚠️"
                st.markdown(f"### {emoji} {top_label}")
                st.markdown(f"**{top_conf:.1f}% confidence**")
                st.progress(float(top_conf) / 100)
                top3 = np.argsort(probs)[-3:][::-1]
                if len(top3) > 1:
                    st.markdown("**Also possible:**")
                    for idx in top3[1:]:
                        st.write(f"• {CLASS_NAMES[key][idx]} ({probs[idx]*100:.1f}%)")

st.markdown("---")
cols = st.columns(6)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/13_Help.py", label="💬 Help")
