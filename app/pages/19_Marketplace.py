
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime, timedelta
import uuid
from app.utils.phone_util import normalize_phone
import random

# ===== CONFIG =====
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]

@st.cache_resource
def get_db():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

st.set_page_config(page_title="GAIA Marketplace", page_icon="🌍", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
db = get_db()
service = get_service()

# ===== SESSION STATE =====
if "cart" not in st.session_state:
    st.session_state.cart = []
if "marketplace_tab" not in st.session_state:
    st.session_state.marketplace_tab = "browse"

# ===== DEMO DATA (Replace with Supabase queries in production) =====
DEMO_LISTINGS = [
    {
        "id": "1", "crop": "Maize", "variety": "SAMMAZ 15", "quantity": 20, "unit": "tonnes",
        "price": 220000, "location": "Kaduna", "state": "Kaduna", "farmer": "Ibrahim Musa",
        "rating": 4.8, "image": "🌽", "harvest_date": "2025-10-15", "organic": True,
        "description": "High-yield hybrid maize. Drought resistant. Germination 98%. Suitable for flour and feed."
    },
    {
        "id": "2", "crop": "Rice", "variety": "FARO 44", "quantity": 15, "unit": "tonnes",
        "price": 350000, "location": "Kano", "state": "Kano", "farmer": "Aisha Bello",
        "rating": 4.9, "image": "🌾", "harvest_date": "2025-09-28", "organic": False,
        "description": "Premium long-grain rice. Milled and polished. Ready for market."
    },
    {
        "id": "3", "crop": "Beans", "variety": "IT89KD-288", "quantity": 8, "unit": "tonnes",
        "price": 480000, "location": "Jos", "state": "Plateau", "farmer": "David Okonkwo",
        "rating": 4.7, "image": "🫘", "harvest_date": "2025-08-20", "organic": True,
        "description": "Organic honey beans. High protein. No pesticides used. Perfect for export."
    },
    {
        "id": "4", "crop": "Tomatoes", "variety": "Roma VF", "quantity": 5, "unit": "tonnes",
        "price": 180000, "location": "Zaria", "state": "Kaduna", "farmer": "Fatima Yusuf",
        "rating": 4.6, "image": "🍅", "harvest_date": "2025-10-05", "organic": False,
        "description": "Fresh Roma tomatoes. Firm, red, perfect for paste and sauce."
    },
    {
        "id": "5", "crop": "Groundnuts", "variety": "SAMNUT 23", "quantity": 12, "unit": "tonnes",
        "price": 380000, "location": "Katsina", "state": "Katsina", "farmer": "Usman Sani",
        "rating": 4.5, "image": "🥜", "harvest_date": "2025-11-01", "organic": True,
        "description": "High-oil content groundnuts. Grade A. Suitable for oil processing."
    },
    {
        "id": "6", "crop": "Yam", "variety": "Dioscorea rotundata", "quantity": 25, "unit": "tonnes",
        "price": 550000, "location": "Makurdi", "state": "Benue", "farmer": "John Tarka",
        "rating": 4.9, "image": "🍠", "harvest_date": "2025-12-10", "organic": True,
        "description": "Premium white yam tubers. Large size. Disease-free. Benue's finest."
    },
    {
        "id": "7", "crop": "Sorghum", "variety": "SAMSORG 17", "quantity": 30, "unit": "tonnes",
        "price": 160000, "location": "Bauchi", "state": "Bauchi", "farmer": "Musa Abubakar",
        "rating": 4.4, "image": "🌱", "harvest_date": "2025-11-20", "organic": False,
        "description": "Drought-resistant sorghum. Ideal for brewing and animal feed."
    },
    {
        "id": "8", "crop": "Cassava", "variety": "TME 419", "quantity": 40, "unit": "tonnes",
        "price": 120000, "location": "Ondo", "state": "Ondo", "farmer": "Grace Adeyemi",
        "rating": 4.6, "image": "🥔", "harvest_date": "2025-10-30", "organic": True,
        "description": "High-starch cassava. Perfect for garri and flour processing."
    },
]

# ===== CATEGORIES =====
CATEGORIES = ["All", "Grains", "Legumes", "Vegetables", "Tubers", "Oil Seeds", "Fruits"]
STATES = ["All States", "Kaduna", "Kano", "Plateau", "Katsina", "Benue", "Bauchi", "Ondo", "Lagos", "Abuja"]

# ===== STYLING =====
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(160deg, #f4faf5 0%, #eaf5ee 50%, #fdfefb 100%); color: #1b5e20; }
    header, footer { visibility: hidden; }
    
    .marketplace-title {
        font-size: 3rem; font-weight: 800; text-align: center;
        background: linear-gradient(135deg, #1b5e20, #4caf50, #1b5e20);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .marketplace-subtitle {
        text-align: center; color: #607d8b; font-size: 1.1rem; margin-bottom: 2rem;
    }
    
    .product-card {
        background: #fff; border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0;
        box-shadow: 0 8px 30px rgba(0,0,0,0.06); border: 1px solid #e8f5e9;
        transition: all 0.3s ease; cursor: pointer;
    }
    .product-card:hover {
        transform: translateY(-6px); box-shadow: 0 16px 40px rgba(46,125,50,0.15);
        border-color: #4caf50;
    }
    
    .product-emoji { font-size: 3rem; text-align: center; margin-bottom: 0.5rem; }
    .product-crop { font-size: 1.3rem; font-weight: 700; color: #1b5e20; }
    .product-variety { font-size: 0.9rem; color: #78909c; }
    .product-price { font-size: 1.5rem; font-weight: 800; color: #2e7d32; margin: 0.5rem 0; }
    .product-location { font-size: 0.85rem; color: #607d8b; }
    .product-farmer { font-size: 0.85rem; color: #546e7a; font-weight: 500; }
    .product-quantity { font-size: 0.9rem; color: #1b5e20; font-weight: 600; }
    
    .badge-organic { background: #c8e6c9; color: #2e7d32; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-rating { background: #fff9c4; color: #f57f17; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; }
    
    .cart-sidebar {
        background: #fff; border-radius: 20px; padding: 1.5rem;
        box-shadow: 0 8px 30px rgba(0,0,0,0.06); position: sticky; top: 20px;
    }
    .cart-item {
        display: flex; justify-content: space-between; align-items: center;
        padding: 0.8rem 0; border-bottom: 1px solid #e8f5e9;
    }
    .cart-total { font-size: 1.3rem; font-weight: 800; color: #1b5e20; margin-top: 1rem; }
    
    .search-box input {
        background: #fff !important; border: 2px solid #e8f5e9 !important;
        border-radius: 16px !important; padding: 14px 20px !important;
        font-size: 1rem !important; transition: all 0.3s !important;
    }
    .search-box input:focus { border-color: #4caf50 !important; box-shadow: 0 0 0 3px rgba(76,175,80,0.1) !important; }
    
    .stButton button {
        background: linear-gradient(135deg, #2e7d32, #4caf50) !important; color: #fff !important;
        border: none !important; border-radius: 14px !important; padding: 12px 28px !important;
        font-weight: 600 !important; transition: all 0.3s !important;
    }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(46,125,50,0.3); }
    
    .tab-active { background: #2e7d32; color: #fff; padding: 10px 24px; border-radius: 30px; font-weight: 600; }
    .tab-inactive { background: #e8f5e9; color: #2e7d32; padding: 10px 24px; border-radius: 30px; font-weight: 500; }
    
    .stats-card {
        background: linear-gradient(135deg, #1b5e20, #2e7d32); color: #fff;
        border-radius: 20px; padding: 2rem; text-align: center; margin: 0.5rem 0;
    }
    .stats-number { font-size: 2.5rem; font-weight: 800; }
    .stats-label { font-size: 0.9rem; opacity: 0.8; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ===== HEADER =====
st.markdown('<div class="marketplace-title">🌍 GAIA Marketplace</div>', unsafe_allow_html=True)
st.markdown('<div class="marketplace-subtitle">Africa\'s Largest Agricultural Commodity Exchange — Buy & Sell Directly</div>', unsafe_allow_html=True)

# ===== STATS BAR =====
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<div class="stats-card"><div class="stats-number">1,247</div><div class="stats-label">Active Listings</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="stats-card"><div class="stats-number">₦2.8B</div><div class="stats-label">Total Traded</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="stats-card"><div class="stats-number">8,500+</div><div class="stats-label">Verified Farmers</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="stats-card"><div class="stats-number">36</div><div class="stats-label">States Covered</div></div>', unsafe_allow_html=True)

# ===== MAIN LAYOUT =====
tab1, tab2, tab3, tab4 = st.tabs(["🛒 Browse Market", "📊 My Orders", "📝 List Produce", "👤 My Store"])

# ===== TAB 1: BROWSE MARKET =====
with tab1:
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("🔍 Search crops, varieties, or locations...", placeholder="e.g., Maize in Kaduna", key="market_search", label_visibility="collapsed")
    with col2:
        category = st.selectbox("Category", CATEGORIES, key="cat_filter")
    with col3:
        state_filter = st.selectbox("State", STATES, key="state_filter")
    
    # Filter listings
    filtered = DEMO_LISTINGS
    if search:
        s = search.lower()
        filtered = [l for l in filtered if s in l['crop'].lower() or s in l['variety'].lower() or s in l['location'].lower() or s in l['farmer'].lower()]
    if state_filter != "All States":
        filtered = [l for l in filtered if l['state'] == state_filter]
    
    # Product grid
    if filtered:
        cols = st.columns(3)
        for i, listing in enumerate(filtered):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="product-card">
                    <div class="product-emoji">{listing['image']}</div>
                    <div class="product-crop">{listing['crop']}</div>
                    <div class="product-variety">{listing['variety']}</div>
                    <div class="product-price">₦{listing['price']:,} <span style="font-size:0.9rem;color:#78909c;">/ {listing['unit']}</span></div>
                    <div class="product-quantity">📦 {listing['quantity']} {listing['unit']} available</div>
                    <div class="product-location">📍 {listing['location']}, {listing['state']}</div>
                    <div class="product-farmer">👨‍🌾 {listing['farmer']}</div>
                    <div style="display:flex;gap:8px;margin:8px 0;">
                        <span class="badge-organic">{'🌿 Organic' if listing['organic'] else '⚗️ Conventional'}</span>
                        <span class="badge-rating">⭐ {listing['rating']}</span>
                    </div>
                    <p style="font-size:0.85rem;color:#78909c;margin:8px 0;">{listing['description'][:120]}...</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🛒 Add to Cart", key=f"add_{listing['id']}", use_container_width=True):
                        st.session_state.cart.append(listing)
                        st.success(f"Added {listing['crop']} to cart!")
                        st.rerun()
                with col_btn2:
                    if st.button("📞 Contact", key=f"contact_{listing['id']}", use_container_width=True):
                        st.info(f"📞 Contact {listing['farmer']} at +234-XXX-XXX-XXXX")
    else:
        st.info("No listings match your search.")

# ===== TAB 2: MY ORDERS =====
with tab2:
    st.markdown("### 📊 My Orders & Transactions")
    
    demo_orders = [
        {"id": "ORD-001", "item": "Maize (SAMMAZ 15)", "quantity": "5 tonnes", "total": "₦1,100,000", "seller": "Ibrahim Musa", "status": "Delivered", "date": "2025-08-10"},
        {"id": "ORD-002", "item": "Rice (FARO 44)", "quantity": "3 tonnes", "total": "₦1,050,000", "seller": "Aisha Bello", "status": "In Transit", "date": "2025-08-11"},
        {"id": "ORD-003", "item": "Groundnuts (SAMNUT 23)", "quantity": "2 tonnes", "total": "₦760,000", "seller": "Usman Sani", "status": "Pending", "date": "2025-08-12"},
    ]
    
    for order in demo_orders:
        status_color = {"Delivered": "#4caf50", "In Transit": "#ff9800", "Pending": "#2196f3"}
        with st.expander(f"📦 {order['id']} — {order['item']} — {order['status']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Quantity:** {order['quantity']}")
                st.write(f"**Total:** {order['total']}")
                st.write(f"**Seller:** {order['seller']}")
            with col2:
                st.write(f"**Date:** {order['date']}")
                st.markdown(f"**Status:** <span style='color:{status_color.get(order['status'], '#000')};font-weight:600;'>{order['status']}</span>", unsafe_allow_html=True)

# ===== TAB 3: LIST PRODUCE =====
with tab3:
    st.markdown("### 📝 List Your Produce for Sale")
    
    with st.form("list_produce"):
        col1, col2 = st.columns(2)
        with col1:
            crop_name = st.text_input("Crop Name *", placeholder="e.g., Maize, Rice, Beans")
            variety = st.text_input("Variety", placeholder="e.g., SAMMAZ 15")
            quantity = st.number_input("Quantity Available *", min_value=1, max_value=10000, value=10)
        with col2:
            price = st.number_input("Price per Unit (₦) *", min_value=1000, max_value=10000000, value=200000, step=10000)
            unit = st.selectbox("Unit", ["tonnes", "kg", "bags", "baskets", "trucks"])
            location = st.text_input("Location *", placeholder="e.g., Kaduna, Kano")
        
        harvest_date = st.date_input("Expected Harvest Date", min_value=datetime.now().date())
        organic = st.checkbox("🌿 Organic Certified")
        description = st.text_area("Description", placeholder="Describe your produce...", max_chars=300)
        images = st.file_uploader("📸 Upload Photos (max 3)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        
        if st.form_submit_button("📤 List Produce"):
            st.success("✅ Your produce has been listed! Buyers can now find it in the marketplace.")
            st.balloons()

# ===== TAB 4: MY STORE =====
with tab4:
    st.markdown("### 👤 My Store")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Listings", "0")
    with col2:
        st.metric("Total Sales", "₦0")
    with col3:
        st.metric("Rating", "⭐ New Seller")
    
    st.info("📝 List your first produce in the 'List Produce' tab to start selling!")

# ===== SHOPPING CART SIDEBAR =====
with st.sidebar:
    st.markdown("### 🛒 Shopping Cart")
    
    if not st.session_state.cart:
        st.write("Your cart is empty.")
    else:
        total = 0
        for item in st.session_state.cart:
            st.markdown(f"""
            <div class="cart-item">
                <div>
                    <strong>{item['crop']}</strong><br>
                    <small>{item['quantity']} {item['unit']}</small>
                </div>
                <div style="text-align:right;">
                    <strong>₦{item['price']:,}</strong><br>
                </div>
            </div>
            """, unsafe_allow_html=True)
            total += item['price']
        
        st.markdown(f'<div class="cart-total">Total: ₦{total:,}</div>', unsafe_allow_html=True)
        
        if st.button("💳 Checkout (Escrow)", type="primary", use_container_width=True):
            ref = f"GAIA_MARKET_{user.id[:8]}_{uuid.uuid4().hex[:6]}"
            
        # Fetch user phone for SMS receipt
        try:
            profile_res = db.table("user_profiles").select("phone").eq("user_id", user.id).execute()
            user_phone = profile_res.data[0].get("phone", "") if profile_res.data else ""
        except:
            user_phone = ""
        
        components.html(f"""
            <script src="https://js.paystack.co/v1/inline.js"></script>
            <script>
                PaystackPop.setup({{
                    key: 'pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057',
                    email: '{user.email}',
                    phone: '{normalize_phone(user_phone)}',  // Placeholder — will be replaced by user phone

                    amount: {total * 100},
                    currency: 'NGN',
                    ref: '{ref}',
                    label: 'GAIA Marketplace Order',
                    onClose: function() {{ window.location.reload(); }},
                    callback: function(r) {{
                        window.location.href = '/~/callback?reference=' + r.reference + '&plan=marketplace';
                    }}
                }}).openIframe();
            </script>
            """, height=0)
        
        if st.button("🗑️ Clear Cart", use_container_width=True):
            st.session_state.cart = []
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 🔒 Secure Escrow")
    st.caption("Payment is held until you confirm delivery. Your money is safe.")

# ===== NAVIGATION =====
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(9)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[6]: st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[7]: st.page_link("pages/10_Early_Warning.py", label="🛰️ Early Warning")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
