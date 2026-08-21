
import streamlit as st
    # Allow demo mode
    from supabase import create_client
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
try:
    session = supabase.auth.get_session()
    user = session.user if session else None
except:
    from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os
import sys
import hashlib
import json
from collections import Counter
import requests
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

user = st.session_state.get("user", None)
if user is None:
    st.warning("Please log in first.")
    st.stop()
DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

st.set_page_config(page_title="GAIA – Soil Analysis", page_icon="🏞️", layout="wide")
st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>", unsafe_allow_html=True)
dark = st.toggle("", value=False, key="soil_theme")
theme = "dark" if dark else "light"

SOIL_NAMES = ["Alluvial","Sandy","Clay","Loamy","Laterite","Black","Red","Peat","Cinder","Sandy Loam","Yellow"]
SOIL_COLORS = {"Alluvial":"#8d6e63","Sandy":"#d4a373","Clay":"#a1887f","Loamy":"#6d4c41","Laterite":"#b7410e","Black":"#3e2723","Red":"#c62828","Peat":"#4e342e","Cinder":"#616161","Sandy Loam":"#bcaaa4","Yellow":"#f9a825"}

language_options = {
    "English (UK)": "en-GB",
    "Hausa": "ha",
    "Yoruba": "yo",
    "Igbo": "ig",
    "Pidgin": "pcm"
}
selected_lang_label = st.selectbox("🔊 Voice language for soil guide", list(language_options.keys()), index=0)
voice_lang = language_options[selected_lang_label]

if theme == "dark":
    st.markdown("""<style>.stApp{background:linear-gradient(rgba(0,0,0,0.30),rgba(0,0,0,0.30)),url('https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80') center/cover fixed;color:#f5f0eb}header,footer{visibility:hidden}.title{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#d4a373,#f5e6d3,#d4a373);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 25px rgba(212,163,115,.7);animation:soilGlow 2s ease-in-out infinite alternate}@keyframes soilGlow{from{text-shadow:0 0 25px rgba(212,163,115,.7)}to{text-shadow:0 0 50px rgba(212,163,115,1),0 0 80px rgba(212,163,115,.6)}}.subtitle{font-size:1.2rem;color:#bcaaa4}.card{background:rgba(255,255,255,.05);backdrop-filter:blur(20px);border-radius:20px;padding:1.5rem;margin:.5rem 0}.stProgress>div>div>div>div{background:linear-gradient(90deg,#d4a373,#f5e6d3)}</style>""", unsafe_allow_html=True)
else:
    st.markdown("""<style>.stApp{background:linear-gradient(rgba(255,255,255,0.45),rgba(255,255,255,0.45)),url('https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80') center/cover fixed;color:#3e2723}header,footer{visibility:hidden}.title{font-size:3.5rem;font-weight:900;text-align:center;background:linear-gradient(90deg,#5d4037,#8d6e63,#5d4037);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.subtitle{font-size:1.2rem;color:#4e342e}.card{background:rgba(255,255,255,.8);backdrop-filter:blur(10px);border-radius:20px;padding:1.5rem;margin:.5rem 0}.stProgress>div>div>div>div{background:linear-gradient(90deg,#8d6e63,#bcaaa4)}</style>""", unsafe_allow_html=True)

def deduct_one_scan():
        return
    from supabase import create_client
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    uid = user.id
    try:
        supabase.table("user_scans").insert({"user_id":uid,"scans_remaining":30,"plan":"free"}).execute()
    except:
        pass
    try:
        supabase.rpc("decrement_scan",{"uid":uid}).execute()
    except:
        pass

def load_soil_model():
    from app.utils.download_models import ensure_model
    checkpoint = ensure_model("soil_11class")
    if not checkpoint or not os.path.exists(checkpoint):
        return None, None

    state = torch.load(checkpoint, map_location="cpu", weights_only=False)

    # Detect prefix
    prefix = "backbone." if any(k.startswith("backbone.") for k in state) else "encoder."
    embed_dim = state[f"{prefix}cls_token"].shape[-1]
    pos = state[f"{prefix}pos_embed"]
    num_patches = pos.shape[1] - 1
    grid = int(num_patches ** 0.5)
    img_size = grid * 16

    # Auto‑detect depth
    depth = len([k for k in state if k.startswith(f"{prefix}blocks") and k.endswith(".norm1.weight")])
    num_heads = 6 if embed_dim == 384 else 3

    from timm.models.vision_transformer import VisionTransformer
    backbone = VisionTransformer(
        img_size=img_size, patch_size=16, embed_dim=embed_dim,
        depth=depth, num_heads=num_heads, num_classes=0, global_pool='token'
    )
    backbone_state = {k.replace(prefix, ""): v for k, v in state.items() if k.startswith(prefix)}
    backbone.load_state_dict(backbone_state, strict=False)

    # Rebuild head dynamically
    n = len(SOIL_NAMES)
    head_keys = [k for k in state if k.startswith("head.")]

    if any(".0.weight" in k for k in head_keys):
        # Deep sequential head
        w_keys = sorted([k for k in head_keys if k.endswith(".weight")], key=lambda x: int(x.split('.')[1]))
        layers = []
        in_feat = embed_dim
        for w_key in w_keys:
            w = state[w_key]
            out_feat = w.shape[0]
            layers.append(nn.Linear(in_feat, out_feat))
            if w_key != w_keys[-1]:
                layers.extend([nn.GELU(), nn.Dropout(0.2)])
            in_feat = out_feat
        head = nn.Sequential(*layers)
        head_state = {k.replace("head.", ""): v for k, v in state.items() if k.startswith("head.")}
        head.load_state_dict(head_state, strict=False)
    else:
        head = nn.Linear(embed_dim, n)
        head.load_state_dict({
            "weight": state.get("head.weight"),
            "bias": state.get("head.bias", torch.zeros(n))
        }, strict=False)

    class SoilViT(torch.nn.Module):
        def __init__(self, bb, hd):
            super().__init__()
            self.backbone = bb
            self.head = hd
        def forward(self, x):
            return self.head(self.backbone(x))

    model = SoilViT(backbone, head)
    model.eval()
    return model, img_size

