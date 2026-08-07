import os, requests, streamlit as st

MODEL_LINKS = {
    "soil_11class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/soil_model.pt",
    "pests_102class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/pests_model.pt",
    "poultry": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/poultry_model.pt",
    "cattle": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/cattle_model.pt",
}

def ensure_model(model_key):
    """Download the model file if it is not already present OR if corrupted."""
    checkpoint_dir = f"checkpoints/{model_key}"
    checkpoint_path = os.path.join(checkpoint_dir, "best_model.pt")
    
    # Check if existing file is valid (must be > 1MB and not HTML)
    if os.path.exists(checkpoint_path):
        size = os.path.getsize(checkpoint_path)
        if size > 1000000:  # > 1MB
            with open(checkpoint_path, "rb") as f:
                header = f.read(10)
            if header[:1] != b'<':  # Not HTML
                return checkpoint_path
        # File is corrupted — delete it
        os.remove(checkpoint_path)
    
    url = MODEL_LINKS.get(model_key)
    if not url:
        st.warning(f"No download URL for {model_key}")
        return None
    
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    with st.spinner(f"Downloading {model_key} model..."):
        try:
            response = requests.get(url, stream=True, timeout=300, allow_redirects=True)
            
            if response.status_code == 200:
                # Check content type
                ct = response.headers.get('content-type', '')
                if 'html' in ct.lower():
                    st.error(f"Server returned HTML instead of model file for {model_key}")
                    return None
                
                with open(checkpoint_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Validate
                size = os.path.getsize(checkpoint_path)
                if size > 1000000:
                    with open(checkpoint_path, "rb") as f:
                        header = f.read(10)
                    if header[:1] == b'<':
                        os.remove(checkpoint_path)
                        st.error(f"Downloaded file is HTML, not a model. Check the URL.")
                        return None
                    st.success(f"Model ready! ({size/1048576:.1f} MB)")
                    return checkpoint_path
                else:
                    os.remove(checkpoint_path)
                    st.error(f"Downloaded file too small ({size} bytes)")
                    return None
            else:
                st.error(f"Download failed (HTTP {response.status_code})")
                return None
        except Exception as e:
            st.error(f"Download error: {str(e)[:100]}")
            return None
