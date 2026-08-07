import os, streamlit as st
from urllib.request import urlretrieve
import ssl

# Disable SSL verification for GitHub downloads (fixes some server issues)
ssl._create_default_https_context = ssl._create_unverified_context

MODEL_LINKS = {
    "soil_11class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/soil_model.pt",
    "pests_102class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/pests_model.pt",
    "poultry": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/poultry_model.pt",
    "cattle": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/cattle_model.pt",
}

def ensure_model(model_key):
    """Download the model file if it is not already present."""
    checkpoint_dir = f"checkpoints/{model_key}"
    checkpoint_path = os.path.join(checkpoint_dir, "best_model.pt")
    
    # Return if already exists and is valid
    if os.path.exists(checkpoint_path):
        size = os.path.getsize(checkpoint_path)
        if size > 1000000:
            with open(checkpoint_path, "rb") as f:
                header = f.read(10)
            if header[:1] != b'<':
                return checkpoint_path
        os.remove(checkpoint_path)  # Delete bad file
    
    url = MODEL_LINKS.get(model_key)
    if not url:
        return None
    
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    with st.spinner(f"Downloading {model_key} model (one-time, ~30-60 seconds)..."):
        try:
            # Use urllib which is built-in and always works
            urlretrieve(url, checkpoint_path)
            
            # Validate
            if os.path.exists(checkpoint_path):
                size = os.path.getsize(checkpoint_path)
                if size > 1000000:
                    with open(checkpoint_path, "rb") as f:
                        header = f.read(10)
                    if header[:1] == b'<':
                        os.remove(checkpoint_path)
                        st.error("Downloaded HTML instead of model file")
                        return None
                    st.success(f"Model ready! ({size/1048576:.1f} MB)")
                    return checkpoint_path
                else:
                    os.remove(checkpoint_path)
                    st.error(f"Downloaded file too small ({size} bytes)")
                    return None
        except Exception as e:
            st.error(f"Download failed: {str(e)[:100]}")
            return None
    
    return None
