import os, streamlit as st

MODEL_LINKS = {
    "poultry": "https://drive.google.com/uc?id=1Ms0aWA83m5eAaOCXO4nR2I_3oq5sSbUi&export=download&confirm=t",
    "cattle":  "https://drive.google.com/uc?id=1cV84OR1pvWzU_KQtR9Wrq2KC6etVvmHh&export=download&confirm=t",
    "pests_102class": "https://drive.google.com/uc?id=1XSmuhteSwdpbBIkzGErlH_1zWPG1kerk&export=download&confirm=t",
    "soil_11class": "https://drive.google.com/uc?id=1to0HP_LaM61MDqjKFObJYjueiVC__ypt&export=download&confirm=t",
    "millet_3class": "",
    "maize": "",
    "rice_11class": "",
    "soybean_14class": "",
    "pepper_13class": "",
    "cabbage_8class": "",
}

def ensure_model(model_key):
    """Download the model file if it is not already present."""
    import requests
    
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
            response = requests.get(url, stream=True, timeout=120)
            
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(checkpoint_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                
                if os.path.exists(checkpoint_path) and os.path.getsize(checkpoint_path) > 1000000:
                    size_mb = os.path.getsize(checkpoint_path) / (1024*1024)
                    st.success(f"Model downloaded! ({size_mb:.1f} MB)")
                    return checkpoint_path
                else:
                    st.error("Downloaded file is too small or empty.")
                    return None
            else:
                st.error(f"Download failed. Status: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Download error: {str(e)[:100]}")
            return None
