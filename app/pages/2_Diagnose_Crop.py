import streamlit as st
from PIL import Image
import numpy as np
import torch
import torch.nn.functional as F
import sys, os, yaml

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.models.gaia_model import GAIAModel
from src.models.pretrained_vit import PretrainedViTClassifier

# ---------- 1. Page config ----------
st.set_page_config(page_title="GAIA – Diagnose", page_icon="🌿")
st.title("Diagnose Crop Disease")
st.markdown("Select a crop and upload a leaf photo to get an instant AI diagnosis.")

# ---------- 2. Crop selection ----------
CROP_LIST = ["cassava", "maize", "tomato", "rice", "beans", "potato"]
crop = st.selectbox("Select crop", CROP_LIST)

# ---------- 3. Helpers ----------
@st.cache_resource
def load_model(crop_name):
    """Load the correct model for the crop based on its config."""
    checkpoint_path = f"checkpoints/{crop_name}/best_model.pt"
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(
            f"No model found at {checkpoint_path}. "
            f"Train and save it first."
        )

    with open(f"configs/{crop_name}.yaml") as f:
        cfg = yaml.safe_load(f)

    model_type = cfg.get("model_type", "tinyvit")
    num_classes = cfg["num_classes"]

    if model_type == "vit_pretrained":
        model = PretrainedViTClassifier(num_classes=num_classes)
    else:
        in_chans = cfg.get("in_channels", 1)
        model = GAIAModel(num_classes=num_classes, in_chans=in_chans)

    state_dict = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()
    return model, cfg

@st.cache_data
def get_config(crop_name):
    with open(f"configs/{crop_name}.yaml") as f:
        return yaml.safe_load(f)

# ---------- 4. Image upload ----------
uploaded_file = st.file_uploader("Choose a leaf image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded leaf", width=300)
    st.write("Analysing…")

    cfg = get_config(crop)
    class_names = cfg.get("class_names", [str(i) for i in range(cfg["num_classes"])])
    num_classes = cfg["num_classes"]
    model_type = cfg.get("model_type", "tinyvit")
    in_chans = cfg.get("in_channels", 1)

    model, _ = load_model(crop)

    # ---------- 5. Preprocess based on model type ----------
    if in_chans == 3:
        from torchvision.transforms import Compose, Resize, ToTensor, Normalize
        transform = Compose([
            Resize((224, 224)),
            ToTensor(),
            Normalize(mean=[0.485, 0.456, 0.406],
                      std=[0.229, 0.224, 0.225])
        ])
        img_tensor = transform(image).unsqueeze(0)
    else:
        gray = image.convert("L").resize((224, 224))
        img_array = np.array(gray, dtype=np.float32) / 255.0
        img_tensor = torch.from_numpy(img_array).unsqueeze(0).unsqueeze(0)

    # ---------- 6. Inference ----------
    with torch.no_grad():
        logits = model(img_tensor)
        probs = F.softmax(logits, dim=1)[0]

    # ---------- 7. Show ALL predictions (not just top‑3) ----------
    st.subheader(f"Predictions — {crop.title()} ({num_classes} diseases)")

    # Sort by probability (highest first)
    sorted_probs, sorted_indices = torch.sort(probs, descending=True)

    for idx, prob in zip(sorted_indices, sorted_probs):
        disease = class_names[idx]
        percent = prob.item() * 100
        st.write(f"**{disease}**: {percent:.1f}%")
        # Progress bar for visual comparison
        st.progress(float(prob))

    # ---------- 8. Grad‑CAM (TinyViT only) ----------
    if model_type == "vit_pretrained":
        st.info("Grad‑CAM visualisation is not yet available for the pretrained ViT model.")
    else:
        try:
            from src.utils.viz import grad_cam
            heatmap = grad_cam(model, img_tensor)
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.imshow(image.resize((224, 224)).convert("L"), cmap='gray')
            ax.imshow(heatmap, alpha=0.5, cmap='jet')
            ax.axis('off')
            ax.set_title("Grad‑CAM: What the AI focused on")
            st.pyplot(fig)
        except Exception as e:
            st.warning(f"Grad‑CAM unavailable: {e}")