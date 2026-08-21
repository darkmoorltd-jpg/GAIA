import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="Farmer Database", page_icon="🌍", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["service_key"])

st.markdown("<h1 style='color:#2e7d32;'>🌍 National Farmer Database</h1>", unsafe_allow_html=True)
st.markdown("Search, filter, and manage farmers across states and LGAs.")

# Fetch all farmers
res = supabase.table("farmer_registry").select("*").execute()
farmers = res.data if res.data else []

if farmers:
    df = pd.DataFrame(farmers)
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        state_filter = st.selectbox("State", ["All"] + sorted(set(df.get("state", []))))
    with col2:
        lga_filter = st.selectbox("LGA", ["All"] + sorted(set(df.get("lga", []))))
    with col3:
        crop_filter = st.selectbox("Crop", ["All"] + sorted(set(df.get("crop", []))))

    filtered = df
    if state_filter != "All":
        filtered = filtered[filtered["state"] == state_filter]
    if lga_filter != "All":
        filtered = filtered[filtered["lga"] == lga_filter]
    if crop_filter != "All":
        filtered = filtered[filtered["crop"] == crop_filter]

    st.dataframe(filtered, use_container_width=True)
else:
    st.info("No farmers registered yet.")

# Add new farmer form
st.markdown("---")
st.markdown("### ➕ Register New Farmer")
with st.form("register_farmer"):
    col1, col2 = st.columns(2)
    with col1:
        state = st.text_input("State")
        lga = st.text_input("LGA")
        phone = st.text_input("Phone")
    with col2:
        crop = st.text_input("Primary Crop")
        farm_size = st.number_input("Farm Size (acres)", min_value=0.0, value=1.0)
    if st.form_submit_button("Register"):
        if state and lga and crop:
            supabase.table("farmer_registry").insert({
                "user_id": st.session_state.user.id,
                "state": state,
                "lga": lga,
                "phone": phone,
                "crop": crop,
                "farm_size_acres": farm_size
            }).execute()
            st.success("Farmer registered!")
            st.rerun()
        else:
            st.error("State, LGA, and Crop are required.")
