
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime, timedelta
import uuid

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

# ===== SELLER PROFILE =====
seller_profile = None
try:
    sp = db.table("seller_profiles").select("*").eq("user_id", user.id).execute()
    seller_profile = sp.data[0] if sp.data else None
except:
    seller_profile = None

has_seller_profile = seller_profile is not None

# ===== DEMO DATA =====
DEMO_LISTINGS = [
    {"id":"demo1","crop":"Maize","variety":"SAMMAZ 15","quantity":20,"unit":"tonnes","price":220000,"location":"Kaduna","state":"Kaduna","farmer":"Ibrahim Musa","user_id":"demo","rating":4.8,"image":"🌽","harvest_date":"2025-10-15","organic":True,"description":"High-yield hybrid maize. Drought resistant. Germination 98%.","seller_type":"Verified Farmer","featured":True,"phone":"0803-XXX-XXXX"},
    {"id":"demo2","crop":"Rice","variety":"FARO 44","quantity":15,"unit":"tonnes","price":350000,"location":"Kano","state":"Kano","farmer":"Aisha Bello","user_id":"demo","rating":4.9,"image":"🌾","harvest_date":"2025-09-28","organic":False,"description":"Premium long-grain rice. Milled and polished.","seller_type":"Premium Seller","featured":True,"phone":"0805-XXX-XXXX"},
    {"id":"demo3","crop":"Beans","variety":"IT89KD-288","quantity":8,"unit":"tonnes","price":480000,"location":"Jos","state":"Plateau","farmer":"David Okonkwo","user_id":"demo","rating":4.7,"image":"🫘","harvest_date":"2025-08-20","organic":True,"description":"Organic honey beans. High protein.","seller_type":"Organic Certified","featured":False,"phone":"0802-XXX-XXXX"},
    {"id":"demo4","crop":"Tomatoes","variety":"Roma VF","quantity":5,"unit":"tonnes","price":180000,"location":"Zaria","state":"Kaduna","farmer":"Fatima Yusuf","user_id":"demo","rating":4.6,"image":"🍅","harvest_date":"2025-10-05","organic":False,"description":"Fresh Roma tomatoes. Firm and red.","seller_type":"Verified Farmer","featured":False,"phone":"0806-XXX-XXXX"},
    {"id":"demo5","crop":"Yam","variety":"Dioscorea rotundata","quantity":25,"unit":"tonnes","price":550000,"location":"Makurdi","state":"Benue","farmer":"John Tarka","user_id":"demo","rating":4.9,"image":"🍠","harvest_date":"2025-12-10","organic":True,"description":"Premium white yam tubers.","seller_type":"Premium Seller","featured":True,"phone":"0804-XXX-XXXX"},
    {"id":"demo6","crop":"Cassava","variety":"TME 419","quantity":40,"unit":"tonnes","price":120000,"location":"Ondo","state":"Ondo","farmer":"Grace Adeyemi","user_id":"demo","rating":4.6,"image":"🥔","harvest_date":"2025-10-30","organic":True,"description":"High-starch cassava.","seller_type":"Organic Certified","featured":False,"phone":"0801-XXX-XXXX"},
]

# ===== FETCH REAL LISTINGS =====
try:
    real_listings = db.table("marketplace_listings").select("*").eq("status", "active").order("created_at", desc=True).execute()
    REAL_LISTINGS = real_listings.data if real_listings.data else []
except:
    REAL_LISTINGS = []

LISTINGS = REAL_LISTINGS if REAL_LISTINGS else DEMO_LISTINGS

# ===== RENDER CARD =====
def render_card(listing, idx=0):
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
    uid = uuid.uuid4().hex[:8]
    
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
        if st.button("🛒 Add to Cart", key=f"add_{uid}", use_container_width=True):
            st.session_state.cart.append(listing)
            st.success(f"Added {crop}!")
            st.rerun()
    with col2:
        if st.button("📞 Contact", key=f"contact_{uid}", use_container_width=True):
            seller_id = listing.get('user_id', '')
            if seller_id and seller_id != 'demo':
                st.session_state.active_chat = seller_id
                st.switch_page("pages/16_Chat.py")
            else:
                st.info(f"📞 Contact {farmer}\n📱 {phone}")
    with col3:
        if st.button("ℹ️ Details", key=f"details_{uid}", use_container_width=True):
            with st.expander("📋 Full Details", expanded=True):
                st.write(f"**Crop:** {crop}")
                st.write(f"**Variety:** {variety or 'N/A'}")
                st.write(f"**Quantity:** {listing.get('quantity','')} {listing.get('unit','tonnes')}")
                st.write(f"**Price:** ₦{price:,} per {listing.get('unit','tonnes')}")
                st.write(f"**Location:** {location}, {state}")
                st.write(f"**Seller:** {farmer} ({seller_type})")
                st.write(f"**Phone:** {phone}")
                st.write(f"**Rating:** {stars_html} ({rating})")
                st.write(f"**Organic:** {'🌿 Yes' if organic else 'No'}")
                if listing.get('description'):
                    st.write(f"**Description:** {listing.get('description','')}")

