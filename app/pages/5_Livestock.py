
import streamlit as st
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os
import sys
import timm

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

# ---------- Theme toggle ----------
st.set_page_config(page_title="GAIA – Livestock Health", page_icon="🐄", layout="wide")

st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=True, key="livestock_theme_toggle")
theme = "dark" if dark_mode else "light"

# ---------- Animal selection ----------
ANIMAL_CLASSES = {
    "cattle": ["Foot‑and‑Mouth Disease", "Healthy", "Lumpy Skin Disease"],
    "poultry": ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]
}

animal = st.selectbox("🐾 Choose animal", list(ANIMAL_CLASSES.keys()))

# ---------- Dynamic background based on animal ----------
if animal == "cattle":
    bg_image = "https://images.unsplash.com/photo-1570042225831-d98fa7577f1e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80"
    bg_overlay = "rgba(20, 10, 5, 0.85)" if theme == "dark" else "rgba(255, 255, 255, 0.85)"
    accent_color = "#d4a373"
    glow_color = "rgba(212, 163, 115, 0.6)"
else:
    bg_image = "https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80"
    bg_overlay = "rgba(30, 20, 5, 0.85)" if theme == "dark" else "rgba(255, 255, 255, 0.85)"
    accent_color = "#ff9800"
    glow_color = "rgba(255, 152, 0, 0.6)"

