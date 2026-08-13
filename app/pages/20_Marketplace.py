
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime, timedelta
import uuid
from app.utils.phone_util import normalize_phone

# ===== CONFIG =====
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_PUBLIC = "pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057"

@st.cache_resource
def get_db():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA Market", page_icon="🌍", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
db = get_db()
service = get_service()

# ===== SESSION STATE =====
if "cart" not in st.session_state:
    st.session_state.cart = []
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "All"

# ===== DEMO DATA =====
DEMO_LISTINGS = [
    {"id":"demo1","crop":"Maize","variety":"SAMMAZ 15","quantity":20,"unit":"tonnes","price":220000,"location":"Kaduna","state":"Kaduna","farmer":"Ibrahim Musa","user_id":"demo","rating":4.8,"image":"🌽","harvest_date":"2025-10-15","organic":True,"description":"High-yield hybrid maize. Drought resistant. Germination 98%.","seller_type":"Verified Farmer","featured":True,"phone":"0803-XXX-XXXX","whatsapp":"0803-XXX-XXXX"},
    {"id":"demo2","crop":"Rice","variety":"FARO 44","quantity":15,"unit":"tonnes","price":350000,"location":"Kano","state":"Kano","farmer":"Aisha Bello","user_id":"demo","rating":4.9,"image":"🌾","harvest_date":"2025-09-28","organic":False,"description":"Premium long-grain rice. Milled and polished.","seller_type":"Premium Seller","featured":True,"phone":"0805-XXX-XXXX","whatsapp":"0805-XXX-XXXX"},
    {"id":"demo3","crop":"Beans","variety":"IT89KD-288","quantity":8,"unit":"tonnes","price":480000,"location":"Jos","state":"Plateau","farmer":"David Okonkwo","user_id":"demo","rating":4.7,"image":"🫘","harvest_date":"2025-08-20","organic":True,"description":"Organic honey beans. High protein.","seller_type":"Organic Certified","featured":False,"phone":"0802-XXX-XXXX","whatsapp":"0802-XXX-XXXX"},
    {"id":"demo4","crop":"Tomatoes","variety":"Roma VF","quantity":5,"unit":"tonnes","price":180000,"location":"Zaria","state":"Kaduna","farmer":"Fatima Yusuf","user_id":"demo","rating":4.6,"image":"🍅","harvest_date":"2025-10-05","organic":False,"description":"Fresh Roma tomatoes. Firm and red.","seller_type":"Verified Farmer","featured":False,"phone":"0806-XXX-XXXX","whatsapp":"0806-XXX-XXXX"},
    {"id":"demo5","crop":"Yam","variety":"Dioscorea rotundata","quantity":25,"unit":"tonnes","price":550000,"location":"Makurdi","state":"Benue","farmer":"John Tarka","user_id":"demo","rating":4.9,"image":"🍠","harvest_date":"2025-12-10","organic":True,"description":"Premium white yam tubers.","seller_type":"Premium Seller","featured":True,"phone":"0804-XXX-XXXX","whatsapp":"0804-XXX-XXXX"},
    {"id":"demo6","crop":"Cassava","variety":"TME 419","quantity":40,"unit":"tonnes","price":120000,"location":"Ondo","state":"Ondo","farmer":"Grace Adeyemi","user_id":"demo","rating":4.6,"image":"🥔","harvest_date":"2025-10-30","organic":True,"description":"High-starch cassava.","seller_type":"Organic Certified","featured":False,"phone":"0801-XXX-XXXX","whatsapp":"0801-XXX-XXXX"},
]

# ===== FETCH REAL LISTINGS =====
try:
    real_listings = db.table("marketplace_listings").select("*").eq("status", "active").order("created_at", desc=True).execute()
    REAL_LISTINGS = real_listings.data if real_listings.data else []
except:
    REAL_LISTINGS = []

LISTINGS = REAL_LISTINGS if REAL_LISTINGS else DEMO_LISTINGS

