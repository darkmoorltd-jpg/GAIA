import streamlit as st
from supabase import create_client, Client
import uuid

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

def upload_file_to_supabase(file_bytes, filename):
    """Upload file to Supabase Storage and return URL."""
    import uuid
    supabase = get_service()
    clean_name = "attachment_" + uuid.uuid4().hex[:10] + ".bin"
    
    try:
        # Try direct upload first
        supabase.storage.from_("support_attachments").upload(
            path=clean_name,
            file=file_bytes,
            file_options={"content-type": "application/octet-stream"}
        )
        url = supabase.storage.from_("support_attachments").get_public_url(clean_name)
        return url, None
    except Exception as e:
        # Try creating bucket via SQL approach
        try:
            supabase.table("storage.buckets").insert({"id": "support_attachments", "name": "support_attachments", "public": True}).execute()
        except:
            pass
        
        # Retry upload
        try:
            supabase.storage.from_("support_attachments").upload(
                path=clean_name,
                file=file_bytes,
                file_options={"content-type": "application/octet-stream"}
            )
            url = supabase.storage.from_("support_attachments").get_public_url(clean_name)
            return url, None
        except Exception as e2:
            return None, f"Upload failed: {str(e2)[:200]}"
st.set_page_config(page_title="GAIA – Help & Support", page_icon="💬", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
supabase = get_service()

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa, #e8f5e9); color: #1b5e20; }
    header, footer { visibility: hidden; }
    .title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #2e7d32; }
    .stButton button { background: #2e7d32 !important; color: #fff !important; border: none !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">💬 Help & Support</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📝 New Ticket", "📋 My Tickets"])

with tab1:
    st.markdown("### Send a message to the GAIA team")
    with st.form("new_ticket_form"):
        subject = st.text_input("Subject *", placeholder="e.g., Payment issue, Crop question")
        message = st.text_area("Your Message *", placeholder="Describe your issue...", height=150)
        uploaded_file = st.file_uploader("📎 Attach Image/File", type=["jpg", "jpeg", "png", "gif", "mp4", "mp3", "wav", "pdf"])
        
        if st.form_submit_button("📤 Send", type="primary", use_container_width=True):
            if not subject or not message:
                st.error("Subject and message are required.")
            else:
                attachment_url = None
                if uploaded_file:
                    file_bytes = uploaded_file.read()
                    attachment_url, err = upload_file_to_supabase(file_bytes, uploaded_file.name)
                    if err:
                        st.error(f"File upload failed: {err}")
                
                try:
                    supabase.table("support_tickets").insert({
                        "user_id": user.id,
                        "subject": subject.strip(),
                        "message": message.strip(),
                        "attachment_url": attachment_url,
                        "status": "open"
                    }).execute()
                    st.success("✅ Ticket submitted!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Failed to submit ticket: {e}")

with tab2:
    st.markdown("### My Support Tickets")
    try:
        tickets = supabase.table("support_tickets").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
        my_tickets = tickets.data if tickets.data else []
    except:
        my_tickets = []
    
    if not my_tickets:
        st.info("No tickets yet.")
    else:
        for ticket in my_tickets:
            status = ticket.get("status", "open")
            emoji = "🟠" if status == "open" else "✅"
            with st.expander(f"{emoji} {ticket.get('subject','')} — {str(ticket.get('created_at',''))[:16]}"):
                st.markdown(f"**Message:** {ticket.get('message','')}")
                if ticket.get("attachment_url"):
                    st.markdown(f"[📎 Download Attachment]({ticket['attachment_url']})")

st.markdown("---")
st.caption("GAIA Support Team — darkmoorltd@gmail.com | Powered by Darkmoor Ltd")
