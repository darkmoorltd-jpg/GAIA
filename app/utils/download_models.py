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
    
    if not os.path.exists(checkpoint_path):
        url = MODEL_PATHS.get(model_key)
        if not url:
            return None
        os.makedirs(checkpoint_dir, exist_ok=True)
        with st.spinner(f"Downloading {model_key} model (one‑time) …"):
            try:
                r = requests.get(url, stream=True, timeout=600)
                if r.status_code == 200:
                    total_size = int(r.headers.get('content-length', 0))
                    downloaded = 0
                    with open(checkpoint_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=65536):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                    
                    # Validate the file is big enough (at least 500KB)
                    actual_size = os.path.getsize(checkpoint_path)
                    if actual_size < 500000:
                        os.remove(checkpoint_path)
                        st.error(f"Download failed: file too small ({actual_size} bytes)")
                        return None
                    
                    st.success(f"Model downloaded ({actual_size/1024/1024:.0f} MB)")
                else:
                    st.error(f"Download failed: HTTP {r.status_code}")
                    return None
            except Exception as e:
                st.error(f"Download failed: {e}")
                if os.path.exists(checkpoint_path):
                    os.remove(checkpoint_path)
                return None
    return checkpoint_path
