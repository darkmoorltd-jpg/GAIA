import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime, timedelta
import uuid
import requests
import pandas as pd
import json

def normalize_phone(phone):
    if not phone:
        return "08000000000"
    phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    if phone.startswith("0"):
        return "234" + phone[1:]
    elif phone.startswith("234"):
        return phone
    else:
        return "234" + phone

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_PUBLIC = "pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057"
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

def upload_listing_image(file_bytes, filename):
    supabase = get_service()
    unique_name = f"{uuid.uuid4().hex[:12]}_{filename}"
    bucket = "listing-images"
    try:
        supabase.storage.from_(bucket).upload(unique_name, file_bytes, {"content-type": "image/jpeg"})
        return supabase.storage.from_(bucket).get_public_url(unique_name), None
    except Exception as e:
        return None, str(e)[:200]

def get_listing_by_id(listing_id):
    supabase = get_service()
    try:
        res = supabase.table("marketplace_listings").select("*").eq("id", listing_id).execute()
        return res.data[0] if res.data else None
    except:
        return None

def get_seller_profile(seller_id):
    supabase = get_service()
    try:
        res = supabase.table("user_profiles").select("*").eq("user_id", seller_id).execute()
        return res.data[0] if res.data else {}
    except:
        return {}

def get_seller_rating(seller_id):
    supabase = get_service()
    res = supabase.table("marketplace_reviews").select("rating").eq("seller_id", seller_id).execute()
    if res.data:
        avg = sum(r["rating"] for r in res.data) / len(res.data)
        return round(avg, 1), len(res.data)
    return 0, 0

def get_seller_trust_score(seller_id):
    supabase = get_service()
    # Combine rating + verification + completed orders
    rating, count = get_seller_rating(seller_id)
    profile = get_seller_profile(seller_id)
    verification = profile.get("verification_status", "pending")
    
    # Base score
    score = 50  # neutral
    
    # Rating contribution (up to 30 points)
    if count > 0:
        score += min(30, rating * 6)
    
    # Verification contribution (up to 20 points)
    if verification == "approved":
        score += 20
    elif verification == "rejected":
        score -= 20
    
    # Completed orders contribution (up to 20 points)
    try:
        orders = supabase.table("marketplace_orders").select("status").eq("seller_id", seller_id).execute().data or []
        completed = sum(1 for o in orders if o.get("status") == "paid")
        score += min(20, completed * 5)
    except:
        pass
    
    return min(100, max(0, score))

def toggle_favorite(user_id, listing_id):
    supabase = get_service()
    res = supabase.table("marketplace_favorites").select("*").eq("user_id", user_id).eq("listing_id", listing_id).execute()
    if res.data:
        supabase.table("marketplace_favorites").delete().eq("user_id", user_id).eq("listing_id", listing_id).execute()
        return False
    else:
        supabase.table("marketplace_favorites").insert({"user_id": user_id, "listing_id": listing_id}).execute()
        return True

def is_favorite(user_id, listing_id):
    supabase = get_service()
    res = supabase.table("marketplace_favorites").select("*").eq("user_id", user_id).eq("listing_id", listing_id).execute()
    return len(res.data) > 0

def get_favorites(user_id):
    supabase = get_service()
    res = supabase.table("marketplace_favorites").select("listing_id").eq("user_id", user_id).execute()
    ids = [r["listing_id"] for r in res.data] if res.data else []
    if not ids:
        return []
    listings = supabase.table("marketplace_listings").select("*").in_("id", ids).execute()
    return listings.data if listings.data else []

def add_review(listing_id, seller_id, reviewer_id, rating, comment):
    supabase = get_service()
    supabase.table("marketplace_reviews").insert({
        "listing_id": listing_id, "seller_id": seller_id,
        "reviewer_id": reviewer_id, "rating": rating, "comment": comment
    }).execute()

def get_reviews(listing_id):
    supabase = get_service()
    res = supabase.table("marketplace_reviews").select("*").eq("listing_id", listing_id).order("created_at", desc=True).execute()
    return res.data if res.data else []

