
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime
import uuid

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

if "cart" not in st.session_state:
    st.session_state.cart = []

DEMO_LISTINGS = [
    {"id":"1","crop":"Maize","variety":"SAMMAZ 15","quantity":20,"unit":"tonnes","price":220000,"location":"Kaduna","state":"Kaduna","farmer":"Ibrahim Musa","rating":4.8,"image":"🌽","harvest_date":"2025-10-15","organic":True,"description":"High-yield hybrid maize. Drought resistant. Germination 98%."},
    {"id":"2","crop":"Rice","variety":"FARO 44","quantity":15,"unit":"tonnes","price":350000,"location":"Kano","state":"Kano","farmer":"Aisha Bello","rating":4.9,"image":"🌾","harvest_date":"2025-09-28","organic":False,"description":"Premium long-grain rice. Milled and polished. Ready for market."},
    {"id":"3","crop":"Beans","variety":"IT89KD-288","quantity":8,"unit":"tonnes","price":480000,"location":"Jos","state":"Plateau","farmer":"David Okonkwo","rating":4.7,"image":"🫘","harvest_date":"2025-08-20","organic":True,"description":"Organic honey beans. High protein. No pesticides."},
    {"id":"4","crop":"Tomatoes","variety":"Roma VF","quantity":5,"unit":"tonnes","price":180000,"location":"Zaria","state":"Kaduna","farmer":"Fatima Yusuf","rating":4.6,"image":"🍅","harvest_date":"2025-10-05","organic":False,"description":"Fresh Roma tomatoes. Firm, red, perfect for paste."},
    {"id":"5","crop":"Groundnuts","variety":"SAMNUT 23","quantity":12,"unit":"tonnes","price":380000,"location":"Katsina","state":"Katsina","farmer":"Usman Sani","rating":4.5,"image":"🥜","harvest_date":"2025-11-01","organic":True,"description":"High-oil content groundnuts. Grade A."},
    {"id":"6","crop":"Yam","variety":"Dioscorea rotundata","quantity":25,"unit":"tonnes","price":550000,"location":"Makurdi","state":"Benue","farmer":"John Tarka","rating":4.9,"image":"🍠","harvest_date":"2025-12-10","organic":True,"description":"Premium white yam tubers. Large size. Disease-free."},
    {"id":"7","crop":"Sorghum","variety":"SAMSORG 17","quantity":30,"unit":"tonnes","price":160000,"location":"Bauchi","state":"Bauchi","farmer":"Musa Abubakar","rating":4.4,"image":"🌱","harvest_date":"2025-11-20","organic":False,"description":"Drought-resistant sorghum. Ideal for brewing."},
    {"id":"8","crop":"Cassava","variety":"TME 419","quantity":40,"unit":"tonnes","price":120000,"location":"Ondo","state":"Ondo","farmer":"Grace Adeyemi","rating":4.6,"image":"🥔","harvest_date":"2025-10-30","organic":True,"description":"High-starch cassava. Perfect for garri processing."},
]

