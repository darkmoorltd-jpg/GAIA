import os, requests, streamlit as st

# GitHub Releases — your actual filenames
BASE = "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0"

MODEL_LINKS = {
    "poultry": f"{BASE}/poultry_best_model.pt",
    "cattle":  f"{BASE}/cattle_best_model.pt",
    "pests_102class": f"{BASE}/pests_102class_best_model.pt",
    "soil_11class": f"{BASE}/soil_11class_best_model.pt",
}

def ensure_model(model_key):
    checkpoint_dir = f"models/{model_key}"
    checkpoint_path = os.path.join(checkpoint_dir, "best_model.pt")
    
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
