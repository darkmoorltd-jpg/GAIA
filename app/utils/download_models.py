import os, requests, streamlit as st

MODEL_LINKS = {
    "poultry": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/poultry_model.pt",
    "cattle":  "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/cattle_model.pt",
    "pests_102class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/pests_model.pt",
    "soil_11class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/soil_model.pt",
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
    
    if os.path.exists(checkpoint_path):
        return checkpoint_path
    
    url = MODEL_LINKS.get(model_key)
    if not url:
        return None
    
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    with st.spinner(f"Downloading {model_key} model (one-time, ~30-60 seconds)..."):
        try:
            response = requests.get(url, stream=True, timeout=300)
            
            if response.status_code == 200:
                with open(checkpoint_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                if os.path.exists(checkpoint_path) and os.path.getsize(checkpoint_path) > 1000000:
                    size_mb = os.path.getsize(checkpoint_path) / (1024*1024)
                    st.success(f"Model ready! ({size_mb:.1f} MB)")
                    return checkpoint_path
            
            st.error(f"Download failed (status {response.status_code})")
            return None
                
        except Exception as e:
            st.error(f"Download error: {str(e)[:100]}")
            return None