# ===== CSS =====
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

# ===== TABS =====
tab1, tab2, tab3, tab4 = st.tabs(["🛒 Browse Market", "📝 Sell Produce", "👤 My Store", "📦 My Orders"])

# ===== TAB 1: BROWSE =====
with tab1:
    search = st.text_input("", placeholder="🔍 Search crops, varieties, or locations...", label_visibility="collapsed", key="jiji_search")
    
    featured = [l for l in LISTINGS if l.get("featured")]
    if featured:
        st.markdown("#### ⭐ Featured")
        cols = st.columns(min(len(featured), 3))
        for i, listing in enumerate(featured[:3]):
            with cols[i % 3]:
                render_card(listing, i)
    
    st.markdown("#### All Listings")
    rows = [LISTINGS[i:i+3] for i in range(0, len(LISTINGS), 3)]
    for row in rows:
        cols = st.columns(len(row))
        for i, listing in enumerate(row):
            with cols[i]:
                render_card(listing, i)

# ===== TAB 2: SELL PRODUCE =====
with tab2:
    st.markdown("## 📝 List Your Produce for Sale")
    
    if not has_seller_profile:
        st.warning("🔐 Complete your seller profile first before listing produce.")
        
        with st.form("seller_profile_form"):
            st.markdown("### 👤 Seller Registration")
            st.markdown("*Fill in all details to become a verified seller.*")
            
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("👤 Full Name *", placeholder="e.g., Ibrahim Musa")
                phone = st.text_input("📞 Phone Number *", placeholder="e.g., 08031234567")
                whatsapp = st.text_input("💬 WhatsApp Number *", placeholder="e.g., 08031234567")
                email = st.text_input("📧 Email Address *", value=user.email)
            with col2:
                address = st.text_input("🏠 Address *", placeholder="e.g., 12, Main Street")
                state = st.text_input("🗺️ State *", placeholder="e.g., Kaduna")
                lga = st.text_input("📍 LGA", placeholder="e.g., Kaduna North")
                farm_location = st.text_input("🌾 Farm Location", placeholder="e.g., Birnin Yero Village")
            
            col1, col2 = st.columns(2)
            with col1:
                farm_size = st.number_input("📐 Farm Size (acres)", min_value=0.1, value=1.0, step=0.5)
            with col2:
                years_exp = st.number_input("📅 Years of Experience", min_value=0, max_value=70, value=1)
            
            primary_crops = st.text_input("🌾 Primary Crops", placeholder="e.g., Maize, Rice, Beans")
            
            if st.form_submit_button("✅ Register as Seller", type="primary", use_container_width=True):
                if not full_name or not phone or not whatsapp or not address or not state:
                    st.error("❌ Please fill in all required fields (*).")
                else:
                    try:
                        db.table("seller_profiles").insert({
                            "user_id": user.id,
                            "full_name": full_name.strip(),
                            "phone": phone.strip(),
                            "whatsapp": whatsapp.strip(),
                            "email": email.strip(),
                            "address": address.strip(),
                            "state": state.strip(),
                            "lga": lga.strip() if lga else None,
                            "farm_location": farm_location.strip() if farm_location else None,
                            "farm_size_acres": farm_size,
                            "years_experience": years_exp,
                            "primary_crops": primary_crops.strip() if primary_crops else None
                        }).execute()
                        st.success("✅ Seller profile created! You can now list your produce.")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)[:200]}")
        
        st.stop()
    
    # Seller profile exists
    st.success(f"✅ Registered as: **{seller_profile.get('full_name','')}** | 📞 {seller_profile.get('phone','')} | 📧 {seller_profile.get('email','')}")
    
    with st.form("sell_produce_form"):
        col1, col2 = st.columns(2)
        with col1:
            crop_name = st.text_input("🌾 Crop Name *", placeholder="e.g., Maize, Rice, Beans")
            variety = st.text_input("🧬 Variety", placeholder="e.g., SAMMAZ 15")
            quantity = st.number_input("📦 Quantity *", min_value=1, value=10)
        with col2:
            price = st.number_input("💰 Price per Unit (₦) *", min_value=500, value=200000, step=10000)
            unit = st.selectbox("📏 Unit", ["tonnes", "kg", "bags", "baskets", "trucks"])
            location = st.text_input("📍 Location (City) *", placeholder="e.g., Kaduna")
        
        state = st.text_input("🗺️ State *", placeholder="e.g., Kaduna")
        harvest_date = st.date_input("📅 Harvest Date", min_value=datetime.now().date())
        organic = st.checkbox("🌿 Organic Certified")
        description = st.text_area("📝 Description", max_chars=300)
        
        if st.form_submit_button("📤 List My Produce", type="primary", use_container_width=True):
            if not crop_name or not location or not state:
                st.error("❌ Crop name, location, and state are required.")
            else:
                try:
                    farmer_name = seller_profile.get('full_name', user.email.split('@')[0])
                    farmer_phone = seller_profile.get('phone', '')
                    
                    db.table("marketplace_listings").insert({
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
                        "phone": farmer_phone
                    }).execute()
                    st.success(f"✅ Your {crop_name} has been listed!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

# ===== TAB 3: MY STORE =====
with tab3:
    st.markdown("## 👤 My Store")
    try:
        my_listings = db.table("marketplace_listings").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
        store = my_listings.data if my_listings.data else []
    except:
        store = []
    
    active = sum(1 for l in store if l.get("status") == "active")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total", len(store))
    col2.metric("Active", active)
    col3.metric("Sold", sum(1 for l in store if l.get("status") == "sold"))
    
    if not store:
        st.info("No listings yet. Go to Sell Produce to start!")
    else:
        for listing in store:
            status = listing.get("status", "active")
            with st.expander(f"{'🟢' if status=='active' else '🔴'} {listing.get('crop','')} — ₦{listing.get('price',0):,}"):
                st.write(f"**Quantity:** {listing.get('quantity','')} {listing.get('unit','tonnes')}")
                st.write(f"**Location:** {listing.get('location','')}, {listing.get('state','')}")
                c1, c2 = st.columns(2)
                if status == "active":
                    if c1.button("🔴 Deactivate", key=f"deact_{listing['id']}"):
                        db.table("marketplace_listings").update({"status": "inactive"}).eq("id", listing["id"]).execute()
                        st.rerun()
                else:
                    if c1.button("🟢 Reactivate", key=f"react_{listing['id']}"):
                        db.table("marketplace_listings").update({"status": "active"}).eq("id", listing["id"]).execute()
                        st.rerun()
                if c2.button("🗑️ Delete", key=f"del_{listing['id']}"):
                    db.table("marketplace_listings").delete().eq("id", listing["id"]).execute()
                    st.rerun()

# ===== TAB 4: MY ORDERS =====
with tab4:
    st.markdown("## 📦 My Orders")
    try:
        orders = db.table("marketplace_orders").select("*").eq("buyer_id", user.id).order("created_at", desc=True).execute()
        order_data = orders.data if orders.data else []
    except:
        order_data = []
    
    if not order_data:
        st.info("No orders yet.")
    else:
        for o in order_data:
            st.write(f"**Order #{o.get('id','?')}** — ₦{o.get('total_amount',0):,} — {o.get('status','pending')}")

# ===== CART =====
st.markdown("---")
with st.expander(f"🛒 Cart ({len(st.session_state.cart)} items)", expanded=len(st.session_state.cart) > 0):
    if not st.session_state.cart:
        st.write("Empty.")
    else:
        total = sum(item.get('price', 0) for item in st.session_state.cart)
        for item in st.session_state.cart:
            st.write(f"**{item.get('crop','')}** — ₦{item.get('price',0):,}")
        st.markdown(f"**Total: ₦{total:,}**")
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
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.cart = []
            st.rerun()

# ===== BOTTOM NAV =====
st.markdown("""
<div style="position:fixed;bottom:0;left:0;right:0;background:#fff;display:flex;justify-content:space-around;padding:10px 0;box-shadow:0 -2px 10px rgba(0,0,0,0.08);z-index:1000;">
    <a href="/~/1_Dashboard" style="text-align:center;color:#888;text-decoration:none;font-size:0.7rem;"><span style="font-size:1.3rem;">🏠</span><br>Home</a>
    <a href="/~/20_Marketplace" style="text-align:center;color:#2e7d32;text-decoration:none;font-size:0.7rem;"><span style="font-size:1.3rem;">🛒</span><br>Market</a>
    <a href="/~/2_Crops" style="text-align:center;color:#888;text-decoration:none;font-size:0.7rem;"><span style="font-size:1.3rem;">🌿</span><br>Diagnose</a>
    <a href="/~/16_Chat" style="text-align:center;color:#888;text-decoration:none;font-size:0.7rem;"><span style="font-size:1.3rem;">💬</span><br>Chat</a>
    <a href="/~/8_Profile" style="text-align:center;color:#888;text-decoration:none;font-size:0.7rem;"><span style="font-size:1.3rem;">👤</span><br>Me</a>
</div>
""", unsafe_allow_html=True)

# ===== FLOATING CART =====
cart_count = len(st.session_state.cart)
st.markdown(f"""
<div style="position:fixed;bottom:80px;right:20px;background:#2e7d32;color:#fff;width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.5rem;box-shadow:0 4px 12px rgba(46,125,50,0.4);z-index:998;">
    🛒
    {f'<div style="position:absolute;top:-4px;right:-4px;background:#f44336;color:#fff;width:22px;height:22px;border-radius:50%;font-size:0.7rem;display:flex;align-items:center;justify-content:center;font-weight:700;">{cart_count}</div>' if cart_count > 0 else ''}
</div>
""", unsafe_allow_html=True)
