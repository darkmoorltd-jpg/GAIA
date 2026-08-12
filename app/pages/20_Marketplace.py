
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime, timedelta
import uuid
import base64
import requests

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
if "market_tab" not in st.session_state:
    st.session_state.market_tab = "browse"

# ===== FETCH REAL LISTINGS =====
try:
    real_listings = db.table("marketplace_listings").select("*").eq("status", "active").order("created_at", desc=True).execute()
    REAL_LISTINGS = real_listings.data if real_listings.data else []
except:
    REAL_LISTINGS = []

# ===== DEMO DATA (shown when no real listings exist) =====
DEMO_LISTINGS = [
    {"id":"demo1","crop":"Maize","variety":"SAMMAZ 15","quantity":20,"unit":"tonnes","price":220000,"location":"Kaduna","state":"Kaduna","farmer":"Ibrahim Musa","user_id":"demo","rating":4.8,"image":"🌽","harvest_date":"2025-10-15","organic":True,"description":"High-yield hybrid maize. Drought resistant. Germination 98%.","seller_type":"Verified Farmer","featured":True,"phone":"0803-XXX-XXXX"},
    {"id":"demo2","crop":"Rice","variety":"FARO 44","quantity":15,"unit":"tonnes","price":350000,"location":"Kano","state":"Kano","farmer":"Aisha Bello","user_id":"demo","rating":4.9,"image":"🌾","harvest_date":"2025-09-28","organic":False,"description":"Premium long-grain rice. Milled and polished.","seller_type":"Premium Seller","featured":True,"phone":"0805-XXX-XXXX"},
    {"id":"demo3","crop":"Beans","variety":"IT89KD-288","quantity":8,"unit":"tonnes","price":480000,"location":"Jos","state":"Plateau","farmer":"David Okonkwo","user_id":"demo","rating":4.7,"image":"🫘","harvest_date":"2025-08-20","organic":True,"description":"Organic honey beans. High protein.","seller_type":"Organic Certified","featured":False,"phone":"0802-XXX-XXXX"},
    {"id":"demo4","crop":"Tomatoes","variety":"Roma VF","quantity":5,"unit":"tonnes","price":180000,"location":"Zaria","state":"Kaduna","farmer":"Fatima Yusuf","user_id":"demo","rating":4.6,"image":"🍅","harvest_date":"2025-10-05","organic":False,"description":"Fresh Roma tomatoes. Firm and red.","seller_type":"Verified Farmer","featured":False,"phone":"0806-XXX-XXXX"},
    {"id":"demo5","crop":"Groundnuts","variety":"SAMNUT 23","quantity":12,"unit":"tonnes","price":380000,"location":"Katsina","state":"Katsina","farmer":"Usman Sani","user_id":"demo","rating":4.5,"image":"🥜","harvest_date":"2025-11-01","organic":True,"description":"High-oil content groundnuts. Grade A.","seller_type":"Organic Certified","featured":False,"phone":"0809-XXX-XXXX"},
    {"id":"demo6","crop":"Yam","variety":"Dioscorea rotundata","quantity":25,"unit":"tonnes","price":550000,"location":"Makurdi","state":"Benue","farmer":"John Tarka","user_id":"demo","rating":4.9,"image":"🍠","harvest_date":"2025-12-10","organic":True,"description":"Premium white yam tubers.","seller_type":"Premium Seller","featured":True,"phone":"0804-XXX-XXXX"},
    {"id":"demo7","crop":"Sorghum","variety":"SAMSORG 17","quantity":30,"unit":"tonnes","price":160000,"location":"Bauchi","state":"Bauchi","farmer":"Musa Abubakar","user_id":"demo","rating":4.4,"image":"🌱","harvest_date":"2025-11-20","organic":False,"description":"Drought-resistant sorghum.","seller_type":"Verified Farmer","featured":False,"phone":"0807-XXX-XXXX"},
    {"id":"demo8","crop":"Cassava","variety":"TME 419","quantity":40,"unit":"tonnes","price":120000,"location":"Ondo","state":"Ondo","farmer":"Grace Adeyemi","user_id":"demo","rating":4.6,"image":"🥔","harvest_date":"2025-10-30","organic":True,"description":"High-starch cassava.","seller_type":"Organic Certified","featured":False,"phone":"0801-XXX-XXXX"},
    {"id":"demo9","crop":"Onions","variety":"Red Creole","quantity":10,"unit":"tonnes","price":250000,"location":"Sokoto","state":"Sokoto","farmer":"Alhaji Bello","user_id":"demo","rating":4.3,"image":"🧅","harvest_date":"2025-11-05","organic":False,"description":"Large red onions. Well-cured.","seller_type":"Verified Farmer","featured":False,"phone":"0808-XXX-XXXX"},
    {"id":"demo10","crop":"Pepper","variety":"Scotch Bonnet","quantity":3,"unit":"tonnes","price":600000,"location":"Jos","state":"Plateau","farmer":"Sarah Luka","user_id":"demo","rating":4.8,"image":"🌶️","harvest_date":"2025-10-20","organic":True,"description":"Hot scotch bonnet peppers.","seller_type":"Premium Seller","featured":True,"phone":"0810-XXX-XXXX"},
]

