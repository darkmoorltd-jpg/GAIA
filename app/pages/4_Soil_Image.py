import streamlit as st
from PIL import Image
import torch
import numpy as np
from app.utils.inference import load_model, get_class_names

st.title("Soil Type Classification")
uploaded = st.file_uploader("Upload a close‑up photo of soil", type=["jpg","jpeg","png"])
if uploaded:
    img = Image.open(uploaded).convert("RGB")
    st.image(img, caption="Soil sample", use_column_width=True)
    # Load soil model (trained)
    model = load_model("soil")  # uses checkpoints/soil/best_model.pt
    class_names = get_class_names("soil")
    # Preprocess
    img = img.resize((224,224))
    img_tensor = torch.from_numpy(np.array(img)).permute(2,0,1).unsqueeze(0).float()/255.0
    with torch.no_grad():
        logits = model(img_tensor)
        probs = torch.softmax(logits, dim=1)[0]
    pred = torch.argmax(probs).item()
    st.success(f"Predicted soil type: **{class_names[pred]}** ({probs[pred]*100:.1f}%)")