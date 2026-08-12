
import streamlit as st
from PIL import Image
import torch, torch.nn as nn, torch.nn.functional as F
import numpy as np
import os, sys, tempfile, subprocess, hashlib, json, time
from collections import Counter
from datetime import datetime
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("OpenCV not available — video pre‑check will use ffmpeg")
from timm.models.vision_transformer import VisionTransformer
from scipy import ndimage

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

# ===== CONSTANTS =====
MIN_VALID_FRAMES = 10
MIN_CONSENSUS_PCT = 0.60
DEFAULT_FPS = 5

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
        .badge-high { background: #00c853; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; }
        .badge-med { background: #ff9800; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; }
        .badge-low { background: #f44336; color: #fff; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; }
        .validation-pass { color: #00c853; }
        .validation-fail { color: #f44336; }
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
        .badge-high { background: #2e7d32; color: #fff; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; }
        .badge-med { background: #ff9800; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; }
        .badge-low { background: #f44336; color: #fff; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; }
        .validation-pass { color: #2e7d32; }
        .validation-fail { color: #c62828; }
    </style>
    """, unsafe_allow_html=True)

# ===== VIDEO PRE-CHECK =====
def pre_check_video(video_path):
    """Quick check: is this a crop field video?"""
    if not HAS_CV2:
        return True, "OpenCV unavailable — skipping pre‑check (ffmpeg will extract frames directly)"
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames < 30:
        cap.release()
        return False, "Video too short. Please record at least 10 seconds walking through your field."
    
    sample_indices = np.linspace(0, total_frames - 1, min(10, total_frames), dtype=int)
    green_scores = []
    
    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, np.array([25, 40, 40]), np.array([85, 255, 255]))
            green_scores.append(mask.mean())
    
    cap.release()
    avg_green = np.mean(green_scores) if green_scores else 0
    
    if avg_green < 8:
        return False, "This doesn't look like a crop field (< 8% green). Please record plants/leaves."
    return True, f"Video looks good — {avg_green:.0f}% green content detected."

# ===== FRAME EXTRACTION =====
def extract_frames_ffmpeg(video_path, output_dir, fps=DEFAULT_FPS):
    os.makedirs(output_dir, exist_ok=True)
    cmd = ["ffmpeg", "-i", video_path, "-vf", f"fps={fps}", "-q:v", "2",
           f"{output_dir}/frame_%06d.jpg", "-y", "-loglevel", "quiet"]
    subprocess.run(cmd, check=True, timeout=120)
    return sorted([os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.jpg')])

# ===== VALIDATION FUNCTIONS =====
def is_frame_blurry(image_path):
    img = Image.open(image_path).convert('L')
    arr = np.array(img, dtype=np.float64)
    laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
    from scipy import ndimage
    filtered = ndimage.convolve(arr, laplacian)
    return filtered.var() < 100

def validate_leaf_content(frame):
    """Check if frame actually contains a real leaf (not just green weeds/soil)."""
    if not HAS_CV2:
        return True, 0.5, "OpenCV unavailable — skipping leaf validation"
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
    green_pct = (mask > 0).sum() / mask.size
    
    if green_pct < 0.15 or green_pct > 0.80:
        return False, green_pct, "Green content outside 15-80% range"
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    texture = cv2.Laplacian(gray, cv2.CV_64F).var()
    if texture < 50:
        return False, green_pct, "Texture too smooth — not a real leaf"
    
    return True, green_pct, "Valid leaf detected"

def detect_lighting_condition(frame):
    if not HAS_CV2:
        return "optimal", 0.85
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    brightness = hsv[:,:,2].mean()
    if brightness < 60: return "low_light", 0.90
    elif brightness > 180: return "harsh_light", 0.88
    else: return "optimal", 0.85

# ===== MODEL LOADING =====
def load_crop_model(crop_name):
    possible_paths = [
        f"checkpoints/{crop_name}_13class/best_model.pt",
        f"checkpoints/{crop_name}_8class/best_model.pt",
        f"checkpoints/{crop_name}_5class/best_model.pt",
        f"checkpoints/{crop_name}_4class/best_model.pt",
        f"checkpoints/{crop_name}/best_model.pt",
    ]
    for checkpoint in possible_paths:
        if os.path.exists(checkpoint):
            try:
                state = torch.load(checkpoint, map_location="cpu", weights_only=False)
                prefix = "backbone." if any(k.startswith("backbone.") for k in state) else "encoder."
                embed_dim = state[f"{prefix}cls_token"].shape[-1]
                pos_embed = state[f"{prefix}pos_embed"]
                num_patches = pos_embed.shape[1] - 1
                grid = int(num_patches ** 0.5)
                img_size = grid * 16
                depth = len([k for k in state if k.startswith(f"{prefix}blocks") and k.endswith(".norm1.weight")])
                num_heads = 6 if embed_dim == 384 else 3
                
                backbone = VisionTransformer(img_size=img_size, patch_size=16, embed_dim=embed_dim,
                                             depth=depth, num_heads=num_heads, num_classes=0, global_pool='token')
                backbone_state = {k.replace(prefix, ""): v for k, v in state.items() if k.startswith(prefix)}
                backbone.load_state_dict(backbone_state, strict=False)
                
                n = len(CROP_CLASSES[crop_name])
                head = nn.Linear(embed_dim, n)
                head_state = {"weight": state.get("head.weight"), "bias": state.get("head.bias", torch.zeros(n))}
                if head_state["weight"] is not None:
                    head.load_state_dict({k: v for k, v in head_state.items() if v is not None}, strict=False)
                
                class CropViT(torch.nn.Module):
                    def __init__(self, bb, hd): super().__init__(); self.backbone = bb; self.head = hd
                    def forward(self, x): return self.head(self.backbone(x))
                
                model = CropViT(backbone, head); model.eval()
                return model, img_size
            except: continue
    return None, None

# ===== MAIN VIDEO ANALYSIS =====
def analyze_video(video_path, model, img_size, class_names, fps=DEFAULT_FPS):
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            frame_paths = extract_frames_ffmpeg(video_path, tmpdir, fps)
    except Exception as e:
        return None, f"FFmpeg extraction failed: {e}", None
    
    if not frame_paths:
        return None, "No frames extracted. Check the video file.", None
    
    transform = Compose([Resize((img_size, img_size)), ToTensor(),
                         Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])
    
    results = []
    validation_log = []
    stats = {"blurry": 0, "invalid_content": 0, "low_confidence": 0, "total": len(frame_paths)}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, fp in enumerate(frame_paths):
        progress_bar.progress((i + 1) / len(frame_paths))
        status_text.text(f"🔍 Analyzing frame {i+1} of {len(frame_paths)}...")
        
        try:
            if HAS_CV2:
                frame_bgr = cv2.imread(fp)
            else:
                frame_bgr = np.array(Image.open(fp).convert('RGB'))
                frame_bgr = frame_bgr[:, :, ::-1].copy()  # RGB to BGR
            if frame_bgr is None: continue
            
            # Layer 1: Blur check
            if is_frame_blurry(fp):
                stats["blurry"] += 1; validation_log.append(f"Frame {i+1}: ❌ Blurry"); continue
            
            # Layer 2: Content validation
            is_leaf, green_pct, msg = validate_leaf_content(frame_bgr)
            if not is_leaf:
                stats["invalid_content"] += 1
                validation_log.append(f"Frame {i+1}: ❌ {msg} ({green_pct*100:.0f}% green)"); continue
            
            # Layer 3: Lighting calibration
            light_condition, conf_threshold = detect_lighting_condition(frame_bgr)
            
            # Run model
            img_pil = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
            img_tensor = transform(img_pil).unsqueeze(0)
            
            with torch.no_grad():
                logits = model(img_tensor)
                probs = F.softmax(logits, dim=1)[0].cpu().numpy()
            
            top_idx = np.argmax(probs)
            confidence = float(probs[top_idx])
            
            if confidence >= conf_threshold:
                results.append({"disease": class_names[top_idx], "confidence": confidence})
                validation_log.append(f"Frame {i+1}: ✅ {class_names[top_idx]} ({confidence*100:.0f}%) [{light_condition}]")
            else:
                stats["low_confidence"] += 1
                validation_log.append(f"Frame {i+1}: ⚠️ Low confidence ({confidence*100:.0f}% < {conf_threshold*100:.0f}%)")
        except Exception as e:
            validation_log.append(f"Frame {i+1}: ❌ Error: {e}")
    
    progress_bar.empty(); status_text.empty()
    
    # Check minimum valid frames
    if len(results) < MIN_VALID_FRAMES:
        return None, f"Only {len(results)} valid frames (minimum {MIN_VALID_FRAMES} required). Record in better light.", validation_log
    
    # Consensus check
    counts = Counter(); confs = {}
    for r in results:
        d = r["disease"]; counts[d] += 1; confs[d] = confs.get(d, 0) + r["confidence"]
    
    total = len(results)
    top_disease, top_count = counts.most_common(1)[0]
    consensus_pct = top_count / total
    
    if consensus_pct < MIN_CONSENSUS_PCT:
        return None, f"No clear consensus. Top result '{top_disease}' only has {consensus_pct*100:.0f}% agreement (minimum {MIN_CONSENSUS_PCT*100:.0f}%). Re-scan.", validation_log
    
    affected_pct = (top_count / total) * 100
    avg_conf = (confs[top_disease] / top_count) * 100
    precision = (total / stats["total"] * 100) if stats["total"] else 0
    
    breakdown = {d: {"count": c, "pct": (c/total)*100, "conf": (confs[d]/c)*100} for d, c in counts.items()}
    recommendation = _recommend(top_disease, affected_pct, avg_conf, consensus_pct)
    
    report = {
        "disease": top_disease, "confidence": avg_conf, "affected_pct": affected_pct,
        "frames_valid": total, "frames_total": stats["total"], "precision_rate": precision,
        "consensus_pct": consensus_pct * 100, "breakdown": breakdown,
        "recommendation": recommendation, "stats": stats
    }
    
    return report, None, validation_log

def _recommend(disease, affected, conf, consensus):
    if consensus < 70: return "⚠️ Low consensus. Re‑scan recommended."
    if conf < 90: return "⚠️ Confidence below 90%. Re‑scan in better light."
    if affected < 10: return f"🟢 Low infection ({affected:.0f}%). Spot treatment only. Monitor for 3 days."
    if affected < 30: return f"🟡 Moderate ({affected:.0f}%). Treat within 48 hours."
    if affected < 60: return f"🟠 Significant ({affected:.0f}%). Full-field treatment NOW."
    return f"🔴 Severe ({affected:.0f}%). Full treatment + notify extension officer. Yield loss: 30-50%."

# ===== SCAN DEDUCTION =====
def deduct_scan():
    if "user" not in st.session_state or st.session_state.user is None: return
    from supabase import create_client
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    uid = st.session_state.user.id
    try: supabase.table("user_scans").insert({"user_id":uid,"scans_remaining":30,"plan":"free"}).execute()
    except: pass
    try: supabase.rpc("decrement_scan",{"uid":uid}).execute()
    except: pass

# ===== UI =====
st.markdown('<div class="title">🎥 Video Field Scanner</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Walk through your field recording a video — GAIA validates every frame with clinical precision</div>', unsafe_allow_html=True)

with st.expander("📸 Tips for best results", expanded=False):
    st.markdown("""
    1. 🌿 Walk **slowly** through your field
    2. 📱 Keep leaves at **20-30 cm** from the phone
    3. ☀️ Use **natural daylight** — avoid shadows
    4. 🎥 **15-30 seconds** is ideal
    5. 🔄 Walk in a **straight line** through the crop row
    6. ❌ Blurry frames are filtered automatically
    7. ✅ Only high‑confidence predictions count
    """)

crop = st.selectbox("🌾 Select Crop", list(CROP_CLASSES.keys()))
video_file = st.file_uploader("📤 Upload field video", type=["mp4", "mov", "avi", "mkv"])

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_file.read())
        video_path = tmp.name

    st.video(video_path)

    if st.button("🔍 Scan Field", type="primary"):
        # Step 1: Pre-check
        with st.spinner("🔍 Validating video content..."):
            is_valid, pre_check_msg = pre_check_video(video_path)
        
        if not is_valid:
            st.error(f"❌ {pre_check_msg}")
            st.info("Please record a video walking through your crop field showing leaves clearly.")
        else:
            st.success(f"✅ {pre_check_msg}")
            
            # Step 2: Load model
            with st.spinner("🧠 Loading crop model..."):
                model, img_size = load_crop_model(crop)
            
            if model is None:
                st.warning("⚠️ Real model unavailable — using demo mode.")
                class_names = CROP_CLASSES[crop]
                seed = int(hashlib.md5(video_file.name.encode()).hexdigest()[:8], 16)
                np.random.seed(seed)
                total_frames = 150
                valid = int(total_frames * np.random.uniform(0.75, 0.90))
                affected_pct = np.random.uniform(10, 80)
                top_disease = class_names[0] if class_names else "Unknown"
                confidence = np.random.uniform(88, 98)
                report = {
                    "disease": top_disease, "confidence": confidence, "affected_pct": affected_pct,
                    "frames_valid": valid, "frames_total": total_frames,
                    "precision_rate": (valid/total_frames)*100,
                    "consensus_pct": np.random.uniform(70, 95),
                    "breakdown": {
                        top_disease: {"count": int(valid*affected_pct/100), "pct": affected_pct, "conf": confidence},
                        "Healthy": {"count": int(valid*(100-affected_pct)/100), "pct": 100-affected_pct, "conf": 95}
                    },
                    "recommendation": f"🟠 Significant ({affected_pct:.0f}%). Full-field treatment recommended.",
                    "stats": {"blurry": 8, "invalid_content": 3, "low_confidence": 5, "total": total_frames}
                }
                validation_log = None
            else:
                # Step 3: Analyze
                class_names = CROP_CLASSES[crop]
                report, error, validation_log = analyze_video(video_path, model, img_size, class_names)
                
                if error:
                    st.error(f"❌ {error}")
                    if validation_log:
                        with st.expander("📋 Frame‑by‑Frame Validation Log"):
                            for log in validation_log:
                                st.write(log)
                    st.stop()
            
            # Step 4: Display Report
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"### 📊 Field Health Report — {crop.title()}")
            
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.markdown(f'<div class="stat-box"><div class="stat-number">{report["frames_valid"]}</div><div class="stat-label">Valid Frames</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="stat-box"><div class="stat-number">{report["confidence"]:.1f}%</div><div class="stat-label">Confidence</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="stat-box"><div class="stat-number">{report["precision_rate"]:.1f}%</div><div class="stat-label">Precision Rate</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="stat-box"><div class="stat-number">{report["consensus_pct"]:.0f}%</div><div class="stat-label">Consensus</div></div>', unsafe_allow_html=True)
            
            conf_badge = "badge-high" if report["confidence"] >= 95 else ("badge-med" if report["confidence"] >= 90 else "badge-low")
            c5.markdown(f'<div class="stat-box"><span class="{conf_badge}">{"HIGH" if report["confidence"]>=95 else "MEDIUM" if report["confidence"]>=90 else "LOW"}</span><div class="stat-label" style="margin-top:8px;">Confidence Tier</div></div>', unsafe_allow_html=True)
            
            st.markdown(f"### 🔬 Disease Breakdown")
            for disease, data in sorted(report["breakdown"].items(), key=lambda x: x[1]["pct"], reverse=True):
                st.markdown(f'<div style="display:flex;align-items:center;margin:8px 0;"><span style="width:180px;font-weight:500;">{disease}</span><span style="width:60px;text-align:right;margin-right:12px;">{data["pct"]:.1f}%</span></div>', unsafe_allow_html=True)
                st.progress(data["pct"] / 100)
            
            st.markdown(f'<div style="background:rgba(255,255,255,0.08);border-radius:15px;padding:1.5rem;margin-top:1rem;"><strong>💡 Recommendation:</strong> {report["recommendation"]}</div>', unsafe_allow_html=True)
            
            if validation_log:
                with st.expander("📋 Frame‑by‑Frame Validation Log"):
                    st.caption(f"✅ = Valid prediction | ❌ = Rejected | ⚠️ = Low confidence")
                    for log in validation_log:
                        st.write(log)
            
            st.markdown('</div>', unsafe_allow_html=True)
            deduct_scan()
        
        os.unlink(video_path)

# ===== NAVIGATION =====
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
