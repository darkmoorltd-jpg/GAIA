import streamlit as st
import torch
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src.models.gaia_model import GAIAModel

@st.cache_resource
def load_model(crop_name):
    """Load the best model for a given crop."""
    checkpoint_path = f"checkpoints/{crop_name}/best_model.pt"
    ckpt_path = f"checkpoints/{crop_name}/best-*.ckpt"
    # Simple: try .pt first
    if os.path.exists(checkpoint_path):
        # Need num_classes from config
        import yaml
        with open(f"configs/{crop_name}.yaml") as f:
            cfg = yaml.safe_load(f)
        model = GAIAModel(num_classes=cfg["num_classes"])
        model.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))
        model.eval()
        return model
    else:
        raise FileNotFoundError(f"No trained model found for {crop_name}. Train it first.")

def get_class_names(crop_name):
    import yaml
    with open(f"configs/{crop_name}.yaml") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("class_names", [str(i) for i in range(cfg["num_classes"])])

def predict(model, img_tensor):
    model.eval()
    with torch.no_grad():
        return model(img_tensor)