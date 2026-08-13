import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime, timedelta
import uuid
from app.utils.phone_util import normalize_phone

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

if "cart" not in st.session_state:
    st.session_state.cart = []

DEMO_LISTINGS = [
    {"id":"demo1","crop":"Maize","variety":"SAMMAZ 15","quantity":20,"unit":"tonnes","price":220000,"location":"Kaduna","state":"Kaduna","farmer":"Ibrahim Musa","user_id":"demo","rating":4.8,"image":"🌽","harvest_date":"2025-10-15","organic":True,"description":"High-yield hybrid maize.","seller_type":"Verified Farmer","featured":True,"phone":"0803-XXX-XXXX","whatsapp":"0803-XXX-XXXX"},
    {"id":"demo2","crop":"Rice","variety":"FARO 44","quantity":15,"unit":"tonnes","price":350000,"location":"Kano","state":"Kano","farmer":"Aisha Bello","user_id":"demo","rating":4.9,"image":"🌾","harvest_date":"2025-09-28","organic":False,"description":"Premium long-grain rice.","seller_type":"Premium Seller","featured":True,"phone":"0805-XXX-XXXX","whatsapp":"0805-XXX-XXXX"},
    {"id":"demo3","crop":"Beans","variety":"IT89KD-288","quantity":8,"unit":"tonnes","price":480000,"location":"Jos","state":"Plateau","farmer":"David Okonkwo","user_id":"demo","rating":4.7,"image":"🫘","harvest_date":"2025-08-20","organic":True,"description":"Organic honey beans.","seller_type":"Organic Certified","featured":False,"phone":"0802-XXX-XXXX","whatsapp":"0802-XXX-XXXX"},
    {"id":"demo4","crop":"Tomatoes","variety":"Roma VF","quantity":5,"unit":"tonnes","price":180000,"location":"Zaria","state":"Kaduna","farmer":"Fatima Yusuf","user_id":"demo","rating":4.6,"image":"🍅","harvest_date":"2025-10-05","organic":False,"description":"Fresh Roma tomatoes.","seller_type":"Verified Farmer","featured":False,"phone":"0806-XXX-XXXX","whatsapp":"0806-XXX-XXXX"},
    {"id":"demo5","crop":"Yam","variety":"Dioscorea rotundata","quantity":25,"unit":"tonnes","price":550000,"location":"Makurdi","state":"Benue","farmer":"John Tarka","user_id":"demo","rating":4.9,"image":"🍠","harvest_date":"2025-12-10","organic":True,"description":"Premium white yam tubers.","seller_type":"Premium Seller","featured":True,"phone":"0804-XXX-XXXX","whatsapp":"0804-XXX-XXXX"},
    {"id":"demo6","crop":"Cassava","variety":"TME 419","quantity":40,"unit":"tonnes","price":120000,"location":"Ondo","state":"Ondo","farmer":"Grace Adeyemi","user_id":"demo","rating":4.6,"image":"🥔","harvest_date":"2025-10-30","organic":True,"description":"High-starch cassava.","seller_type":"Organic Certified","featured":False,"phone":"0801-XXX-XXXX","whatsapp":"0801-XXX-XXXX"},
]

