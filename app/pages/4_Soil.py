import streamlit as st
from PIL import Image
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np, os, sys
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from timm.models.vision_transformer import VisionTransformer
from collections import Counter

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

st.set_page_config(page_title="GAIA – Soil Analysis", page_icon="🏞️", layout="wide")
st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>", unsafe_allow_html=True)
dark = st.toggle("", value=False, key="soil_theme")
theme = "dark" if dark else "light"

# ===== SOIL NAMES & COLORS =====
SOIL_NAMES = ["Alluvial","Sandy","Clay","Loamy","Laterite","Black","Red","Peat","Cinder","Sandy Loam","Yellow"]
SOIL_COLORS = {"Alluvial":"#8d6e63","Sandy":"#d4a373","Clay":"#a1887f","Loamy":"#6d4c41","Laterite":"#b7410e","Black":"#3e2723","Red":"#c62828","Peat":"#4e342e","Cinder":"#616161","Sandy Loam":"#bcaaa4","Yellow":"#f9a825"}

# ===== SOIL INTELLIGENCE DATABASE =====
SOIL_INTEL = {
    "Alluvial": {"pH":"6.0–7.5","acidity":"Neutral","summary":"River‑deposited fertile soil. Holds moisture well.","crops":[{"name":"Rice","variety":"FARO 44","yield":"4–6 t/ha","germination":"5–7 days","maturity":"90–120 days","spacing":"20cm×20cm","bed":"Flat or puddled"},{"name":"Wheat","variety":"Norman Borlaug","yield":"3–4 t/ha","germination":"4–7 days","maturity":"100–120 days","spacing":"15cm×5cm","bed":"Flat beds"}],"organic_fertilizer":{"type":"Compost/Farmyard manure","rate":"10–15 t/ha","when":"2 weeks before planting","how":"Broadcast and incorporate"},"inorganic_fertilizer":{"NPK":"15:15:15","rate":"400 kg/ha","when":"At planting + top‑dress urea at 6 weeks","how":"Side‑dress 5cm from plant"},"irrigation":"Every 5–7 days. Water early morning.","pest_watch":"Stem borers (maize), leaf blast (rice), aphids."},
    "Sandy": {"pH":"5.0–6.5","acidity":"Slightly acidic","summary":"Loose, well‑drained. Low nutrients, dries fast.","crops":[{"name":"Carrots","variety":"Nantes","yield":"20–30 t/ha","germination":"10–14 days","maturity":"70–90 days","spacing":"30cm×5cm","bed":"Raised beds"},{"name":"Groundnuts","variety":"SAMNUT 23","yield":"2–3 t/ha","germination":"7–10 days","maturity":"90–120 days","spacing":"45cm×15cm","bed":"Ridges"}],"organic_fertilizer":{"type":"Compost/Poultry manure","rate":"15–20 t/ha","when":"3 weeks before planting","how":"Broadcast, mix top 15cm"},"inorganic_fertilizer":{"NPK":"10:10:10","rate":"300 kg/ha","when":"Split: half at planting, half at 4 weeks","how":"Side‑dress"},"irrigation":"Every 2–3 days. Drip irrigation recommended.","pest_watch":"Nematodes, rosette virus, mealybugs."},
    "Clay": {"pH":"6.0–7.0","acidity":"Neutral","summary":"Dense, sticky. Holds water/nutrients but can waterlog.","crops":[{"name":"Rice","variety":"FARO 44","yield":"5–7 t/ha","germination":"5–7 days","maturity":"100–130 days","spacing":"20cm×20cm","bed":"Puddled/flooded"},{"name":"Cabbage","variety":"Copenhagen Market","yield":"30–40 t/ha","germination":"5–10 days","maturity":"70–90 days","spacing":"60cm×45cm","bed":"Raised beds"}],"organic_fertilizer":{"type":"Compost/Gypsum","rate":"10–12 t/ha","when":"4 weeks before planting","how":"Incorporate deeply"},"inorganic_fertilizer":{"NPK":"20:10:10","rate":"400 kg/ha","when":"At planting + top‑dress at 8 weeks","how":"Band 10cm from plant"},"irrigation":"Every 7–10 days. Avoid over‑watering.","pest_watch":"Tuber rot, black sigatoka, diamondback moth."},
    "Loamy": {"pH":"6.0–7.5","acidity":"Neutral","summary":"Gold standard. Perfect sand/silt/clay balance.","crops":[{"name":"Tomato","variety":"Roma VF","yield":"30–50 t/ha","germination":"6–10 days","maturity":"70–85 days","spacing":"60cm×45cm","bed":"Raised beds"},{"name":"Maize","variety":"SAMMAZ 15","yield":"6–9 t/ha","germination":"5–8 days","maturity":"90–110 days","spacing":"75cm×25cm","bed":"Ridges"}],"organic_fertilizer":{"type":"Compost/Green manure","rate":"8–10 t/ha","when":"2 weeks before planting","how":"Broadcast, lightly incorporate"},"inorganic_fertilizer":{"NPK":"12:12:17","rate":"350 kg/ha","when":"Split: planting + flowering","how":"Ring application"},"irrigation":"Every 4–5 days.","pest_watch":"Whitefly, pod borer, fruit fly."},
    "Laterite": {"pH":"5.0–6.5","acidity":"Acidic","summary":"Iron‑rich, weathered. Needs lime. Good for trees.","crops":[{"name":"Cashew","variety":"Brazilian Jumbo","yield":"1–2 t/ha","germination":"14–21 days","maturity":"3–5 years","spacing":"8m×8m","bed":"Deep holes"},{"name":"Cassava","variety":"TME 419","yield":"20–30 t/ha","germination":"14–21 days","maturity":"10–12 months","spacing":"1m×1m","bed":"Mounds"}],"organic_fertilizer":{"type":"Compost/Poultry manure","rate":"12–15 t/ha","when":"Before planting + annually","how":"Incorporate in holes"},"inorganic_fertilizer":{"NPK":"15:15:15 + lime","rate":"300 kg/ha","when":"At planting + after first rain","how":"Broadcast under canopy"},"irrigation":"Minimal. Water young seedlings twice weekly.","pest_watch":"Root rot, tea mosquito bug, coffee berry borer."},
    "Black": {"pH":"7.0–8.5","acidity":"Alkaline","summary":"Dark, nutrient‑rich. Cracks when dry. Good for cotton.","crops":[{"name":"Cotton","variety":"SAMCOT 8","yield":"2–3 t/ha","germination":"5–10 days","maturity":"150–180 days","spacing":"90cm×30cm","bed":"Ridges"},{"name":"Soybean","variety":"TGX 1448-2E","yield":"2–3 t/ha","germination":"5–8 days","maturity":"90–110 days","spacing":"60cm×5cm","bed":"Flat/ridges"}],"organic_fertilizer":{"type":"Vermicompost/Green manure","rate":"8–10 t/ha","when":"3 weeks before planting","how":"Broadcast, disc in"},"inorganic_fertilizer":{"NPK":"DAP + potash","rate":"250 kg/ha DAP + 100 kg/ha MOP","when":"At planting","how":"Band at seeding"},"irrigation":"Every 10–14 days.","pest_watch":"Bollworm, rust, midge."},
    "Red": {"pH":"5.5–7.0","acidity":"Slightly acidic","summary":"Iron‑oxide rich, well‑drained. Good for legumes.","crops":[{"name":"Groundnut","variety":"SAMNUT 23","yield":"2–3.5 t/ha","germination":"7–10 days","maturity":"90–120 days","spacing":"45cm×15cm","bed":"Ridges"},{"name":"Millet","variety":"SOSAT C88","yield":"2–3 t/ha","germination":"4–6 days","maturity":"75–90 days","spacing":"60cm×15cm","bed":"Flat/ridges"}],"organic_fertilizer":{"type":"Farmyard manure/Compost","rate":"8–10 t/ha","when":"2 weeks before planting","how":"Broadcast, plough in"},"inorganic_fertilizer":{"NPK":"SSP + NPK 15:15:15","rate":"200 kg/ha SSP + 200 kg/ha NPK","when":"At planting","how":"Band"},"irrigation":"Every 5–6 days.","pest_watch":"Rosette virus, stem borer, aphids."},
    "Peat": {"pH":"3.5–5.0","acidity":"Very acidic","summary":"Organic‑rich swamp soil. Needs lime.","crops":[{"name":"Pineapple","variety":"Smooth Cayenne","yield":"60–80 t/ha","germination":"14–28 days","maturity":"18–24 months","spacing":"60cm×30cm","bed":"Raised beds"},{"name":"Oil Palm","variety":"Tenera","yield":"15–25 t/ha","germination":"30–60 days","maturity":"3–4 years","spacing":"9m×9m","bed":"Deep holes"}],"organic_fertilizer":{"type":"Compost/Wood ash","rate":"10–12 t/ha + 2 t/ha ash","when":"4 weeks before planting","how":"Incorporate deeply"},"inorganic_fertilizer":{"NPK":"Lime + NPK 15:15:15","rate":"2 t/ha lime + 300 kg/ha NPK","when":"Lime at prep, NPK at planting","how":"Broadcast lime, band NPK"},"irrigation":"Only when top 5cm is dry.","pest_watch":"Root rot, termites, nematodes."},
    "Cinder": {"pH":"5.5–6.5","acidity":"Slightly acidic","summary":"Volcanic fragments. Excellent drainage. Jos Plateau.","crops":[{"name":"Irish Potato","variety":"Nicola","yield":"20–30 t/ha","germination":"10–14 days","maturity":"90–120 days","spacing":"75cm×30cm","bed":"Ridges"},{"name":"Strawberry","variety":"Chandler","yield":"15–25 t/ha","germination":"7–14 days","maturity":"60–90 days","spacing":"30cm×30cm","bed":"Raised, mulched"}],"organic_fertilizer":{"type":"Compost/Peat moss","rate":"12–15 t/ha","when":"3 weeks before planting","how":"Incorporate thoroughly"},"inorganic_fertilizer":{"NPK":"10:10:10 slow‑release","rate":"350 kg/ha","when":"At planting","how":"Band"},"irrigation":"Every 2–3 days.","pest_watch":"Late blight, aphids, slugs."},
    "Sandy Loam": {"pH":"5.5–7.0","acidity":"Slightly acidic","summary":"Workhorse soil. Drains well, retains moisture.","crops":[{"name":"Maize","variety":"SAMMAZ 15","yield":"5–8 t/ha","germination":"5–8 days","maturity":"90–110 days","spacing":"75cm×25cm","bed":"Ridges"},{"name":"Yam","variety":"Dioscorea rotundata","yield":"20–30 t/ha","germination":"21–28 days","maturity":"8–10 months","spacing":"1m×1m","bed":"Mounds"}],"organic_fertilizer":{"type":"Compost/Green manure","rate":"8–10 t/ha","when":"2 weeks before planting","how":"Broadcast, incorporate"},"inorganic_fertilizer":{"NPK":"15:15:15","rate":"350 kg/ha","when":"At planting + top‑dress urea at 6 weeks","how":"Side‑dress along rows"},"irrigation":"Every 4–5 days.","pest_watch":"Stem borers, armyworm, nematodes."},
    "Yellow": {"pH":"5.0–6.5","acidity":"Acidic","summary":"Hydrated iron oxides. Responds to fertilizer.","crops":[{"name":"Maize","variety":"SAMMAZ 15","yield":"4–6 t/ha","germination":"5–8 days","maturity":"90–110 days","spacing":"75cm×25cm","bed":"Ridges"},{"name":"Beans","variety":"IT89KD-288","yield":"1.5–2.5 t/ha","germination":"5–7 days","maturity":"60–75 days","spacing":"60cm×20cm","bed":"Flat"}],"organic_fertilizer":{"type":"Compost/Farmyard manure","rate":"10–12 t/ha","when":"3 weeks before planting","how":"Broadcast, plough in"},"inorganic_fertilizer":{"NPK":"15:15:15 + iron","rate":"350 kg/ha","when":"At planting + iron spray at 4 weeks","how":"Band + foliar"},"irrigation":"Every 4–5 days.","pest_watch":"Termites, leaf blight, aphids."},
}

