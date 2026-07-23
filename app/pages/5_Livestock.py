
import streamlit as st
from PIL import Image
import torch, torch.nn as nn, torch.nn.functional as F
import numpy as np, os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from timm.models.vision_transformer import VisionTransformer
import timm

st.set_page_config(page_title="GAIA – Livestock Health", page_icon="🐄", layout="wide")
st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>", unsafe_allow_html=True)
dark = st.toggle("", value=False, key="livestock_theme")
theme = "dark" if dark else "light"

ANIMALS = {
    "cattle": ["Foot‑and‑Mouth Disease", "Healthy", "Lumpy Skin Disease"],
    "poultry": ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]
}

# ---------- Safe model loader for livestock ----------
def load_animal_model(animal, num_classes):
    checkpoint = f"checkpoints/{animal}/best_model.pt"
    if not os.path.exists(checkpoint):
        return None, None

    state_dict = torch.load(checkpoint, map_location="cpu", weights_only=False)

    # Determine architecture from state dict
    # If keys start with "backbone.", it's a pretrained ViT
    if any(k.startswith("backbone.") for k in state_dict.keys()):
        # It's a ViT-Small-384 or similar
        embed_dim = state_dict["backbone.cls_token"].shape[-1]
        pos_embed = state_dict["backbone.pos_embed"]
        num_patches = pos_embed.shape[1] - 1
        grid = int(num_patches ** 0.5)
        img_size = grid * 16
        depth = len([k for k in state_dict if k.startswith("backbone.blocks") and k.endswith(".norm1.weight")])
        num_heads = 6 if embed_dim == 384 else 3

        backbone = VisionTransformer(
            img_size=img_size, patch_size=16,
            embed_dim=embed_dim, depth=depth, num_heads=num_heads,
            num_classes=0, global_pool='token'
        )
        # Load backbone weights
        backbone_state = {k.replace("backbone.", ""): v for k, v in state_dict.items() if k.startswith("backbone.")}
        backbone.load_state_dict(backbone_state, strict=False)

        # Build head – check if deep head
        head_keys = [k for k in state_dict if k.startswith("head.")]
        if any(".0.weight" in k for k in head_keys):
            # Deep head: 3 linear layers
            head = nn.Sequential(
                nn.Linear(embed_dim, 2048), nn.GELU(), nn.Dropout(0.3),
                nn.Linear(2048, 1024), nn.GELU(), nn.Dropout(0.2),
                nn.Linear(1024, num_classes)
            )
        else:
            head = nn.Linear(embed_dim, num_classes)

        # Load head weights
        head_state = {k.replace("head.", ""): v for k, v in state_dict.items() if k.startswith("head.")}
        try:
            head.load_state_dict(head_state, strict=False)
        except:
            pass

    else:
        # It's a TinyViT or original GAIAModel
        embed_dim = state_dict["encoder.cls_token"].shape[-1]
        pos_embed = state_dict["encoder.pos_embed"]
        num_patches = pos_embed.shape[1] - 1
        grid = int(num_patches ** 0.5)
        img_size = grid * 16
        depth = len([k for k in state_dict if k.startswith("encoder.blocks") and k.endswith(".norm1.weight")])
        num_heads = 3

        backbone = VisionTransformer(
            img_size=img_size, patch_size=16,
            embed_dim=embed_dim, depth=depth, num_heads=num_heads,
            num_classes=0, global_pool='token'
        )
        backbone_state = {k.replace("encoder.", ""): v for k, v in state_dict.items() if k.startswith("encoder.")}
        backbone.load_state_dict(backbone_state, strict=False)

        head = nn.Linear(embed_dim, num_classes)
        head.load_state_dict({"weight": state_dict["head.weight"], "bias": state_dict.get("head.bias", torch.zeros(num_classes))}, strict=False)

    class AnimalViT(torch.nn.Module):
        def __init__(self, backbone, head):
            super().__init__()
            self.backbone = backbone
            self.head = head
        def forward(self, x):
            return self.head(self.backbone(x))

    model = AnimalViT(backbone, head)
    model.eval()
    return model, img_size

def deduct_one_scan():
    if "user" not in st.session_state or st.session_state.user is None:
        return
    from supabase import create_client
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    uid = st.session_state.user.id
    try:
        supabase.table("user_scans").insert({"user_id":uid,"scans_remaining":30,"plan":"free"}).execute()
    except:
        pass
    try:
        supabase.table("user_scans").update({"scans_remaining": supabase.raw("scans_remaining - 1")}).eq("user_id", uid).execute()
    except:
        supabase.rpc("decrement_scan", {"uid": uid}).execute()
    res = supabase.table("user_scans").select("scans_remaining").eq("user_id", uid).execute()
    if res.data:
        st.success(f"✅ Scan deducted. Remaining scans: {res.data[0]['scans_remaining']}")

