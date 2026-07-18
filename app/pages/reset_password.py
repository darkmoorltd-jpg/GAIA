
import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="GAIA – Reset Password", page_icon="🔑", layout="centered")

query_params = st.query_params
token = query_params.get("token", [None])[0]
type_param = query_params.get("type", [None])[0]

if type_param != "recovery" or not token:
    st.error("Invalid password reset link.")
    st.stop()

st.title("🔑 Set New Password")

with st.form("new_password_form"):
    new_password = st.text_input("New password", type="password")
    confirm_password = st.text_input("Confirm new password", type="password")
    
    if st.form_submit_button("Update Password"):
        if new_password != confirm_password:
            st.error("Passwords do not match.")
        elif len(new_password) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            supabase = init_supabase()
            try:
                supabase.auth.update_user({"password": new_password})
                st.success("Password updated! You can now close this page and log in with your new password.")
                st.markdown("[Go to login](https://gaiagpt.streamlit.app)")
            except Exception as e:
                st.error(f"Failed to update password: {e}")