def stream_deepseek_soil_guide(soil_name, confidence):
    """Stream a soil management guide directly from DeepSeek."""
    prompt = f"""GAIA identified soil type: {soil_name} with {confidence:.1f}% confidence.
Please provide a comprehensive soil management guide covering:
1. Soil Characteristics
2. Organic Improvement
3. Fertilizer Guide (specific NPK ratios and application rates)
4. Best Crops for this soil
5. Water Management
6. Land Preparation
7. Yield Potential
8. Input Cost Estimate
9. Soil Conservation
10. Common Mistakes to Avoid
Be practical, specific, and use Nigerian/local context."""
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are GAIA, an expert agricultural advisor built by Darkmoor Ltd in Nigeria. Give practical, specific, Nigerian-context answers. Never mention DeepSeek or any other AI company. You ARE GAIA."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000,
        "stream": True
    }
    r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, stream=True, timeout=60)
    for line in r.iter_lines():
        if not line:
            continue
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = line[6:]
            if data.strip() == "[DONE]":
                break
            try:
                chunk = json.loads(data)
                delta = chunk['choices'][0].get('delta', {}).get('content', '')
                if delta:
                    yield delta
            except:
                continue

@st.cache_data(show_spinner=False)
def get_voice_guide(explanation, lang):
    from app.utils.deepseek_explainer import text_to_speech
    audio_bytes, err = text_to_speech(explanation[:2000], lang)
    return audio_bytes, err

st.markdown('<div class="title">🏞️ Soil Type Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload 2–3 photos for consensus diagnosis with AI‑generated management guide</div>', unsafe_allow_html=True)

with st.expander("📸 Tips for best results", expanded=False):
    st.markdown("1. 🏞️ Take 2–3 photos from slightly different angles\n2. ☀️ Use natural daylight\n3. 📤 Upload all photos together\n4. 🔄 More photos = better accuracy")

files = st.file_uploader("📤 Upload 2–3 soil photos", type=["jpg","jpeg","png"], accept_multiple_files=True)

if files:
    model, img_size = load_soil_model()
    if model is None:
        st.error("🚫 Soil model could not be loaded.")
        st.info("🔄 Try refreshing the page. The model may need to download first (one‑time, ~87 MB).")
        st.stop()

    all_predictions = []
    all_probs_list = []

    for f in files:
        img = Image.open(f).convert("RGB")
        with st.expander(f"🏞️ {f.name}", expanded=True):
            c1, c2 = st.columns([1, 2])
            c1.image(img, caption=f.name, width=200)
            transform = Compose([Resize((img_size, img_size)), ToTensor(), Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
            with torch.no_grad():
                probs = F.softmax(model(transform(img).unsqueeze(0)), dim=1)[0].detach().cpu().numpy()
            top_idx = np.argmax(probs)
            soil_name = SOIL_NAMES[top_idx]
            all_predictions.append(top_idx)
            all_probs_list.append(probs)
            c2.markdown(f"**This photo says:** {soil_name} ({probs[top_idx]*100:.1f}%)")

    vote_counts = Counter(all_predictions)
    consensus_idx, vote_count = vote_counts.most_common(1)[0]
    consensus_name = SOIL_NAMES[consensus_idx]
    agreement_pct = (vote_count / len(files)) * 100
    avg_probs = np.mean(all_probs_list, axis=0)
    confidence = avg_probs[consensus_idx] * 100
    color = SOIL_COLORS.get(consensus_name, "#8d6e63")

    st.markdown(f"""<div class="card" style="border-left:5px solid {color};"><h3>🗳️ Consensus: {vote_count}/{len(files)} photos agree ({agreement_pct:.0f}%)</h3><h2 style="color:{color};">{consensus_name} ({confidence:.1f}%)</h2></div>""", unsafe_allow_html=True)

    # ===== STREAMING AI SOIL GUIDE + VOICE =====
    with st.spinner("🧠 GAIA is preparing your soil management guide..."):
        with st.expander("📋 Complete Soil Management Guide (AI-Generated)", expanded=True):
            full_guide = []
            def local_generator():
                for chunk in stream_deepseek_soil_guide(consensus_name, confidence):
                    full_guide.append(chunk)
                    yield chunk
            st.write_stream(local_generator)
            guide_text = ''.join(full_guide)
            if guide_text:
                audio_bytes, tts_err = get_voice_guide(guide_text, voice_lang)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
                else:
                    st.caption(f"🔇 Voice unavailable: {tts_err}")

    deduct_one_scan()

st.markdown("---")

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
