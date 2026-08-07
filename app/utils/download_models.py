import os, requests, streamlit as st, re

MODEL_LINKS = {
    "poultry": "https://drive.google.com/uc?id=1Ms0aWA83m5eAaOCXO4nR2I_3oq5sSbUi&export=download",
    "cattle":  "https://drive.google.com/uc?id=1cV84OR1pvWzU_KQtR9Wrq2KC6etVvmHh&export=download",
    "pests_102class": "https://drive.google.com/uc?id=1XSmuhteSwdpbBIkzGErlH_1zWPG1kerk&export=download",
    "soil_11class": "https://drive.google.com/uc?id=1to0HP_LaM61MDqjKFObJYjueiVC__ypt&export=download",
    "millet_3class": "",
    "maize": "",
    "rice_11class": "",
    "soybean_14class": "",
    "pepper_13class": "",
    "cabbage_8class": "",
}

def download_file_from_google_drive(url, destination):
    """Download a file from Google Drive handling confirmation tokens."""
    session = requests.Session()
    
    # First request
    response = session.get(url, stream=True)
    
    # Check if we got a confirmation page (for large files)
    if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
        # Look for the confirmation link in the page
        confirm_match = re.search(r'href="(/uc\?export=download[^"]+)"', response.text)
        if confirm_match:
            confirm_url = "https://drive.google.com" + confirm_match.group(1).replace('&amp;', '&')
            response = session.get(confirm_url, stream=True)
    
    # Check for cookie-based confirmation
    if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                response = session.get(url + f"&confirm={value}", stream=True)
                break
    
    # Write the file
    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)
    
    # Validate
    with open(destination, "rb") as f:
        header = f.read(4)
    if header[:1] == b'<':
        os.remove(destination)
        raise ValueError("Downloaded file is HTML - check sharing settings")
    
    return destination

def ensure_model(model_key):
    """Download the model file if it is not already present."""
    checkpoint_dir = f"checkpoints/{model_key}"
    checkpoint_path = os.path.join(checkpoint_dir, "best_model.pt")
    if not os.path.exists(checkpoint_path):
        url = MODEL_LINKS.get(model_key)
        if not url:
            return None
        os.makedirs(checkpoint_dir, exist_ok=True)
        with st.spinner(f"Downloading {model_key} model (one‑time) …"):
            try:
                download_file_from_google_drive(url, checkpoint_path)
            except Exception as e:
                st.error(f"Download failed for {model_key}: {e}")
                return None
    return checkpoint_path
