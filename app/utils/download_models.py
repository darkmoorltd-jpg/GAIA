import os, requests, streamlit as st

# GitHub Releases — your actual filenames
BASE = "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v2.0-gaialens"

MODEL_LINKS = {
    "poultry": f"{BASE}/poultry_best_model.pt",
    "cattle":  f"{BASE}/cattle_best_model.pt",
    "pests_102class": f"{BASE}/pests_102class_best_model.pt",
    "soil_11class": f"{BASE}/soil_11class_best_model.pt",
    "maize": f"{BASE}/gaia_maize_4class.pt",
    "millet_3class": f"{BASE}/gaia_millet_3class.pt",
    "rice_10class": f"{BASE}/gaia_rice_10class_384px.pt",
}


# GaiaLens ONNX models (from GitHub Releases v2.0-gaialens)
GAIA_LENS_MODELS = {
    "gaia_crop.onnx": f"{BASE}/gaia_crop.onnx",
    "gaia_crop.onnx.data": f"{BASE}/gaia_crop.onnx.data",
    "gaia_pest.onnx": f"{BASE}/gaia_pest.onnx",
    "gaia_pest.onnx.data": f"{BASE}/gaia_pest.onnx.data",
    "gaia_soil.onnx": f"{BASE}/gaia_soil.onnx",
    "gaia_soil.onnx.data": f"{BASE}/gaia_soil.onnx.data",
    "gaia_livestock.onnx": f"{BASE}/gaia_livestock.onnx",
    "gaia_livestock.onnx.data": f"{BASE}/gaia_livestock.onnx.data",
    "yolov8_detector.onnx": f"{BASE}/yolov8_detector.onnx",
}

def ensure_gaialens_model(filename):
    """Download a GaiaLens ONNX file if missing."""
    import os, requests
    os.makedirs("onnx", exist_ok=True)
    dest = os.path.join("onnx", filename)
    if not os.path.exists(dest) or os.path.getsize(dest) < 1000:
        url = GAIA_LENS_MODELS.get(filename)
        if url:
            print(f"⬇️ Downloading {filename}...")
            r = requests.get(url, stream=True, timeout=300)
            if r.status_code == 200:
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(32768):
                        f.write(chunk)
    return dest if os.path.exists(dest) else None


def ensure_model(model_key):
    checkpoint_dir = f"models/{model_key}"
    checkpoint_path = os.path.join(checkpoint_dir, "model.pt")
    
    # Check if file exists AND is valid (not corrupted/empty)
    file_exists = os.path.exists(checkpoint_path)
    file_valid = file_exists and os.path.getsize(checkpoint_path) > 10000  # > 10KB
    
    if not file_valid:
        # Delete corrupted file if it exists
        if file_exists:
            os.remove(checkpoint_path)
        
        url = MODEL_LINKS.get(model_key)
        if not url:
            st.warning(f"No download URL for {model_key}")
            return None
        
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        with st.spinner(f"Downloading {model_key} model (one‑time) …"):
            try:
                r = requests.get(url, stream=True, timeout=300, allow_redirects=True)
                r.raise_for_status()
                
                total_size = 0
                with open(checkpoint_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=32768):
                        if chunk:
                            f.write(chunk)
                            total_size += len(chunk)
                
                size_mb = total_size / (1024*1024)
                if total_size < 10000:
                    os.remove(checkpoint_path)
                    st.error(f"Download failed — file too small ({total_size} bytes).")
                    return None
                
                st.success(f"Model ready: {size_mb:.1f} MB")
            except Exception as e:
                st.error(f"Download failed: {str(e)[:200]}")
                if os.path.exists(checkpoint_path):
                    os.remove(checkpoint_path)
                return None
    
    return checkpoint_path