def create_escrow(order_id, amount):
    supabase = get_service()
    supabase.table("marketplace_escrow").insert({"order_id": order_id, "amount": amount, "status": "held"}).execute()

def release_escrow(order_id):
    supabase = get_service()
    supabase.table("marketplace_escrow").update({"status": "released", "released_at": datetime.now().isoformat()}).eq("order_id", order_id).execute()
    supabase.table("marketplace_orders").update({"status": "paid"}).eq("id", order_id).execute()

def add_delivery_tracking(order_id):
    supabase = get_service()
    supabase.table("marketplace_delivery_tracking").insert({"order_id": order_id, "status": "pending"}).execute()

def get_delivery_status(order_id):
    supabase = get_service()
    res = supabase.table("marketplace_delivery_tracking").select("*").eq("order_id", order_id).execute()
    return res.data[0] if res.data else {"status": "pending"}

def create_negotiation(listing_id, buyer_id, seller_id, proposed_price, proposed_quantity, message):
    supabase = get_service()
    supabase.table("marketplace_negotiations").insert({
        "listing_id": listing_id, "buyer_id": buyer_id, "seller_id": seller_id,
        "proposed_price": proposed_price, "proposed_quantity": proposed_quantity, "message": message
    }).execute()

def get_negotiations(user_id):
    supabase = get_service()
    res = supabase.table("marketplace_negotiations").select("*").or_(f"buyer_id.eq.{user_id},seller_id.eq.{user_id}").order("created_at", desc=True).execute()
    return res.data if res.data else []

def save_search(user_id, query):
    supabase = get_service()
    supabase.table("marketplace_saved_searches").insert({"user_id": user_id, "query": query}).execute()

def get_saved_searches(user_id):
    supabase = get_service()
    res = supabase.table("marketplace_saved_searches").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data if res.data else []

def get_price_index():
    supabase = get_service()
    res = supabase.table("marketplace_price_index").select("*").execute()
    return res.data if res.data else []

def get_currency_rates():
    supabase = get_service()
    try:
        res = supabase.table("currency_rates").select("*").execute()
        return res.data if res.data else [{"code":"NGN","rate":1}]
    except:
        return [{"code":"NGN","rate":1}]

def generate_description(crop, variety, location):
    """Generate AI description using DeepSeek (fallback: simple template)."""
    try:
        from app.utils.deepseek_explainer import explain_diagnosis, DEEPSEEK_API_KEY
        import requests
        prompt = f"Write a compelling marketplace listing description for {crop} {variety} from {location}, Nigeria. Include quality, uses, and call to action. Keep under 100 words."
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "system", "content": "You are a helpful Nigerian farmer."}, {"role": "user", "content": prompt}],
            "temperature": 0.7, "max_tokens": 200
        }
        r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except:
        pass
    return f"Premium {crop} {variety} from {location}. Fresh, high‑quality, and ready for delivery. Contact for bulk pricing."

def get_listing_analytics(seller_id):
    supabase = get_service()
    total_views = sum(l.get("view_count", 0) for l in supabase.table("marketplace_listings").select("view_count").eq("user_id", seller_id).execute().data or [])
    total_listings = len(supabase.table("marketplace_listings").select("id").eq("user_id", seller_id).execute().data or [])
    total_orders = len(supabase.table("marketplace_orders").select("id").eq("seller_id", seller_id).execute().data or [])
    return total_views, total_listings, total_orders


def get_admin_analytics():
    supabase = get_service()
    total_listings = len(supabase.table("marketplace_listings").select("*").execute().data or [])
    total_orders = len(supabase.table("marketplace_orders").select("*").execute().data or [])
    total_users = len(supabase.table("user_profiles").select("*").execute().data or [])
    total_revenue = sum(o.get("total_amount", 0) for o in supabase.table("marketplace_orders").select("total_amount").execute().data or [])
    return total_listings, total_orders, total_users, total_revenue

