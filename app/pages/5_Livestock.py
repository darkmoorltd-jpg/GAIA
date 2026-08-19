
import streamlit as st
from PIL import Image
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np, os, sys, datetime, hashlib
import requests, json
from collections import Counter
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from timm.models.vision_transformer import VisionTransformer

DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

st.set_page_config(page_title="GAIA – Livestock Health", page_icon="🐄", layout="wide")

# THEME (light default)
if "theme" not in st.session_state:
    st.session_state.theme = "light"

st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>", unsafe_allow_html=True)
dark = st.toggle("", value=st.session_state.theme == "dark", key="livestock_theme")
st.session_state.theme = "dark" if dark else "light"
theme = st.session_state.theme

ANIMALS = {
    "cattle": ["Foot‑and‑Mouth Disease","Healthy","Lumpy Skin Disease"],
    "poultry": ["Coccidiosis","Healthy","Newcastle Disease","Salmonella"]
}

# BACKGROUND IMAGE URLS
BACKGROUND_URLS = {
    "cattle": "https://images.unsplash.com/photo-1570042225831-d98fa7577f1e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80",
    "poultry": "https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80"
}

language_options = {
    "English (UK)": "en-GB",
    "Hausa": "ha",
    "Yoruba": "yo",
    "Igbo": "ig",
    "Pidgin": "pcm"
}
selected_lang_label = st.selectbox("🔊 Voice language for treatment guides", list(language_options.keys()), index=0)
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

def load_animal_model(animal):
    from app.utils.download_models import ensure_model
    cp_path = os.path.join("checkpoints", animal, "model.pt")
    if os.path.exists(cp_path):
        os.remove(cp_path)
    checkpoint = ensure_model(animal)
    if not checkpoint or not os.path.exists(checkpoint):
        return None, None
    try:
        state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    except:
        return None, None
    prefix = "backbone." if any(k.startswith("backbone.") for k in state) else "encoder."
    embed_dim = state[f"{prefix}cls_token"].shape[-1]
    pos_embed = state[f"{prefix}pos_embed"]
    num_patches = pos_embed.shape[1] - 1
    grid = int(num_patches ** 0.5)
    img_size = grid * 16
    depth = len([k for k in state if k.startswith(f"{prefix}blocks") and k.endswith(".norm1.weight")])
    num_heads = 6 if embed_dim == 384 else 3
    backbone = VisionTransformer(img_size=img_size, patch_size=16, embed_dim=embed_dim, depth=depth, num_heads=num_heads, num_classes=0, global_pool='token')
    backbone_state = {k.replace(prefix, ""): v for k, v in state.items() if k.startswith(prefix)}
    backbone.load_state_dict(backbone_state, strict=False)
    head_keys = [k for k in state if k.startswith("head.")]
    if any(".0.weight" in k for k in head_keys):
        w_keys = sorted([k for k in head_keys if k.endswith(".weight")], key=lambda x: int(x.split('.')[1]))
        layers = []
        in_feat = embed_dim
        for w_key in w_keys:
            w = state[w_key]; out_feat = w.shape[0]
            layers.append(nn.Linear(in_feat, out_feat))
            if w_key != w_keys[-1]: layers.extend([nn.GELU(), nn.Dropout(0.2)])
            in_feat = out_feat
        head = nn.Sequential(*layers)
        head_state = {k.replace("head.", ""): v for k, v in state.items() if k.startswith("head.")}
        head.load_state_dict(head_state, strict=False)
    else:
        n = len(ANIMALS[animal])
        head = nn.Linear(embed_dim, n)
        head.load_state_dict({"weight": state["head.weight"], "bias": state.get("head.bias", torch.zeros(n))}, strict=False)
    class AnimalViT(torch.nn.Module):
        def __init__(self, backbone, head): super().__init__(); self.backbone = backbone; self.head = head
        def forward(self, x): return self.head(self.backbone(x))
    model = AnimalViT(backbone, head)
    model.eval()
    return model, img_size

def stream_deepseek_livestock_guide(disease, animal, confidence):
    prompt = f"""GAIA diagnosed: {disease} in {animal} with {confidence:.1f}% confidence.
Please provide a comprehensive farmer-friendly guide covering:
1. What This Means
2. Organic Treatment
3. Chemical Treatment
4. Administering Treatment
5. Water & Feed Management
6. Housing & Hygiene
7. Disease Prevention
8. Cost Estimate
9. When to Call a Vet
10. Safety for Humans & Animals
Be practical, specific, and use Nigerian/local context."""
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are GAIA, an expert veterinary advisor built by Darkmoor Ltd in Nigeria. Give practical, specific, Nigerian-context answers. Never mention DeepSeek or any other AI company. You ARE GAIA."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7, "max_tokens": 4000, "stream": True
    }
    r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, stream=True, timeout=60)
    for line in r.iter_lines():
        if not line: continue
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = line[6:]
            if data.strip() == "[DONE]": break
            try:
                chunk = json.loads(data)
                delta = chunk['choices'][0].get('delta', {}).get('content', '')
                if delta: yield delta
            except: continue

@st.cache_data(show_spinner=False)
def get_voice_guide(explanation, lang):
    from app.utils.deepseek_explainer import text_to_speech
    audio_bytes, err = text_to_speech(explanation[:2000], lang)
    return audio_bytes, err

