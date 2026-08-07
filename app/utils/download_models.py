import os, gdown, streamlit as st

MODEL_LINKS = {
    "poultry": "https://drive.google.com/uc?id=1Ms0aWA83m5eAaOCXO4nR2I_3oq5sSbUi",
    "cattle":  "https://drive.google.com/uc?id=1cV84OR1pvWzU_KQtR9Wrq2KC6etVvmHh",
    "pests_102class": "https://drive.google.com/uc?id=1XSmuhteSwdpbBIkzGErlH_1zWPG1kerk",
    "soil_11class": "https://drive.google.com/uc?id=1to0HP_LaM61MDqjKFObJYjueiVC__ypt",
    "millet_3class": "",
    "maize": "",
    "rice_11class": "",
    "soybean_14class": "",
    "pepper_13class": "",
    "cabbage_8class": "",
}

def ensure_model(model_key):
    """Download the model file if it is not already present."""
    checkpoint_dir = f"checkpoints/{model_key}"
    checkpoint_path = os.path.join(checkpoint_dir, "best_model.pt")
    if not os.path.exists(checkpoint_path):
        url = MODEL_LINKS.get(model_key)
        if not url:
            return None
        os.makedirs(checkpoint_dir, exist_ok=True)
        with st.spinner(f"Downloading {model_key} model (one‑time) …"):
            try:
                gdown.download(url, checkpoint_path, quiet=False)
            except Exception as e:
                st.error(f"Download failed for {model_key}: {e}")
                return None
    return checkpoint_path
