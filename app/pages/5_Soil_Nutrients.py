import streamlit as st
import pandas as pd
import torch
import numpy as np
from src.models.soil_regressor import SoilRegressor

st.title("Soil Nutrient Level Prediction")
st.markdown("Upload a CSV with soil measurements (features).")
uploaded_csv = st.file_uploader("CSV file", type="csv")
if uploaded_csv:
    df = pd.read_csv(uploaded_csv)
    st.dataframe(df.head())
    # Load regressor
    model = SoilRegressor.load_from_checkpoint("checkpoints/soil_regressor.ckpt")
    model.eval()
    # Assume CSV has columns named as in config; we'll just take first N numeric columns
    feature_cols = [c for c in df.columns if c.startswith("feat")][:model.hparams.input_dim]  # adjust
    X = torch.tensor(df[feature_cols].values, dtype=torch.float32)
    with torch.no_grad():
        preds = model(X).numpy()
    targets = ["Nitrogen", "Phosphorus", "Potassium", "pH", "Organic Carbon"]
    for i, name in enumerate(targets):
        st.metric(name, f"{preds[0][i]:.2f}")