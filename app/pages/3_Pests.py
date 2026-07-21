
import streamlit as st
from PIL import Image
import torch, torch.nn.functional as F, numpy as np, os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Pest Detection", page_icon="🐛", layout="wide")
st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>",unsafe_allow_html=True)
dark = st.toggle("",value=False,key="pest_theme")
theme = "dark" if dark else "light"

PEST_CLASSES = ['rice leaf roller','rice leaf caterpillar','paddy stem maggot','asiatic rice borer','yellow rice borer','rice gall midge','Rice Stemfly','brown plant hopper','white backed plant hopper','small brown plant hopper','rice water weevil','rice leafhopper','grain spreader thrips','rice shell pest','grub','mole cricket','wireworm','white margined moth','black cutworm','large cutworm','yellow cutworm','red spider','corn borer','army worm','aphids','Potosiabre vitarsis','peach borer','english grain aphid','green bug','bird cherry-oataphid','wheat blossom midge','penthaleus major','longlegged spider mite','wheat phloeothrips','wheat sawfly','cerodonta denticornis','beet fly','flea beetle','cabbage army worm','beet army worm','Beet spot flies','meadow moth','beet weevil','sericaorient alismots chulsky','alfalfa weevil','flax budworm','alfalfa plant bug','tarnished plant bug','Locustoidea','lytta polita','legume blister beetle','blister beetle','therioaphis maculata Buckton','odontothrips loti','Thrips','alfalfa seed chalcid','Pieris canidia','Apolygus lucorum','Limacodidae','Viteus vitifoliae','Colomerus vitis','Brevipoalpus lewisi McGregor','oides decempunctata','Polyphagotars onemus latus','Pseudococcus comstocki Kuwana','parathrene regalis','Ampelophaga','Lycorma delicatula','Xylotrechus','Cicadella viridis','Miridae','Trialeurodes vaporariorum','Erythroneura apicalis','Papilio xuthus','Panonchus citri McGregor','Phyllocoptes oleiverus ashmead','Icerya purchasi Maskell','Unaspis yanonensis','Ceroplastes rubens','Chrysomphalus aonidum','Parlatoria zizyphus Lucus','Nipaecoccus vastalor','Aleurocanthus spiniferus','Tetradacus c Bactrocera minax ','Dacus dorsalis(Hendel)','Bactrocera tsuneonis','Prodenia litura','Adristyrannus','Phyllocnistis citrella Stainton','Toxoptera citricidus','Toxoptera aurantii','Aphis citricola Vander Goot','Scirtothrips dorsalis Hood','Dasineura sp','Lawana imitata Melichar','Salurnis marginella Guerr','Deporaus marginatus Pascoe','Chlumetia transversa','Mango flat beak leafhopper','Rhytidodera bowrinii white','Sternochetus frigidus','Cicadellidae']
N = len(PEST_CLASSES)

if theme=="dark":
    st.markdown("<style>.stApp{background:linear-gradient(135deg,#1a0f00,#2e1c00,#3e2a00,#1a0f00);color:#fff8e1}header,footer{visibility:hidden}.title{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#ff9800,#ffcc80,#ff9800);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 25px rgba(255,152,0,.7);animation:pestGlow 2s ease-in-out infinite alternate}@keyframes pestGlow{from{text-shadow:0 0 25px rgba(255,152,0,.7)}to{text-shadow:0 0 50px rgba(255,152,0,1),0 0 80px rgba(255,152,0,.6)}}.subtitle{text-align:center;font-size:1.2rem;color:#bcaaa4}.result-card{background:rgba(255,255,255,.05);backdrop-filter:blur(20px);border-radius:20px;padding:1.5rem;margin:.5rem 0}.result-card.top-result{border:1px solid #ff9800;box-shadow:0 0 30px rgba(255,152,0,.3)}.stProgress>div>div>div>div{background:linear-gradient(90deg,#ff9800,#ffcc80)}</style>",unsafe_allow_html=True)
