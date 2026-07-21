
import os, requests, streamlit as st, re

MODEL_LINKS = {
    "poultry": "https://drive.google.com/uc?id=1Ms0aWA83m5eAaOCXO4nR2I_3oq5sSbUi",
    "cattle":  "https://drive.google.com/uc?id=1cV84OR1pvWzU_KQtR9Wrq2KC6etVvmHh",
    "pests_102class": "https://drive.google.com/uc?id=1XSmuhteSwdpbBIkzGErlH_1zWPG1kerk"
}

# Backup download links for crop models (Google Drive file IDs)
CROP_MODEL_LINKS = {
    "grape":  "1YOUR_GRAPE_FILE_ID",      # ← Replace with the real ID from Google Drive
    "apple":  None,                       # will work if LFS pulled the file
    "mango":  None,
    "orange": None,
    "rice":   None,
    "maize":  None,
    "beans":  None,
    "potato": None,
    "wheat":  None,
    "banana": None,
}

def download_file_from_google_drive(file_id, destination):
    """Download a file from Google Drive, handling the confirmation page."""
    base_url = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(base_url, params={"id": file_id}, stream=True)
    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break
    if token is None:
        html = response.text
        match = re.search(r'confirm=([0-9A-Za-z]+)', html)
        if match:
            token = match.group(1)
    if token:
        response = session.get(base_url, params={"id": file_id, "confirm": token}, stream=True)
    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)
    with open(destination, "rb") as f:
        header = f.read(4)
    if header[:1] == b'<':
        os.remove(destination)
        raise ValueError("Downloaded file appears to be HTML. Please check the file is publicly shared.")
    return destination

def ensure_model(animal):
    """Download a livestock model if missing."""
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

def ensure_crop_model(crop_name):
    """Download a crop model if missing, using the CROP_MODEL_LINKS dictionary."""
    possible_paths = [
        f"checkpoints/{crop_name}_13class/best_model.pt",
        f"checkpoints/{crop_name}_8class/best_model.pt",
        f"checkpoints/{crop_name}_5class/best_model.pt",
        f"checkpoints/{crop_name}_11class/best_model.pt",
        f"checkpoints/{crop_name}_4class/best_model.pt",
        f"checkpoints/{crop_name}/best_model.pt",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path

    # If none found, try to download from Google Drive
    file_id = CROP_MODEL_LINKS.get(crop_name)
    if file_id and file_id != "None" and not file_id.startswith("1YOUR_"):
        # Determine correct subfolder name from the links above
        # e.g., grape -> grape_4class
        for pattern in ["_13class", "_8class", "_5class", "_11class", "_4class"]:
            folder = f"checkpoints/{crop_name}{pattern}"
            if file_id:
                # We'll just download to {crop_name}_4class for grape, etc.
                # For simplicity, we'll download to the first matching pattern if known.
                pass
        # Simple fallback: download to checkpoints/{crop_name}_4class/ if crop is grape, else generic
        if crop_name == "grape":
            folder = f"checkpoints/{crop_name}_4class"
        else:
            folder = f"checkpoints/{crop_name}"
        os.makedirs(folder, exist_ok=True)
        dest = os.path.join(folder, "best_model.pt")
        with st.spinner(f"Downloading {crop_name} model (one‑time) …"):
            download_file_from_google_drive(file_id, dest)
        return dest

    return None
