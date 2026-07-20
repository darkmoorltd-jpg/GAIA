
import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]

@st.cache_resource
def init_supabase():
    """Anon client for read-only operations."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def init_service_client():
    """Service client to bypass RLS for writes."""
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA – Help & Support", page_icon="💬", layout="wide", initial_sidebar_state="expanded")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = init_supabase()
service_client = init_service_client()

st.title("💬 Help & Support")
st.markdown("Send a message to the GAIA team. We'll reply as soon as possible.")

tab1, tab2 = st.tabs(["📝 New Message", "📋 Message History"])

with tab1:
    with st.form("new_message_form"):
        message_text = st.text_area("Your message", height=150)
        uploaded_file = st.file_uploader("Attach a file (image, PDF, voice note)", 
                                         type=["jpg", "jpeg", "png", "pdf", "doc", "docx", "mp3", "wav", "ogg"])
        
        if st.form_submit_button("Send Message"):
            if not message_text and not uploaded_file:
                st.error("Please enter a message or attach a file.")
            else:
                attachment_url = None
                attachment_type = None
                
                if uploaded_file:
                    file_ext = uploaded_file.name.split('.')[-1].lower()
                    if file_ext in ['jpg', 'jpeg', 'png']:
                        attachment_type = 'image'
                    elif file_ext == 'pdf':
                        attachment_type = 'pdf'
                    elif file_ext in ['mp3', 'wav', 'ogg']:
                        attachment_type = 'voice'
                    else:
                        attachment_type = 'document'
                    
                    file_path = f"{user.id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                    try:
                        service_client.storage.from_("message_attachment").upload(
                            file_path, uploaded_file.getvalue()
                        )
                        attachment_url = service_client.storage.from_("message_attachment").get_public_url(file_path)
                    except Exception as e:
                        st.warning(f"Attachment upload skipped: {e}")
                        attachment_url = None
                
                # Insert message
                try:
                    service_client.table("messages").insert({
                        "user_id": user.id,
                        "message": message_text if message_text else "",
                        "attachment_url": attachment_url,
                        "attachment_type": attachment_type
                    }).execute()
                    st.success("Message sent! We'll reply soon.")
                except Exception as e:
                    st.error(f"Failed to send message: {e}")

with tab2:
    resp = supabase.table("messages").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
    messages = resp.data if resp.data else []
    
    if not messages:
        st.info("No messages yet.")
    else:
        for msg in messages:
            sender = "🔐 Admin" if msg["is_from_admin"] else "👤 You"
            timestamp = msg["created_at"][:16] if msg.get("created_at") else ""
            with st.chat_message("assistant" if msg["is_from_admin"] else "user"):
                st.write(f"**{sender}** – {timestamp}")
                if msg.get("message"):
                    st.write(msg["message"])
                if msg.get("attachment_url"):
                    if msg.get("attachment_type") == "image":
                        st.image(msg["attachment_url"], width=200)
                    else:
                        st.markdown(f"[📎 Download attachment]({msg['attachment_url']})")
