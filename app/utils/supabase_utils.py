
import streamlit as st
from supabase import create_client, Client

def get_supabase() -> Client:
    """Return a Supabase client using Streamlit secrets."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

def decrement_scan(user_id: str):
    """Atomically subtract one scan from the user's balance."""
    supabase = get_supabase()
    supabase.rpc("decrement_scan", {"uid": user_id}).execute()
