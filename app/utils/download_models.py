import os, requests, streamlit as st

# Hugging Face model URLs (free, fast, no limits)
MODEL_LINKS = {
    "poultry": "https://huggingface.co/tjgguy12/gaia-poultry/resolve/main/best_model.pt",
    "cattle":  "https://huggingface.co/tjgguy12/gaia-cattle/resolve/main/best_model.pt",
    "pests_102class": "https://huggingface.co/tjgguy12/gaia-pests-102class/resolve/main/best_model.pt",
    "soil_11class": "https://huggingface.co/tjgguy12/gaia-soil-11class/resolve/main/best_model.pt",
}

def ensure_model(model_key):
    checkpoint_dir = f"checkpoints/{model_key}"
    checkpoint_path = os.path.join(checkpoint_dir, "best_model.pt")
    
    if not os.path.exists(checkpoint_path):
        url = MODEL_LINKS.get(model_key)
        if not url:
            return None
        
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        with st.spinner(f"Downloading {model_key} model (one‑time) …"):
            try:
                r = requests.get(url, stream=True, timeout=120)
                r.raise_for_status()
                with open(checkpoint_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                size = os.path.getsize(checkpoint_path)
                if size < 1000:
                    os.remove(checkpoint_path)
                    raise ValueError(f"Downloaded file too small ({size} bytes)")
            except Exception as e:
                st.error(f"Download failed for {model_key}: {e}")
                return None
    
    return checkpoint_path
