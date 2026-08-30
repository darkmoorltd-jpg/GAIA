import os, requests, streamlit as st

# GitHub Releases — your actual filenames
BASE = "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0"

MODEL_LINKS = {
    # Livestock
    "poultry": f"{BASE}/poultry_best_model.pt",
    "cattle":  f"{BASE}/cattle_best_model.pt",
    
    # Pests
    "pests_102class": f"{BASE}/pests_102class_best_model.pt",
    
    # Soil
    "soil_11class": f"{BASE}/soil_11class_best_model.pt",
    
    # New crop models (Apple, Cassava, Coffee, Grape, Sugarcane, Tea)
    "apple": f"{BASE}/gaia_apple.pt",
    "cassava": f"{BASE}/gaia_cassava.pt",
    "coffee": f"{BASE}/gaia_coffee.pt",
    "grape": f"{BASE}/gaia_grape.pt",
    "sugarcane": f"{BASE}/gaia_sugarcane.pt",
    "tea": f"{BASE}/gaia_tea.pt",
    
    # Existing crop models
    "maize": f"{BASE}/gaia_maize_4class.pt",
    "millet_3class": f"{BASE}/gaia_millet_3class.pt",
    "rice_10class": f"{BASE}/gaia_rice_10class_384px.pt",
    "soybean": f"{BASE}/gaia_soybean_14class.pt",
    "pepper": f"{BASE}/gaia_pepper_13class.pt",
    "cabbage": f"{BASE}/gaia_cabbage_8class.pt",
}

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
