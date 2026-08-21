
import streamlit as st

def get_current_user():
    """Get current user from Streamlit session state."""
    user = st.session_state.get("user", None)
    if user is None:
        st.warning("Please log in first.")
        st.stop()
    return user
