
import os, requests, streamlit as st, json

MODEL_LINKS = {
    "poultry": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/poultry_best_model.pt",
    "cattle":  "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/cattle_best_model.pt",
    "pests_102class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/pests_102class_best_model.pt",
    "soil_11class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/soil_11class_best_model.pt",
    "maize": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/gaia_maize_4class.pt",
    "millet_3class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/gaia_millet_3class.pt",
    "rice_10class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/gaia_rice_10class_384px.pt",
    "soybean_14class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/gaia_soybean_14class.pt",
    "pepper_13class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/gaia_pepper_13class.pt",
    "cabbage_8class": "https://github.com/darkmoorltd-jpg/GAIA/releases/download/v1.0/gaia_cabbage_8class.pt",
}

def _get_cached_url(model_key):
    """Return the URL stored in the .url file, if any."""
    meta_path = f"models/{model_key}/.url"
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            return f.read().strip()
    return None

def _write_cached_url(model_key, url):
    """Save the URL to a .url file."""
    os.makedirs(f"models/{model_key}", exist_ok=True)
    with open(f"models/{model_key}/.url", "w") as f:
        f.write(url)

def ensure_model(model_key):
    checkpoint_dir = f"models/{model_key}"
    checkpoint_path = os.path.join(checkpoint_dir, "model.pt")
    expected_url = MODEL_LINKS.get(model_key)

    if not expected_url:
        st.warning(f"No download URL for {model_key}")
        return None

    # Delete cache if the URL doesn't match or file is too small
    cached_url = _get_cached_url(model_key)
    file_exists = os.path.exists(checkpoint_path)
    file_valid = file_exists and os.path.getsize(checkpoint_path) > 10000

    if not file_valid or cached_url != expected_url:
        if file_exists:
            os.remove(checkpoint_path)
        # Also remove any old .url
        meta_path = f"models/{model_key}/.url"
        if os.path.exists(meta_path):
            os.remove(meta_path)

        os.makedirs(checkpoint_dir, exist_ok=True)

        with st.spinner(f"Downloading {model_key} model (one‑time) …"):
            try:
                r = requests.get(expected_url, stream=True, timeout=300, allow_redirects=True)
                r.raise_for_status()
                total_size = 0
                with open(checkpoint_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=32768):
                        if chunk:
                            f.write(chunk)
                            total_size += len(chunk)
                size_mb = total_size / (1024*1024)
                if total_size < 10000:
                    os.remove(checkpoint_path)
                    st.error(f"Download failed — file too small ({total_size} bytes).")
                    return None
                # Save the URL we just downloaded
                _write_cached_url(model_key, expected_url)
                st.success(f"Model ready: {size_mb:.1f} MB")
            except Exception as e:
                st.error(f"Download failed: {str(e)[:200]}")
                if os.path.exists(checkpoint_path):
                    os.remove(checkpoint_path)
                return None
    else:
        # File is valid and URL matches
        pass

    return checkpoint_path
