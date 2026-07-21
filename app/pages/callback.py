
import streamlit as st

st.set_page_config(page_title="Redirecting…", page_icon="⏳", layout="centered")

query_params = st.query_params
reference = query_params.get("reference", [None])[0]
plan = query_params.get("plan", [None])[0]

if reference and plan:
    redirect_url = f"https://gaiagpt.streamlit.app/?pending_reference={reference}&pending_plan={plan}"
    st.markdown(f'<meta http-equiv="refresh" content="0; url={redirect_url}">', unsafe_allow_html=True)
    st.info("Redirecting to GAIA to complete your payment…")
else:
    st.error("Invalid payment link.")