# ===== LOCATION PRIORS =====
LOCATION_PRIORS = {
    "Abia":{"Laterite":0.40,"Sandy Loam":0.25,"Alluvial":0.15,"Clay":0.10,"Red":0.10},
    "FCT":{"Laterite":0.30,"Clay":0.25,"Sandy Loam":0.20,"Red":0.15,"Cinder":0.10},
    "Kano":{"Sandy":0.35,"Clay":0.25,"Black":0.20,"Alluvial":0.10,"Loamy":0.10},
    "Lagos":{"Sandy":0.40,"Alluvial":0.25,"Clay":0.15,"Peat":0.10,"Sandy Loam":0.10},
    "Plateau":{"Cinder":0.30,"Laterite":0.25,"Clay":0.20,"Black":0.15,"Sandy Loam":0.10},
}
NIGERIAN_STATES = list(LOCATION_PRIORS.keys())

# ===== HELPER FUNCTIONS =====
def detect_moisture(image):
    hsv = np.array(image.convert('HSV'))
    brightness = hsv[:,:,2].mean()
    if brightness < 80: return "wet", brightness
    elif brightness > 150: return "dry", brightness
    else: return "moist", brightness

def adjust_for_moisture(probs, moisture_state):
    if moisture_state == "wet":
        for soil in ["Black","Peat","Clay","Loamy","Alluvial"]:
            if soil in SOIL_NAMES: probs[SOIL_NAMES.index(soil)] *= 1.15
    elif moisture_state == "dry":
        for soil in ["Sandy","Sandy Loam","Cinder","Yellow","Red"]:
            if soil in SOIL_NAMES: probs[SOIL_NAMES.index(soil)] *= 1.15
    return probs / probs.sum()

