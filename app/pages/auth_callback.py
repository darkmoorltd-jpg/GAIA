
import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = "https://pxvtvuwlpzwlkdoxjrep.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB4dnR2dXdscHp3bGtkb3hqcmVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQyMTA0NTcsImV4cCI6MjA5OTc4NjQ1N30.gZH1uepXwrCrxC6ElRzkzvGEyGlp-Ep-o4CHXgBMXiY"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("Completing sign in…")

# Get the auth code from URL parameters
query_params = st.experimental_get_query_params()
code = query_params.get("code", [None])[0]

if code:
    supabase = init_supabase()
    try:
        # Exchange the code for a session
        supabase.auth.exchange_code_for_session({"auth_code": code})
        st.success("Signed in successfully! Redirecting…")
        # Redirect to the main app
        st.switch_page("app/main.py")
    except Exception as e:
        st.error(f"Sign in failed: {e}")
else:
    st.error("No authentication code found. Please try signing in again.")
