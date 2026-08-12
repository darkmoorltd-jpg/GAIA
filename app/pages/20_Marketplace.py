
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime, timedelta
import uuid
import random

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
if "market_view" not in st.session_state:
    st.session_state.market_view = "browse"
if "selected_listing" not in st.session_state:
    st.session_state.selected_listing = None

# ===== FETCH REAL LISTINGS =====
try:
    real_listings = db.table("marketplace_listings").select("*").eq("status", "active").order("created_at", desc=True).execute()
    REAL_LISTINGS = real_listings.data if real_listings.data else []
except:
    REAL_LISTINGS = []

# ===== DEMO DATA =====
DEMO_LISTINGS = [
    {"id":"1","crop":"Maize","variety":"SAMMAZ 15","quantity":20,"unit":"tonnes","price":220000,"location":"Kaduna","state":"Kaduna","farmer":"Ibrahim Musa","rating":4.8,"image":"🌽","harvest_date":"2025-10-15","organic":True,"description":"High-yield hybrid maize. Drought resistant. Germination 98%. Suitable for flour and feed. Ready for immediate delivery.","seller_type":"Verified Farmer","featured":True},
    {"id":"2","crop":"Rice","variety":"FARO 44","quantity":15,"unit":"tonnes","price":350000,"location":"Kano","state":"Kano","farmer":"Aisha Bello","rating":4.9,"image":"🌾","harvest_date":"2025-09-28","organic":False,"description":"Premium long-grain rice. Milled and polished. Perfect for restaurants and households.","seller_type":"Premium Seller","featured":True},
    {"id":"3","crop":"Beans","variety":"IT89KD-288","quantity":8,"unit":"tonnes","price":480000,"location":"Jos","state":"Plateau","farmer":"David Okonkwo","rating":4.7,"image":"🫘","harvest_date":"2025-08-20","organic":True,"description":"Organic honey beans. High protein. No pesticides. Export quality.","seller_type":"Organic Certified","featured":False},
    {"id":"4","crop":"Tomatoes","variety":"Roma VF","quantity":5,"unit":"tonnes","price":180000,"location":"Zaria","state":"Kaduna","farmer":"Fatima Yusuf","rating":4.6,"image":"🍅","harvest_date":"2025-10-05","organic":False,"description":"Fresh Roma tomatoes. Firm, red, perfect for paste and sauce. Harvested this week.","seller_type":"Verified Farmer","featured":False},
    {"id":"5","crop":"Groundnuts","variety":"SAMNUT 23","quantity":12,"unit":"tonnes","price":380000,"location":"Katsina","state":"Katsina","farmer":"Usman Sani","rating":4.5,"image":"🥜","harvest_date":"2025-11-01","organic":True,"description":"High-oil content groundnuts. Grade A. Suitable for oil processing and snacks.","seller_type":"Organic Certified","featured":False},
    {"id":"6","crop":"Yam","variety":"Dioscorea rotundata","quantity":25,"unit":"tonnes","price":550000,"location":"Makurdi","state":"Benue","farmer":"John Tarka","rating":4.9,"image":"🍠","harvest_date":"2025-12-10","organic":True,"description":"Premium white yam tubers. Large size. Disease-free. Benue's finest.","seller_type":"Premium Seller","featured":True},
    {"id":"7","crop":"Sorghum","variety":"SAMSORG 17","quantity":30,"unit":"tonnes","price":160000,"location":"Bauchi","state":"Bauchi","farmer":"Musa Abubakar","rating":4.4,"image":"🌱","harvest_date":"2025-11-20","organic":False,"description":"Drought-resistant sorghum. Ideal for brewing and animal feed.","seller_type":"Verified Farmer","featured":False},
    {"id":"8","crop":"Cassava","variety":"TME 419","quantity":40,"unit":"tonnes","price":120000,"location":"Ondo","state":"Ondo","farmer":"Grace Adeyemi","rating":4.6,"image":"🥔","harvest_date":"2025-10-30","organic":True,"description":"High-starch cassava. Perfect for garri and flour processing.","seller_type":"Organic Certified","featured":False},
    {"id":"9","crop":"Onions","variety":"Red Creole","quantity":10,"unit":"tonnes","price":250000,"location":"Sokoto","state":"Sokoto","farmer":"Alhaji Bello","rating":4.3,"image":"🧅","harvest_date":"2025-11-05","organic":False,"description":"Large red onions. Well-cured. Long shelf life.","seller_type":"Verified Farmer","featured":False},
    {"id":"10","crop":"Pepper","variety":"Scotch Bonnet","quantity":3,"unit":"tonnes","price":600000,"location":"Jos","state":"Plateau","farmer":"Sarah Luka","rating":4.8,"image":"🌶️","harvest_date":"2025-10-20","organic":True,"description":"Hot scotch bonnet peppers. Organic. Perfect for spice markets.","seller_type":"Premium Seller","featured":True},
]

LISTINGS = REAL_LISTINGS if REAL_LISTINGS else DEMO_LISTINGS

