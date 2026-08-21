
import streamlit as st
from supabase import create_client

def get_supabase():
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )

def get_current_user():
    """Get current user from Supabase session (works across all pages)."""
    try:
        supabase = get_supabase()
        session = supabase.auth.get_session()
        if session and session.user:
            return session.user
    except:
        pass
    return None