# ===== SELLER PROFILE CHECK =====
seller_profile = None
try:
    sp = db.table("seller_profiles").select("*").eq("user_id", user.id).execute()
    seller_profile = sp.data[0] if sp.data else None
except:
    seller_profile = None

has_seller_profile = seller_profile is not None

# ===== RENDER CARD FUNCTION =====
def render_card(listing, idx):
    crop = listing.get('crop', 'Unknown')
    variety = listing.get('variety', '')
    price = listing.get('price', 0)
    location = listing.get('location', 'Unknown')
    state = listing.get('state', '')
    farmer = listing.get('farmer', 'Unknown')
    rating = listing.get('rating', 4.5)
    organic = listing.get('organic', False)
    featured = listing.get('featured', False)
    seller_type = listing.get('seller_type', 'Verified Farmer')
    image = listing.get('image', '🌱')
    phone = listing.get('phone', '')
    whatsapp = listing.get('whatsapp', phone)
    lid = listing.get('id', str(idx))
    
    full_stars = int(rating)
    stars_html = "⭐" * full_stars
    
    st.markdown(f"""
    <div class="jiji-card">
        <div class="image-area" style="background: linear-gradient(135deg, {'#e8f5e9' if organic else '#f5f5f5'}, {'#c8e6c9' if organic else '#e0e0e0'});">
            <span style="font-size:3.5rem;">{image}</span>
            {('<div class="featured-badge">⭐ Featured</div>' if featured else '')}
            {('<div class="organic-badge">🌿</div>' if organic else '')}
        </div>
        <div class="info-area">
            <div class="crop-name">{crop}</div>
            {('<div style="font-size:0.75rem;color:#888;">' + variety + '</div>' if variety else '')}
            <div class="price">₦{price:,} <small>/ {listing.get('unit','tonnes')}</small></div>
            <div class="location">📍 {location}, {state}</div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
                <span class="seller-badge {'verified' if 'Verified' in seller_type else 'premium' if 'Premium' in seller_type else 'organic'}">{seller_type}</span>
                <span class="stars">{stars_html} {rating}</span>
            </div>
            <div class="seller" style="margin-top:6px;">👨‍🌾 {farmer}</div>
            <div class="seller">📞 {phone or 'N/A'} | 💬 {whatsapp or 'N/A'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🛒 Add", key=f"add_{lid}_{idx}", use_container_width=True):
            st.session_state.cart.append(listing)
            st.success(f"Added {crop}!")
            st.rerun()
    with col2:
        if st.button("📞 Contact", key=f"contact_{lid}_{idx}", use_container_width=True):
            seller_uid = listing.get('user_id', '')
            if seller_uid and seller_uid != 'demo':
                st.session_state.active_chat = seller_uid
                st.switch_page("pages/16_Chat.py")
            else:
                st.info(f"📞 Call/WhatsApp {farmer}: {phone}")
                st.info(f"💬 WhatsApp: {whatsapp}")
    with col3:
        if st.button("ℹ️ Details", key=f"details_{lid}_{idx}", use_container_width=True):
            with st.expander("📋 Full Details", expanded=True):
                st.write(f"**Crop:** {crop}")
                st.write(f"**Variety:** {variety or 'N/A'}")
                st.write(f"**Quantity:** {listing.get('quantity','')} {listing.get('unit','tonnes')}")
                st.write(f"**Price:** ₦{price:,} per {listing.get('unit','tonnes')}")
                st.write(f"**Location:** {location}, {state}")
                st.write(f"**Seller:** {farmer} ({seller_type})")
                st.write(f"**Rating:** {stars_html} ({rating})")
                st.write(f"**Organic:** {'🌿 Yes' if organic else 'No'}")
                st.write(f"**Harvest Date:** {listing.get('harvest_date','N/A')}")
                st.write(f"**Phone:** {phone or 'N/A'}")
                st.write(f"**WhatsApp:** {whatsapp or 'N/A'}")
                if listing.get('description'):
                    st.write(f"**Description:** {listing.get('description','')}")

# ===== JIJI-STYLE CSS =====

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
