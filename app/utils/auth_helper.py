
import streamlit as st
from supabase import create_client, Client

def get_supabase():
    """Get Supabase client."""
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )

def get_current_user():
    """Get current user from Supabase session."""
    try:
        supabase = get_supabase()
        session = supabase.auth.get_session()
        if session and session.user:
            return session.user
    except:
        pass
    return None

def require_login():
    """Check if user is logged in. Returns user or None."""
    user = get_current_user()
    if user is None:
        st.warning("Please log in first.")
        st.stop()
    return user
