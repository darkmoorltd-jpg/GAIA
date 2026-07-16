
import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = "https://pxvtvuwlpzwlkdoxjrep.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB4dnR2dXdscHp3bGtkb3hqcmVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQyMTA0NTcsImV4cCI6MjA5OTc4NjQ1N30.gZH1uepXwrCrxC6ElRzkzvGEyGlp-Ep-o4CHXgBMXiY"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def sign_up(email: str, password: str):
    supabase = init_supabase()
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        return res.user, None
    except Exception as e:
        return None, str(e)

def sign_in(email: str, password: str):
    supabase = init_supabase()
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return res.user, None
    except Exception as e:
        return None, str(e)

def sign_out():
    supabase = init_supabase()
    supabase.auth.sign_out()

def reset_password(email: str):
    supabase = init_supabase()
    try:
        supabase.auth.reset_password_for_email(email)
        return None
    except Exception as e:
        return str(e)

def get_current_user():
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user
    return None
