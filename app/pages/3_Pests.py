
import streamlit as st
from PIL import Image
import torch, torch.nn.functional as F, numpy as np, os, sys, datetime, hashlib
from collections import Counter
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Pest Detection", page_icon="🐛", layout="wide")
st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>", unsafe_allow_html=True)
dark = st.toggle("", value=False, key="pest_theme")
theme = "dark" if dark else "light"

PEST_CLASSES = [
    'rice leaf roller','rice leaf caterpillar','paddy stem maggot','asiatic rice borer','yellow rice borer',
    'rice gall midge','Rice Stemfly','brown plant hopper','white backed plant hopper','small brown plant hopper',
    'rice water weevil','rice leafhopper','grain spreader thrips','rice shell pest','grub','mole cricket','wireworm',
    'white margined moth','black cutworm','large cutworm','yellow cutworm','red spider','corn borer','army worm','aphids',
    'Potosiabre vitarsis','peach borer','english grain aphid','green bug','bird cherry-oataphid','wheat blossom midge',
    'penthaleus major','longlegged spider mite','wheat phloeothrips','wheat sawfly','cerodonta denticornis','beet fly',
    'flea beetle','cabbage army worm','beet army worm','Beet spot flies','meadow moth','beet weevil','sericaorient alismots chulsky',
    'alfalfa weevil','flax budworm','alfalfa plant bug','tarnished plant bug','Locustoidea','lytta polita','legume blister beetle',
    'blister beetle','therioaphis maculata Buckton','odontothrips loti','Thrips','alfalfa seed chalcid','Pieris canidia',
    'Apolygus lucorum','Limacodidae','Viteus vitifoliae','Colomerus vitis','Brevipoalpus lewisi McGregor','oides decempunctata',
    'Polyphagotars onemus latus','Pseudococcus comstocki Kuwana','parathrene regalis','Ampelophaga','Lycorma delicatula','Xylotrechus',
    'Cicadella viridis','Miridae','Trialeurodes vaporariorum','Erythroneura apicalis','Papilio xuthus','Panonchus citri McGregor',
    'Phyllocoptes oleiverus ashmead','Icerya purchasi Maskell','Unaspis yanonensis','Ceroplastes rubens','Chrysomphalus aonidum',
    'Parlatoria zizyphus Lucus','Nipaecoccus vastalor','Aleurocanthus spiniferus','Tetradacus c Bactrocera minax ','Dacus dorsalis(Hendel)',
    'Bactrocera tsuneonis','Prodenia litura','Adristyrannus','Phyllocnistis citrella Stainton','Toxoptera citricidus','Toxoptera aurantii',
    'Aphis citricola Vander Goot','Scirtothrips dorsalis Hood','Dasineura sp','Lawana imitata Melichar','Salurnis marginella Guerr',
    'Deporaus marginatus Pascoe','Chlumetia transversa','Mango flat beak leafhopper','Rhytidodera bowrinii white','Sternochetus frigidus',
    'Cicadellidae'
]
N = len(PEST_CLASSES)

language_options = {
    "English (UK)": "en-GB",
    "Hausa": "ha",
    "Yoruba": "yo",
    "Igbo": "ig",
    "Pidgin": "pcm"
}
selected_lang_label = st.selectbox("🔊 Voice language for pest guide", list(language_options.keys()), index=0)
voice_lang = language_options[selected_lang_label]

def save_feedback(image_name, predicted_class, helpful):
    if "user" not in st.session_state or st.session_state.user is None: return
    from supabase import create_client
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    try: supabase.table("user_feedback").insert({"user_id": st.session_state.user.id, "image_name": image_name, "predicted_class": predicted_class, "helpful": helpful, "created_at": datetime.datetime.now().isoformat()}).execute()
    except: pass

def deduct_one_scan():
    if "user" not in st.session_state or st.session_state.user is None: return
    from supabase import create_client
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    uid = st.session_state.user.id
    try: supabase.table("user_scans").insert({"user_id":uid,"scans_remaining":30,"plan":"free"}).execute()
    except: pass
    try: supabase.table("user_scans").update({"scans_remaining": supabase.raw("scans_remaining - 1")}).eq("user_id", uid).execute()
    except: supabase.rpc("decrement_scan", {"uid": uid}).execute()
    res = supabase.table("user_scans").select("scans_remaining").eq("user_id", uid).execute()
    if res.data: st.success(f"Scan deducted. Remaining scans: {res.data[0]['scans_remaining']}")

@st.cache_data(show_spinner=False)
def get_voice_guide(explanation, lang):
    from app.utils.deepseek_explainer import text_to_speech
    audio_bytes, err = text_to_speech(explanation[:2000], lang)
    return audio_bytes, err

if theme == "dark":
    st.markdown("""<style>.stApp{background:linear-gradient(135deg,#1a0f00,#2e1c00,#3e2a00,#1a0f00);color:#fff8e1}header,footer{visibility:hidden}.title{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#ff9800,#ffcc80,#ff9800);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 25px rgba(255,152,0,.7);animation:pestGlow 2s ease-in-out infinite alternate}@keyframes pestGlow{from{text-shadow:0 0 25px rgba(255,152,0,.7)}to{text-shadow:0 0 50px rgba(255,152,0,1),0 0 80px rgba(255,152,0,.6)}}.subtitle{text-align:center;font-size:1.2rem;color:#bcaaa4}.result-card{background:rgba(255,255,255,.05);backdrop-filter:blur(20px);border-radius:20px;padding:1.5rem;margin:.5rem 0}.result-card.top-result{border:1px solid #ff9800;box-shadow:0 0 30px rgba(255,152,0,.3)}.stProgress>div>div>div>div{background:linear-gradient(90deg,#ff9800,#ffcc80)}</style>""", unsafe_allow_html=True)