LISTINGS = DEMO_LISTINGS

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #f5f5f5; color: #222; }
    header, footer { visibility: hidden; }
    .jiji-card {
        background: #fff; border-radius: 12px; overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06); transition: all 0.2s;
        cursor: pointer; position: relative; margin-bottom: 16px;
    }
    .jiji-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.12); }
    .jiji-card .image-area {
        height: 160px; background: #f0f0f0; display: flex; align-items: center;
        justify-content: center; font-size: 3rem; position: relative;
    }
    .jiji-card .featured-badge {
        position: absolute; top: 8px; left: 8px;
        background: #ff9800; color: #fff; padding: 4px 10px;
        border-radius: 4px; font-size: 0.7rem; font-weight: 700;
    }
    .jiji-card .organic-badge {
        position: absolute; top: 8px; right: 8px;
        background: #4caf50; color: #fff; padding: 4px 8px;
        border-radius: 4px; font-size: 0.65rem; font-weight: 600;
    }
    .jiji-card .info-area { padding: 12px; }
    .jiji-card .crop-name { font-size: 1rem; font-weight: 600; color: #222; margin-bottom: 4px; }
    .jiji-card .price { font-size: 1.2rem; font-weight: 800; color: #2e7d32; }
    .jiji-card .price small { font-size: 0.75rem; color: #999; font-weight: 400; }
    .jiji-card .location { font-size: 0.8rem; color: #888; margin-top: 4px; }
    .jiji-card .seller { font-size: 0.75rem; color: #aaa; margin-top: 2px; }
    .stars { color: #ffc107; font-size: 0.85rem; }
    .seller-badge {
        display: inline-block; padding: 2px 8px; border-radius: 4px;
        font-size: 0.65rem; font-weight: 600;
    }
    .seller-badge.verified { background: #e3f2fd; color: #1565c0; }
    .seller-badge.premium { background: #fff3e0; color: #e65100; }
    .seller-badge.organic { background: #e8f5e9; color: #2e7d32; }
    .stButton button {
        background: #2e7d32 !important; color: #fff !important;
        border: none !important; border-radius: 8px !important;
        font-weight: 600 !important; width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div style="font-size:2.5rem;font-weight:800;text-align:center;color:#2e7d32;">🌍 GAIA Market</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;color:#607d8b;margin-bottom:2rem;">Buy and sell farm produce directly</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Browse Market", "📝 Sell Produce", "👤 My Store", "📦 My Orders"])

with tab1:
    search = st.text_input("", placeholder="🔍 Search crops, varieties, or locations...", label_visibility="collapsed", key="market_search")
    
    featured = [l for l in LISTINGS if l.get("featured")]
    regular = [l for l in LISTINGS if not l.get("featured")]
    
    if featured:
        st.markdown("### ⭐ Featured Listings")
        cols = st.columns(3)
        for i, listing in enumerate(featured[:3]):
            with cols[i]:
                crop = listing.get('crop', 'Unknown')
                price = listing.get('price', 0)
                location = listing.get('location', '')
                state = listing.get('state', '')
                image = listing.get('image', '🌱')
                organic = listing.get('organic', False)
                rating = listing.get('rating', 4.5)
                stars_html = "⭐" * int(rating)
                
                organic_style = '#e8f5e9' if organic else '#f5f5f5'
                organic_style2 = '#c8e6c9' if organic else '#e0e0e0'
                
                st.markdown(
                    '<div class="jiji-card">'
                    '<div class="image-area" style="background: linear-gradient(135deg, ' + organic_style + ', ' + organic_style2 + ');">'
                    '<span style="font-size:3.5rem;">' + image + '</span>'
                    '<div class="featured-badge">⭐ Featured</div>'
                    '</div>'
                    '<div class="info-area">'
                    '<div class="crop-name">' + crop + '</div>'
                    '<div class="price">₦' + format(price, ',') + ' <small>/ tonnes</small></div>'
                    '<div class="location">📍 ' + location + ', ' + state + '</div>'
                    '<span class="stars">' + stars_html + ' ' + str(rating) + '</span>'
                    '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
    
    st.markdown("### 📋 All Listings")
    cols = st.columns(3)
    for i, listing in enumerate(regular[:6]):
        with cols[i % 3]:
            crop = listing.get('crop', 'Unknown')
            price = listing.get('price', 0)
            location = listing.get('location', '')
            state = listing.get('state', '')
            image = listing.get('image', '🌱')
            organic = listing.get('organic', False)
            rating = listing.get('rating', 4.5)
            stars_html = "⭐" * int(rating)
            
            organic_style = '#e8f5e9' if organic else '#f5f5f5'
            organic_style2 = '#c8e6c9' if organic else '#e0e0e0'
            organic_badge = '<div class="organic-badge">🌿</div>' if organic else ''
            
            st.markdown(
                '<div class="jiji-card">'
                '<div class="image-area" style="background: linear-gradient(135deg, ' + organic_style + ', ' + organic_style2 + ');">'
                '<span style="font-size:3.5rem;">' + image + '</span>'
                + organic_badge +
                '</div>'
                '<div class="info-area">'
                '<div class="crop-name">' + crop + '</div>'
                '<div class="price">₦' + format(price, ',') + ' <small>/ tonnes</small></div>'
                '<div class="location">📍 ' + location + ', ' + state + '</div>'
                '<span class="stars">' + stars_html + ' ' + str(rating) + '</span>'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )

with tab2:
    st.markdown("### 📝 Sell Your Produce")
    st.info("Sell produce feature coming soon. Contact support to list your produce.")

with tab3:
    st.markdown("### 👤 My Store")
    st.info("Your store listings will appear here.")

with tab4:
    st.markdown("### 📦 My Orders")
    st.info("Your orders will appear here.")

st.markdown("---")
st.caption("Powered by Darkmoor Ltd")

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
