
import os, requests, streamlit as st
import torch

BASE = "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0"

MODEL_LINKS = {
    "poultry": f"{BASE}/poultry_best_model.pt",
    "cattle":  f"{BASE}/cattle_best_model.pt",
    "pests_102class": f"{BASE}/pests_102class_best_model.pt",
    "soil_11class": f"{BASE}/soil_11class_best_model.pt",
    "maize": f"{BASE}/gaia_maize_4class.pt",
    "millet_3class": f"{BASE}/gaia_millet_3class.pt",
    "rice_10class": f"{BASE}/gaia_rice_10class_384px.pt",
    "potato_lcmt": f"{BASE}/gaia_potato_lcmt.pt",
}

def is_valid_checkpoint(path):
    """Return True if the file is a valid PyTorch checkpoint."""
    if not os.path.exists(path) or os.path.getsize(path) < 10000:
        return False
    try:
        torch.load(path, map_location="cpu", weights_only=False)
        return True
    except Exception:
        return False

def download_file(url, destination):
    """Download file with progress to destination."""
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    r = requests.get(url, stream=True, timeout=600, allow_redirects=True)
    r.raise_for_status()
    total = 0
    with open(destination, "wb") as f:
        for chunk in r.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)
                total += len(chunk)
    return total

def ensure_model(model_key):
    """Download and return path to a valid model checkpoint."""
    checkpoint_dir = f"models/{model_key}"
    checkpoint_path = os.path.join(checkpoint_dir, "model.pt")

    # If file exists but is corrupt, remove it so we re-download
    if os.path.exists(checkpoint_path) and not is_valid_checkpoint(checkpoint_path):
        st.warning(f"Removing corrupted {model_key} model…")
        os.remove(checkpoint_path)

    if not os.path.exists(checkpoint_path):
        url = MODEL_LINKS.get(model_key)
        if not url:
            st.warning(f"No download URL for {model_key}")
            return None

        with st.spinner(f"Downloading {model_key} model (one‑time)…"):
            try:
                size = download_file(url, checkpoint_path)
                size_mb = size / (1024 * 1024)
                if not is_valid_checkpoint(checkpoint_path):
                    os.remove(checkpoint_path)
                    st.error(f"Downloaded {model_key} model is invalid.")
                    return None
                st.success(f"{model_key} model ready: {size_mb:.1f} MB")
            except Exception as e:
                st.error(f"Download failed: {str(e)[:200]}")
                if os.path.exists(checkpoint_path):
                    os.remove(checkpoint_path)
                return None

    return checkpoint_path