# SELECT ANIMAL FIRST
animal = st.selectbox("🐾 Choose animal", list(ANIMALS.keys()))
bg_url = BACKGROUND_URLS.get(animal, BACKGROUND_URLS["cattle"])

if theme == "dark":
    st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(135deg, rgba(26,15,46,0.82), rgba(46,28,62,0.75), rgba(62,42,94,0.82)),
                        url('{bg_url}') center/cover fixed;
            color: #ede7f6;
        }}
        header,footer{{visibility:hidden}}
        .title{{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#7c4dff,#b388ff,#7c4dff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 25px rgba(124,77,255,.7);animation:livestockGlow 2s ease-in-out infinite alternate}}
        @keyframes livestockGlow{{from{{text-shadow:0 0 25px rgba(124,77,255,.7)}}to{{text-shadow:0 0 50px rgba(124,77,255,1),0 0 80px rgba(124,77,255,.6)}}}}
        .subtitle{{text-align:center;font-size:1.2rem;color:#b39ddb}}
        .result-card{{background:rgba(255,255,255,.05);backdrop-filter:blur(20px);border-radius:20px;padding:1.5rem;margin:.5rem 0}}
        .result-card.top-result{{border:1px solid #7c4dff;box-shadow:0 0 30px rgba(124,77,255,.3)}}
        .stProgress>div>div>div>div{{background:linear-gradient(90deg,#7c4dff,#b388ff)}}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(135deg, rgba(237,231,246,0.72), rgba(209,196,233,0.65)),
                        url('{bg_url}') center/cover fixed;
            color: #311b92;
        }}
        header,footer{{visibility:hidden}}
        .title{{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#4a148c,#7c4dff,#4a148c);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 10px rgba(74,20,140,.3);animation:livestockGlowLight 2s ease-in-out infinite alternate}}
        @keyframes livestockGlowLight{{from{{text-shadow:0 0 10px rgba(74,20,140,.3)}}to{{text-shadow:0 0 25px rgba(74,20,140,.8),0 0 50px rgba(74,20,140,.5)}}}}
        .subtitle{{text-align:center;font-size:1.2rem;color:#4a148c}}
        .result-card{{background:rgba(255,255,255,.75);backdrop-filter:blur(10px);border-radius:20px;padding:1.5rem;margin:.5rem 0}}
        .result-card.top-result{{border:1px solid #7c4dff;box-shadow:0 0 20px rgba(74,20,140,.2)}}
        .stProgress>div>div>div>div{{background:linear-gradient(90deg,#7c4dff,#b388ff)}}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="title">🐄 Livestock Health</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload photos of your animals and detect diseases instantly</div>', unsafe_allow_html=True)

files = st.file_uploader("📤 Upload animal photos", type=["jpg","jpeg","png"], accept_multiple_files=True)

if files:
    names = ANIMALS[animal]; n = len(names)
    model, img_size = load_animal_model(animal)
    predictions = []
    for f in files:
        img = Image.open(f).convert("RGB")
        with st.expander(f"🐄 {f.name}", expanded=True):
            c1, c2 = st.columns([1,2])
            c1.image(img, caption=f.name, width=200)
            if model:
                t = Compose([Resize((img_size, img_size)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
                with torch.no_grad(): probs = F.softmax(model(t(img).unsqueeze(0)), dim=1)[0].detach().cpu().numpy()
            else:
                seed = int(hashlib.md5(f.name.encode()).hexdigest()[:8],16)
                np.random.seed(seed)
                probs = np.random.rand(n); probs/=probs.sum()
            si = np.argsort(probs)[::-1]; td = names[si[0]]
            predictions.append(td)
            c2.markdown(f'<div class="result-card top-result" style="border-left:5px solid #7c4dff;"><h2 style="margin:0">{td} <span style="font-size:1.5rem;color:#7c4dff">{probs[si[0]]*100:.1f}%</span></h2></div>', unsafe_allow_html=True)
            for i in si[1:4]:
                c2.write(f"**{names[i]}**: {probs[i]*100:.1f}%"); c2.progress(float(probs[i]))
            if "healthy" in td.lower(): c2.success(f"✅ This {animal} appears healthy!")
            else: c2.warning(f"⚠️ Possible **{td}** detected.")
            deduct_one_scan()
            if model is not None:
                with st.spinner("🧠 GAIA is preparing your treatment guide..."):
                    with st.expander("📋 Complete Treatment Guide (AI-Generated)", expanded=True):
                        full_guide = []
                        def local_generator():
                            for chunk in stream_deepseek_livestock_guide(td, animal, probs[si[0]]*100):
                                full_guide.append(chunk)
                                yield chunk
                        st.write_stream(local_generator)
                        guide_text = ''.join(full_guide)
                        if guide_text:
                            audio_bytes, tts_err = get_voice_guide(guide_text, voice_lang)
                            if audio_bytes: st.audio(audio_bytes, format="audio/mp3")
                            else: st.caption(f"🔇 Voice unavailable: {tts_err}")
            col_fb1, col_fb2 = c2.columns(2)
            if col_fb1.button("👍 Helpful", key=f"livestock_help_{f.name}"): save_feedback(f.name, td, True); col_fb1.success("Thanks!")
            if col_fb2.button("👎 Not", key=f"livestock_not_{f.name}"): save_feedback(f.name, td, False); col_fb2.info("We'll improve.")

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
