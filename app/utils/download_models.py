
import os, requests, streamlit as st, re, io

MODEL_LINKS = {
    "poultry": "https://drive.google.com/uc?id=1Ms0aWA83m5eAaOCXO4nR2I_3oq5sSbUi",
    "cattle":  "https://drive.google.com/uc?id=1cV84OR1pvWzU_KQtR9Wrq2KC6etVvmHh",
    "pests_102class": "https://drive.google.com/uc?id=1XSmuhteSwdpbBIkzGErlH_1zWPG1kerk"
}

def download_file_from_google_drive(file_id, destination):
    """Download a file from Google Drive, handling the confirmation page."""
    base_url = "https://docs.google.com/uc?export=download"
    session = requests.Session()

    # First attempt
    response = session.get(base_url, params={"id": file_id}, stream=True)

    # Check for confirmation token (cookie method)
    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break

    # If no cookie token, try to extract from the HTML content
    if token is None:
        html = response.text
        # Look for the confirm code in the page
        match = re.search(r'confirm=([0-9A-Za-z]+)', html)
        if match:
            token = match.group(1)

    if token:
        # Second request with confirmation
        response = session.get(base_url, params={"id": file_id, "confirm": token}, stream=True)

    # Write the file
    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)

    # Validate that it's a real PyTorch file
    with open(destination, "rb") as f:
        header = f.read(4)
    # If the file starts with '<' it's likely HTML (error page)
    if header[:1] == b'<':
        os.remove(destination)
        raise ValueError("Downloaded file appears to be HTML. Please check the file is publicly shared with 'Anyone with the link'.")

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
                try:
                    download_file_from_google_drive(file_id, checkpoint_path)
                except Exception as e:
                    st.error(f"Download failed: {e}. Ensure the file is shared with 'Anyone with the link'.")
                    raise e
    return checkpoint_path
