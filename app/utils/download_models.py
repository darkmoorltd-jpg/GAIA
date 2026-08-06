
import os, requests, streamlit as st, re

MODEL_LINKS = {
    "poultry": "https://drive.google.com/uc?id=1Ms0aWA83m5eAaOCXO4nR2I_3oq5sSbUi",
    "cattle":  "https://drive.google.com/uc?id=1cV84OR1pvWzU_KQtR9Wrq2KC6etVvmHh",
    "pests_102class": "https://drive.google.com/uc?id=1XSmuhteSwdpbBIkzGErlH_1zWPG1kerk",
    "soil_11class": "https://drive.google.com/uc?id=1to0HP_LaM61MDqjKFObJYjueiVC__ypt",
    "millet_3class": "",
    "maize": "",
    "rice_11class": "",
    "soybean_14class": "",
    "pepper_13class": "",
    "cabbage_8class": "",
}

def download_file_from_google_drive(file_id, destination):
    base_url = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(base_url, params={"id": file_id}, stream=True)
    if "Virus scan warning" in response.text:
        form_match = re.search(r'<form id="download-form" action="([^"]+)" method="get">(.*?)</form>', response.text, re.DOTALL)
        if form_match:
            form_action = form_match.group(1).replace('&amp;', '&')
            form_body = form_match.group(2)
            inputs = re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', form_body)
            params = dict(inputs)
            response = session.get(form_action, params=params, stream=True)
    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break
    if token is None:
        match = re.search(r'confirm=([0-9A-Za-z]+)', response.text)
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
        raise ValueError("Downloaded file is HTML – make sure the file is shared with 'Anyone with the link'.")
    return destination

def ensure_model(model_key):
    checkpoint_dir = f"checkpoints/{model_key}"
    checkpoint_path = os.path.join(checkpoint_dir, "best_model.pt")
    if not os.path.exists(checkpoint_path):
        url = MODEL_LINKS.get(model_key)
        if not url:
            return None
        os.makedirs(checkpoint_dir, exist_ok=True)
        file_id = url.split("id=")[-1]
        with st.spinner(f"Downloading {model_key} model (one‑time) …"):
            try:
                download_file_from_google_drive(file_id, checkpoint_path)
            except Exception as e:
                st.error(f"Download failed for {model_key}: {e}")
                return None
    return checkpoint_path
