import os, streamlit as st

# Direct download links from GitHub Releases (verified working)
MODEL_LINKS = {
    "soil_11class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/soil_model.pt",
    "pests_102class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/pests_model.pt",
    "poultry": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/poultry_model.pt",
    "cattle": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/cattle_model.pt",
}

def ensure_model(model_key):
    """Download the model file if it is not already present."""
    import subprocess, sys

    checkpoint_dir = f"checkpoints/{model_key}"
    checkpoint_path = os.path.join(checkpoint_dir, "best_model.pt")

    if os.path.exists(checkpoint_path):
        size = os.path.getsize(checkpoint_path)
        if size > 1000000:
            return checkpoint_path
        os.remove(checkpoint_path)

    url = MODEL_LINKS.get(model_key)
    if not url:
        return None

    os.makedirs(checkpoint_dir, exist_ok=True)

    with st.spinner(f"Downloading {model_key} model..."):
        try:
            # Use wget via subprocess - most reliable on Linux
            result = subprocess.run(
                ["wget", "-q", "-O", checkpoint_path, url],
                capture_output=True, text=True, timeout=300
            )

            if os.path.exists(checkpoint_path):
                size = os.path.getsize(checkpoint_path)
                if size > 1000000:
                    st.success(f"Model ready! ({size/1048576:.1f} MB)")
                    return checkpoint_path
                else:
                    os.remove(checkpoint_path)
                    st.error(f"Download failed (file too small: {size} bytes)")
                    return None
            else:
                st.error(f"wget failed: {result.stderr[:200]}")
                return None
        except Exception as e:
            st.error(f"Download error: {str(e)[:100]}")
            return None
