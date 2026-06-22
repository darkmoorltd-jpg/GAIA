import streamlit as st

st.title("GAIA Dashboard")
st.write("Welcome to the Global Agricultural Intelligence Assistant.")
st.metric(label="Crops Supported", value="3")
st.metric(label="Disease Classes", value="19")
st.markdown("Upload a leaf photo in the **Diagnose Crop** tab to get started.")