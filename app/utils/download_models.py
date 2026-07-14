
import os, gdown, streamlit as st

MODEL_LINKS = {
    "poultry": "https://drive.google.com/uc?id=1Ms0aWA83m5eAaOCXO4nR2I_3oq5sSbUi",
    "cattle":  "https://drive.google.com/uc?id=1cV84OR1pvWzU_KQtR9Wrq2KC6etVvmHh",
}

def ensure_model(animal):
    """Download the model file if it is not already present."""
    checkpoint_dir = f"checkpoints/{animal}"
    checkpoint_path = os.path.join(checkpoint_dir, "best_model.pt")
    if not os.path.exists(checkpoint_path):
        os.makedirs(checkpoint_dir, exist_ok=True)
        url = MODEL_LINKS.get(animal)
        if url:
            with st.spinner(f"Downloading {animal} model (one‑time) …"):
                gdown.download(url, checkpoint_path, quiet=False)
    return checkpoint_path
