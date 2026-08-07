import os, requests, streamlit as st

RELEASE = "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0"

MODEL_PATHS = {
    "poultry": f"{RELEASE}/poultry_best_model.pt",
    "cattle": f"{RELEASE}/cattle_best_model.pt",
    "pests_102class": f"{RELEASE}/pests_102class_best_model.pt",
    "soil_11class": f"{RELEASE}/soil_11class_best_model.pt",
    "millet_3class": "",
    "maize": "",
    "rice_11class": "",
    "soybean_14class": "",
    "pepper_13class": "",
    "cabbage_8class": "",
}

def ensure_model(model_key):
    checkpoint_dir = f"checkpoints/{model_key}"
    checkpoint_path = os.path.join(checkpoint_dir, "best_model.pt")
    
    # If file exists but is too small, delete it (corrupted download)
    if os.path.exists(checkpoint_path):
        size = os.path.getsize(checkpoint_path)
        if size < 100000:  # Less than 100KB = corrupted
            os.remove(checkpoint_path)
    
    if not os.path.exists(checkpoint_path):
        url = MODEL_PATHS.get(model_key)
        if not url:
            return None
        os.makedirs(checkpoint_dir, exist_ok=True)
        with st.spinner(f"Downloading {model_key} model (one‑time) …"):
            try:
                r = requests.get(url, stream=True, timeout=600)
                if r.status_code == 200:
                    with open(checkpoint_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=65536):
                            if chunk:
                                f.write(chunk)
                    
                    actual_size = os.path.getsize(checkpoint_path)
                    if actual_size < 500000:
                        os.remove(checkpoint_path)
                        st.error(f"Download failed: file too small ({actual_size} bytes). Retrying...")
                        return None
                else:
                    st.error(f"Download failed: HTTP {r.status_code}")
                    return None
            except Exception as e:
                st.error(f"Download failed: {e}")
                if os.path.exists(checkpoint_path):
                    os.remove(checkpoint_path)
                return None
    return checkpoint_path
