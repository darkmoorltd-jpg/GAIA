import streamlit as st

st.set_page_config(page_title="GAIA", page_icon="🌱", layout="wide")

dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard", icon="🏠")
crops_page     = st.Page("pages/2_Crops.py", title="Crop Disease", icon="🌿")
pests_page     = st.Page("pages/3_Pests.py", title="Pest Detection", icon="🐛")
soil_page      = st.Page("pages/4_Soil.py", title="Soil Analysis", icon="🏞️")
livestock_page = st.Page("pages/5_Livestock.py", title="Livestock Health", icon="🐄")

pg = st.navigation(
    {
        "GAIA": [dashboard_page],
        "Diagnose": [crops_page, pests_page, soil_page, livestock_page],
    }
)
pg.run()