# ---------- CSS ----------
if theme == "dark":
    st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #e0e0e0;
        }}
        header, footer {{visibility: hidden;}}
        
        /* Dynamic background */
        .bg-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -2;
            background: url('{bg_image}') center/cover no-repeat fixed;
        }}
        .bg-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background: {bg_overlay};
        }}
        
        /* Title */
        .title {{
            font-size: 3rem; font-weight: 900; text-align: center;
            background: linear-gradient(90deg, {accent_color}, #fff, {accent_color});
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px {glow_color};
            animation: titleGlow 2s ease-in-out infinite alternate;
            position: relative; z-index: 1;
        }}
        @keyframes titleGlow {{
            from {{ text-shadow: 0 0 30px {glow_color}; }}
            to {{ text-shadow: 0 0 60px {glow_color}, 0 0 100px {glow_color}; }}
        }}
        .subtitle {{ text-align: center; font-size: 1.1rem; color: #ddd; margin-bottom: 2rem; position: relative; z-index: 1; }}
        
        /* Upload zone */
        .stFileUploader > div {{
            background: rgba(255,255,255,0.03) !important; backdrop-filter: blur(15px) !important;
            border: 2px dashed rgba({accent_color.replace('#','')}, 0.3) !important;
            border-radius: 20px !important; padding: 2rem !important;
            position: relative; z-index: 1;
        }}
        .stFileUploader > div:hover {{
            border-color: {accent_color} !important;
            box-shadow: 0 0 30px {glow_color};
        }}
        
        /* Image preview */
        .stImage img {{
            border-radius: 20px;
            box-shadow: 0 0 40px {glow_color};
            border: 1px solid {accent_color};
            position: relative; z-index: 1;
        }}
        
        /* Result cards */
        .result-card {{
            background: rgba(0,0,0,0.6); backdrop-filter: blur(25px);
            border: 1px solid {accent_color}44;
            border-radius: 20px; padding: 1.5rem;
            margin: 0.8rem 0; position: relative; overflow: hidden;
        }}
        .result-card::before {{
            content: ''; position: absolute; top: -50%; left: -50%;
            width: 200%; height: 200%;
            background: conic-gradient(transparent, {accent_color}22, transparent, transparent);
            animation: rotate 6s linear infinite;
        }}
        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        .result-card > * {{ position: relative; z-index: 1; }}
        
        .top-result {{
            background: rgba(0,0,0,0.8); border: 2px solid {accent_color};
            box-shadow: 0 0 50px {glow_color}, inset 0 0 30px {accent_color}11;
        }}
        .top-result h3 {{
            font-size: 1.2rem; text-transform: uppercase; letter-spacing: 2px;
            color: {accent_color}; margin: 0.3rem 0;
        }}
        .counter {{
            font-size: 2rem; font-weight: 900; color: {accent_color};
            text-shadow: 0 0 30px {glow_color};
            animation: pulse 2s ease-in-out infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}
        
        .progress-container {{ margin: 0.6rem 0; position: relative; }}
        .progress-label {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem; }}
        .progress-label span {{ font-weight: 600; color: #ddd; }}
        .progress-label .percent {{ color: {accent_color}; font-size: 1rem; font-weight: 700; }}
        .progress-bar {{ height: 6px; background: rgba(255,255,255,0.05); border-radius: 8px; overflow: hidden; }}
        .progress-fill {{
            height: 100%; border-radius: 8px;
            background: linear-gradient(90deg, {accent_color}, #fff, {accent_color});
            background-size: 200% 100%;
            animation: shimmer 2s ease infinite, grow 1.5s ease-out;
            box-shadow: 0 0 10px {glow_color};
            transition: width 1s ease;
        }}
        @keyframes shimmer {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}
        @keyframes grow {{ from {{ width: 0% !important; }} }}
        
        .action-box {{
            background: {accent_color}11; border: 1px solid {accent_color}33;
            border-radius: 15px; padding: 1rem; text-align: center; margin-top: 1rem;
            backdrop-filter: blur(10px);
        }}
    </style>
    <div class="bg-container"></div>
    <div class="bg-overlay"></div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(135deg, #f5f7fa 0%, #e8f5e9 100%);
            color: #1b5e20;
        }}
        .bg-container, .bg-overlay {{ display: none; }}
        .title {{
            font-size: 3rem; font-weight: 900; text-align: center;
            background: linear-gradient(90deg, {accent_color}, #333, {accent_color});
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 10px {glow_color};
            animation: titleGlowLight 2s ease-in-out infinite alternate;
        }}
        @keyframes titleGlowLight {{
            from {{ text-shadow: 0 0 10px {glow_color}; }}
            to {{ text-shadow: 0 0 25px {glow_color}, 0 0 50px {glow_color}; }}
        }}
        .subtitle {{ text-align: center; font-size: 1.1rem; color: #333; margin-bottom: 2rem; }}
        .stFileUploader > div {{
            background: rgba(255,255,255,0.8) !important; backdrop-filter: blur(10px) !important;
            border: 2px dashed {accent_color}66 !important; border-radius: 20px !important;
            padding: 2rem !important;
        }}
        .stImage img {{ border-radius: 20px; box-shadow: 0 0 20px rgba(0,0,0,0.2); }}
        .result-card {{
            background: rgba(255,255,255,0.8); backdrop-filter: blur(10px);
            border: 1px solid rgba(0,0,0,0.1); border-radius: 20px;
            padding: 1.5rem; margin: 0.8rem 0;
        }}
        .top-result {{ border-color: {accent_color}; box-shadow: 0 0 20px {accent_color}44; }}
        .top-result h3 {{ font-size: 1.2rem; color: #1b5e20; }}
        .counter {{ font-size: 2rem; font-weight: 900; color: {accent_color}; }}
        .progress-container {{ margin: 0.6rem 0; }}
        .progress-label {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem; }}
        .progress-label span {{ font-weight: 600; color: #1b5e20; }}
        .progress-label .percent {{ color: {accent_color}; font-size: 1rem; font-weight: 700; }}
        .progress-bar {{ height: 6px; background: rgba(0,0,0,0.05); border-radius: 8px; overflow: hidden; }}
        .progress-fill {{
            height: 100%; border-radius: 8px;
            background: linear-gradient(90deg, {accent_color}, #fff);
            animation: grow 1.5s ease-out;
        }}
        @keyframes grow {{ from {{ width: 0% !important; }} }}
        .action-box {{
            background: {accent_color}11; border: 1px solid {accent_color}33;
            border-radius: 15px; padding: 1rem; text-align: center; margin-top: 1rem;
        }}
    </style>
    """, unsafe_allow_html=True)

# ---------- Custom model class (matches the trained architecture) ----------
class LivestockClassifier(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.backbone = timm.create_model('vit_tiny_patch16_224', pretrained=False, num_classes=0)
        self.head = nn.Linear(self.backbone.embed_dim, num_classes)
    def forward(self, x):
        return self.head(self.backbone(x))

@st.cache_resource
def load_animal_model(animal: str):
    checkpoint = f"checkpoints/{animal}/best_model.pt"
    if not os.path.exists(checkpoint):
        raise FileNotFoundError(f"Model not found at {checkpoint}")
    num_classes = len(ANIMAL_CLASSES[animal])
    model = LivestockClassifier(num_classes=num_classes)
    state_dict = torch.load(checkpoint, map_location="cpu", weights_only=False)
    model.load_state_dict(state_dict)
    model.eval()
    return model

def predict_image(model, image: Image.Image):
    transform = Compose([
        Resize((224, 224)),
        ToTensor(),
        Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    img_tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        logits = model(img_tensor)
        probs = F.softmax(logits, dim=1)[0].cpu().numpy()
    return probs

# ---------- UI ----------
st.markdown('<div class="title">🐄 LIVESTOCK HEALTH</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Select animal, upload photo, get instant diagnosis.</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("📤 UPLOAD ANIMAL PHOTO", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="", width=300)

    st.markdown("---")

    try:
        model = load_animal_model(animal)
        probs = predict_image(model, image)
    except FileNotFoundError as e:
        st.error(f"🚫 {e}")
        st.info("Model not installed. Please contact support.")
        st.stop()
    except Exception as e:
        st.error(f"Scan failed: {e}")
        st.stop()

    class_names = ANIMAL_CLASSES[animal]
    top_idx = np.argmax(probs)
    top_prob = probs[top_idx] * 100

    # Top result card
    st.markdown(f"""
    <div class="result-card top-result">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <p style="color: {accent_color}; margin: 0; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px;">Diagnosis</p>
                <h3 style="margin: 0.3rem 0;">{class_names[top_idx]}</h3>
            </div>
            <div class="counter">{top_prob:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 PROBABILITY BREAKDOWN")

    sorted_idx = np.argsort(probs)[::-1]
    for i in sorted_idx:
        disease = class_names[i]
        percent = probs[i] * 100
        bar_class = " warning" if percent < 40 else (" danger" if percent < 20 else "")

        st.markdown(f"""
        <div class="result-card">
            <div class="progress-container">
                <div class="progress-label">
                    <span>{disease.upper()}</span>
                    <span class="percent">{percent:.1f}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill{bar_class}" style="width: {percent}%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Recommendation
    recommendation = _get_recommendation(class_names[top_idx], animal)
    st.markdown(f"""
    <div class="action-box">
        <h3 style="color: {accent_color}; margin: 0;">⚡ RECOMMENDATION</h3>
        <p style="margin-top: 0.5rem;">{recommendation}</p>
    </div>
    """, unsafe_allow_html=True)

    # Scan deduction
    if st.session_state.get("user"):
        try:
            from app.utils.supabase_utils import decrement_scan
            decrement_scan(st.session_state.user.id)
            st.success("Scan deducted.")
        except:
            pass

# ---------- Helper ----------
def _get_recommendation(disease, animal):
    if animal == "cattle":
        recs = {
            "Foot‑and‑Mouth Disease": "Isolate immediately. Contact veterinarian. Vaccinate herd. Disinfect all equipment.",
            "Healthy": "Animal appears healthy. Continue regular check‑ups and vaccination schedule.",
            "Lumpy Skin Disease": "Isolate affected cattle. Apply insecticide to control flies. Vaccinate remaining herd."
        }
    else:
        recs = {
            "Coccidiosis": "Administer anticoccidial drugs. Improve litter management. Provide clean water.",
            "Healthy": "Bird appears healthy. Maintain biosecurity protocols.",
            "Newcastle Disease": "Isolate immediately. This is a notifiable disease. Contact veterinary authorities urgently.",
            "Salmonella": "Administer antibiotics as prescribed. Improve sanitation. Isolate affected birds."
        }
    return recs.get(disease, "Consult a veterinarian for proper diagnosis and treatment plan.")
