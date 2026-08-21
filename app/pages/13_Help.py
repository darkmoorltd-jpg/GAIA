import streamlit as st
from app.utils.auth_helper import get_current_user
user = get_current_user()
from supabase import create_client, Client
import uuid

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

def upload_file_to_supabase(file_bytes, filename):
    """Upload file to Supabase Storage and return URL."""
    supabase = get_service()
    clean_name = "attachment_" + uuid.uuid4().hex[:10] + ".bin"
    try:
        supabase.storage.from_("support_attachments").upload(clean_name, file_bytes)
        url = supabase.storage.from_("support_attachments").get_public_url(clean_name)
        return url, None
    except Exception as e:
        try:
            supabase.storage.create_bucket("support_attachments", {"public": True})
            supabase.storage.from_("support_attachments").upload(clean_name, file_bytes)
            url = supabase.storage.from_("support_attachments").get_public_url(clean_name)
            return url, None
        except Exception as e2:
            return None, f"Upload failed: {str(e2)[:200]}"

st.set_page_config(page_title="GAIA – Help & Support", page_icon="💬", layout="wide")

user = get_current_user()
if user is None:
    st.warning("Please log in first.")
    st.stop()

user = user
supabase = get_service()

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fa, #e8f5e9); color: #1b5e20; }
    header, footer { visibility: hidden; }
    .title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #2e7d32; }
    .msg-user { background: #e8f5e9; padding: 10px 15px; border-radius: 12px; margin: 5px 0; margin-left: 40px; border-left: 4px solid #4caf50; }
    .msg-admin { background: #fff3e0; padding: 10px 15px; border-radius: 12px; margin: 5px 0; margin-right: 40px; border-left: 4px solid #ff9800; }
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
    except Exception as e:
        my_tickets = []
    
    if not my_tickets:
        st.info("No tickets yet.")
    else:
        for ticket in my_tickets:
            status = ticket.get("status", "open")
            emoji = "🟠" if status == "open" else "✅"
            ticket_id = ticket.get("id")
            
            with st.expander(f"{emoji} {ticket.get('subject','')} — {str(ticket.get('created_at',''))[:16]}", expanded=True):
                st.markdown(f"**You wrote:** {ticket.get('message','')}")
                
                if ticket.get("attachment_url"):
                    st.markdown(f"[📎 Download Attachment]({ticket['attachment_url']})")
                
                st.markdown("---")
                st.markdown("**Conversation:**")
                
                try:
                    replies = supabase.table("support_replies").select("*").eq("ticket_id", ticket_id).order("created_at").execute()
                    reply_list = replies.data if replies.data else []
                except:
                    reply_list = []
                
                if reply_list:
                    for reply in reply_list:
                        if reply.get("is_admin"):
                            st.markdown(f'<div class="msg-admin"><strong>🔐 GAIA Team:</strong><br>{reply.get("message","")}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="msg-user"><strong>👤 You:</strong><br>{reply.get("message","")}</div>', unsafe_allow_html=True)
                else:
                    st.info("No replies yet. The GAIA team will respond soon.")
                
                st.markdown("---")
                with st.form(f"user_reply_form_{ticket_id}"):
                    user_reply = st.text_area("Add a reply", key=f"user_reply_text_{ticket_id}", height=60)
                    if st.form_submit_button("📤 Send Reply"):
                        if user_reply.strip():
                            try:
                                supabase.table("support_replies").insert({
                                    "ticket_id": ticket_id,
                                    "sender_id": user.id,
                                    "is_admin": False,
                                    "message": user_reply.strip()
                                }).execute()
                                st.success("Reply sent!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to send reply: {e}")

st.markdown("---")
st.caption("GAIA Support Team — darkmoorltd@gmail.com | Powered by Darkmoor Ltd")

# ============================================
# FULL NAVIGATION
# ============================================
st.markdown("---")
st.markdown("### Quick Navigation")
cols = st.columns(10)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="Livestock")
with cols[5]: st.page_link("pages/17_Video_Scan.py", label="Video Scan")
with cols[6]: st.page_link("pages/19_Satellite.py", label="Satellite")
with cols[7]: st.page_link("pages/18_Voice_Agronomist.py", label="Voice AI")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="Buy Scans")
with cols[9]: st.page_link("pages/10_Early_Warning.py", label="Alerts")

st.markdown("### More Features")
cols2 = st.columns(10)
with cols2[0]: st.page_link("pages/11_Verify_Farmer.py", label="Verify")
with cols2[1]: st.page_link("pages/12_Verification_History.py", label="History")
with cols2[2]: st.page_link("pages/14_Wallet.py", label="Wallet")
with cols2[3]: st.page_link("pages/15_Badges.py", label="Badges")
with cols2[4]: st.page_link("pages/16_Chat.py", label="Chat")
with cols2[5]: st.page_link("pages/20_Marketplace.py", label="Market")
with cols2[6]: st.page_link("pages/21_Crop_Insurance.py", label="Insurance")
with cols2[7]: st.page_link("pages/6_Payment_History.py", label="Payments")
with cols2[8]: st.page_link("pages/8_Profile.py", label="Profile")
with cols2[9]: st.page_link("pages/13_Help.py", label="Help")