st.set_page_config(page_title="GAIA Market", page_icon="🌍", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

user = st.session_state.user
service = get_service()

if "cart" not in st.session_state:
    st.session_state.cart = []
if "selected_listing" not in st.session_state:
    st.session_state.selected_listing = None

@st.cache_data(ttl=60)
def fetch_listings():
    res = service.table("marketplace_listings").select("*").eq("status", "active").order("created_at", desc=True).execute()
    return res.data if res.data else []

LISTINGS = fetch_listings()
CURRENCY_RATES = {r["code"]: r["rate"] for r in get_currency_rates()}
selected_currency = st.selectbox("💱 Currency", list(CURRENCY_RATES.keys()))
rate = CURRENCY_RATES.get(selected_currency, 1)

# CSS (abbreviated)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #f5f5f5; color: #222; }
    header, footer { visibility: hidden; }
    .jiji-card { background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); transition: all 0.2s; cursor: pointer; position: relative; margin-bottom: 16px; }
    .jiji-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.12); }
    .jiji-card .image-area { height: 160px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; font-size: 3rem; position: relative; overflow: hidden; }
    .jiji-card .image-area img { width: 100%; height: 100%; object-fit: cover; }
    .jiji-card .info-area { padding: 12px; }
    .jiji-card .crop-name { font-size: 1rem; font-weight: 600; color: #222; margin-bottom: 4px; }
    .jiji-card .price { font-size: 1.2rem; font-weight: 800; color: #2e7d32; }
    .jiji-card .location { font-size: 0.8rem; color: #888; margin-top: 4px; }
    .stars { color: #ffc107; font-size: 0.85rem; }
    .trust-badge { background: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
    .empty-state { text-align: center; padding: 60px 20px; color: #888; }
    .contact-btn { background: #25d366; color: #fff; padding: 10px 20px; border-radius: 8px; text-decoration: none; display: inline-block; font-weight: 600; }
    .call-btn { background: #2196f3; color: #fff; padding: 10px 20px; border-radius: 8px; text-decoration: none; display: inline-block; font-weight: 600; }
    .stTabs [data-baseweb="tab-list"] { gap: 0; }
    .stTabs [data-baseweb="tab"] { padding: 8px 20px; font-weight: 600; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background: #e8f5e9; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div style="font-size:2.5rem;font-weight:800;text-align:center;color:#2e7d32;">🌍 GAIA Market</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;color:#607d8b;margin-bottom:2rem;">Buy, sell, negotiate, and deliver farm produce securely</div>', unsafe_allow_html=True)

tab_browse, tab_sell, tab_store, tab_orders, tab_cart, tab_favs, tab_neg, tab_chat, tab_alerts, tab_prices, tab_saved, tab_admin = st.tabs([
    "🛒 Browse", "📝 Sell", "👤 Store", "📦 Orders", "💳 Cart", "❤️ Saved", "🤝 Negotiate", "💬 Chat", "🔔 Alerts", "📊 Prices", "🔍 Searches", "📈 Analytics"
])

# BROWSE TAB with trust score and AI description
with tab_browse:
    search = st.text_input("🔍 Search", label_visibility="collapsed")
    if search:
        filtered = [l for l in LISTINGS if search.lower() in (l.get("crop","")+" "+l.get("variety","")+" "+l.get("location","")).lower()]
    else:
        filtered = LISTINGS
    if not filtered:
        st.markdown('<div class="empty-state"><h3>🌱 No listings yet</h3></div>', unsafe_allow_html=True)
    else:
        cols = st.columns(3)
        for i, listing in enumerate(filtered):
            with cols[i % 3]:
                image_urls = listing.get("image_urls", [])
                image_src = image_urls[0] if image_urls else "🌱"
                price_ngn = listing.get("price", 0)
                price_display = price_ngn / rate if selected_currency != "NGN" else price_ngn
                crop = listing.get("crop", "")
                variety = listing.get("variety", "")
                seller_id = listing.get("user_id")
                rating, count = get_seller_rating(seller_id)
                trust = get_seller_trust_score(seller_id)
                card_html = f'''
                <div class="jiji-card" onclick="window.location.href='?listing_id={listing["id"]}';">
                    <div class="image-area" style="background: linear-gradient(135deg, #e8f5e9, #c8e6c9);">
                        {f"<img src='{image_src}' alt='{crop}'/>" if image_src != "🌱" else f"<span style='font-size:3.5rem;'>{image_src}</span>"}
                    </div>
                    <div class="info-area">
                        <div class="crop-name">{crop} {variety}</div>
                        <div class="price">{selected_currency} {price_display:,.0f} <small>/ {listing.get("unit","tonne")}</small></div>
                        <div class="location">📍 {listing.get("location","")}, {listing.get("state","")}</div>
                        <span class="stars">{"⭐"*int(rating)} {rating}({count})</span> 
                        <span class="trust-badge">Trust: {trust}/100</span>
                    </div>
                </div>
                '''
                st.markdown(card_html, unsafe_allow_html=True)
                col_btn, col_fav = st.columns([4,1])
                with col_btn:
                    if st.button("Details", key=f"view_{listing['id']}", use_container_width=True):
                        st.session_state.selected_listing = listing
                        st.rerun()
                with col_fav:
                    fav = is_favorite(user.id, listing["id"])
                    if st.button("❤️" if fav else "🤍", key=f"fav_{listing['id']}"):
                        toggle_favorite(user.id, listing["id"])
                        st.rerun()

    if st.session_state.get("selected_listing"):
        listing = st.session_state.selected_listing
        st.markdown("---")
        st.markdown("## 🧾 Listing Details")
        c1, c2 = st.columns([2,1])
        with c1:
            for img in listing.get("image_urls", []):
                st.image(img, use_container_width=True)
            st.markdown(f"**Description:** {listing.get('description','')}")
            st.markdown("### ⭐ Reviews")
            for rev in get_reviews(listing["id"]):
                st.markdown(f'<div class="review-card">{"⭐"*rev.get("rating",0)}<br>{rev.get("comment","")}</div>', unsafe_allow_html=True)
            with st.expander("Write Review"):
                with st.form(f"rev_{listing['id']}"):
                    rating = st.slider("Rating", 1, 5, 5)
                    comment = st.text_area("Comment")
                    if st.form_submit_button("Submit"):
                        add_review(listing["id"], listing["user_id"], user.id, rating, comment)
                        st.rerun()
        with c2:
            seller_profile = get_seller_profile(listing.get("user_id"))
            seller_name = f"{seller_profile.get('first_name','')} {seller_profile.get('last_name','')}".strip() or "Seller"
            st.markdown(f"**Seller:** {seller_name}")
            rating, count = get_seller_rating(listing.get("user_id"))
            trust = get_seller_trust_score(listing.get("user_id"))
            st.markdown(f"**Rating:** ⭐ {rating} ({count}) | **Trust Score:** {trust}/100")
            seller_phone = seller_profile.get("phone","")
            if seller_phone:
                st.markdown(f'<a class="call-btn" href="tel:{seller_phone}">📞 Call</a>', unsafe_allow_html=True)
                st.markdown(f'<a class="contact-btn" href="https://wa.me/{normalize_phone(seller_phone)}">💬 WhatsApp</a>', unsafe_allow_html=True)
            qty = st.number_input("Quantity", min_value=1, value=1)
            unit_price = listing.get("price",0)
            if qty >= 10:
                discounted = unit_price * 0.95
                st.write(f"Bulk discount: ₦{unit_price:,.0f} → ₦{discounted:,.0f}")
                total_price = discounted * qty
            else:
                total_price = unit_price * qty
            st.write(f"**Total: ₦{total_price:,.0f}**")
            if st.button("Add to Cart"):
                st.session_state.cart.append({
                    "listing_id": listing["id"], "crop": listing.get("crop"),
                    "variety": listing.get("variety"), "price": unit_price,
                    "quantity": qty, "seller_id": listing.get("user_id"),
                    "total_price": total_price
                })
                st.rerun()
            with st.expander("🤝 Negotiate Price"):
                with st.form(f"neg_{listing['id']}"):
                    neg_price = st.number_input("Proposed Price", min_value=0.0)
                    neg_qty = st.number_input("Quantity", min_value=1, value=1)
                    neg_msg = st.text_area("Message")
                    if st.form_submit_button("Send Negotiation"):
                        create_negotiation(listing["id"], user.id, listing["user_id"], neg_price, neg_qty, neg_msg)
                        st.success("Negotiation sent!")
            if st.button("Close"):
                st.session_state.selected_listing = None
                st.rerun()

# SELL TAB with AI description generator
with tab_sell:
    st.markdown("### 📝 Sell Your Produce")
    with st.form("sell_form"):
        crop = st.text_input("Crop *")
        variety = st.text_input("Variety")
        quantity = st.number_input("Quantity", min_value=1.0, value=1.0)
        unit = st.selectbox("Unit", ["tonne", "kg", "bag", "bunch", "piece"])
        price = st.number_input("Price per unit (₦)", min_value=0.0, value=0.0)
        location = st.text_input("Location")
        state = st.text_input("State")
        description = st.text_area("Description")
        if crop and variety and location:
            if st.checkbox("✨ Generate AI Description"):
                description = generate_description(crop, variety, location)
                st.text_area("AI Description", description, key="ai_desc")
        organic = st.checkbox("Organic")
        harvest_date = st.date_input("Harvest Date")
        uploaded_images = st.file_uploader("Photos", type=["jpg","jpeg","png"], accept_multiple_files=True)
        if st.form_submit_button("📤 Publish"):
            if not crop or not price or not location or not state:
                st.error("Required fields missing.")
            else:
                image_urls = []
                for img_file in uploaded_images:
                    url, _ = upload_listing_image(img_file.read(), img_file.name)
                    if url:
                        image_urls.append(url)
                service.table("marketplace_listings").insert({
                    "user_id": user.id, "crop": crop, "variety": variety, "quantity": quantity,
                    "unit": unit, "price": price, "location": location, "state": state,
                    "description": description, "organic": organic, "harvest_date": harvest_date.isoformat() if harvest_date else None,
                    "image_urls": image_urls, "status": "active"
                }).execute()
                st.success("Listing published!")
                st.rerun()

# STORE TAB with analytics
with tab_store:
    st.markdown("### 👤 My Store")
    total_views, total_listings, total_orders = get_listing_analytics(user.id)
    col1, col2, col3 = st.columns(3)
    col1.metric("Listings", total_listings)
    col2.metric("Total Views", total_views)
    col3.metric("Orders", total_orders)
    my_listings = service.table("marketplace_listings").select("*").eq("user_id", user.id).execute().data or []
    for listing in my_listings:
        with st.expander(f"{listing.get('crop','')} {listing.get('variety','')} — ₦{listing.get('price',0):,} ({listing.get('status')})"):
            st.write(f"Views: {listing.get('view_count', 0)}")
            if st.button("Delete", key=f"del_{listing['id']}"):
                service.table("marketplace_listings").delete().eq("id", listing["id"]).execute()
                st.rerun()

# Other tabs (orders, cart, favorites, negotiations, chat, alerts, prices, saved searches) similar to previous versions

with tab_orders:
    st.markdown("### 📦 Orders")
    orders = service.table("marketplace_orders").select("*").or_(f"buyer_id.eq.{user.id},seller_id.eq.{user.id}").order("created_at", desc=True).execute().data or []
    for order in orders:
        role = "Buyer" if order["buyer_id"] == user.id else "Seller"
        with st.expander(f"Order {order['id'][:8]} — {role} — {order.get('status')}"):
            listing = get_listing_by_id(order.get("listing_id"))
            if listing:
                st.write(f"Item: {listing.get('crop','')} {listing.get('variety','')}")
            st.write(f"Amount: ₦{order.get('total_amount',0):,}")
            st.write(f"Delivery: {order.get('delivery_method','pickup')}")
            delivery_status = get_delivery_status(order["id"])
            st.write(f"Delivery status: {delivery_status.get('status')}")
            escrow = service.table("marketplace_escrow").select("*").eq("order_id", order["id"]).execute().data
            if escrow:
                esc = escrow[0]
                st.write(f"Escrow: {esc.get('status')}")
                if esc.get('status') == 'held' and order.get('buyer_id') == user.id:
                    if st.button(f"Confirm Delivery #{order['id'][:8]}"):
                        release_escrow(order["id"])
                        st.rerun()

with tab_cart:
    st.markdown("### 💳 Cart")
    if not st.session_state.cart:
        st.info("Cart empty.")
    else:
        total = sum(item.get("total_price", item["price"] * item["quantity"]) for item in st.session_state.cart)
        st.write(f"Subtotal: ₦{total:,}")
        delivery = st.radio("Delivery", ["Pickup", "Delivery"])
        fee = 0 if delivery == "Pickup" else 1000
        st.write(f"Delivery: ₦{fee:,}")
        final = total + fee
        st.write(f"**Total: ₦{final:,}**")
        if st.button("Checkout with Paystack"):
            seller_id = st.session_state.cart[0]["seller_id"]
            ref = f"GAIA_MKT_{user.id[:8]}_{uuid.uuid4().hex[:6]}"
            order_data = {
                "listing_id": st.session_state.cart[0]["listing_id"],
                "buyer_id": user.id, "seller_id": seller_id,
                "quantity": sum(i["quantity"] for i in st.session_state.cart),
                "total_amount": final, "status": "pending", "payment_reference": ref,
                "delivery_method": delivery.lower(), "delivery_fee": fee
            }
            service.table("marketplace_orders").insert(order_data).execute()
            order_id = service.table("marketplace_orders").select("*").eq("payment_reference", ref).execute().data[0]["id"]
            create_escrow(order_id, final)
            add_delivery_tracking(order_id)
            components.html(f"""
            <script src="https://js.paystack.co/v1/inline.js"></script>
            <script>
                PaystackPop.setup({{key:'{PAYSTACK_PUBLIC}', email:'{user.email}', amount:{final*100}, currency:'NGN', ref:'{ref}', label:'GAIA Market', callback:function(response){{window.location.href='/~/payment_callback?reference='+response.reference+'&order_type=market';}}}}).openIframe();
            </script>
            """, height=100)

with tab_favs:
    st.markdown("### ❤️ Favorites")
    favs = get_favorites(user.id)
    for listing in favs:
        st.markdown(f"**{listing.get('crop','')} {listing.get('variety','')}** — ₦{listing.get('price',0):,}")
        if st.button("Remove", key=f"rem_{listing['id']}"):
            toggle_favorite(user.id, listing["id"])
            st.rerun()

with tab_neg:
    st.markdown("### 🤝 Negotiations")
    for neg in get_negotiations(user.id):
        listing = get_listing_by_id(neg.get("listing_id"))
        crop = listing.get("crop","") if listing else "Unknown"
        st.markdown(f"**{crop}** — Proposed: ₦{neg.get('proposed_price',0):,}")
        st.write(f"Status: {neg.get('status')}")
        st.markdown("---")

with tab_chat:
    st.markdown("### 💬 Seller Chat")
    if st.session_state.get("selected_listing"):
        listing = st.session_state.selected_listing
        st.write(f"Chat about {listing.get('crop','')} {listing.get('variety','')}")
        # Simplified chat display
        st.info("Full chat coming soon. Use WhatsApp for now.")
    else:
        st.info("Select a listing to chat.")

with tab_alerts:
    st.markdown("### 🔔 Alerts & Notifications")
    st.info("Price alerts are set on listing details page.")

with tab_prices:
    st.markdown("### 📊 Market Prices")
    for p in get_price_index():
        st.write(f"**{p.get('crop')}** in {p.get('state')}: ₦{p.get('avg_price',0):,.2f}")

with tab_saved:
    st.markdown("### 🔍 Saved Searches")
    for s in get_saved_searches(user.id):
        st.write(f"🔍 {s.get('query')}")

with tab_admin:
    st.markdown("### 📈 Marketplace Analytics")
    total_listings, total_orders, total_users, total_revenue = get_admin_analytics()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Listings", total_listings)
    col2.metric("Orders", total_orders)
    col3.metric("Users", total_users)
    col4.metric("Revenue", f"₦{total_revenue:,.0f}")

st.markdown("---")
st.caption("Powered by Darkmoor Ltd")