def apply_location_prior(probs, state):
    if state not in LOCATION_PRIORS: return probs
    for soil_name, prior in LOCATION_PRIORS[state].items():
        if soil_name in SOIL_NAMES:
            probs[SOIL_NAMES.index(soil_name)] *= (0.5 + prior)
    return probs / probs.sum()

@st.cache_resource(ttl=3600)
def load_soil_model():
    from app.utils.download_models import ensure_model
    checkpoint = ensure_model("soil_11class")
    if not checkpoint or not os.path.exists(checkpoint):
        st.warning("Soil model not available. Check your internet connection.")
        return None, None
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)

    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    # Build model from state dict
    prefix = "backbone." if any(k.startswith("backbone.") for k in state) else "encoder."
    embed_dim = state[f"{prefix}cls_token"].shape[-1]
    pos = state[f"{prefix}pos_embed"]; num_patches = pos.shape[1]-1; grid = int(num_patches**0.5); img_size = grid*16
    depth = len([k for k in state if k.startswith(f"{prefix}blocks") and k.endswith(".norm1.weight")])
    backbone = VisionTransformer(img_size=img_size, patch_size=16, embed_dim=embed_dim, depth=depth, num_heads=6, num_classes=0, global_pool='token')
    backbone.load_state_dict({k.replace(prefix,""):v for k,v in state.items() if k.startswith(prefix)}, strict=False)
    head_keys = [k for k in state if k.startswith("head.")]
    w_keys = sorted([k for k in head_keys if k.endswith(".weight")], key=lambda x: int(x.split('.')[1]))
    layers = []; in_feat = embed_dim
    for wk in w_keys:
        w = state[wk]; out_feat = w.shape[0]
        layers.append(nn.Linear(in_feat, out_feat))
        if wk != w_keys[-1]: layers.extend([nn.GELU(), nn.Dropout(0.2)])
        in_feat = out_feat
    head = nn.Sequential(*layers)
    head.load_state_dict({k.replace("head.",""):v for k,v in state.items() if k.startswith("head.")}, strict=False)
    class SoilViT(torch.nn.Module):
        def __init__(self,b,h): super().__init__(); self.backbone=b; self.head=h
        def forward(self,x): return self.head(self.backbone(x))
    model = SoilViT(backbone, head); model.eval()
    return model, img_size

