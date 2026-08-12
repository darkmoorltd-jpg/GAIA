
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime
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

if "cart" not in st.session_state:
    st.session_state.cart = []

# ===== SELLER PROFILE =====
try:
    sp = db.table("seller_profiles").select("*").eq("user_id", user.id).execute()
    seller_profile = sp.data[0] if sp.data else None
except:
    seller_profile = None

has_seller_profile = seller_profile is not None

# ===== DEMO LISTINGS =====
DEMO_LISTINGS = [
    {"id":"demo1","crop":"Maize","variety":"SAMMAZ 15","quantity":20,"unit":"tonnes","price":220000,"location":"Kaduna","state":"Kaduna","farmer":"Ibrahim Musa","user_id":"demo","rating":4.8,"image":"🌽","organic":True,"description":"High-yield hybrid maize.","seller_type":"Verified Farmer","featured":True,"phone":"0803-XXX-XXXX","whatsapp":"0803-XXX-XXXX"},
    {"id":"demo2","crop":"Rice","variety":"FARO 44","quantity":15,"unit":"tonnes","price":350000,"location":"Kano","state":"Kano","farmer":"Aisha Bello","user_id":"demo","rating":4.9,"image":"🌾","organic":False,"description":"Premium long-grain rice.","seller_type":"Premium Seller","featured":True,"phone":"0805-XXX-XXXX","whatsapp":"0805-XXX-XXXX"},
    {"id":"demo3","crop":"Beans","variety":"IT89KD-288","quantity":8,"unit":"tonnes","price":480000,"location":"Jos","state":"Plateau","farmer":"David Okonkwo","user_id":"demo","rating":4.7,"image":"🫘","organic":True,"description":"Organic honey beans.","seller_type":"Organic Certified","featured":False,"phone":"0802-XXX-XXXX","whatsapp":"0802-XXX-XXXX"},
    {"id":"demo4","crop":"Tomatoes","variety":"Roma VF","quantity":5,"unit":"tonnes","price":180000,"location":"Zaria","state":"Kaduna","farmer":"Fatima Yusuf","user_id":"demo","rating":4.6,"image":"🍅","organic":False,"description":"Fresh Roma tomatoes.","seller_type":"Verified Farmer","featured":False,"phone":"0806-XXX-XXXX","whatsapp":"0806-XXX-XXXX"},
    {"id":"demo5","crop":"Yam","variety":"Dioscorea rotundata","quantity":25,"unit":"tonnes","price":550000,"location":"Makurdi","state":"Benue","farmer":"John Tarka","user_id":"demo","rating":4.9,"image":"🍠","organic":True,"description":"Premium white yam tubers.","seller_type":"Premium Seller","featured":True,"phone":"0804-XXX-XXXX","whatsapp":"0804-XXX-XXXX"},
    {"id":"demo6","crop":"Cassava","variety":"TME 419","quantity":40,"unit":"tonnes","price":120000,"location":"Ondo","state":"Ondo","farmer":"Grace Adeyemi","user_id":"demo","rating":4.6,"image":"🥔","organic":True,"description":"High-starch cassava.","seller_type":"Organic Certified","featured":False,"phone":"0801-XXX-XXXX","whatsapp":"0801-XXX-XXXX"},
]

try:
    real_listings = db.table("marketplace_listings").select("*").eq("status", "active").order("created_at", desc=True).execute()
    REAL_LISTINGS = real_listings.data if real_listings.data else []
except:
    REAL_LISTINGS = []

LISTINGS = REAL_LISTINGS if REAL_LISTINGS else DEMO_LISTINGS

