
import streamlit as st
from PIL import Image
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np, os, sys, hashlib, datetime
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from timm.models.vision_transformer import VisionTransformer
from collections import Counter
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

st.set_page_config(page_title="GAIA – Crop Disease", page_icon="🌾", layout="wide")

# ---- SESSION STATE FOR AUDIO ----
if "audio_to_play" not in st.session_state:
    st.session_state.audio_to_play = None

CROP_CLASSES = {
    "millet": ["Blast", "Rust", "Healthy"],
    "maize": ["Blight", "Common_Rust", "Gray_Leaf_Spot", "Healthy"],
    "rice": ["Bacterial Leaf Blight","Brown Spot","Healthy Rice Leaf","Leaf Blast","Leaf Scald","Narrow Brown Spot","Neck Blast","Rice Hispa","Sheath Blight","Tungro"],
    "soybean": ["Bacterial Pustule","Frogeye Leaf Spot","Healthy","Mosaic Virus","Rust","Southern blight","Sudden Death Syndrome","Target Leaf Spot","Yellow Mosaic","brown_spot","crestamento","ferrugen","powdery_mildew","septoria"],
    "pepper": ["Aphid","Bacterial spot","Blossom end rot","Burn","Edema","Healthy","Leaf curl","Leaf miners","Mosaic virus","Nutrient deficiency","Powdery mildew","Spider mite","Thrips"],
    "cabbage": ["Alternaria Leaf Spot","Bacterial Spot Rot","Black Rot","Cabbage Aphid Colony","Downy Mildew","Healthy","Club Root","Ring Spot"],
    "potato": ["Bacteria","Fungi","Healthy","Nematode","Pest","Phytopthora","Virus"],
}

CHECKPOINT_MAP = {
    "millet": os.path.join("models", "millet_3class", "model.pt"),
    "maize": os.path.join("models", "maize", "model.pt"),
    "rice": os.path.join("models", "rice_10class", "model.pt"),
    "soybean": os.path.join("models", "soybean_14class", "model.pt"),
    "pepper": os.path.join("models", "pepper_13class", "model.pt"),
    "cabbage": os.path.join("models", "cabbage_8class", "model.pt"),
}

if "selected_crop" not in st.session_state:
    st.session_state.selected_crop = None
crop = st.session_state.selected_crop

st.markdown("<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>", unsafe_allow_html=True)
dark = st.toggle("", value=False, key="crops_theme")
theme = "dark" if dark else "light"

def load_crop_model(crop_name):
    from app.utils.download_models import ensure_model
    DOWNLOAD_KEYS = {
        "millet": "millet_3class",
        "maize": "maize",
        "rice": "rice_10class",
    }
    key = DOWNLOAD_KEYS.get(crop_name, crop_name)
    checkpoint = ensure_model(key)
    if checkpoint is None or not os.path.exists(checkpoint):
        return None, None
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
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
        n = len(CROP_CLASSES[crop_name])
        head = nn.Linear(embed_dim, n)
        head.load_state_dict({"weight": state["head.weight"], "bias": state.get("head.bias", torch.zeros(n))}, strict=False)
    class CropViT(torch.nn.Module):
        def __init__(self, backbone, head): super().__init__(); self.backbone = backbone; self.head = head
        def forward(self, x): return self.head(self.backbone(x))
    model = CropViT(backbone, head)
    model.eval()
    return model, img_size


def load_potato_lcmt():
    import requests as req
    from src.models.lcmt import LCMT
    checkpoint_dir = "models/potato_lcmt"
    checkpoint_path = os.path.join(checkpoint_dir, "model.pt")
    if not os.path.exists(checkpoint_path) or os.path.getsize(checkpoint_path) < 10000:
        os.makedirs(checkpoint_dir, exist_ok=True)
        url = "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/gaia_potato_lcmt.pt"
        with st.spinner("Downloading potato LCMT model (one-time, ~259 MB)…"):
            r = req.get(url, stream=True, timeout=600)
            total = 0
            with open(checkpoint_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=32768):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
            if total < 10000:
                st.error("Potato LCMT download failed.")
                return None
    model = LCMT(num_classes=7)
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model.load_state_dict(state)
    model.eval()
    return model

