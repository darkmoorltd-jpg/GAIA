
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import datetime, timedelta
import uuid
from app.utils.phone_util import normalize_phone
from app.utils.marketplace_util import (
    get_service_client, upload_listing_image, verify_payment,
    get_listing_by_id, get_seller_profile, add_review, get_reviews,
    toggle_favorite, is_favorite, get_favorites
)

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_PUBLIC = "pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057"
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

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
if "delivery_method" not in st.session_state:
    st.session_state.delivery_method = "pickup"
if "delivery_address" not in st.session_state:
    st.session_state.delivery_address = ""
if "delivery_fee" not in st.session_state:
    st.session_state.delivery_fee = 0

@st.cache_data(ttl=60)
def fetch_listings():
    res = service.table("marketplace_listings").select("*").eq("status", "active").order("created_at", desc=True).execute()
    return res.data if res.data else []

LISTINGS = fetch_listings()

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
        justify-content: center; font-size: 3rem; position: relative; overflow: hidden;
    }
    .jiji-card .image-area img { width: 100%; height: 100%; object-fit: cover; }
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
    .empty-state { text-align: center; padding: 60px 20px; color: #888; }
    .contact-btn { background: #25d366; color: #fff; padding: 10px 20px; border-radius: 8px; text-decoration: none; display: inline-block; font-weight: 600; }
    .call-btn { background: #2196f3; color: #fff; padding: 10px 20px; border-radius: 8px; text-decoration: none; display: inline-block; font-weight: 600; }
    .fav-btn { background: #fff; border: 1px solid #ddd; border-radius: 50%; width: 36px; height: 36px; cursor: pointer; font-size: 1.2rem; line-height: 1; padding: 0; display: flex; align-items: center; justify-content: center; }
    .fav-btn.active { background: #ffebee; border-color: #f44336; color: #f44336; }
    .review-card { background: #fff; border-radius: 10px; padding: 12px; margin: 8px 0; box-shadow: 0 1px 4px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab-list"] { gap: 0; }
    .stTabs [data-baseweb="tab"] { padding: 8px 20px; font-weight: 600; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background: #e8f5e9; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div style="font-size:2.5rem;font-weight:800;text-align:center;color:#2e7d32;">🌍 GAIA Market</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;color:#607d8b;margin-bottom:2rem;">Buy and sell farm produce directly</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🛒 Browse", "📝 Sell", "👤 My Store", "📦 Orders", "💳 Cart", "❤️ Favorites"])

with tab1:
    search = st.text_input("", placeholder="🔍 Search crops, varieties, or locations...", label_visibility="collapsed", key="market_search")
    if search:
        filtered = [l for l in LISTINGS if search.lower() in (l.get("crop","")+" "+l.get("variety","")+" "+l.get("location","")).lower()]
    else:
        filtered = LISTINGS

    if not filtered:
        st.markdown('<div class="empty-state"><h3>🌱 No listings yet</h3><p>Be the first to sell your produce!</p></div>', unsafe_allow_html=True)
    else:
        cols = st.columns(3)
        for i, listing in enumerate(filtered):
            with cols[i % 3]:
                image_urls = listing.get("image_urls", [])
                image_src = image_urls[0] if image_urls else "🌱"
                price = listing.get("price", 0)
                location = listing.get("location", "")
                state = listing.get("state", "")
                organic = listing.get("organic", False)
                featured = listing.get("featured", False)
                crop = listing.get("crop", "Unknown")
                variety = listing.get("variety", "")

                card_html = f'<div class="jiji-card" onclick="window.location.href=\'?listing_id={listing["id"]}\';"><div class="image-area" style="background: linear-gradient(135deg, #e8f5e9, #c8e6c9);">{f"<img src=\'{image_src}\' alt=\'{crop}\'/>" if image_src != "🌱" else f"<span style=\'font-size:3.5rem;\'>{image_src}</span>"}{f"<div class=\'featured-badge\'>⭐ Featured</div>" if featured else ""}{f"<div class=\'organic-badge\'>🌿</div>" if organic else ""}</div><div class="info-area"><div class="crop-name">{crop} {variety}</div><div class="price">₦{price:,} <small>/ {listing.get("unit","tonne")}</small></div><div class="location">📍 {location}, {state}</div></div></div>'
                st.markdown(card_html, unsafe_allow_html=True)
                
                col_btn, col_fav = st.columns([4,1])
                with col_btn:
                    if st.button("View Details", key=f"view_{listing['id']}", use_container_width=True):
                        st.session_state.selected_listing = listing
                        st.rerun()
                with col_fav:
                    fav = is_favorite(user.id, listing["id"])
                    if st.button("❤️" if fav else "🤍", key=f"fav_{listing['id']}", help="Toggle favorite"):
                        toggle_favorite(user.id, listing["id"])
                        st.rerun()

    if "selected_listing" in st.session_state and st.session_state.selected_listing is not None:
        listing = st.session_state.selected_listing
        st.markdown("---")
        st.markdown("## 🧾 Listing Details")
        c1, c2 = st.columns([2, 1])
        with c1:
            image_urls = listing.get("image_urls", [])
            if image_urls:
                for img_url in image_urls:
                    st.image(img_url, use_container_width=True)
            else:
                st.markdown('<div style="font-size:5rem;text-align:center;">🌱</div>', unsafe_allow_html=True)
            st.markdown(f"**Description:** {listing.get('description','')}")
            
            # Reviews section
            st.markdown("### ⭐ Reviews")
            reviews = get_reviews(listing["id"])
            if not reviews:
                st.info("No reviews yet.")
            else:
                for rev in reviews:
                    stars = "⭐" * rev.get("rating", 0)
                    st.markdown(f'<div class="review-card"><strong>{stars}</strong><br>{rev.get("comment","")}</div>', unsafe_allow_html=True)
            
            # Add review form
            with st.expander("Write a Review", expanded=False):
                with st.form(f"review_form_{listing['id']}"):
                    rating = st.slider("Rating", 1, 5, 5)
                    comment = st.text_area("Comment")
                    if st.form_submit_button("Submit Review"):
                        add_review(listing["id"], listing["user_id"], user.id, rating, comment)
                        st.success("Review submitted!")
                        st.rerun()
        with c2:
            st.markdown(f"**Crop:** {listing.get('crop','')}")
            st.markdown(f"**Variety:** {listing.get('variety','')}")
            st.markdown(f"**Price:** ₦{listing.get('price',0):,} / {listing.get('unit','tonne')}")
            st.markdown(f"**Location:** {listing.get('location','')}, {listing.get('state','')}")
            seller_profile = get_seller_profile(listing.get('user_id'))
            seller_name = f"{seller_profile.get('first_name','')} {seller_profile.get('last_name','')}".strip() or "Seller"
            st.markdown(f"**Seller:** {seller_name}")
            seller_phone = seller_profile.get('phone','')
            if seller_phone:
                st.markdown(f'<a class="call-btn" href="tel:{seller_phone}">📞 Call Seller</a>', unsafe_allow_html=True)
                st.markdown(f'<a class="contact-btn" href="https://wa.me/{normalize_phone(seller_phone)}">💬 WhatsApp</a>', unsafe_allow_html=True)
            
            quantity = st.number_input("Quantity", min_value=1, value=1)
            if st.button("Add to Cart", key="add_to_cart", use_container_width=True):
                st.session_state.cart.append({
                    "listing_id": listing["id"],
                    "crop": listing.get("crop"),
                    "variety": listing.get("variety"),
                    "price": listing.get("price",0),
                    "quantity": quantity,
                    "seller_id": listing.get("user_id")
                })
                st.success(f"Added {quantity} {listing.get('unit','unit')} to cart!")
                st.rerun()
            if st.button("Close", key="close_details"):
                st.session_state.selected_listing = None
                st.rerun()

with tab2:
    st.markdown("### 📝 Sell Your Produce")
    with st.form("sell_form"):
        crop = st.text_input("Crop *")
        variety = st.text_input("Variety")
        quantity = st.number_input("Quantity", min_value=1.0, value=1.0)
        unit = st.selectbox("Unit", ["tonne", "kg", "bag", "bunch", "piece"])
        price = st.number_input("Price per unit (₦)", min_value=0.0, value=0.0)
        location = st.text_input("Location (e.g., Kaduna)")
        state = st.text_input("State")
        description = st.text_area("Description")
        organic = st.checkbox("Organic")
        harvest_date = st.date_input("Harvest Date")
        uploaded_images = st.file_uploader("Upload photos", type=["jpg","jpeg","png"], accept_multiple_files=True)
        
        if st.form_submit_button("📤 Publish Listing"):
            if not crop or not price or not location or not state:
                st.error("Crop, price, location, and state are required.")
            else:
                image_urls = []
                for img_file in uploaded_images:
                    url, err = upload_listing_image(img_file.read(), img_file.name)
                    if url:
                        image_urls.append(url)
                    else:
                        st.warning(f"Image upload failed: {err}")
                listing_data = {
                    "user_id": user.id,
                    "crop": crop.strip(),
                    "variety": variety.strip(),
                    "quantity": quantity,
                    "unit": unit,
                    "price": price,
                    "location": location.strip(),
                    "state": state.strip(),
                    "description": description.strip(),
                    "organic": organic,
                    "harvest_date": harvest_date.isoformat() if harvest_date else None,
                    "image_urls": image_urls,
                    "status": "active"
                }
                try:
                    service.table("marketplace_listings").insert(listing_data).execute()
                    st.success("✅ Listing published!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to publish: {e}")

with tab3:
    st.markdown("### 👤 My Store")
    my_listings = service.table("marketplace_listings").select("*").eq("user_id", user.id).execute().data or []
    if not my_listings:
        st.info("You haven't created any listings yet.")
    else:
        for listing in my_listings:
            status = listing.get("status")
            with st.expander(f"{listing.get('crop','')} {listing.get('variety','')} — ₦{listing.get('price',0):,} ({status})"):
                st.write(f"**Location:** {listing.get('location','')}, {listing.get('state','')}")
                if listing.get("image_urls"):
                    for img in listing["image_urls"]:
                        st.image(img, width=150)
                if st.button("Delete", key=f"del_{listing['id']}"):
                    service.table("marketplace_listings").delete().eq("id", listing["id"]).execute()
                    st.success("Listing deleted.")
                    st.rerun()

with tab4:
    st.markdown("### 📦 My Orders")
    my_orders = service.table("marketplace_orders").select("*").or_(f"buyer_id.eq.{user.id},seller_id.eq.{user.id}").order("created_at", desc=True).execute().data or []
    if not my_orders:
        st.info("No orders yet.")
    else:
        for order in my_orders:
            role = "Buyer" if order["buyer_id"] == user.id else "Seller"
            status = order.get("status")
            st.markdown(f"**Order ID:** {order['id'][:8]} | Role: {role} | Status: {status}")
            listing = get_listing_by_id(order.get("listing_id"))
            if listing:
                st.write(f"Item: {listing.get('crop','')} {listing.get('variety','')}")
            st.write(f"Amount: ₦{order.get('total_amount',0):,}")
            st.write(f"Delivery: {order.get('delivery_method','pickup')}")
            if order.get('delivery_address'):
                st.write(f"Address: {order.get('delivery_address')}")
            st.markdown("---")

with tab5:
    st.markdown("### 💳 Cart")
    if not st.session_state.cart:
        st.info("Your cart is empty.")
    else:
        total = 0
        for item in st.session_state.cart:
            st.write(f"{item['quantity']} x {item['crop']} {item['variety']} @ ₦{item['price']:,}")
            total += item['price'] * item['quantity']
        st.markdown(f"**Subtotal: ₦{total:,}**")
        
        # Delivery options
        st.markdown("### 🚚 Delivery Method")
        delivery_method = st.radio("Choose delivery", ["Pickup", "Delivery"])
        if delivery_method == "Delivery":
            st.session_state.delivery_address = st.text_area("Delivery Address")
            # Simple flat fee for now; you can calculate by state later
            st.session_state.delivery_fee = 1000  # ₦1000 flat
            st.write(f"Delivery Fee: ₦{st.session_state.delivery_fee:,}")
        else:
            st.session_state.delivery_fee = 0
        
        final_total = total + st.session_state.delivery_fee
        st.markdown(f"**Total: ₦{final_total:,}**")
        
        if st.button("Checkout with Paystack", type="primary"):
            seller_id = st.session_state.cart[0]["seller_id"]
            ref = f"GAIA_MKT_{user.id[:8]}_{uuid.uuid4().hex[:6]}"
            order_data = {
                "listing_id": st.session_state.cart[0]["listing_id"],
                "buyer_id": user.id,
                "seller_id": seller_id,
                "quantity": sum(item["quantity"] for item in st.session_state.cart),
                "total_amount": final_total,
                "status": "pending",
                "payment_reference": ref,
                "delivery_method": delivery_method.lower(),
                "delivery_address": st.session_state.delivery_address if delivery_method == "Delivery" else None,
                "delivery_fee": st.session_state.delivery_fee
            }
            service.table("marketplace_orders").insert(order_data).execute()
            components.html(f"""
            <script src="https://js.paystack.co/v1/inline.js"></script>
            <script>
                PaystackPop.setup({{
                    key: '{PAYSTACK_PUBLIC}',
                    email: '{user.email}',
                    amount: {final_total * 100},
                    currency: 'NGN',
                    ref: '{ref}',
                    label: 'GAIA Market Purchase',
                    callback: function(response) {{
                        window.location.href = '/~/payment_callback?reference=' + response.reference + '&order_type=market';
                    }}
                }}).openIframe();
            </script>
            """, height=100)

with tab6:
    st.markdown("### ❤️ Favorites")
    fav_listings = get_favorites(user.id)
    if not fav_listings:
        st.info("No favorites yet.")
    else:
        cols = st.columns(3)
        for i, listing in enumerate(fav_listings):
            with cols[i % 3]:
                st.markdown(f"**{listing.get('crop','')} {listing.get('variety','')}**")
                st.write(f"₦{listing.get('price',0):,}")
                if st.button("Remove from Favorites", key=f"rem_fav_{listing['id']}"):
                    toggle_favorite(user.id, listing["id"])
                    st.rerun()

st.markdown("---")
st.caption("Powered by Darkmoor Ltd")