# ===== JIJI-STYLE CSS =====
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    
    .stApp { background: #f5f5f5; color: #222; }
    header, footer { visibility: hidden; }
    
    /* Top search bar */
    .search-bar {
        background: #fff; border-radius: 12px; padding: 12px 20px;
        display: flex; align-items: center; gap: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 16px;
    }
    .search-bar input {
        border: none; outline: none; font-size: 1rem; flex: 1; background: transparent;
    }
    
    /* Category pills */
    .category-pill {
        display: inline-block; padding: 8px 16px; border-radius: 20px;
        background: #fff; color: #555; font-size: 0.85rem; font-weight: 500;
        margin: 4px; cursor: pointer; border: 1px solid #e0e0e0;
        transition: all 0.2s; white-space: nowrap;
    }
    .category-pill.active { background: #2e7d32; color: #fff; border-color: #2e7d32; }
    .category-pill:hover { background: #e8f5e9; }
    
    /* Product card – Jiji style */
    .jiji-card {
        background: #fff; border-radius: 12px; overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06); transition: all 0.2s;
        cursor: pointer; position: relative;
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
    
    /* Stars */
    .stars { color: #ffc107; font-size: 0.85rem; }
    
    /* Bottom nav */
    .bottom-nav {
        position: fixed; bottom: 0; left: 0; right: 0; background: #fff;
        display: flex; justify-content: space-around; padding: 10px 0;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.08); z-index: 1000;
    }
    .bottom-nav a {
        text-align: center; color: #888; text-decoration: none;
        font-size: 0.7rem; display: flex; flex-direction: column; align-items: center; gap: 2px;
    }
    .bottom-nav a.active { color: #2e7d32; }
    .bottom-nav .icon { font-size: 1.3rem; }
    
    /* Listing detail modal */
    .detail-overlay {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.6); z-index: 999;
        display: flex; align-items: center; justify-content: center;
    }
    .detail-card {
        background: #fff; border-radius: 16px; padding: 24px;
        max-width: 500px; width: 90%; max-height: 80vh; overflow-y: auto;
    }
    
    /* Seller badge */
    .seller-badge {
        display: inline-block; padding: 2px 8px; border-radius: 4px;
        font-size: 0.65rem; font-weight: 600;
    }
    .seller-badge.verified { background: #e3f2fd; color: #1565c0; }
    .seller-badge.premium { background: #fff3e0; color: #e65100; }
    .seller-badge.organic { background: #e8f5e9; color: #2e7d32; }
    
    /* Chat button */
    .chat-btn {
        background: #25d366; color: #fff; border: none; padding: 10px 20px;
        border-radius: 8px; font-weight: 600; cursor: pointer; width: 100%;
    }
    
    /* Hide Streamlit elements */
    .stButton button {
        background: #2e7d32 !important; color: #fff !important;
        border: none !important; border-radius: 8px !important;
        font-weight: 600 !important; width: 100% !important;
    }
    .stButton button:hover { background: #1b5e20 !important; }
    
    /* Cart floating button */
    .cart-float {
        position: fixed; bottom: 80px; right: 20px;
        background: #2e7d32; color: #fff; width: 56px; height: 56px;
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        font-size: 1.5rem; box-shadow: 0 4px 12px rgba(46,125,50,0.4);
        cursor: pointer; z-index: 998;
    }
    .cart-badge {
        position: absolute; top: -4px; right: -4px;
        background: #f44336; color: #fff; width: 22px; height: 22px;
        border-radius: 50%; font-size: 0.7rem; display: flex;
        align-items: center; justify-content: center; font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ===== TOP SEARCH BAR =====
col1, col2 = st.columns([5, 1])
with col1:
    search = st.text_input("", placeholder="🔍 Search crops, varieties, or locations...", label_visibility="collapsed", key="jiji_search")
with col2:
    location_filter = st.selectbox("", ["📍 All Nigeria"] + sorted(list(set(l.get("state","") for l in LISTINGS if l.get("state")))), label_visibility="collapsed", key="jiji_location")

# ===== CATEGORY PILLS =====
CATEGORIES = ["All", "Grains", "Legumes", "Vegetables", "Tubers", "Oil Seeds", "Fruits"]
category_map = {
    "Grains": ["Maize","Rice","Sorghum","Millet"],
    "Legumes": ["Beans","Groundnuts","Soybean"],
    "Vegetables": ["Tomatoes","Onions","Pepper","Cabbage"],
    "Tubers": ["Yam","Cassava","Potato"],
    "Oil Seeds": ["Groundnuts","Soybean"],
    "Fruits": ["Mango","Orange","Banana"]
}

selected_cat = st.session_state.get("selected_category", "All")
cols = st.columns(len(CATEGORIES))
for i, cat in enumerate(CATEGORIES):
    with cols[i]:
        if st.button(cat, key=f"cat_{cat}", use_container_width=True,
                     type="primary" if selected_cat == cat else "secondary"):
            st.session_state.selected_category = cat
            st.rerun()

selected_cat = st.session_state.get("selected_category", "All")

# ===== FILTER LISTINGS =====
filtered = LISTINGS
if search:
    s = search.lower()
    filtered = [l for l in filtered if s in str(l.get('crop','')).lower() or s in str(l.get('variety','')).lower() or s in str(l.get('location','')).lower() or s in str(l.get('farmer','')).lower() or s in str(l.get('description','')).lower()]
if location_filter != "📍 All Nigeria":
    filtered = [l for l in filtered if l.get("state") == location_filter]
if selected_cat != "All":
    cat_crops = category_map.get(selected_cat, [])
    filtered = [l for l in filtered if l.get("crop") in cat_crops]

# ===== PRODUCT GRID =====
st.markdown(f"### {len(filtered)} results found")

# Featured section
featured = [l for l in filtered if l.get("featured")]
if featured:
    st.markdown("#### ⭐ Featured Listings")
    cols = st.columns(min(len(featured), 4))
    for i, listing in enumerate(featured[:4]):
        with cols[i % 4]:
            render_card(listing, db, user)

# All listings
if filtered:
    st.markdown("#### All Listings")
    rows = [filtered[i:i+4] for i in range(0, len(filtered), 4)]
    for row in rows:
        cols = st.columns(len(row))
        for i, listing in enumerate(row):
            with cols[i]:
                render_card(listing, db, user)
else:
    st.info("No listings found. Try a different search or category.")

# ===== BOTTOM NAVIGATION =====
st.markdown("""
<div class="bottom-nav">
    <a href="/~/1_Dashboard" class="active"><span class="icon">🏠</span>Home</a>
    <a href="/~/20_Marketplace"><span class="icon">🛒</span>Market</a>
    <a href="/~/2_Crops"><span class="icon">🌿</span>Diagnose</a>
    <a href="/~/16_Chat"><span class="icon">💬</span>Chat</a>
    <a href="/~/8_Profile"><span class="icon">👤</span>Me</a>
</div>
""", unsafe_allow_html=True)

# ===== FLOATING CART BUTTON =====
cart_count = len(st.session_state.cart)
st.markdown(f"""
<div class="cart-float" onclick="document.getElementById('cart-anchor').scrollIntoView()">
    🛒
    {f'<div class="cart-badge">{cart_count}</div>' if cart_count > 0 else ''}
</div>
""", unsafe_allow_html=True)

# ===== CART SIDEBAR (at the bottom) =====
st.markdown('<div id="cart-anchor"></div>', unsafe_allow_html=True)
with st.expander(f"🛒 Shopping Cart ({cart_count} items)", expanded=cart_count > 0):
    if not st.session_state.cart:
        st.write("Your cart is empty.")
    else:
        total = 0
        for item in st.session_state.cart:
            crop = item.get('crop', 'Unknown')
            price = item.get('price', 0)
            st.write(f"**{crop}** — ₦{price:,}")
            total += price
        st.markdown(f"**Total: ₦{total:,}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💳 Pay with Paystack", use_container_width=True):
                ref = f"GAIA_MKT_{user.id[:8]}_{uuid.uuid4().hex[:8]}"
                components.html(f"""
                <script src="https://js.paystack.co/v1/inline.js"></script>
                <script>
                    PaystackPop.setup({{
                        key: '{PAYSTACK_PUBLIC}',
                        email: '{user.email}',
                        amount: {total * 100},
                        currency: 'NGN',
                        ref: '{ref}',
                        label: 'GAIA Market',
                        onClose: function() {{ window.location.reload(); }},
                        callback: function(r) {{ window.location.href = '/~/callback?reference=' + r.reference + '&plan=marketplace'; }}
                    }}).openIframe();
                </script>
                """, height=0)
        with col2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.cart = []
                st.rerun()

# ===== HELPER: RENDER A PRODUCT CARD =====
def render_card(listing, db, user):
    crop = listing.get('crop', 'Unknown')
    variety = listing.get('variety', '')
    price = listing.get('price', 0)
    location = listing.get('location', 'Unknown')
    state = listing.get('state', '')
    farmer = listing.get('farmer', 'Unknown')
    rating = listing.get('rating', 4.5)
    organic = listing.get('organic', False)
    featured = listing.get('featured', False)
    description = listing.get('description', '')
    image = listing.get('image', '🌱')
    seller_type = listing.get('seller_type', 'Verified Farmer')
    
    # Generate star display
    full_stars = int(rating)
    half_star = (rating - full_stars) >= 0.5
    stars_html = "⭐" * full_stars
    if half_star:
        stars_html += "⭐"
    
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
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🛒 Add", key=f"add_{listing.get('id','')}", use_container_width=True):
            st.session_state.cart.append(listing)
            st.success(f"Added {crop}!")
            st.rerun()
    with col2:
        if st.button("📞 Chat", key=f"chat_{listing.get('id','')}", use_container_width=True):
            st.session_state.active_chat = listing.get('user_id', '')
            st.switch_page("pages/16_Chat.py")
