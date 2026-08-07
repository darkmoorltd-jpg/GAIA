import os, requests, streamlit as st

# Google Drive links (primary - works on Streamlit Cloud)
GDRIVE = {
    "poultry": "https://drive.google.com/uc?export=download&id=1Ms0aWA83m5eAaOCXO4nR2I_3oq5sSbUi",
    "cattle": "https://drive.google.com/uc?export=download&id=1cV84OR1pvWzU_KQtR9Wrq2KC6etVvmHh",
    "soil_11class": "https://drive.google.com/uc?export=download&id=1to0HP_LaM61MDqjKFObJYjueiVC__ypt",
}

# GitHub Releases (fallback)
GITHUB = {
    "pests_102class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/pests_102class_best_model.pt",
}

def download_from_gdrive(url, destination):
    """Download from Google Drive handling confirmation tokens."""
    session = requests.Session()
    response = session.get(url, stream=True)
    
    # Handle confirmation token for large files
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            response = session.get(f"{url}&confirm={value}", stream=True)
            break
    
    if response.status_code == 200:
        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
        return True
    return False

def download_from_github(url, destination):
    """Download from GitHub Releases."""
    r = requests.get(url, stream=True, timeout=300)
    if r.status_code == 200:
        with open(destination, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
        return True
    return False

def ensure_model(model_key):
    """Download the model file from Google Drive (with GitHub fallback)."""
    checkpoint_dir = f"checkpoints/{model_key}"
    checkpoint_path = os.path.join(checkpoint_dir, "best_model.pt")
    
    # Delete any corrupted file
    if os.path.exists(checkpoint_path) and os.path.getsize(checkpoint_path) < 1000000:
        os.remove(checkpoint_path)
    
    if not os.path.exists(checkpoint_path):
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Try Google Drive first
        gdrive_url = GDRIVE.get(model_key)
        if gdrive_url:
            with st.spinner(f"Downloading {model_key} model from Google Drive..."):
                success = download_from_gdrive(gdrive_url, checkpoint_path)
                if success and os.path.getsize(checkpoint_path) > 1000000:
                    return checkpoint_path
                elif os.path.exists(checkpoint_path):
                    os.remove(checkpoint_path)
        
        # Try GitHub Releases as fallback
        github_url = GITHUB.get(model_key)
        if github_url:
            with st.spinner(f"Downloading {model_key} model from GitHub Releases..."):
                success = download_from_github(github_url, checkpoint_path)
                if success and os.path.getsize(checkpoint_path) > 1000000:
                    return checkpoint_path
                elif os.path.exists(checkpoint_path):
                    os.remove(checkpoint_path)
        
        st.error(f"Could not download {model_key} model. Please try again.")
        return None
    
    return checkpoint_path
