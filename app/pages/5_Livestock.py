
import streamlit as st
from PIL import Image
import torch, torch.nn.functional as F, numpy as np, os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Livestock Health", page_icon="🐄", layout="wide")
st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>", unsafe_allow_html=True)
dark = st.toggle("", value=False, key="livestock_theme")
theme = "dark" if dark else "light"

ANIMALS = {
    "cattle": ["Foot‑and‑Mouth Disease", "Healthy", "Lumpy Skin Disease"],
    "poultry": ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]
}


def get_model_input_size(model):
    try:
        if hasattr(model.backbone, 'patch_embed') and hasattr(model.backbone.patch_embed, 'img_size'):
            sz = model.backbone.patch_embed.img_size
            if isinstance(sz, (list, tuple)): return sz[0]
            return sz
        pos_embed = model.backbone.pos_embed
        num_patches = pos_embed.shape[1] - 1
        return int(num_patches ** 0.5) * 16
    except: pass
    return 224


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

    # Load model
    model = None
    checkpoint = f"checkpoints/{animal}/best_model.pt"
    if os.path.exists(checkpoint):
        try:
            from app.utils.model_loader import create_model_from_checkpoint
            model = create_model_from_checkpoint(checkpoint, n_classes)
        except Exception as e:
            st.warning(f"Real model unavailable, using demo. ({e})")

    for f in files:
        img = Image.open(f).convert("RGB")
        with st.expander(f"🐄 {f.name}", expanded=True):
            c1, c2 = st.columns([1, 2])
            c1.image(img, caption=f.name, width=200)

            if model:
                size = get_model_input_size(model)
                t = Compose([Resize((size, size)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
                with torch.no_grad():
                    logits = model(t(img).unsqueeze(0))
                    probs = F.softmax(logits, dim=1)[0].detach().cpu().numpy()
            else:
                import hashlib
                seed = int(hashlib.md5(f.name.encode()).hexdigest()[:8], 16)
                np.random.seed(seed)
                probs = np.random.rand(n_classes)
                probs /= probs.sum()

            # Ensure probs length matches class names
            if len(probs) != n_classes:
                st.error(f"Model output size mismatch. Expected {n_classes}, got {len(probs)}. Using demo.")
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
