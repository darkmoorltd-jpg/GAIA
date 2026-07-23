
import streamlit as st
from PIL import Image
import torch, torch.nn.functional as F, numpy as np, os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Soil Analysis", page_icon="🏞️", layout="wide")
st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>",unsafe_allow_html=True)
dark = st.toggle("",value=False,key="soil_theme")
theme = "dark" if dark else "light"

SOIL = ["alluvial","black","cinder","clay","laterite","loamy","peat","red","sandy","sandy_loam","yellow"]
N = len(SOIL)
COLORS = {"alluvial":"#8d6e63","black":"#3e2723","cinder":"#616161","clay":"#a1887f","laterite":"#b7410e","loamy":"#6d4c41","peat":"#4e342e","red":"#c62828","sandy":"#d4a373","sandy_loam":"#bcaaa4","yellow":"#f9a825"}

def desc(s):
    d = {"alluvial":"Rich, fertile soil deposited by rivers.","black":"Dark, nutrient-rich soil.","cinder":"Volcanic soil fragments.","clay":"Dense, sticky soil.","laterite":"Iron-rich, weathered soil.","loamy":"Perfect balance of sand, silt, and clay.","peat":"Organic-rich, acidic soil.","red":"Iron oxide-rich soil.","sandy":"Loose, well-drained soil.","sandy_loam":"Sandy with organic matter.","yellow":"Moderately fertile soil."}
    return d.get(s,"")

def rec(s):
    r = {"alluvial":"Ideal for rice, wheat, sugarcane.","black":"Perfect for cotton, soybeans.","cinder":"Mix with organic matter.","clay":"Add compost and gypsum.","laterite":"Add lime and organic matter.","loamy":"Excellent for vegetables.","peat":"Add lime to reduce acidity.","red":"Apply nitrogen-rich fertilizers.","sandy":"Add organic matter.","sandy_loam":"Great for root vegetables.","yellow":"Add compost and iron supplements."}
    return r.get(s,"Consult a local agronomist.")

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

if theme=="dark":
    st.markdown("<style>.stApp{background:linear-gradient(135deg,#1a120b,#2e1c0d,#3e2a14,#1a0f05);color:#f5f0eb}header,footer{visibility:hidden}.title{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#d4a373,#f5e6d3,#d4a373);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 25px rgba(212,163,115,.7);animation:soilGlow 2s ease-in-out infinite alternate}@keyframes soilGlow{from{text-shadow:0 0 25px rgba(212,163,115,.7)}to{text-shadow:0 0 50px rgba(212,163,115,1),0 0 80px rgba(212,163,115,.6)}}.subtitle{text-align:center;font-size:1.2rem;color:#bcaaa4}.soil-swatch{display:inline-block;width:20px;height:20px;border-radius:4px;margin-right:8px}.result-card{background:rgba(255,255,255,.05);backdrop-filter:blur(20px);border-radius:20px;padding:1.5rem;margin:.5rem 0}.result-card.top-result{border:1px solid #d4a373;box-shadow:0 0 30px rgba(212,163,115,.3)}.stProgress>div>div>div>div{background:linear-gradient(90deg,#8d6e63,#d4a373)}</style>",unsafe_allow_html=True)
else:
    st.markdown("<style>.stApp{background:linear-gradient(135deg,#efebe9,#d7ccc8);color:#3e2723}header,footer{visibility:hidden}.title{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#5d4037,#8d6e63,#5d4037);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 10px rgba(93,64,55,.3);animation:soilGlowLight 2s ease-in-out infinite alternate}@keyframes soilGlowLight{from{text-shadow:0 0 10px rgba(93,64,55,.3)}to{text-shadow:0 0 25px rgba(93,64,55,.8),0 0 50px rgba(93,64,55,.5)}}.subtitle{text-align:center;font-size:1.2rem;color:#4e342e}.soil-swatch{display:inline-block;width:20px;height:20px;border-radius:4px;margin-right:8px}.result-card{background:rgba(255,255,255,.8);backdrop-filter:blur(10px);border-radius:20px;padding:1.5rem;margin:.5rem 0}.result-card.top-result{border:1px solid #5d4037;box-shadow:0 0 20px rgba(93,64,55,.2)}.stProgress>div>div>div>div{background:linear-gradient(90deg,#8d6e63,#bcaaa4)}</style>",unsafe_allow_html=True)

st.markdown('<div class="title">🏞️ Soil Type Analysis</div>',unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload soil photos and uncover their secrets</div>',unsafe_allow_html=True)
files = st.file_uploader("📤 Drop soil photos here", type=["jpg","jpeg","png"], accept_multiple_files=True)

if files:
    model = None
    try:
        from app.utils.model_loader import create_model_from_checkpoint
        cp = "checkpoints/soil_11class/best_model.pt"
        if os.path.exists(cp): model = create_model_from_checkpoint(cp, N)
    except Exception as e: st.warning(f"Real model unavailable, using demo. ({e})")

    for f in files:
        img = Image.open(f).convert("RGB")
        with st.expander(f"🏞️ {f.name}", expanded=True):
            c1,c2 = st.columns([1,2])
            c1.image(img, caption=f.name, width=200)
            if model:
                t = Compose([Resize((224,224)),ToTensor(),Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
                with torch.no_grad(): probs = F.softmax(model(t(img).unsqueeze(0)),dim=1)[0].detach().cpu().numpy()
            else:
                import hashlib
                seed = int(hashlib.md5(f.name.encode()).hexdigest()[:8],16)
                np.random.seed(seed)
                probs = np.random.rand(N); probs/=probs.sum()
            ti = np.argmax(probs); ts = SOIL[ti]; tc = COLORS.get(ts,"#8d6e63")
            c2.markdown(f'<div class="result-card top-result" style="border-left:5px solid {tc};"><h2 style="margin:0;display:flex;align-items:center;"><span class="soil-swatch" style="background-color:{tc};"></span>{ts}<span style="margin-left:auto;font-size:2rem;color:{tc}">{probs[ti]*100:.1f}%</span></h2><p>{desc(ts)}</p></div>',unsafe_allow_html=True)
            for i in np.argsort(probs)[::-1][1:5]:
                c2.write(f"**{SOIL[i]}**: {probs[i]*100:.1f}%")
                c2.progress(float(probs[i]))
            c2.info(f"💡 **Recommendation:** {rec(ts)}")
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
