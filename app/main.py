import streamlit as st

# ---------- GAIA Navigation ----------
st.set_page_config(page_title="GAIA", page_icon="🌱", layout="wide")

# Build navigation pages
dashboard_page = st.Page(
    "pages/1_Dashboard.py",
    title="Dashboard",
    icon="🏠",
)
diagnose_page = st.Page(
    "pages/2_Diagnose_Crop.py",
    title="Diagnose Crop",
    icon="🌿",
)
history_page = st.Page(
    "pages/3_History.py",
    title="History",
    icon="📋",
)
# Add more pages later (soil, nutrients, …) by creating st.Page objects

pg = st.navigation(
    {
        "GAIA": [dashboard_page, diagnose_page, history_page],
    }
)

pg.run()