# Theme CSS
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #1a0f2e, #2e1c3e, #3e2a5e, #1a0f2e); color: #ede7f6; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center;
                 background: linear-gradient(90deg, #7c4dff, #b388ff, #7c4dff);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 text-shadow: 0 0 25px rgba(124,77,255,.7);
                 animation: livestockGlow 2s ease-in-out infinite alternate; }
        @keyframes livestockGlow { from { text-shadow: 0 0 25px rgba(124,77,255,.7); }
                                   to { text-shadow: 0 0 50px rgba(124,77,255,1), 0 0 80px rgba(124,77,255,.6); } }
        .subtitle { text-align: center; font-size: 1.2rem; color: #b39ddb; }
        .result-card { background: rgba(255,255,255,.05); backdrop-filter: blur(20px); border-radius: 20px; padding: 1.5rem; margin: .5rem 0; }
        .result-card.top-result { border: 1px solid #7c4dff; box-shadow: 0 0 30px rgba(124,77,255,.3); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #7c4dff, #b388ff); }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #ede7f6, #d1c4e9); color: #311b92; }
        header, footer {visibility: hidden;}
        .title { font-size: 3.5rem; font-weight: 900; text-align: center;
                 background: linear-gradient(90deg, #4a148c, #7c4dff, #4a148c);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 text-shadow: 0 0 10px rgba(74,20,140,.3);
                 animation: livestockGlowLight 2s ease-in-out infinite alternate; }
        @keyframes livestockGlowLight { from { text-shadow: 0 0 10px rgba(74,20,140,.3); }
                                        to { text-shadow: 0 0 25px rgba(74,20,140,.8), 0 0 50px rgba(74,20,140,.5); } }
        .subtitle { text-align: center; font-size: 1.2rem; color: #4a148c; }
        .result-card { background: rgba(255,255,255,.8); backdrop-filter: blur(10px); border-radius: 20px; padding: 1.5rem; margin: .5rem 0; }
        .result-card.top-result { border: 1px solid #7c4dff; box-shadow: 0 0 20px rgba(74,20,140,.2); }
        .stProgress > div > div > div > div { background: linear-gradient(90deg, #7c4dff, #b388ff); }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="title">🐄 Livestock Health</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload photos of your animals and detect diseases instantly</div>', unsafe_allow_html=True)

animal = st.selectbox("🐾 Choose animal", list(ANIMALS.keys()))
files = st.file_uploader("📤 Upload animal photos", type=["jpg","jpeg","png"], accept_multiple_files=True)

if files:
    names = ANIMALS[animal]
    n_classes = len(names)

    model, img_size = load_animal_model(animal, n_classes)

    for f in files:
        img = Image.open(f).convert("RGB")
        with st.expander(f"🐄 {f.name}", expanded=True):
            c1, c2 = st.columns([1, 2])
            c1.image(img, caption=f.name, width=200)

            if model and img_size:
                t = Compose([Resize((img_size, img_size)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
                with torch.no_grad():
                    logits = model(t(img).unsqueeze(0))
                    probs = F.softmax(logits, dim=1)[0].detach().cpu().numpy()
            else:
                # Demo fallback
                import hashlib
                seed = int(hashlib.md5(f.name.encode()).hexdigest()[:8], 16)
                np.random.seed(seed)
                probs = np.random.rand(n_classes)
                probs /= probs.sum()
                st.warning("Real model unavailable – using demo predictions.")

            if len(probs) != n_classes:
                st.error("Model output mismatch. Falling back to demo.")
                import hashlib
                seed = int(hashlib.md5(f.name.encode()).hexdigest()[:8], 16)
                np.random.seed(seed)
                probs = np.random.rand(n_classes)
                probs /= probs.sum()

            si = np.argsort(probs)[::-1]
            td = names[si[0]]

            c2.markdown(f'<div class="result-card top-result" style="border-left:5px solid #7c4dff;"><h2 style="margin:0">{td} <span style="font-size:1.5rem;color:#7c4dff">{probs[si[0]]*100:.1f}%</span></h2></div>', unsafe_allow_html=True)

            for i in si[1:4]:
                c2.write(f"**{names[i]}**: {probs[i]*100:.1f}%")
                c2.progress(float(probs[i]))

            if "healthy" in td.lower():
                c2.success(f"✅ This {animal} appears healthy!")
            else:
                c2.warning(f"⚠️ Possible **{td}** detected.")

            deduct_one_scan()

# Bottom navigation
cols = st.columns(5)
for col, (label, path) in zip(cols, [
    ("🏠 Dashboard", "pages/1_Dashboard.py"),
    ("🌾 Crops", "pages/2_Crops.py"),
    ("🐛 Pests", "pages/3_Pests.py"),
    ("🏞️ Soil", "pages/4_Soil.py"),
    ("🐄 Livestock", "pages/5_Livestock.py")
]):
    with col:
        st.page_link(path, label=label)