CATEGORIES = ["All","Grains","Legumes","Vegetables","Tubers","Oil Seeds","Fruits"]
STATES = ["All States","Kaduna","Kano","Plateau","Katsina","Benue","Bauchi","Ondo","Lagos","Abuja"]

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(160deg, #f4faf5 0%, #eaf5ee 50%, #fdfefb 100%); color: #1b5e20; }
    header, footer { visibility: hidden; }
    .marketplace-title { font-size: 3rem; font-weight: 800; text-align: center; background: linear-gradient(135deg, #1b5e20, #4caf50, #1b5e20); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.3rem; }
    .marketplace-subtitle { text-align: center; color: #607d8b; font-size: 1.1rem; margin-bottom: 2rem; }
    .product-card { background: #fff; border-radius: 20px; padding: 1.5rem; margin: 0.8rem 0; box-shadow: 0 8px 30px rgba(0,0,0,0.06); border: 1px solid #e8f5e9; transition: all 0.3s ease; }
    .product-card:hover { transform: translateY(-6px); box-shadow: 0 16px 40px rgba(46,125,50,0.15); border-color: #4caf50; }
    .product-emoji { font-size: 3rem; text-align: center; margin-bottom: 0.5rem; }
    .product-crop { font-size: 1.3rem; font-weight: 700; color: #1b5e20; }
    .product-variety { font-size: 0.9rem; color: #78909c; }
    .product-price { font-size: 1.5rem; font-weight: 800; color: #2e7d32; margin: 0.5rem 0; }
    .product-location { font-size: 0.85rem; color: #607d8b; }
    .product-farmer { font-size: 0.85rem; color: #546e7a; font-weight: 500; }
    .product-quantity { font-size: 0.9rem; color: #1b5e20; font-weight: 600; }
    .badge-organic { background: #c8e6c9; color: #2e7d32; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; display: inline-block; }
    .badge-rating { background: #fff9c4; color: #f57f17; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; display: inline-block; }
    .cart-sidebar { background: #fff; border-radius: 20px; padding: 1.5rem; box-shadow: 0 8px 30px rgba(0,0,0,0.06); }
    .cart-item { display: flex; justify-content: space-between; align-items: center; padding: 0.8rem 0; border-bottom: 1px solid #e8f5e9; }
    .cart-total { font-size: 1.3rem; font-weight: 800; color: #1b5e20; margin-top: 1rem; }
    .search-box input { background: #fff !important; border: 2px solid #e8f5e9 !important; border-radius: 16px !important; padding: 14px 20px !important; font-size: 1rem !important; }
    .search-box input:focus { border-color: #4caf50 !important; box-shadow: 0 0 0 3px rgba(76,175,80,0.1) !important; }
    .stButton button { background: linear-gradient(135deg, #2e7d32, #4caf50) !important; color: #fff !important; border: none !important; border-radius: 14px !important; padding: 12px 28px !important; font-weight: 600 !important; transition: all 0.3s !important; }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(46,125,50,0.3); }
    .stats-card { background: linear-gradient(135deg, #1b5e20, #2e7d32); color: #fff; border-radius: 20px; padding: 2rem; text-align: center; margin: 0.5rem 0; }
    .stats-number { font-size: 2.5rem; font-weight: 800; }
    .stats-label { font-size: 0.9rem; opacity: 0.8; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="marketplace-title">🌍 GAIA Marketplace</div>', unsafe_allow_html=True)
st.markdown('<div class="marketplace-subtitle">Africa\'s Agricultural Commodity Exchange — Buy & Sell Directly</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown('<div class="stats-card"><div class="stats-number">1,247</div><div class="stats-label">Active Listings</div></div>', unsafe_allow_html=True)
with c2: st.markdown('<div class="stats-card"><div class="stats-number">₦2.8B</div><div class="stats-label">Total Traded</div></div>', unsafe_allow_html=True)
with c3: st.markdown('<div class="stats-card"><div class="stats-number">8,500+</div><div class="stats-label">Verified Farmers</div></div>', unsafe_allow_html=True)
with c4: st.markdown('<div class="stats-card"><div class="stats-number">36</div><div class="stats-label">States Covered</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Browse Market", "📊 My Orders", "📝 List Produce", "👤 My Store"])

with tab1:
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: search = st.text_input("🔍 Search crops, varieties, or locations...", placeholder="e.g., Maize in Kaduna", key="market_search", label_visibility="collapsed")
    with col2: category = st.selectbox("Category", CATEGORIES, key="cat_filter")
    with col3: state_filter = st.selectbox("State", STATES, key="state_filter")
    
    filtered = DEMO_LISTINGS
    if search:
        s = search.lower()
        filtered = [l for l in filtered if s in l['crop'].lower() or s in l['variety'].lower() or s in l['location'].lower() or s in l['farmer'].lower()]
    if state_filter != "All States":
        filtered = [l for l in filtered if l['state'] == state_filter]
    
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
                    <div class="product-quantity">📦 {listing['quantity']} {listing['unit']}</div>
                    <div class="product-location">📍 {listing['location']}, {listing['state']}</div>
                    <div class="product-farmer">👨‍🌾 {listing['farmer']}</div>
                    <div style="display:flex;gap:8px;margin:8px 0;">
                        <span class="badge-organic">{'🌿 Organic' if listing['organic'] else '⚗️ Conventional'}</span>
                        <span class="badge-rating">⭐ {listing['rating']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                cbtn1, cbtn2 = st.columns(2)
                if cbtn1.button("🛒 Add", key=f"add_{listing['id']}", use_container_width=True):
                    st.session_state.cart.append(listing)
                    st.success(f"Added {listing['crop']}!")
                    st.rerun()
                if cbtn2.button("📞 Contact", key=f"contact_{listing['id']}", use_container_width=True):
                    st.info(f"📞 Contact {listing['farmer']}")
    else:
        st.info("No listings match your search.")

with tab2:
    st.markdown("### 📊 My Orders")
    demo_orders = [
        {"id":"ORD-001","item":"Maize (SAMMAZ 15)","quantity":"5 tonnes","total":"₦1,100,000","seller":"Ibrahim Musa","status":"Delivered","date":"2025-08-10"},
        {"id":"ORD-002","item":"Rice (FARO 44)","quantity":"3 tonnes","total":"₦1,050,000","seller":"Aisha Bello","status":"In Transit","date":"2025-08-11"},
        {"id":"ORD-003","item":"Groundnuts","quantity":"2 tonnes","total":"₦760,000","seller":"Usman Sani","status":"Pending","date":"2025-08-12"},
    ]
    for order in demo_orders:
        with st.expander(f"📦 {order['id']} — {order['item']} — {order['status']}"):
            c1, c2 = st.columns(2)
            c1.write(f"**Quantity:** {order['quantity']}")
            c1.write(f"**Total:** {order['total']}")
            c1.write(f"**Seller:** {order['seller']}")
            c2.write(f"**Date:** {order['date']}")
            c2.write(f"**Status:** {order['status']}")

with tab3:
    st.markdown("### 📝 List Your Produce")
    with st.form("list_produce"):
        c1, c2 = st.columns(2)
        with c1:
            crop_name = st.text_input("Crop Name *", placeholder="e.g., Maize")
            variety = st.text_input("Variety", placeholder="e.g., SAMMAZ 15")
            quantity = st.number_input("Quantity *", min_value=1, max_value=10000, value=10)
        with c2:
            price = st.number_input("Price per Unit (₦) *", min_value=1000, max_value=10000000, value=200000, step=10000)
            unit = st.selectbox("Unit", ["tonnes","kg","bags","baskets","trucks"])
            location = st.text_input("Location *", placeholder="e.g., Kaduna")
        harvest_date = st.date_input("Harvest Date", min_value=datetime.now().date())
        organic = st.checkbox("🌿 Organic Certified")
        description = st.text_area("Description", max_chars=300)
        if st.form_submit_button("📤 List Produce"):
            st.success("✅ Listed! Buyers can now find your produce.")
            st.balloons()

with tab4:
    st.markdown("### 👤 My Store")
    c1, c2, c3 = st.columns(3)
    c1.metric("Listings", "0")
    c2.metric("Sales", "₦0")
    c3.metric("Rating", "⭐ New Seller")
    st.info("📝 List your first produce in the 'List Produce' tab!")

with st.sidebar:
    st.markdown("### 🛒 Cart")
    if not st.session_state.cart:
        st.write("Empty.")
    else:
        total = 0
        for item in st.session_state.cart:
            st.write(f"**{item['crop']}** — ₦{item['price']:,}")
            total += item['price']
        st.markdown(f"**Total: ₦{total:,}**")
        if st.button("💳 Checkout (Escrow)", type="primary", use_container_width=True):
            components.html(f"""
            <script src="https://js.paystack.co/v1/inline.js"></script>
            <script>
                PaystackPop.setup({{
                    key: 'pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057',
                    email: '{user.email}',
                    amount: {total * 100},
                    currency: 'NGN',
                    ref: 'GAIA_MKT_{uuid.uuid4().hex[:8]}',
                    label: 'GAIA Marketplace',
                    onClose: function() {{ window.location.reload(); }},
                    callback: function(r) {{ window.location.href = '/~/callback?reference=' + r.reference + '&plan=marketplace'; }}
                }}).openIframe();
            </script>
            """, height=0)
        if st.button("🗑️ Clear"): st.session_state.cart = []; st.rerun()

st.markdown("---")
cols = st.columns(9)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/20_Marketplace.py", label="🌍 Market")
with cols[6]: st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[7]: st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[8]: st.page_link("pages/10_Early_Warning.py", label="🛰️ Early Warning")