else:
    st.markdown("""<style>.stApp{background:linear-gradient(135deg,#fff3e0,#ffe0b2);color:#3e2723}header,footer{visibility:hidden}.title{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#e65100,#ff9800,#e65100);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 10px rgba(230,81,0,.3);animation:pestGlowLight 2s ease-in-out infinite alternate}@keyframes pestGlowLight{from{text-shadow:0 0 10px rgba(230,81,0,.3)}to{text-shadow:0 0 25px rgba(230,81,0,.8),0 0 50px rgba(230,81,0,.5)}}.subtitle{text-align:center;font-size:1.2rem;color:#4e342e}.result-card{background:rgba(255,255,255,.8);backdrop-filter:blur(10px);border-radius:20px;padding:1.5rem;margin:.5rem 0}.result-card.top-result{border:1px solid #e65100;box-shadow:0 0 20px rgba(230,81,0,.2)}.stProgress>div>div>div>div{background:linear-gradient(90deg,#ff9800,#ffcc80)}</style>""", unsafe_allow_html=True)

st.markdown('<div class="title">🐛 Pest Detection & Management</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Snap a photo — get identification and an AI‑generated pest management guide</div>', unsafe_allow_html=True)

with st.expander("📸 How to take a good insect photo"):
    st.markdown("1. 🔍 Get as close as possible while keeping the insect in focus.\n2. 📱 Hold phone steady.\n3. ☀️ Good lighting is essential.\n4. 📤 Upload 2‑3 photos for better results.")

files = st.file_uploader("📤 Upload insect photos", type=["jpg","jpeg","png"], accept_multiple_files=True)

if files:
    model = None
    try:
        from app.utils.model_loader import create_model_from_checkpoint
        from app.utils.download_models import ensure_model
        cp_path = os.path.join("checkpoints", "pests_102class", "model.pt")
        if os.path.exists(cp_path):
            os.remove(cp_path)
        cp = ensure_model("pests_102class")
        if cp and os.path.exists(cp):
            try:
                model = create_model_from_checkpoint(cp, N)
            except:
                if os.path.exists(cp_path):
                    os.remove(cp_path)
                raise
    except Exception as e:
        st.warning(f"Real model unavailable, using demo. ({e})")

    predictions = []
    for f in files:
        img = Image.open(f).convert("RGB")
        with st.expander(f"🐛 {f.name}", expanded=True):
            c1, c2 = st.columns([1,2])
            c1.image(img, caption=f.name, width=200)
            if model:
                t = Compose([Resize((224,224)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
                with torch.no_grad():
                    probs = F.softmax(model(t(img).unsqueeze(0)), dim=1)[0].detach().cpu().numpy()
            else:
                seed = int(hashlib.md5(f.name.encode()).hexdigest()[:8],16)
                np.random.seed(seed)
                probs = np.random.rand(N)
                probs /= probs.sum()
            top_idx = np.argmax(probs)
            pest_name = PEST_CLASSES[top_idx]
            confidence = probs[top_idx] * 100
            predictions.append(pest_name)

            c2.markdown(f'<div class="result-card top-result" style="border-left:5px solid #ff9800;"><h2 style="margin:0">{pest_name.title()} <span style="font-size:1.5rem;color:#ff9800">{confidence:.1f}%</span></h2></div>', unsafe_allow_html=True)
            for i in np.argsort(probs)[::-1][1:5]:
                c2.write(f"**{PEST_CLASSES[i].title()}**: {probs[i]*100:.1f}%")
                c2.progress(float(probs[i]))
            deduct_one_scan()

            # ===== AI PEST GUIDE (streaming) + VOICE =====
            if model is not None:
                with st.spinner("🧠 GAIA is preparing your pest management guide..."):
                    with st.expander("📋 Complete Pest Management Guide (AI-Generated)", expanded=True):
                        from app.utils.deepseek_explainer import explain_diagnosis_stream
                        full_guide = []
                        def generator():
                            for chunk in explain_diagnosis_stream(pest_name, confidence, "various crops", "pest"):
                                full_guide.append(chunk)
                                yield chunk
                        st.write_stream(generator)
                        guide_text = ''.join(full_guide)
                        if guide_text:
                            audio_bytes, tts_err = get_voice_guide(guide_text, voice_lang)
                            if audio_bytes:
                                st.audio(audio_bytes, format="audio/mp3")
                            else:
                                st.caption(f"🔇 Voice unavailable: {tts_err}")
            col_fb1, col_fb2 = c2.columns(2)
            if col_fb1.button("👍 Helpful", key=f"pest_help_{f.name}"):
                save_feedback(f.name, pest_name, True)
                col_fb1.success("Thanks!")
            if col_fb2.button("👎 Not", key=f"pest_not_{f.name}"):
                save_feedback(f.name, pest_name, False)
                col_fb2.info("We'll improve.")

    if len(predictions) >= 2:
        vote = Counter(predictions).most_common(1)[0]
        if vote[1] > len(predictions)//2:
            st.success(f"🗳️ Majority vote: **{vote[0].title()}** ({vote[1]}/{len(predictions)} photos)")
        else:
            st.info("🗳️ No clear consensus. Consider retaking.")

# ---------- Quick Navigation ----------
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(9)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[6]: st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[7]: st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