# ===== CSS =====
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #f5f5f5; color: #222; }
    header, footer { visibility: hidden; }
    .jiji-card {
        background: #fff; border-radius: 12px; overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 16px;
    }
    .jiji-card .image-area {
        height: 140px; display: flex; align-items: center; justify-content: center;
        font-size: 3rem; position: relative;
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
    .jiji-card .crop-name { font-size: 1rem; font-weight: 600; margin-bottom: 4px; }
    .jiji-card .price { font-size: 1.2rem; font-weight: 800; color: #2e7d32; }
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
        font-size: 0.8rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ===== TABS =====
tab1, tab2, tab3, tab4 = st.tabs(["🛒 Browse", "📝 Sell", "👤 My Store", "📦 Orders"])

# ===== TAB 1: BROWSE =====
with tab1:
    search = st.text_input("", placeholder="🔍 Search crops...", label_visibility="collapsed")
    
    filtered = LISTINGS
    if search:
        s = search.lower()
        filtered = [l for l in LISTINGS if s in str(l.get('crop','')).lower() or s in str(l.get('location','')).lower()]
    
    featured = [l for l in filtered if l.get("featured")]
    if featured:
        st.markdown("#### ⭐ Featured")
        cols = st.columns(min(len(featured), 3))
        for i, listing in enumerate(featured[:3]):
            with cols[i]:
                render_market_card(listing, i, user, db, st)
    
    st.markdown("#### All Listings")
    for i, listing in enumerate(filtered):
        render_market_card(listing, i + 100, user, db, st)

# ===== TAB 2: SELL =====
with tab2:
    st.markdown("## 📝 Sell Your Produce")
    
    if not has_seller_profile:
        st.warning("🔐 Complete your seller profile first.")
        
        with st.form("seller_registration_form"):
            st.markdown("### 👤 Seller Registration")
            
            c1, c2 = st.columns(2)
            with c1:
                full_name = st.text_input("👤 Full Name *")
                phone = st.text_input("📞 Phone *")
                whatsapp = st.text_input("💬 WhatsApp *")
                email = st.text_input("📧 Email *", value=user.email)
            with c2:
                address = st.text_input("🏠 Address *")
                state = st.text_input("🗺️ State *")
                lga = st.text_input("📍 LGA")
                farm_location = st.text_input("🌾 Farm Location")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                farm_size = st.number_input("📐 Farm Size (acres)", min_value=0.1, value=1.0, step=0.5)
            with c2:
                years_exp = st.number_input("📅 Years Experience", min_value=0, max_value=70, value=1)
            with c3:
                primary_crops = st.text_input("🌾 Primary Crops")
            
            if st.form_submit_button("✅ Register", type="primary", use_container_width=True):
                if not full_name or not phone or not whatsapp or not address or not state:
                    st.error("❌ Fill all required fields (*)")
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
                        st.success("✅ Profile created!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)[:200]}")
        st.stop()
    
    st.success(f"✅ Seller: **{seller_profile.get('full_name','')}** | 📞 {seller_profile.get('phone','')}")
    
    with st.form("sell_form"):
        c1, c2 = st.columns(2)
        with c1:
            crop_name = st.text_input("🌾 Crop *")
            variety = st.text_input("🧬 Variety")
            quantity = st.number_input("📦 Quantity *", min_value=1, value=10)
        with c2:
            price = st.number_input("💰 Price (₦) *", min_value=500, value=200000, step=10000)
            unit = st.selectbox("📏 Unit", ["tonnes","kg","bags","baskets"])
            location = st.text_input("📍 Location *")
        
        state = st.text_input("🗺️ State *")
        organic = st.checkbox("🌿 Organic")
        description = st.text_area("📝 Description", max_chars=300)
        
        if st.form_submit_button("📤 List Produce", type="primary", use_container_width=True):
            if not crop_name or not location or not state:
                st.error("❌ Crop, location, and state required.")
            else:
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
                    "status": "active",
                    "farmer": seller_profile.get("full_name",""),
                    "phone": seller_profile.get("phone",""),
                    "whatsapp": seller_profile.get("whatsapp","")
                }).execute()
                st.success(f"✅ Listed {crop_name}!")
                st.balloons()

# ===== TAB 3: MY STORE =====
with tab3:
    st.markdown("## 👤 My Store")
    try:
        my_listings = db.table("marketplace_listings").select("*").eq("user_id", user.id).execute()
        store = my_listings.data if my_listings.data else []
    except:
        store = []
    
    active = sum(1 for l in store if l.get("status") == "active")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(store))
    c2.metric("Active", active)
    c3.metric("Sold", sum(1 for l in store if l.get("status") == "sold"))
    
    if not store:
        st.info("No listings yet.")
    else:
        for l in store:
            status = l.get("status", "active")
            with st.expander(f"{'🟢' if status=='active' else '🔴'} {l.get('crop','')} — ₦{l.get('price',0):,}"):
                st.write(f"**Qty:** {l.get('quantity','')} {l.get('unit','tonnes')}")
                st.write(f"**Location:** {l.get('location','')}, {l.get('state','')}")
                c1, c2 = st.columns(2)
                if status == "active":
                    if c1.button("🔴 Deactivate", key=f"deact_{l['id']}"):
                        db.table("marketplace_listings").update({"status":"inactive"}).eq("id", l["id"]).execute()
                        st.rerun()
                else:
                    if c1.button("🟢 Activate", key=f"act_{l['id']}"):
                        db.table("marketplace_listings").update({"status":"active"}).eq("id", l["id"]).execute()
                        st.rerun()
                if c2.button("🗑️ Delete", key=f"del_{l['id']}"):
                    db.table("marketplace_listings").delete().eq("id", l["id"]).execute()
                    st.rerun()