def predict(model, img, img_size):
    t = Compose([Resize((img_size, img_size)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
    with torch.no_grad():
        return F.softmax(model(t(img).unsqueeze(0)), dim=1)[0].detach().cpu().numpy()

def green_check(image, threshold=0.2):
    arr = np.array(image)
    r, g, b = arr[:,:,0].astype(float), arr[:,:,1].astype(float), arr[:,:,2].astype(float)
    mask = (g > r + 20) & (g > b + 20)
    return mask.mean() >= threshold, mask.mean()

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

def save_feedback(image_name, predicted_class, helpful):
    if "user" not in st.session_state or st.session_state.user is None: return
    from supabase import create_client
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    try: supabase.table("user_feedback").insert({"user_id": st.session_state.user.id, "image_name": image_name, "predicted_class": predicted_class, "helpful": helpful, "created_at": datetime.datetime.now().isoformat()}).execute()
    except: pass

@st.cache_data(show_spinner=False)
def get_treatment_guide(disease, crop, confidence):
    from app.utils.deepseek_explainer import explain_diagnosis
    explanation, err = explain_diagnosis(disease, confidence, crop, "crop")
    if err:
        return None, err
    return explanation, None

def detect_language(text):
    t = text.lower()
    if any(w in t for w in ["biko", "kedu", "ndewo", "imo", "igbo"]):
        return "ig"
    if any(w in t for w in ["sannu", "barka", "hausa", "zamu", "ya ya"]):
        return "ha"
    if any(w in t for w in ["e kaaro", "bawo", "yoruba", "se", "mo wa"]):
        return "yo"
    if any(w in t for w in ["wetin", "how far", "abi", "dey", "pidgin"]):
        return "pcm"
    return "en-GB"

def speak_answer(text, language="en-GB"):
    try:
        from app.utils.deepseek_explainer import text_to_speech
        audio_bytes, err = text_to_speech(text, language)
        if audio_bytes:
            return audio_bytes, None
        return None, err or "Voice unavailable"
    except Exception as e:
        return None, str(e)

overlay = "rgba(0,0,0,0.55)" if theme == "dark" else "rgba(255,255,255,0.75)"
bg_url = "https://images.unsplash.com/photo-1600112356915-089abb8fc71a"
bg_css = f'.stApp {{ background-color: #2c3e50; background: linear-gradient({overlay}, {overlay}), url("{bg_url}") center/cover fixed; }}'

if theme == "dark":
    st.markdown(f"<style>.stApp{{background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);color:#fff}}header,footer{{visibility:hidden}}.title{{font-size:2.8rem;font-weight:800;background:linear-gradient(90deg,#2e7d32,#4caf50);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.subtitle{{font-size:1.2rem;color:#b0bec5;margin-bottom:2rem}}.pred-box{{background:rgba(255,255,255,.05);backdrop-filter:blur(12px);border-left:5px solid #4caf50;padding:1rem 1.5rem;border-radius:10px;margin:.5rem 0}}.pred-box-high{{border-left-color:#2e7d32;background:rgba(255,255,255,.1)}}.stProgress>div>div>div>div{{background:linear-gradient(90deg,#4caf50,#81c784)}}.crop-btn{{background:rgba(255,255,255,0.08);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.15);border-radius:20px;padding:2rem 1rem;width:100%;height:120px;color:#fff!important;font-size:1.3rem;font-weight:600;transition:all 0.3s ease;cursor:pointer;text-align:center}}.crop-btn:hover{{transform:translateY(-8px);box-shadow:0 20px 40px rgba(0,200,83,0.3);border-color:#00c853;background:rgba(0,200,83,0.15)}}{bg_css}</style>", unsafe_allow_html=True)
else:
    st.markdown(f"<style>.stApp{{background:linear-gradient(135deg,#e8f5e9,#f1f8e9);color:#1b5e20}}header,footer{{visibility:hidden}}.title{{font-size:2.8rem;font-weight:800;background:linear-gradient(90deg,#2e7d32,#4caf50);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.subtitle{{font-size:1.2rem;color:#33691e;margin-bottom:2rem}}.pred-box{{background:rgba(255,255,255,0.9);border-left:5px solid #4caf50;padding:1rem 1.5rem;border-radius:10px;margin:.5rem 0}}.pred-box-high{{border-left-color:#2e7d32;background:rgba(255,255,255,1)}}.stProgress>div>div>div>div{{background:linear-gradient(90deg,#4caf50,#81c784)}}.crop-btn{{background:rgba(255,255,255,0.9);backdrop-filter:blur(10px);border:1px solid rgba(0,0,0,0.1);border-radius:20px;padding:2rem 1rem;width:100%;height:120px;color:#1b5e20!important;font-size:1.3rem;font-weight:600;transition:all 0.3s ease;cursor:pointer;text-align:center}}.crop-btn:hover{{transform:translateY(-8px);box-shadow:0 20px 40px rgba(46,125,50,0.2);border-color:#2e7d32;background:rgba(46,125,50,0.1)}}{bg_css}</style>", unsafe_allow_html=True)

# ===== PLAY STORED AUDIO (before rendering content) =====
if st.session_state.audio_to_play:
    st.audio(st.session_state.audio_to_play, format="audio/mp3")
    st.session_state.audio_to_play = None

st.markdown('<div class="title">🌾 Crop Disease Diagnosis</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Select a crop, upload leaf photos, and let AI detect diseases in seconds</div>', unsafe_allow_html=True)

with st.expander("📸 How to take a good leaf photo", expanded=False):
    st.markdown("1. 🌿 Pick a single leaf showing symptoms – place on white paper.\n2. 📱 Hold phone 20‑30 cm above.\n3. ☀️ Avoid shadows.\n4. 📤 Upload 2‑3 photos for best results.")

if crop is None:
    cols = st.columns(len(CROP_CLASSES))
    for i, name in enumerate(CROP_CLASSES.keys()):
        with cols[i]:
            if st.button(name.title(), key=f"crop_{name}", use_container_width=True):
                st.session_state.selected_crop = name
                st.rerun()
else:
    if st.button("← Back to Crops"):
        st.session_state.selected_crop = None
        st.rerun()
    st.markdown(f"### 🌱 Selected Crop: **{crop.title()}**")
    files = st.file_uploader("📤 Upload leaf images", type=["jpg","jpeg","png"], accept_multiple_files=True)
    if files:
        if crop == "potato":
            model = load_potato_lcmt()
            img_size = 224
            class_names = CROP_CLASSES[crop]
        else:
            model, img_size = load_crop_model(crop)
            class_names = CROP_CLASSES[crop]
        predictions = []
        for f in files:
            img = Image.open(f).convert("RGB")
            is_green, pct = green_check(img)
            if not is_green:
                st.warning(f"⚠️ {f.name}: only {pct*100:.0f}% green pixels. Are you sure this is a leaf?")
            with st.expander(f"📷 {f.name}", expanded=True):
                c1, c2 = st.columns([1, 2])
                c1.image(img, caption=f.name, width=200)
                if model is None:
                    c2.warning("No trained model – using demo predictions.")
                    seed = int(hashlib.md5(f.name.encode()).hexdigest()[:8], 16)
                    np.random.seed(seed)
                    probs = np.random.rand(len(class_names)); probs /= probs.sum()
                    lesion_count = 0
                    severity = 0
                else:
                    if crop == "potato":
                        from torchvision.transforms import Compose, Resize, ToTensor, Normalize
                        transform = Compose([Resize((224,224)), ToTensor(), Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
                        img_tensor = transform(img).unsqueeze(0)
                        with torch.no_grad():
                            output = model(img_tensor)
                            probs = F.softmax(output['logits'], dim=1)[0].detach().cpu().numpy()
                            lesion_count = output['lesion_count'].item()
                            severity = output['severity'].item() * 100
                    else:
                        try:
                            probs = predict(model, img, img_size)
                            lesion_count = 0
                            severity = 0
                        except Exception as e:
                            c2.error(f"Error: {e}")
                            continue
                top_idx = np.argmax(probs)
                predictions.append(class_names[top_idx])
                c2.markdown(f"**Top Result:** {class_names[top_idx]} ({probs[top_idx]*100:.1f}%)")
                if crop == "potato":
                    c2.markdown(f"🔬 Lesion Count: **{lesion_count:.0f}**")
                    c2.markdown(f"📊 Severity: **{severity:.1f}%**")
                for i in np.argsort(probs)[::-1][1:5]:
                    c2.write(f"{class_names[i]}: {probs[i]*100:.1f}%")
                    c2.progress(float(probs[i]))
                deduct_one_scan()

                # ---- Treatment guide on demand (cached) ----
                if model is not None:
                    top_disease = class_names[top_idx]
                    if st.button("📋 Get Treatment Guide", key=f"guide_{f.name}"):
                        with st.spinner("🧠 Generating treatment guide..."):
                            explanation, err = get_treatment_guide(top_disease, crop, probs[top_idx]*100)
                        if err:
                            st.warning(f"Could not generate guide: {err}")
                        elif explanation:
                            with st.expander("📋 Complete Treatment Guide (AI-Generated)", expanded=True):
                                st.markdown(explanation)
                                st.markdown("---")
                                st.markdown("### 🔊 Listen to Guide")
                                lang_options = {
                                    "English (UK)": "en-GB",
                                    "Hausa": "ha",
                                    "Yoruba": "yo",
                                    "Igbo": "ig",
                                    "Pidgin": "pcm"
                                }
                                selected_lang = st.selectbox("Choose voice language", list(lang_options.keys()), key=f"lang_{f.name}")
                                lang_code = lang_options[selected_lang]
                                if st.button("🔊 Speak Guide", key=f"speak_guide_{f.name}"):
                                    with st.spinner("🔊 Generating voice..."):
                                        audio_bytes, tts_err = speak_answer(explanation[:2000], lang_code)
                                    if audio_bytes:
                                        # Store in session state and rerun to play
                                        st.session_state.audio_to_play = audio_bytes
                                        st.rerun()
                                    else:
                                        st.warning(f"Voice unavailable: {tts_err}")

                col_fb1, col_fb2 = c2.columns(2)
                if col_fb1.button("👍 Helpful", key=f"helpful_{f.name}"):
                    save_feedback(f.name, class_names[top_idx], True); col_fb1.success("Thanks!")
                if col_fb2.button("👎 Not", key=f"not_{f.name}"):
                    save_feedback(f.name, class_names[top_idx], False); col_fb2.info("We'll improve.")
        if len(predictions) >= 2:
            vote = Counter(predictions).most_common(1)[0]
            if vote[1] > len(predictions)//2:
                st.success(f"🗳️ Majority vote: **{vote[0]}** ({vote[1]}/{len(predictions)} photos)")
            else:
                st.info("🗳️ No clear consensus. Consider retaking.")


# ---------- Quick Navigation ----------
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(9)
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
    st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[7]:
    st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[8]:
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