def deduct_one_scan()

# ===== DEEPSEEK EXPLANATION + VOICE =====
if model is not None:
    with st.spinner("🧠 GAIA is preparing your soil management guide..."):
        from app.utils.deepseek_explainer import explain_diagnosis, text_to_speech
        
        top_soil = SOIL_NAMES[top_idx]
        explanation, explain_err = explain_diagnosis(top_soil, probs[top_idx] * 100, "your farm", "soil")
        
        if explanation:
            with st.expander("📋 Complete Soil Management Guide (AI-Generated)", expanded=True):
                st.markdown(explanation)
                
                if st.button("🔊 Listen to Soil Guide", key=f"voice_soil_{uploaded_file.name}"):
                    with st.spinner("🔊 Generating voice..."):
                        audio_bytes, tts_err = text_to_speech(explanation[:2000])
                        if audio_bytes:
                            st.audio(audio_bytes, format="audio/mp3")
                        else:
                            st.warning(f"Voice unavailable: {tts_err}")
:
    if "user" not in st.session_state or st.session_state.user is None: return
    from supabase import create_client
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    uid = st.session_state.user.id
    try: supabase.table("user_scans").insert({"user_id":uid,"scans_remaining":30,"plan":"free"}).execute()
    except: pass
    try: supabase.rpc("decrement_scan",{"uid":uid}).execute()
    except: pass

