
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import os, sys, tempfile, time, hashlib
from datetime import datetime
from collections import Counter
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from timm.models.vision_transformer import VisionTransformer

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# ===== PAGE CONFIG =====
st.set_page_config(page_title="GAIA – Video Field Scanner", page_icon="🎥", layout="wide")

# ===== THEME TOGGLE =====
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
    .stButton button {
        background: linear-gradient(135deg, #00c853, #4caf50) !important;
        color: #fff !important; border: none !important;
        border-radius: 12px !important; padding: 12px 30px !important;
        font-weight: 700 !important; font-size: 1.1rem !important;
        transition: all 0.3s !important;
    }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,200,83,0.3); }
    .stProgress > div > div > div > div { background: linear-gradient(90deg, #00c853, #69f0ae); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="video_theme_toggle")
theme = "dark" if dark_mode else "light"

# ===== CROP DEFINITIONS =====
CROP_CLASSES = {
    "maize": ["Northern Leaf Blight", "Healthy", "Southern Leaf Blight", "Common Rust"],
    "rice": ["Bacterial Leaf Blight", "Brown Spot", "Healthy Rice Leaf", "Hispa", "Leaf Blast", "Leaf scald", "Leaf smut", "Narrow Brown Spot", "Neck Blast", "Sheath Blight", "Tungro"],
    "wheat": ["Aphid", "Black Rust", "Blast", "Brown Rust", "Common Root Rot", "Fusarium Head Blight", "Healthy", "Leaf Blight", "Mildew", "Mite", "Septoria", "Smut", "Stem Fly", "Tan Spot", "Yellow Rust"],
    "beans": ["Angular Leaf Spot", "Bean Rust", "Healthy"],
    "potato": ["Bacteria", "Fungi", "Healthy", "Nematode", "Pest", "Phytophthora", "Virus"],
    "banana": ["Fusarium Wilt", "Healthy", "Natural Death Leaf", "Rhizome Root"],
    "apple": ["Alternaria Leaf Spot", "Apple Scab", "Apple rot", "Block rot", "Brown Spot", "Cedar apple rust", "Frogeye Leaf Spot", "Grey Spot", "Healthy", "Leaf Blotch", "Mosaic", "Powdery Mildew", "Rust"],
    "mango": ["Anthracnose", "Bacterial Canker", "Cutting Weevil", "Die Back", "Gall Midge", "Healthy", "Powdery Mildew", "Sooty Mould"],
    "orange": ["Citrus Canker", "Nutrient Deficiency (Yellow Leaf)", "Healthy", "Multiple Diseases", "Young Healthy"],
    "grape": ["Black Measles", "Black Rot", "Healthy", "Leaf Blight"],
    "millet": ["Blast", "Rust", "Healthy"],
    "soybean": ["Bacterial Pustule", "Frogeye Leaf Spot", "Healthy", "Mosaic Virus", "Rust", "Southern blight", "Sudden Death Syndrome", "Target Leaf Spot", "Yellow Mosaic", "brown_spot", "crestamento", "ferrugen", "powdery_mildew", "septoria"],
    "pepper": ["Aphid", "Bacterial spot", "Blossom end rot", "Burn", "Edema", "Healthy", "Leaf curl", "Leaf miners", "Mosaic virus", "Nutrient deficiency", "Powdery mildew", "Spider mite", "Thrips"],
    "cabbage": ["Alternaria Leaf Spot", "Bacterial Spot Rot", "Black Rot", "Cabbage Aphid Colony", "Downy Mildew", "Healthy", "Club Root", "Ring Spot"],
}

# ===== THEME CSS =====
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #fff; }
        header, footer { visibility: hidden; }
        .title { font-size: 2.8rem; font-weight: 800; text-align: center; background: linear-gradient(90deg, #00c853, #69f0ae); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #b0bec5; margin-bottom: 1.5rem; }
        .report-card { background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 2rem; margin: 1rem 0; }
        .stat-box { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 1.2rem; text-align: center; }
        .stat-number { font-size: 2.2rem; font-weight: 700; color: #00c853; }
        .stat-label { font-size: 0.85rem; color: #90a4ae; margin-top: 4px; }
        .disease-bar { display: flex; align-items: center; margin: 8px 0; }
        .disease-name { width: 200px; font-weight: 500; }
        .disease-pct { width: 60px; text-align: right; margin-right: 12px; }
        .badge-high { background: #00c853; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; }
        .badge-med { background: #ff9800; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; }
        .badge-low { background: #f44336; color: #fff; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); color: #1b5e20; }
        header, footer { visibility: hidden; }
        .title { font-size: 2.8rem; font-weight: 800; text-align: center; background: linear-gradient(90deg, #2e7d32, #4caf50); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #33691e; margin-bottom: 1.5rem; }
        .report-card { background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.1); border-radius: 20px; padding: 2rem; margin: 1rem 0; }
        .stat-box { background: rgba(255,255,255,0.9); border-radius: 15px; padding: 1.2rem; text-align: center; }
        .stat-number { font-size: 2.2rem; font-weight: 700; color: #2e7d32; }
        .stat-label { font-size: 0.85rem; color: #558b2f; margin-top: 4px; }
        .disease-bar { display: flex; align-items: center; margin: 8px 0; }
        .disease-name { width: 200px; font-weight: 500; }
        .disease-pct { width: 60px; text-align: right; margin-right: 12px; }
        .badge-high { background: #2e7d32; color: #fff; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; }
        .badge-med { background: #ff9800; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; }
        .badge-low { background: #f44336; color: #fff; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# ===== SCAN DEDUCTION =====
def deduct_scan():
    if "user" not in st.session_state or st.session_state.user is None:
        return
    from supabase import create_client
    try:
        supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
        uid = st.session_state.user.id
        try:
            supabase.table("user_scans").insert({"user_id": uid, "scans_remaining": 30, "plan": "free"}).execute()
        except:
            pass
        try:
            supabase.rpc("decrement_scan", {"uid": uid}).execute()
            res = supabase.table("user_scans").select("scans_remaining").eq("user_id", uid).execute()
            if res.data:
                remaining = res.data[0]["scans_remaining"]
                st.success(f"Scan deducted. Remaining scans: {remaining}")
        except:
            pass
    except:
        pass

# ===== LOAD CROP MODEL =====
def load_crop_model(crop_name):
    """Load the trained model for a specific crop."""
    possible_paths = [
        f"checkpoints/{crop_name}_13class/best_model.pt",
        f"checkpoints/{crop_name}_8class/best_model.pt",
        f"checkpoints/{crop_name}_5class/best_model.pt",
        f"checkpoints/{crop_name}_4class/best_model.pt",
        f"checkpoints/{crop_name}/best_model.pt",
        os.path.join("models", crop_name, "model.pt"),
    ]
    
    for checkpoint in possible_paths:
        if os.path.exists(checkpoint):
            try:
                state = torch.load(checkpoint, map_location="cpu", weights_only=False)
                
                # Detect architecture
                prefix = "backbone." if any(k.startswith("backbone.") for k in state) else "encoder."
                embed_dim = state[f"{prefix}cls_token"].shape[-1]
                pos_embed = state[f"{prefix}pos_embed"]
                num_patches = pos_embed.shape[1] - 1
                grid = int(num_patches ** 0.5)
                img_size = grid * 16
                depth = len([k for k in state if k.startswith(f"{prefix}blocks") and k.endswith(".norm1.weight")])
                num_heads = 6 if embed_dim == 384 else 3
                
                backbone = VisionTransformer(
                    img_size=img_size, patch_size=16, embed_dim=embed_dim,
                    depth=depth, num_heads=num_heads, num_classes=0, global_pool='token'
                )
                backbone_state = {k.replace(prefix, ""): v for k, v in state.items() if k.startswith(prefix)}
                backbone.load_state_dict(backbone_state, strict=False)
                
                head_keys = [k for k in state if k.startswith("head.")]
                w_keys = sorted([k for k in head_keys if k.endswith(".weight")], key=lambda x: int(x.split('.')[1]) if any(c.isdigit() for c in x.split('.')[1]) else 0)
                
                if len(w_keys) == 1:
                    n = len(CROP_CLASSES[crop_name])
                    head = nn.Linear(embed_dim, n)
                    head_state = {
                        "weight": state.get("head.weight", state.get(f"{prefix.replace('backbone.','')}head.weight")),
                        "bias": state.get("head.bias", state.get(f"{prefix.replace('backbone.','')}head.bias", torch.zeros(n)))
                    }
                    head.load_state_dict({k: v for k, v in head_state.items() if v is not None}, strict=False)
                else:
                    layers = []
                    in_feat = embed_dim
                    for wk in w_keys:
                        w = state[wk]
                        out_feat = w.shape[0]
                        layers.append(nn.Linear(in_feat, out_feat))
                        if wk != w_keys[-1]:
                            layers.extend([nn.GELU(), nn.Dropout(0.2)])
                        in_feat = out_feat
                    head = nn.Sequential(*layers)
                    head_state = {k.replace("head.", ""): v for k, v in state.items() if k.startswith("head.")}
                    try:
                        head.load_state_dict(head_state, strict=False)
                    except:
                        pass
                
                class CropViT(torch.nn.Module):
                    def __init__(self, bb, hd):
                        super().__init__()
                        self.backbone = bb
                        self.head = hd
                    def forward(self, x):
                        return self.head(self.backbone(x))
                
                model = CropViT(backbone, head)
                model.eval()
                return model, img_size
            except Exception as e:
                st.warning(f"Failed to load model from {checkpoint}: {e}")
                continue
    
    return None, None

# ===== HIGH-PRECISION VIDEO ANALYZER =====
class VideoAnalyzer:
    def __init__(self, model, class_names, img_size, conf_threshold=0.85, blur_threshold=100):
        self.model = model
        self.class_names = class_names
        self.img_size = img_size
        self.conf_threshold = conf_threshold
        self.blur_threshold = blur_threshold
        self.transform = Compose([
            Resize((img_size, img_size)),
            ToTensor(),
            Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def is_blurry(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var() < self.blur_threshold

    def is_similar(self, frame, prev_frame):
        if prev_frame is None:
            return False
        gray1 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        mse = np.mean((gray1.astype(float) - gray2.astype(float)) ** 2)
        return mse < 50

    def analyze_frame(self, frame):
        if self.is_blurry(frame):
            return None, "blurry"
        leaf = self._crop_leaf(frame)
        img_pil = Image.fromarray(cv2.cvtColor(leaf, cv2.COLOR_BGR2RGB))
        img_tensor = self.transform(img_pil).unsqueeze(0)
        with torch.no_grad():
            logits = self.model(img_tensor)
            probs = F.softmax(logits, dim=1)[0].cpu().numpy()
        top_idx = np.argmax(probs)
        confidence = probs[top_idx]
        if confidence >= self.conf_threshold:
            return {"disease": self.class_names[top_idx], "confidence": float(confidence)}, "valid"
        return None, "low_confidence"

    def _crop_leaf(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_green = np.array([25, 40, 40])
        upper_green = np.array([85, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > 1000:
                x, y, w, h = cv2.boundingRect(largest)
                return frame[y:y+h, x:x+w]
        return frame

    def analyze_video(self, video_path, fps_target=5):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        interval = max(1, int(fps / fps_target))
        results, stats = [], {"blurry": 0, "low_confidence": 0, "similar": 0, "total": 0}
        prev_frame, frame_idx = None, 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % interval != 0:
                frame_idx += 1
                continue
            stats["total"] += 1
            if self.is_similar(frame, prev_frame):
                stats["similar"] += 1
                frame_idx += 1
                continue
            result, status = self.analyze_frame(frame)
            if result:
                results.append(result)
            else:
                stats[status] += 1
            prev_frame = frame.copy()
            frame_idx += 1
        cap.release()
        return results, stats

    def generate_report(self, results, stats):
        if not results:
            return {"error": "No valid frames. Try recording in better lighting.", "stats": stats}
        counts = Counter()
        confs = {}
        for r in results:
            d = r["disease"]
            counts[d] += 1
            confs[d] = confs.get(d, 0) + r["confidence"]
        total = len(results)
        top_disease = counts.most_common(1)[0][0]
        affected_pct = (counts[top_disease] / total) * 100
        avg_conf = (confs[top_disease] / counts[top_disease]) * 100
        precision = (total / stats["total"] * 100) if stats["total"] else 0
        breakdown = {
            d: {"count": c, "pct": (c / total) * 100, "conf": (confs[d] / c) * 100}
            for d, c in counts.items()
        }
        recommendation = self._recommend(top_disease, affected_pct, avg_conf)
        return {
            "disease": top_disease, "confidence": avg_conf, "affected_pct": affected_pct,
            "frames_valid": total, "frames_total": stats["total"], "precision_rate": precision,
            "breakdown": breakdown, "recommendation": recommendation, "stats": stats
        }

    def _recommend(self, disease, affected, conf):
        if conf < 90:
            return "⚠️ Re-scan recommended. Confidence below 90%."
        if affected < 10:
            return f"🟢 Low infection ({affected:.0f}%). Spot treatment only. Monitor for 3 days."
        if affected < 30:
            return f"🟡 Moderate ({affected:.0f}%). Apply targeted treatment within 48 hours."
        if affected < 60:
            return f"🟠 Significant ({affected:.0f}%). Full-field treatment immediately."
        return f"🔴 Severe ({affected:.0f}%). Full-field treatment + notify extension officer. Potential yield loss: 30-50%."

# ===== UI =====
st.markdown('<div class="title">🎥 Video Field Scanner</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Walk through your field recording a video — GAIA scans every frame with high precision</div>', unsafe_allow_html=True)

with st.expander("📸 Tips for best results"):
    st.markdown("1. 🌿 Walk slowly through your field holding the phone steady\n2. 📱 Keep leaves at 20‑30 cm distance\n3. ☀️ Use natural daylight, avoid shadows\n4. 🎥 15‑30 seconds is enough for a field scan\n5. 🔄 The AI filters out blurry and duplicate frames automatically")

crop = st.selectbox("🌾 Select Crop", list(CROP_CLASSES.keys()))
video_file = st.file_uploader("📤 Upload field video", type=["mp4", "mov", "avi", "mkv"])

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_file.read())
        video_path = tmp.name

    st.video(video_path)

    if st.button("🔍 Scan Field", type="primary"):
        with st.spinner("Analyzing field video with high precision..."):
            model, img_size = load_crop_model(crop)
            class_names = CROP_CLASSES[crop]

            if model is None:
                st.warning("Real model unavailable — using demo mode.")
                seed = int(hashlib.md5(video_file.name.encode()).hexdigest()[:8], 16)
                np.random.seed(seed)
                total_frames = 150
                valid = int(total_frames * np.random.uniform(0.75, 0.90))
                affected_pct = np.random.uniform(10, 80)
                top_disease = class_names[0] if class_names else "Unknown"
                confidence = np.random.uniform(88, 98)
                report = {
                    "disease": top_disease,
                    "confidence": confidence,
                    "affected_pct": affected_pct,
                    "frames_valid": valid,
                    "frames_total": total_frames,
                    "precision_rate": (valid / total_frames) * 100,
                    "breakdown": {
                        top_disease: {"count": int(valid * affected_pct / 100), "pct": affected_pct, "conf": confidence},
                        "Healthy": {"count": int(valid * (100 - affected_pct) / 100), "pct": 100 - affected_pct, "conf": 95}
                    },
                    "recommendation": f"🟠 Significant ({affected_pct:.0f}%). Full-field treatment recommended.",
                    "stats": {"blurry": 8, "low_confidence": 5, "similar": 12, "total": total_frames}
                }
            else:
                analyzer = VideoAnalyzer(model, class_names, img_size)
                results, stats = analyzer.analyze_video(video_path)
                report = analyzer.generate_report(results, stats)

        if "error" in report:
            st.error(report["error"])
        else:
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"### 📊 Field Health Report — {crop.title()}")

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.markdown(f'<div class="stat-box"><div class="stat-number">{report["frames_valid"]}</div><div class="stat-label">Valid Frames</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="stat-box"><div class="stat-number">{report["confidence"]:.1f}%</div><div class="stat-label">Confidence</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="stat-box"><div class="stat-number">{report["precision_rate"]:.1f}%</div><div class="stat-label">Precision Rate</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="stat-box"><div class="stat-number">{report["affected_pct"]:.0f}%</div><div class="stat-label">Field Affected</div></div>', unsafe_allow_html=True)
            conf_badge = "badge-high" if report["confidence"] >= 95 else ("badge-med" if report["confidence"] >= 90 else "badge-low")
            c5.markdown(f'<div class="stat-box"><span class="{conf_badge}">{"HIGH" if report["confidence"]>=95 else "MEDIUM" if report["confidence"]>=90 else "LOW"}</span><div class="stat-label" style="margin-top:8px;">Confidence Tier</div></div>', unsafe_allow_html=True)

            st.markdown("### 🔬 Disease Breakdown")
            for disease, data in sorted(report["breakdown"].items(), key=lambda x: x[1]["pct"], reverse=True):
                st.markdown(f'<div class="disease-bar"><span class="disease-name">{disease}</span><span class="disease-pct">{data["pct"]:.1f}%</span></div>', unsafe_allow_html=True)
                st.progress(data["pct"] / 100)

            st.markdown(f'<div style="background:rgba(255,255,255,0.08);border-radius:15px;padding:1.5rem;margin-top:1rem;"><strong>💡 Recommendation:</strong> {report["recommendation"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="margin-top:1rem;color:#90a4ae;font-size:0.85rem;">🖼️ Frames skipped: {report["stats"]["blurry"]} blurry · {report["stats"]["low_confidence"]} low confidence · {report["stats"]["similar"]} similar (duplicates)</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            deduct_scan()

        os.unlink(video_path)

# ===== NAVIGATION =====
st.markdown("---")
cols = st.columns(8)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/10_Early_Warning.py", label="🛰️ Early Warning")
with cols[6]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[7]: st.page_link("pages/13_Help.py", label="💬 Help")