# ===== TAB 4: ORDERS =====
with tab4:
    st.markdown("## 📦 My Orders")
    try:
        orders = db.table("marketplace_orders").select("*").eq("buyer_id", user.id).execute()
        od = orders.data if orders.data else []
    except:
        od = []
    
    if not od:
        st.info("No orders yet.")
    else:
        for o in od:
            st.write(f"**Order #{o.get('id','?')}** — ₦{o.get('total_amount',0):,} — {o.get('status','pending')}")

# ===== CART =====
st.markdown("---")
with st.expander(f"🛒 Cart ({len(st.session_state.cart)})", expanded=len(st.session_state.cart) > 0):
    if not st.session_state.cart:
        st.write("Empty.")
    else:
        total = sum(i.get('price',0) for i in st.session_state.cart)
        for i in st.session_state.cart:
            st.write(f"**{i.get('crop','')}** — ₦{i.get('price',0):,}")
        st.markdown(f"**Total: ₦{total:,}**")
        if st.button("💳 Pay", use_container_width=True):
            st.info("Payment coming soon.")
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.cart = []
            st.rerun()

# ===== HELPER FUNCTION =====
def render_market_card(listing, idx, user, db, st):
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
    whatsapp = listing.get('whatsapp', '')
    lid = listing.get('id', str(idx))
    
    stars = "⭐" * int(rating)
    
    st.markdown(f"""
    <div class="jiji-card">
        <div class="image-area" style="background: linear-gradient(135deg, {'#e8f5e9' if organic else '#f5f5f5'}, {'#c8e6c9' if organic else '#e0e0e0'});">
            <span style="font-size:3rem;">{image}</span>
            {('<div class="featured-badge">⭐ Featured</div>' if featured else '')}
            {('<div class="organic-badge">🌿</div>' if organic else '')}
        </div>
        <div class="info-area">
            <div class="crop-name">{crop}</div>
            {('<div style="font-size:0.75rem;color:#888;">' + variety + '</div>' if variety else '')}
            <div class="price">₦{price:,} <small>/ {listing.get('unit','tonnes')}</small></div>
            <div class="location">📍 {location}, {state}</div>
            <div style="display:flex;justify-content:space-between;margin-top:6px;">
                <span class="seller-badge {'verified' if 'Verified' in seller_type else 'premium' if 'Premium' in seller_type else 'organic'}">{seller_type}</span>
                <span class="stars">{stars} {rating}</span>
            </div>
            <div class="seller">👨‍🌾 {farmer}</div>
            {('<div class="seller">📞 ' + phone + '</div>' if phone else '')}
            {('<div class="seller">💬 ' + whatsapp + '</div>' if whatsapp else '')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🛒 Add", key=f"add_{lid}_{idx}_{uuid.uuid4().hex[:6]}", use_container_width=True):
            st.session_state.cart.append(listing)
            st.success(f"Added {crop}!")
            st.rerun()
    with c2:
        if st.button("📞 Contact", key=f"ct_{lid}_{idx}_{uuid.uuid4().hex[:6]}", use_container_width=True):
            st.info(f"📞 {farmer}: {phone or 'N/A'} | 💬 {whatsapp or 'N/A'}")
    with c3:
        if st.button("ℹ️ Details", key=f"dt_{lid}_{idx}_{uuid.uuid4().hex[:6]}", use_container_width=True):
            with st.expander("📋 Details", expanded=True):
                st.write(f"**Crop:** {crop}")
                st.write(f"**Variety:** {variety or 'N/A'}")
                st.write(f"**Qty:** {listing.get('quantity','')} {listing.get('unit','tonnes')}")
                st.write(f"**Price:** ₦{price:,}")
                st.write(f"**Location:** {location}, {state}")
                st.write(f"**Seller:** {farmer}")
                st.write(f"**Phone:** {phone or 'N/A'}")
                st.write(f"**WhatsApp:** {whatsapp or 'N/A'}")