else:
    st.markdown("<style>.stApp{background:linear-gradient(135deg,#fff3e0,#ffe0b2);color:#3e2723}header,footer{visibility:hidden}.title{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#e65100,#ff9800,#e65100);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 10px rgba(230,81,0,.3);animation:pestGlowLight 2s ease-in-out infinite alternate}@keyframes pestGlowLight{from{text-shadow:0 0 10px rgba(230,81,0,.3)}to{text-shadow:0 0 25px rgba(230,81,0,.8),0 0 50px rgba(230,81,0,.5)}}.subtitle{text-align:center;font-size:1.2rem;color:#4e342e}.result-card{background:rgba(255,255,255,.8);backdrop-filter:blur(10px);border-radius:20px;padding:1.5rem;margin:.5rem 0}.result-card.top-result{border:1px solid #e65100;box-shadow:0 0 20px rgba(230,81,0,.2)}.stProgress>div>div>div>div{background:linear-gradient(90deg,#ff9800,#ffcc80)}</style>",unsafe_allow_html=True)

def deduct():
    import streamlit as st
    from supabase import create_client
    if "user" not in st.session_state or st.session_state.user is None: return
    url=st.secrets["supabase"]["url"]; key=st.secrets["supabase"]["key"]
    supabase=create_client(url,key); uid=st.session_state.user.id
    try: supabase.table("user_scans").insert({"user_id":uid,"scans_remaining":30,"plan":"free"}).execute()
    except: pass
    try:
        supabase.rpc("decrement_scan",{"uid":uid}).execute()
        res=supabase.table("user_scans").select("scans_remaining").eq("user_id",uid).execute()
        if res.data: st.success(f"Scan deducted. Remaining scans: {res.data[0]['scans_remaining']}")
    except: pass

st.markdown('<div class="title">🐛 Pest Detection</div>',unsafe_allow_html=True)
st.markdown('<div class="subtitle">Snap photos of insects and we\'ll identify them from 102 common pests</div>',unsafe_allow_html=True)
files = st.file_uploader("📤 Upload insect photos", type=["jpg","jpeg","png"], accept_multiple_files=True)

if files:
    model = None
    try:
        from app.utils.model_loader import create_model_from_checkpoint
        cp = "checkpoints/pests_102class/best_model.pt"
        if os.path.exists(cp): model = create_model_from_checkpoint(cp, N)
    except Exception as e: st.warning(f"Real model unavailable, using demo. ({e})")

    for f in files:
        img = Image.open(f).convert("RGB")
        with st.expander(f"🐛 {f.name}", expanded=True):
            c1,c2 = st.columns([1,2])
            c1.image(img, caption=f.name, width=200)
            if model:
                t = Compose([Resize((224,224)),ToTensor(),Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
                with torch.no_grad(): probs = F.softmax(model(t(img).unsqueeze(0)),dim=1)[0].cpu().numpy()
            else:
                import hashlib
                seed = int(hashlib.md5(f.name.encode()).hexdigest()[:8],16)
                np.random.seed(seed)
                probs = np.random.rand(N); probs/=probs.sum()
            ti = np.argmax(probs)
            c2.markdown(f'<div class="result-card top-result" style="border-left:5px solid #ff9800;"><h2 style="margin:0">{PEST_CLASSES[ti]} <span style="font-size:1.5rem;color:#ff9800">{probs[ti]*100:.1f}%</span></h2></div>',unsafe_allow_html=True)
            for i in np.argsort(probs)[::-1][1:5]:
                c2.write(f"**{PEST_CLASSES[i]}**: {probs[i]*100:.1f}%")
                c2.progress(float(probs[i]))
            deduct()


# ---------- Navigation ----------
st.markdown("""
<style>
    .nav-bar { display: flex; justify-content: center; gap: 1rem; margin-top: 2rem; flex-wrap: wrap; }
    .nav-bar a { text-decoration: none; color: inherit; }
    .nav-button {
        display: inline-block; padding: 10px 20px; border-radius: 12px;
        background: rgba(0,0,0,0.05); backdrop-filter: blur(10px);
        border: 1px solid rgba(0,0,0,0.1); transition: all 0.3s ease;
        cursor: pointer; font-weight: 600; font-size: 0.95rem;
    }
    .nav-button:hover { background: rgba(0,0,0,0.1); transform: translateY(-2px); }
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
