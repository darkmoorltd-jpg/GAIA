
import streamlit as st
from supabase import create_client, Client
import uuid
import base64

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

def upload_file_to_supabase(file_bytes, filename):
    """Upload file to Supabase Storage and return URL."""
    supabase = get_service()
    unique_name = f"{uuid.uuid4().hex[:12]}_{filename}"
    try:
        supabase.storage.from_("support_attachments").upload(
            unique_name,
            file_bytes,
            {"content-type": "application/octet-stream"}
        )
        url = supabase.storage.from_("support_attachments").get_public_url(unique_name)
        return url, None
    except Exception as e:
        return None, str(e)

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
    .ticket-card { background: #fff; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .ticket-open { border-left: 5px solid #ff9800; }
    .ticket-closed { border-left: 5px solid #4caf50; }
    .msg-user { background: #e8f5e9; padding: 10px 15px; border-radius: 12px; margin: 5px 0; margin-left: 40px; }
    .msg-admin { background: #fff3e0; padding: 10px 15px; border-radius: 12px; margin: 5px 0; margin-right: 40px; }
    .stButton button { background: #2e7d32 !important; color: #fff !important; border: none !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">💬 Help & Support</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📝 New Ticket", "📋 My Tickets"])

# ===== TAB 1: NEW TICKET =====
with tab1:
    st.markdown("### Send a message to the GAIA team")
    
    with st.form("new_ticket_form"):
        subject = st.text_input("Subject *", placeholder="e.g., Payment issue, Crop question, App error")
        message = st.text_area("Your Message *", placeholder="Describe your issue or question...", height=150)
        
        uploaded_file = st.file_uploader("📎 Attach Image/File/Video", 
                                         type=["jpg", "jpeg", "png", "gif", "mp4", "mp3", "wav", "pdf", "doc", "docx"])
        
        if st.form_submit_button("📤 Send", type="primary", use_container_width=True):
            if not subject or not message:
                st.error("Subject and message are required.")
            else:
                attachment_url = None
                attachment_type = None
                
                if uploaded_file:
                    file_bytes = uploaded_file.read()
                    attachment_url, err = upload_file_to_supabase(file_bytes, uploaded_file.name)
                    if err:
                        st.error(f"File upload failed: {err}")
                        st.stop()
                    attachment_type = uploaded_file.type
                
                supabase.table("support_tickets").insert({
                    "user_id": user.id,
                    "subject": subject.strip(),
                    "message": message.strip(),
                    "attachment_url": attachment_url,
                    "attachment_type": attachment_type,
                    "status": "open"
                }).execute()
                
                st.success("✅ Ticket submitted! The GAIA team will respond soon.")
                st.balloons()

# ===== TAB 2: MY TICKETS =====
with tab2:
    st.markdown("### My Support Tickets")
    
    try:
        tickets = supabase.table("support_tickets").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
        my_tickets = tickets.data if tickets.data else []
    except:
        my_tickets = []
    
    if not my_tickets:
        st.info("No tickets yet. Send your first message in the 'New Ticket' tab!")
    else:
        for ticket in my_tickets:
            status = ticket.get("status", "open")
            status_emoji = {"open": "🟠", "closed": "✅"}.get(status, "⚪")
            
            with st.expander(f"{status_emoji} {ticket.get('subject','')} — {ticket.get('created_at','')[:16]}"):
                st.markdown(f"**Message:** {ticket.get('message','')}")
                
                # Show attachment
                if ticket.get("attachment_url"):
                    if ticket.get("attachment_type", "").startswith("image"):
                        st.image(ticket["attachment_url"], width=300)
                    else:
                        st.markdown(f"[📎 Download Attachment]({ticket['attachment_url']})")
                
                st.markdown("---")
                st.markdown("**Conversation:**")
                
                # Get replies
                try:
                    replies = supabase.table("support_replies").select("*").eq("ticket_id", ticket["id"]).order("created_at").execute()
                    reply_list = replies.data if replies.data else []
                except:
                    reply_list = []
                
                for reply in reply_list:
                    if reply.get("is_admin"):
                        st.markdown(f'<div class="msg-admin"><strong>🔐 GAIA Team:</strong><br>{reply.get("message","")}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="msg-user"><strong>👤 You:</strong><br>{reply.get("message","")}</div>', unsafe_allow_html=True)
                
                # Reply form
                with st.form(f"reply_form_{ticket['id']}"):
                    reply_text = st.text_area("Reply", key=f"reply_text_{ticket['id']}", height=60)
                    if st.form_submit_button("📤 Send Reply"):
                        if reply_text.strip():
                            supabase.table("support_replies").insert({
                                "ticket_id": ticket["id"],
                                "sender_id": user.id,
                                "is_admin": False,
                                "message": reply_text.strip()
                            }).execute()
                            st.success("Reply sent!")
                            st.rerun()

st.markdown("---")
st.caption("GAIA Support Team — darkmoorltd@gmail.com | Powered by Darkmoor Ltd")

cols = st.columns(9)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/8_Profile.py", label="👤 Profile")
with cols[6]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[7]: st.page_link("pages/20_Marketplace.py", label="🌍 Market")
with cols[8]: st.page_link("pages/7_Admin.py", label="🔐 Admin")
