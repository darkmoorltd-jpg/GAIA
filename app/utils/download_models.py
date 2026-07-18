
import os, requests, streamlit as st

MODEL_LINKS = {
    "poultry": "https://drive.google.com/uc?id=1Ms0aWA83m5eAaOCXO4nR2I_3oq5sSbUi",
    "cattle":  "https://drive.google.com/uc?id=1cV84OR1pvWzU_KQtR9Wrq2KC6etVvmHh",
    "pests_102class": "https://drive.google.com/uc?id=1XSmuhteSwdpbBIkzGErlH_1zWPG1kerk"
}

def download_file_from_google_drive(file_id, destination):
    """Download a file from Google Drive using requests (no extra libraries)."""
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={"id": file_id}, stream=True)
    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break
    if token:
        response = session.get(URL, params={"id": file_id, "confirm": token}, stream=True)
    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)
    return destination

def ensure_model(animal):
    """Download the model file if it is not already present."""
    checkpoint_dir = f"checkpoints/{animal}"
    checkpoint_path = os.path.join(checkpoint_dir, "best_model.pt")
    if not os.path.exists(checkpoint_path):
        os.makedirs(checkpoint_dir, exist_ok=True)
        url = MODEL_LINKS.get(animal)
        if url:
            file_id = url.split("id=")[-1]
            with st.spinner(f"Downloading {animal} model (one‑time) …"):
                download_file_from_google_drive(file_id, checkpoint_path)
    return checkpoint_path
