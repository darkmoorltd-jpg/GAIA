import streamlit as st
from PIL import Image
import numpy as np
import torch
import torch.nn.functional as F
import sys, os

# Add project root to path so we can import src modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.models.gaia_model import GAIAModel
from src.utils.viz import grad_cam

# ---------- 1. Page config ----------
st.set_page_config(page_title="GAIA – Diagnose", page_icon="🌿")
st.title("Diagnose Crop Disease")
st.markdown("Select a crop and upload a leaf photo to get an instant AI diagnosis.")

# ---------- 2. Crop selection ----------
crop = st.selectbox("Select crop", [
    "cassava",
    "maize",
    "tomato",
    "rice",
    # Add more crops here as you train them
])

# ---------- 3. Helper: load model (cached) ----------
@st.cache_resource
def load_model(crop_name):
    """Load the best checkpoint for the selected crop."""
    checkpoint_path = f"checkpoints/{crop_name}/best_model.pt"
    ckpt_path = f"checkpoints/{crop_name}/best-*.ckpt"
    
    # Try .pt first (our exported state dict)
    if os.path.exists(checkpoint_path):
        import yaml
        with open(f"configs/{crop_name}.yaml") as f:
            cfg = yaml.safe_load(f)
        model = GAIAModel(num_classes=cfg["num_classes"])
        model.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))
        model.eval()
        return model
    
    # Fallback: try Lightning checkpoint (if you saved that way)
    if os.path.exists(ckpt_path):
        model = GAIAModel.load_from_checkpoint(ckpt_path)
        model.eval()
        return model
    
    raise FileNotFoundError(
        f"No trained model found for {crop_name}. "
        f"Place it at checkpoints/{crop_name}/best_model.pt"
    )

@st.cache_data
def get_class_names(crop_name):
    """Return list of disease names for the crop."""
    import yaml
    with open(f"configs/{crop_name}.yaml") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("class_names", [str(i) for i in range(cfg["num_classes"])])

# ---------- 4. Image upload ----------
uploaded_file = st.file_uploader(
    "Choose a leaf image...",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    # Display image
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded leaf", use_column_width=True)
    st.write("Analysing…")
    
    # Load model and class names
    model = load_model(crop)
    class_names = get_class_names(crop)
    
    # Preprocess: grayscale, resize to 224x224, normalize
    gray = image.convert("L")  # grayscale
    gray_resized = gray.resize((224, 224))
    img_array = np.array(gray_resized, dtype=np.float32) / 255.0
    img_tensor = torch.from_numpy(img_array).unsqueeze(0).unsqueeze(0)  # (1,1,224,224)
    
    # ---------- 5. Inference ----------
    with torch.no_grad():
        logits = model(img_tensor)
        probs = F.softmax(logits, dim=1)[0]
    
    # Show top‑3 predictions
    top_probs, top_indices = torch.topk(probs, min(3, len(class_names)))
    
    st.subheader("Predictions")
    for i, idx in enumerate(top_indices):
        disease = class_names[idx]
        percent = top_probs[i] * 100
        st.write(f"**{disease}**: {percent:.1f}%")
    
    # ---------- 6. Grad‑CAM heatmap ----------
    try:
        heatmap = grad_cam(model, img_tensor)
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.imshow(gray_resized, cmap='gray')
        ax.imshow(heatmap, alpha=0.5, cmap='jet')
        ax.axis('off')
        ax.set_title("Grad‑CAM: What the AI focused on")
        st.pyplot(fig)
    except Exception as e:
        st.warning(f"Grad‑CAM visualisation unavailable: {e}")