LISTINGS = REAL_LISTINGS if REAL_LISTINGS else DEMO_LISTINGS

# ===== JIJI-STYLE CSS =====
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    
    .stApp { background: #f5f5f5; color: #222; }
    header, footer { visibility: hidden; }
    
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
    
    /* Seller badge */
    .seller-badge {
        display: inline-block; padding: 2px 8px; border-radius: 4px;
        font-size: 0.65rem; font-weight: 600;
    }
    .seller-badge.verified { background: #e3f2fd; color: #1565c0; }
    .seller-badge.premium { background: #fff3e0; color: #e65100; }
    .seller-badge.organic { background: #e8f5e9; color: #2e7d32; }
    
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
    
    /* Seller dashboard cards */
    .seller-stat-card {
        background: #fff; border-radius: 12px; padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06); text-align: center;
    }
    .seller-stat-card .stat-number { font-size: 2rem; font-weight: 800; color: #2e7d32; }
    .seller-stat-card .stat-label { font-size: 0.8rem; color: #888; margin-top: 4px; }
    
    .stButton button {
        background: #2e7d32 !important; color: #fff !important;
        border: none !important; border-radius: 8px !important;
        font-weight: 600 !important; width: 100% !important;
    }
    .stButton button:hover { background: #1b5e20 !important; }
</style>


""", unsafe_allow_html=True)

# ===== MAIN TABS =====
tab1, tab2, tab3, tab4 = st.tabs(["🛒 Browse Market", "📝 Sell Produce", "👤 My Store", "📦 My Orders"])

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

# ===== TAB 1: BROWSE MARKET =====
with tab1:
    col1, col2 = st.columns([5, 1])
    with col1:
        search = st.text_input("", placeholder="🔍 Search crops, varieties, or locations...", label_visibility="collapsed", key="jiji_search")
    with col2:
        location_filter = st.selectbox("", ["📍 All Nigeria"] + sorted(list(set(l.get("state","") for l in LISTINGS if l.get("state")))), label_visibility="collapsed", key="jiji_location")
    
    # Category pills
    selected_cat = st.session_state.get("selected_category", "All")
    cols = st.columns(len(CATEGORIES))
    for i, cat in enumerate(CATEGORIES):
        with cols[i]:
            if st.button(cat, key=f"cat_{cat}", use_container_width=True,
                         type="primary" if selected_cat == cat else "secondary"):
                st.session_state.selected_category = cat
                st.rerun()
    
    selected_cat = st.session_state.get("selected_category", "All")
    
    # Filter
    filtered = LISTINGS
    if search:
        s = search.lower()
        filtered = [l for l in filtered if s in str(l.get('crop','')).lower() or s in str(l.get('variety','')).lower() or s in str(l.get('location','')).lower() or s in str(l.get('farmer','')).lower()]
    if location_filter != "📍 All Nigeria":
        filtered = [l for l in filtered if l.get("state") == location_filter]
    if selected_cat != "All":
        cat_crops = category_map.get(selected_cat, [])
        filtered = [l for l in filtered if l.get("crop") in cat_crops]
    
    st.markdown(f"### {len(filtered)} results found")
    
    # Featured first
    featured = [l for l in filtered if l.get("featured")]
    if featured:
        st.markdown("#### ⭐ Featured")
        cols = st.columns(min(len(featured), 4))
        for i, listing in enumerate(featured[:4]):
            with cols[i % 4]:
                render_card(listing)
    
    if filtered:
        st.markdown("#### All Listings")
        rows = [filtered[i:i+4] for i in range(0, len(filtered), 4)]
        for row in rows:
            cols = st.columns(len(row))
            for i, listing in enumerate(row):
                with cols[i]:
                    render_card(listing)
    else:
        st.info("No listings match your search. Try a different category or location.")

# ===== TAB 2: SELL PRODUCE =====
with tab2:
    st.markdown("## 📝 List Your Produce for Sale")
    st.markdown("*Fill in the details below to list your produce on the GAIA Marketplace.*")
    
    with st.form("sell_produce_form"):
        col1, col2 = st.columns(2)
        with col1:
            crop_name = st.text_input("🌾 Crop Name *", placeholder="e.g., Maize, Rice, Beans, Yam")
            variety = st.text_input("🧬 Variety (optional)", placeholder="e.g., SAMMAZ 15, FARO 44")
            quantity = st.number_input("📦 Quantity Available *", min_value=1, max_value=100000, value=10, step=1)
        with col2:
            price = st.number_input("💰 Price per Unit (₦) *", min_value=500, max_value=50000000, value=200000, step=10000, format="%d")
            unit = st.selectbox("📏 Unit", ["tonnes", "kg", "bags", "baskets", "trucks", "crates", "bunches"])
            location = st.text_input("📍 Location (City) *", placeholder="e.g., Kaduna, Kano, Lagos")
        
        state = st.text_input("🗺️ State *", placeholder="e.g., Kaduna, Kano, Lagos")
        
        col1, col2 = st.columns(2)
        with col1:
            harvest_date = st.date_input("📅 Harvest Date", min_value=datetime.now().date(), help="When was or will this produce be harvested?")
        with col2:
            organic = st.checkbox("🌿 Organic Certified", help="Check if your produce is organically grown")
        
        description = st.text_area("📝 Description", placeholder="Describe your produce – quality, size, germination rate, any certifications, delivery options...", max_chars=500)
        
        # Photo upload
        st.markdown("### 📸 Add Photos (optional)")
        uploaded_photos = st.file_uploader("Upload up to 5 photos of your produce", type=["jpg","jpeg","png"], accept_multiple_files=True, help="Clear photos help you sell faster!")
        
        if uploaded_photos:
            cols = st.columns(min(len(uploaded_photos), 5))
            for i, photo in enumerate(uploaded_photos[:5]):
                with cols[i]:
                    st.image(photo, caption=f"Photo {i+1}", width=100)
        
        submit = st.form_submit_button("📤 List My Produce", type="primary", use_container_width=True)
        
        if submit:
            if not crop_name or not location or not state:
                st.error("❌ Crop name, location, and state are required.")
            elif price <= 0:
                st.error("❌ Price must be greater than zero.")
            else:
                with st.spinner("📤 Publishing your listing..."):
                    try:
                        # Get seller info
                        profile = db.table("user_profiles").select("first_name,last_name,phone").eq("user_id", user.id).execute()
                        profile_data = profile.data[0] if profile.data else {}
                        farmer_name = f"{profile_data.get('first_name','')} {profile_data.get('last_name','')}".strip()
                        if not farmer_name:
                            farmer_name = user.email.split('@')[0]
                        phone = profile_data.get("phone", "")
                        
                        # Insert listing
                        listing_data = {
                            "user_id": user.id,
                            "crop": crop_name.strip(),
                            "variety": variety.strip() if variety else None,
                            "quantity": quantity,
                            "unit": unit,
                            "price": price,
                            "location": location.strip(),
                            "state": state.strip(),
                            "description": description.strip(),
                            "organic": organic,
                            "harvest_date": harvest_date.isoformat(),
                            "status": "active",
                            "farmer": farmer_name,
                            "phone": phone
                        }
                        
                        result = db.table("marketplace_listings").insert(listing_data).execute()
                        
                        if result.data:
                            st.success(f"✅ Your {crop_name} has been listed successfully! Buyers can now find it in the marketplace.")
                            st.balloons()
                            st.info("💡 Tip: Listings with photos get 3x more inquiries. Add photos next time for better results!")
                        else:
                            st.error("Failed to create listing. Please try again.")
                    except Exception as e:
                        st.error(f"Error: {str(e)[:200]}")

# ===== TAB 3: MY STORE =====
with tab3:
    st.markdown("## 👤 My Store")
    
    # Fetch seller's listings
    try:
        my_listings = db.table("marketplace_listings").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
        store_listings = my_listings.data if my_listings.data else []
    except:
        store_listings = []
    
    # Stats
    active_count = sum(1 for l in store_listings if l.get("status") == "active")
    sold_count = sum(1 for l in store_listings if l.get("status") == "sold")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="seller-stat-card"><div class="stat-number">{len(store_listings)}</div><div class="stat-label">Total Listings</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="seller-stat-card"><div class="stat-number">{active_count}</div><div class="stat-label">Active</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="seller-stat-card"><div class="stat-number">{sold_count}</div><div class="stat-label">Sold</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    if not store_listings:
        st.info("📝 You haven't listed any produce yet. Go to the **Sell Produce** tab to start selling!")
        if st.button("📝 List My First Produce", use_container_width=True):
            st.session_state.market_tab = "sell"
            st.rerun()
    else:
        for listing in store_listings:
            status = listing.get("status", "active")
            status_emoji = {"active": "🟢", "inactive": "🔴", "sold": "✅"}.get(status, "⚪")
            
            with st.expander(f"{status_emoji} {listing.get('crop','')} — ₦{listing.get('price',0):,} ({status.upper()})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Variety:** {listing.get('variety','N/A')}")
                    st.write(f"**Quantity:** {listing.get('quantity','')} {listing.get('unit','tonnes')}")
                    st.write(f"**Location:** {listing.get('location','')}, {listing.get('state','')}")
                with col2:
                    st.write(f"**Listed:** {listing.get('created_at','')[:10]}")
                    st.write(f"**Harvest:** {listing.get('harvest_date','')}")
                    st.write(f"**Organic:** {'🌿 Yes' if listing.get('organic') else 'No'}")
                
                if listing.get("description"):
                    st.write(f"**Description:** {listing.get('description','')[:200]}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if status == "active":
                        if st.button("🔴 Deactivate", key=f"deact_{listing['id']}", use_container_width=True):
                            db.table("marketplace_listings").update({"status": "inactive"}).eq("id", listing["id"]).execute()
                            st.success("Listing deactivated.")
                            st.rerun()
                    elif status == "inactive":
                        if st.button("🟢 Reactivate", key=f"react_{listing['id']}", use_container_width=True):
                            db.table("marketplace_listings").update({"status": "active"}).eq("id", listing["id"]).execute()
                            st.success("Listing reactivated!")
                            st.rerun()
                with col2:
                    if status == "active":
                        if st.button("✅ Mark as Sold", key=f"sold_{listing['id']}", use_container_width=True):
                            db.table("marketplace_listings").update({"status": "sold"}).eq("id", listing["id"]).execute()
                            st.success("Marked as sold!")
                            st.rerun()
                with col3:
                    if st.button("🗑️ Delete", key=f"del_{listing['id']}", use_container_width=True):
                        db.table("marketplace_listings").delete().eq("id", listing["id"]).execute()
                        st.success("Listing deleted.")
                        st.rerun()

# ===== TAB 4: MY ORDERS =====
with tab4:
    st.markdown("## 📦 My Orders")
    st.markdown("*Track your purchases and sales.*")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🛒 As Buyer")
        try:
            buyer_orders = db.table("marketplace_orders").select("*").eq("buyer_id", user.id).order("created_at", desc=True).execute()
            orders = buyer_orders.data if buyer_orders.data else []
        except:
            orders = []
        
        if not orders:
            st.info("No purchases yet. Browse the market to find produce!")
        else:
            for order in orders:
                status = order.get("status", "pending")
                emoji = {"pending":"⏳","confirmed":"✅","shipped":"🚚","delivered":"📦","cancelled":"❌"}.get(status, "⏳")
                with st.expander(f"{emoji} Order #{order.get('id','?')} — {status.upper()}"):
                    st.write(f"**Amount:** ₦{order.get('total_amount',0):,}")
                    st.write(f"**Date:** {order.get('created_at','')[:10]}")
                    st.write(f"**Reference:** {order.get('payment_reference','N/A')}")
    
    with col2:
        st.markdown("### 💰 As Seller")
        try:
            seller_orders = db.table("marketplace_orders").select("*").eq("seller_id", user.id).order("created_at", desc=True).execute()
            s_orders = seller_orders.data if seller_orders.data else []
        except:
            s_orders = []
        
        if not s_orders:
            st.info("No sales yet. Your listings are visible to buyers!")
        else:
            for order in s_orders:
                status = order.get("status", "pending")
                emoji = {"pending":"⏳","confirmed":"✅","shipped":"🚚","delivered":"📦","cancelled":"❌"}.get(status, "⏳")
                with st.expander(f"{emoji} Sale #{order.get('id','?')} — {status.upper()}"):
                    st.write(f"**Amount:** ₦{order.get('total_amount',0):,}")
                    st.write(f"**Date:** {order.get('created_at','')[:10]}")

# ===== CART SECTION =====
st.markdown("---")
with st.expander(f"🛒 Shopping Cart ({len(st.session_state.cart)} items)", expanded=len(st.session_state.cart) > 0):
    if not st.session_state.cart:
        st.write("Your cart is empty. Browse the market and add items!")
    else:
        total = 0
        for item in st.session_state.cart:
            crop = item.get('crop', 'Unknown')
            price = item.get('price', 0)
            qty = item.get('quantity', 0)
            unit = item.get('unit', 'tonnes')
            total += price
            st.write(f"**{crop}** ({qty} {unit}) — ₦{price:,}")
        
        st.markdown(f"### Total: ₦{total:,}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💳 Pay with Paystack", use_container_width=True, type="primary"):
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
            if st.button("🗑️ Clear Cart", use_container_width=True):
                st.session_state.cart = []
                st.rerun()
        with col3:
            if st.button("📞 Contact Sellers", use_container_width=True):
                st.switch_page("pages/16_Chat.py")

# ===== BOTTOM NAVIGATION =====
st.markdown("""
<div class="bottom-nav">
    <a href="/~/1_Dashboard"><span class="icon">🏠</span>Home</a>
    <a href="/~/20_Marketplace" class="active"><span class="icon">🛒</span>Market</a>
    <a href="/~/2_Crops"><span class="icon">🌿</span>Diagnose</a>
    <a href="/~/16_Chat"><span class="icon">💬</span>Chat</a>
    <a href="/~/8_Profile"><span class="icon">👤</span>Me</a>
</div>
""", unsafe_allow_html=True)

# ===== FLOATING CART =====
cart_count = len(st.session_state.cart)
st.markdown(f"""
<div class="cart-float" onclick="window.location.href='#cart-section'">
    🛒
    {f'<div class="cart-badge">{cart_count}</div>' if cart_count > 0 else ''}
</div>
""", unsafe_allow_html=True)

# ===== RENDER CARD HELPER =====
def render_card(listing):
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
            <div class="seller" style="margin-top:6px;">👨‍🌾 {farmer}{(' · 📞 ' + phone) if phone else ''}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🛒 Add to Cart", key=f"add_{listing.get('id','')}", use_container_width=True):
            st.session_state.cart.append(listing)
            st.success(f"Added {crop}!")
            st.rerun()
    with col2:
        if st.button("📞 Contact", key=f"contact_{listing.get('id','')}", use_container_width=True):
            seller_id = listing.get('user_id', '')
            if seller_id and seller_id != 'demo':
                st.session_state.active_chat = seller_id
                st.switch_page("pages/16_Chat.py")
            else:
                st.info(f"📞 Contact {farmer} via GAIA Chat or phone: {phone}")
    with col3:
        if st.button("ℹ️ Details", key=f"details_{listing.get('id','')}", use_container_width=True):
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
                if listing.get('description'):
                    st.write(f"**Description:** {listing.get('description','')}")