# ===== CSS =====
if theme == "dark":
    st.markdown("""<style>.stApp{background:linear-gradient(135deg,#1a120b,#2e1c0d,#3e2a14,#1a0f05);color:#f5f0eb}header,footer{visibility:hidden}.title{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#d4a373,#f5e6d3,#d4a373);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 25px rgba(212,163,115,.7);animation:soilGlow 2s ease-in-out infinite alternate}@keyframes soilGlow{from{text-shadow:0 0 25px rgba(212,163,115,.7)}to{text-shadow:0 0 50px rgba(212,163,115,1),0 0 80px rgba(212,163,115,.6)}}.subtitle{font-size:1.2rem;color:#bcaaa4}.card{background:rgba(255,255,255,.05);backdrop-filter:blur(20px);border-radius:20px;padding:1.5rem;margin:.5rem 0}.stProgress>div>div>div>div{background:linear-gradient(90deg,#d4a373,#f5e6d3)}</style>""", unsafe_allow_html=True)
else:
    st.markdown("""<style>.stApp{background:linear-gradient(135deg,#efebe9,#d7ccc8);color:#3e2723}header,footer{visibility:hidden}.title{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#5d4037,#8d6e63,#5d4037);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.subtitle{font-size:1.2rem;color:#4e342e}.card{background:rgba(255,255,255,.8);backdrop-filter:blur(10px);border-radius:20px;padding:1.5rem;margin:.5rem 0}.stProgress>div>div>div>div{background:linear-gradient(90deg,#8d6e63,#bcaaa4)}</style>""", unsafe_allow_html=True)

# ===== UI =====
st.markdown('<div class="title">🏞️ Soil Type Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload 2–3 photos for consensus diagnosis with farming recommendations</div>', unsafe_allow_html=True)

with st.expander("📸 Tips for best results", expanded=False):
    st.markdown("1. 🏞️ Take 2–3 photos from slightly different angles\n2. ☀️ Use natural daylight\n3. 📤 Upload all photos together\n4. 🔄 More photos = better accuracy")

state = st.selectbox("📍 Your State (optional)", ["None"] + NIGERIAN_STATES)
files = st.file_uploader("📤 Upload 2–3 soil photos", type=["jpg","jpeg","png"], accept_multiple_files=True)

