
import streamlit as st
from PIL import Image
import torch, torch.nn.functional as F, numpy as np, os, sys, timm

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

st.set_page_config(page_title="GAIA – Livestock Health", page_icon="🐄", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .top-nav { display: flex; justify-content: center; gap: 2rem; padding: 0.8rem; background: rgba(255,255,255,0.9); backdrop-filter: blur(15px); border-radius: 15px; margin-bottom: 2rem; }
    .top-nav a { color: #2e7d32; text-decoration: none; font-weight: 600; font-size: 1rem; padding: 0.5rem 1.5rem; border-radius: 30px; }
</style>
<div class="top-nav"><a href="/" target="_self">🏠 Dashboard</a></div>
""", unsafe_allow_html=True)

if "theme" not in st.session_state: st.session_state.theme = "dark"
dark_mode = st.toggle("", value=(st.session_state.theme == "dark"), key="livestock_theme_toggle")
st.session_state.theme = "dark" if dark_mode else "light"
theme = st.session_state.theme

ANIMAL_CLASSES = {
    "cattle": ["Foot‑and‑Mouth Disease", "Healthy", "Lumpy Skin Disease"],
    "poultry": ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]
}

class LivestockClassifier(nn.Module):
    def __init__(self, num_classes): super().__init__(); self.backbone = timm.create_model('vit_tiny_patch16_224', pretrained=False, num_classes=0); self.head = nn.Linear(self.backbone.embed_dim, num_classes)
    def forward(self, x): return self.head(self.backbone(x))

@st.cache_resource
def load_animal_model(animal: str):
    checkpoint = f"checkpoints/{animal}/best_model.pt"
    if not os.path.exists(checkpoint): raise FileNotFoundError(f"Model not found at {checkpoint}")
    model = LivestockClassifier(num_classes=len(ANIMAL_CLASSES[animal]))
    state_dict = torch.load(checkpoint, map_location="cpu", weights_only=False); model.load_state_dict(state_dict); model.eval()
    return model

def predict_image(model, image):
    transform = Compose([Resize((224, 224)), ToTensor(), Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    with torch.no_grad(): return F.softmax(model(transform(image).unsqueeze(0)), dim=1)[0].cpu().numpy()

def deduct_and_show(user_id):
    from supabase import create_client
    url = st.secrets["supabase"]["url"]; key = st.secrets["supabase"]["key"]; supabase = create_client(url, key)
    try: supabase.table("user_scans").insert({"user_id": user_id, "scans_remaining": 30, "plan": "free"}).execute()
    except: pass
    try:
        supabase.rpc("decrement_scan", {"uid": user_id}).execute()
        res = supabase.table("user_scans").select("scans_remaining").eq("user_id", user_id).execute()
        if res.data: st.success(f"Scan deducted. Remaining: {res.data[0]['scans_remaining']}")
    except: pass

st.markdown('<h1 style="text-align:center;color:#4a148c;">🐄 Livestock Health</h1>', unsafe_allow_html=True)
animal = st.selectbox("🐾 Choose animal", list(ANIMAL_CLASSES.keys()))
uploaded_files = st.file_uploader("📤 Upload animal photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file).convert("RGB")
        col1, col2 = st.columns([1, 2])
        with col1: st.image(image, caption=uploaded_file.name, width=200)
        with col2:
            try:
                model = load_animal_model(animal); probs = predict_image(model, image)
                class_names = ANIMAL_CLASSES[animal]; top_idx = np.argmax(probs)
                st.success(f"**{class_names[top_idx]}** ({probs[top_idx]*100:.1f}%)")
                if st.session_state.get("user"): deduct_and_show(st.session_state.user.id)
            except Exception as e: st.error(str(e))
        st.markdown("---")
