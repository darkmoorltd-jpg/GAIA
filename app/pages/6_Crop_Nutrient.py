import streamlit as st
from PIL import Image
import torch
import numpy as np
from app.utils.inference import load_model, get_class_names

st.title("Crop Nutrient Deficiency Diagnosis")
st.markdown("Upload a leaf photo showing possible deficiency.")
uploaded = st.file_uploader("Leaf image", type=["jpg","jpeg","png"])
if uploaded:
    img = Image.open(uploaded).convert("RGB")
    st.image(img, caption="Leaf", use_column_width=True)
    model = load_model("crop_nutrient")
    class_names = get_class_names("crop_nutrient")
    img = img.resize((224,224))
    img_tensor = torch.from_numpy(np.array(img)).permute(2,0,1).unsqueeze(0).float()/255.0
    with torch.no_grad():
        logits = model(img_tensor)
        probs = torch.softmax(logits, dim=1)[0]
    pred = torch.argmax(probs).item()
    st.success(f"Diagnosis: **{class_names[pred]}** ({probs[pred]*100:.1f}%)")
    # Show top-3
    st.write("Top predictions:")
    top_probs, top_idx = torch.topk(probs, 3)
    for i in range(3):
        st.write(f"{class_names[top_idx[i]]}: {top_probs[i]*100:.1f}%")