if files:
    model, img_size = load_soil_model()
    if model is None:
        st.error("🚫 Soil model could not be loaded.")
        st.info("🔄 Try refreshing the page. The model may need to download first (one‑time, ~87 MB).")
        if st.button("🔄 Retry Download"):
            st.cache_resource.clear()
            st.rerun()
        st.stop()

    all_predictions = []
    all_probs_list = []

    for f in files:
        img = Image.open(f).convert("RGB")
        with st.expander(f"🏞️ {f.name}", expanded=True):
            c1, c2 = st.columns([1,2])
            c1.image(img, caption=f.name, width=200)
            transform = Compose([Resize((img_size,img_size)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
            with torch.no_grad():
                probs = F.softmax(model(transform(img).unsqueeze(0)), dim=1)[0].detach().cpu().numpy()
            moisture, brightness = detect_moisture(img)
            probs = adjust_for_moisture(probs, moisture)
            if state != "None":
                probs = apply_location_prior(probs, state)
            top_idx = np.argmax(probs)
            soil_name = SOIL_NAMES[top_idx]
            all_predictions.append(top_idx)
            all_probs_list.append(probs)
            c2.markdown(f"**This photo says:** {soil_name} ({probs[top_idx]*100:.1f}%)")
            c2.caption(f"Soil appears {moisture}")

    vote_counts = Counter(all_predictions)
    consensus_idx, vote_count = vote_counts.most_common(1)[0]
    consensus_name = SOIL_NAMES[consensus_idx]
    agreement_pct = (vote_count / len(files)) * 100
    avg_probs = np.mean(all_probs_list, axis=0)
    moisture, _ = detect_moisture(Image.open(files[0]).convert("RGB"))
    avg_probs = adjust_for_moisture(avg_probs, moisture)
    if state != "None":
        avg_probs = apply_location_prior(avg_probs, state)
    confidence = avg_probs[consensus_idx] * 100
    color = SOIL_COLORS.get(consensus_name, "#8d6e63")

    st.markdown(f"""<div class="card" style="border-left:5px solid {color};"><h3>🗳️ Consensus: {vote_count}/{len(files)} photos agree ({agreement_pct:.0f}%)</h3><h2 style="color:{color};">{consensus_name} ({confidence:.1f}%)</h2></div>""", unsafe_allow_html=True)

    if confidence < 70 or agreement_pct < 60:
        st.warning(f"⚠️ Low confidence ({confidence:.0f}%). Try more photos in daylight.")
    elif confidence < 85:
        st.info(f"💡 Moderate confidence ({confidence:.0f}%). 1–2 more photos help.")
    else:
        st.success(f"✅ High confidence ({confidence:.0f}%) — {consensus_name} soil.")

    # ===== SOIL INTELLIGENCE PANEL (SAFE — INSIDE 'if files:' BLOCK) =====
    info = SOIL_INTEL.get(consensus_name, {})
    if info:
        with st.expander(f"📋 Complete Farming Guide for {consensus_name} Soil", expanded=False):
            st.markdown(f"### 🟫 {consensus_name} Soil")
            st.markdown(f"**pH:** {info.get('pH','N/A')} | **Acidity:** {info.get('acidity','N/A')}")
            st.markdown(f"**Summary:** {info.get('summary','')}")
            
            crops = info.get('crops', [])
            if crops:
                st.markdown("### 🌾 Best Crops")
                for crop in crops:
                    with st.expander(f"🌱 {crop['name']} — {crop['variety']}"):
                        cols = st.columns(3)
                        cols[0].metric("Yield", crop['yield'])
                        cols[1].metric("Germination", crop['germination'])
                        cols[2].metric("Maturity", crop['maturity'])
                        st.write(f"**Spacing:** {crop['spacing']}")
                        st.write(f"**Bed:** {crop['bed']}")
            
            org = info.get('organic_fertilizer', {})
            inorg = info.get('inorganic_fertilizer', {})
            if org or inorg:
                st.markdown("### 🧪 Fertilizer Guide")
                c1, c2 = st.columns(2)
                if org:
                    c1.markdown("**🌿 Organic**")
                    c1.write(f"Type: {org.get('type','')}")
                    c1.write(f"Rate: {org.get('rate','')}")
                    c1.write(f"When: {org.get('when','')}")
                    c1.write(f"How: {org.get('how','')}")
                if inorg:
                    c2.markdown("**⚗️ Inorganic**")
                    c2.write(f"NPK: {inorg.get('NPK','')}")
                    c2.write(f"Rate: {inorg.get('rate','')}")
                    c2.write(f"When: {inorg.get('when','')}")
                    c2.write(f"How: {inorg.get('how','')}")
            
            st.markdown("### 💧 Water Management")
            st.info(info.get('irrigation', 'Water as needed.'))
            st.markdown("### 🐛 Pest Watch")
            st.warning(info.get('pest_watch', 'Scout regularly.'))

    deduct_one_scan()

    # ===== DEEPSEEK EXPLANATION + VOICE =====
    if model is not None:
        with st.spinner("🧠 GAIA is preparing your soil management guide..."):
            try:
                from app.utils.deepseek_explainer import explain_diagnosis, text_to_speech
                top_soil = SOIL_NAMES[top_idx]
                explanation, explain_err = explain_diagnosis(top_soil, probs[top_idx] * 100, "your farm", "soil")
                if explanation:
                    with st.expander("📋 Complete Soil Management Guide (AI-Generated)", expanded=True):
                        st.markdown(explanation)
                        if st.button("🔊 Listen to Soil Guide", key=f"voice_soil_{uploaded_file.name}"):
                            with st.spinner("🔊 Generating voice..."):
                                audio_bytes, tts_err = text_to_speech(explanation[:2000])
                                if audio_bytes:
                                    st.audio(audio_bytes, format="audio/mp3")
                                else:
                                    st.warning(f"Voice unavailable: {tts_err}")
            except Exception as e:
                st.warning(f"Soil guide unavailable: {str(e)[:100]}")
    deduct_one_scan()
    
    # ===== DEEPSEEK EXPLANATION + VOICE =====
    if model is not None:
        with st.spinner("🧠 GAIA is preparing your soil management guide..."):
            try:
                from app.utils.deepseek_explainer import explain_diagnosis, text_to_speech
                
                top_soil = SOIL_NAMES[top_idx]
                explanation, explain_err = explain_diagnosis(top_soil, probs[top_idx] * 100, "your farm", "soil")
                
                if explanation:
                    with st.expander("📋 Complete Soil Management Guide (AI-Generated)", expanded=True):
                        st.markdown(explanation)
                        
                        if st.button("🔊 Listen to Soil Guide", key=f"voice_soil_{uploaded_file.name}"):
                            with st.spinner("🔊 Generating voice..."):
                                audio_bytes, tts_err = text_to_speech(explanation[:2000])
                                if audio_bytes:
                                    st.audio(audio_bytes, format="audio/mp3")
                                else:
                                    st.warning(f"Voice unavailable: {tts_err}")
            except Exception as e:
                st.warning(f"Soil guide unavailable: {str(e)[:100]})

# ===== DEEPSEEK EXPLANATION + VOICE =====
if model is not None:
    with st.spinner("🧠 GAIA is preparing your soil management guide..."):
        from app.utils.deepseek_explainer import explain_diagnosis, text_to_speech
        
        top_soil = SOIL_NAMES[top_idx]
        explanation, explain_err = explain_diagnosis(top_soil, probs[top_idx] * 100, "your farm", "soil")
        
        if explanation:
            with st.expander("📋 Complete Soil Management Guide (AI-Generated)", expanded=True):
                st.markdown(explanation)
                
                if st.button("🔊 Listen to Soil Guide", key=f"voice_soil_{uploaded_file.name}"):
                    with st.spinner("🔊 Generating voice..."):
                        audio_bytes, tts_err = text_to_speech(explanation[:2000])
                        if audio_bytes:
                            st.audio(audio_bytes, format="audio/mp3")
                        else:
                            st.warning(f"Voice unavailable: {tts_err}")


# ===== QUICK NAVIGATION =====
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(8)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/10_Early_Warning.py", label="🛰️ Early Warning")
with cols[6]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[7]: st.page_link("pages/13_Help.py", label="💬 Help")
# ---------- Quick Navigation ----------
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(8)
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
    st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[6]:
    st.page_link("pages/10_Early_Warning.py", label="🛰️ Early Warning")
with cols[7]:
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")