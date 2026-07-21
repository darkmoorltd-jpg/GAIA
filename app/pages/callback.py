
import streamlit as st

st.set_page_config(page_title="Processing Payment", page_icon="⏳", layout="centered")

# The callback page just reads the parameters and immediately redirects to the main app.
# The main app will handle everything.

query_params = st.query_params
reference = query_params.get("reference", [None])[0]
plan = query_params.get("plan", [None])[0]

if not reference or not plan:
    st.error("Invalid payment link.")
    st.stop()

# Redirect to the main app with the payment details
redirect_url = f"https://gaiagpt.streamlit.app/?pending_reference={reference}&pending_plan={plan}"
st.markdown(f'<meta http-equiv="refresh" content="0; url={redirect_url}">', unsafe_allow_html=True)
st.info("Redirecting to GAIA to complete your payment…")
