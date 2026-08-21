
import os
import json
import hmac
import hashlib
import requests
import uuid
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import streamlit as st

user = st.session_state.get("user", None)
if user is None:
    st.warning("Please log in first.")
    st.stop()
    # Allow demo mode
    from supabase import create_client
supabase = create_client(
    st.secrets["supabase"]["url"],
     st.secrets["supabase"]["key"])
try:
    session = supabase.auth.get_session()
    user = session.user if session else None
except:
    import streamlit.components.v1 as components

try:
    import plotly.express as px
except ImportError:
    px = None

# CONFIG
SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
PAYSTACK_PUBLIC = "pk_live_3af5d245e74f86f0517d214b6872f4ac8236e057"
PAYSTACK_SECRET = st.secrets["paystack"]["secret_key"]


@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)


def normalize_phone(phone):
    if not phone:
        return "08000000000"
    phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    if phone.startswith("0"):
        return "234" + phone[1:]
    elif phone.startswith("234"):
        return phone
    return "234" + phone


# ============================================================
# MULTI-LANGUAGE (abbreviated, no emoji in f-strings)
# ============================================================
TRANSLATIONS = {
    "English": {
        "marketplace": "GAIA Marketplace",
        "buy_sell": "Buy and sell farm produce securely",
        "search": "Search",
        "crop": "Crop",
        "state": "State",
        "price": "Price",
        "organic": "Organic",
        "listings_found": "listings found",
        "no_listings": "No listings match your filters.",
        "add_to_cart": "Add to Cart",
        "details": "Details",
        "sell_tab": "Sell Your Produce",
        "verify_warning": "You must verify your identity before selling.",
        "verify_now": "Verify Now",
        "cart_empty": "Your cart is empty.",
        "checkout": "Checkout with Paystack",
        "delivery_method": "Delivery Method",
        "pickup": "Pickup",
        "home_delivery": "Home Delivery",
        "subtotal": "Subtotal",
        "delivery_fee": "Delivery",
        "total": "Total",
        "clear_cart": "Clear Cart",
        "orders": "My Orders",
        "no_orders": "No orders yet.",
        "order_id": "Order ID",
        "amount": "Amount",
        "quantity": "Quantity",
        "status": "Status",
        "created": "Created",
        "reference": "Reference",
        "escrow": "Escrow",
        "confirm_delivery": "Confirm Delivery — Release Payment",
        "delivery_status": "Delivery Status",
        "negotiate": "Negotiate",
        "dispute": "Raise Dispute",
        "dispute_reason": "Reason",
        "submit_dispute": "Submit Dispute",
        "price_alerts": "Price Alerts",
        "set_alert": "Set Alert",
        "alert_crop": "Crop",
        "alert_max_price": "Max Price (₦)",
        "featured": "Featured",
        "feature_7days": "Feature for 7 days (₦500)",
        "seller_store": "Seller Store",
        "my_store": "My Store",
        "wallet": "Seller Wallet",
        "available_balance": "Available Balance",
        "pending_escrow": "Pending Escrow",
        "withdraw": "Withdraw to Bank",
        "withdrawal_amount": "Amount (₦)",
        "request_withdrawal": "Request Withdrawal",
        "price_trends": "Market Price Trends",
        "avg_price": "Average Price",
        "regional_prices": "Regional Prices",
        "buyer_badge": "Buyer Badge",
        "verified_buyer": "Verified Buyer",
        "top_buyer": "Top Buyer",
        "first_time": "First-Time Buyer",
        "language": "Language",
        "logistics": "Logistics",
        "pickup_request": "Request Pickup",
        "seller_name": "Seller",
        "rating": "Rating",
        "trust": "Trust Score",
        "call": "Call",
        "whatsapp": "WhatsApp",
        "reviews": "Reviews",
        "write_review": "Write Review",
        "submit": "Submit",
        "description": "Description",
        "publish": "Publish Listing",
        "buyer": "Buyer",
        "seller": "Seller",
        "paid": "Paid",
        "completed": "Completed",
        "pending": "Pending",
        "cancelled": "Cancelled",
        "held": "Held",
        "released": "Released",
    }
}

# ============================================================
# SESSION STATE
# ============================================================
if "language" not in st.session_state:
    st.session_state.language = "English"
if "cart" not in st.session_state:
    st.session_state.cart = []
if "selected_listing" not in st.session_state:
    st.session_state.selected_listing = None

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="GAIA Marketplace", page_icon="🌍", layout="wide")

    st.session_state["user"] = None
    user = user
service = get_service()
TXT = TRANSLATIONS["English"]

# ============================================================
# HELPER FUNCTIONS
# ============================================================


def upload_listing_image(file_bytes, filename):
    supabase = get_service()
    unique_name = f"{uuid.uuid4().hex[:12]}_{filename}"
    try:
        supabase.storage.from_(
            "listing-images").upload(unique_name, file_bytes, {"content-type": "image/jpeg"})
        return supabase.storage.from_(
            "listing-images").get_public_url(unique_name), None
    except Exception as e:
        return None, str(e)[:200]


def get_listing_by_id(listing_id):
    supabase = get_service()
    res = supabase.table("marketplace_listings").select(
        "*").eq("id", listing_id).execute()
    return res.data[0] if res.data else None


def get_seller_profile(seller_id):
    supabase = get_service()
    res = supabase.table("user_profiles").select(
        "*").eq("user_id", seller_id).execute()
    return res.data[0] if res.data else {}


def get_seller_rating(seller_id):
    supabase = get_service()
    res = supabase.table("marketplace_reviews").select(
        "rating").eq("seller_id", seller_id).execute()
    if res.data:
        avg = sum(r["rating"] for r in res.data) / len(res.data)
        return round(avg, 1), len(res.data)
    return 0, 0


def get_seller_trust_score(seller_id):
    supabase = get_service()
    rating, count = get_seller_rating(seller_id)
    profile = get_seller_profile(seller_id)
    verification = profile.get("verification_status", "pending")
    score = 50
    if count > 0:
        score += min(30, rating * 6)
    if verification == "approved":
        score += 20
    elif verification == "rejected":
        score -= 20
    try:
        orders = supabase.table("marketplace_orders").select(
            "status").eq("seller_id", seller_id).execute().data or []
        completed = sum(1 for o in orders if o.get("status") == "completed")
        score += min(20, completed * 5)
    except:
        pass
    return min(100, max(0, score))


def is_verified_seller(user_id):
    supabase = get_service()
    res = supabase.table("user_profiles").select(
        "verification_status").eq("user_id", user_id).execute()
    return bool(res.data and res.data[0].get(
        "verification_status") == "approved")


def toggle_favorite(user_id, listing_id):
    supabase = get_service()
    res = supabase.table("marketplace_favorites").select(
        "*").eq("user_id", user_id).eq("listing_id", listing_id).execute()
    if res.data:
        supabase.table("marketplace_favorites").delete().eq(
    "user_id", user_id).eq(
        "listing_id", listing_id).execute()
        return False
    supabase.table("marketplace_favorites").insert(
        {"user_id": user_id, "listing_id": listing_id}).execute()
    return True


def is_favorite(user_id, listing_id):
    supabase = get_service()
    res = supabase.table("marketplace_favorites").select(
        "*").eq("user_id", user_id).eq("listing_id", listing_id).execute()
    return len(res.data) > 0


def get_favorites(user_id):
    supabase = get_service()
    res = supabase.table("marketplace_favorites").select(
        "listing_id").eq("user_id", user_id).execute()
    ids = [r["listing_id"] for r in res.data] if res.data else []
    if not ids:
        return []
    listings = supabase.table("marketplace_listings").select(
        "*").in_("id", ids).execute()
    return listings.data if listings.data else []


def add_review(listing_id, seller_id, reviewer_id, rating, comment):
    supabase = get_service()
    supabase.table("marketplace_reviews").insert({
        "listing_id": listing_id, "seller_id": seller_id,
        "reviewer_id": reviewer_id, "rating": rating, "comment": comment
    }).execute()


def get_reviews(listing_id):
    supabase = get_service()
    res = supabase.table("marketplace_reviews").select(
        "*").eq("listing_id", listing_id).order("created_at", desc=True).execute()
    return res.data if res.data else []


def create_escrow(order_id, amount):
    supabase = get_service()
    supabase.table("marketplace_escrow").insert(
        {"order_id": order_id, "amount": amount, "status": "held"}).execute()


def release_escrow(order_id):
    supabase = get_service()
    supabase.table("marketplace_escrow").update(
    {
        "status": "released",
        "released_at": datetime.now().isoformat()}).eq(
            "order_id",
             order_id).execute()
    supabase.table("marketplace_orders").update(
        {"status": "completed"}).eq("id", order_id).execute()


def create_dispute(order_id, user_id, reason):
    supabase = get_service()
    supabase.table("marketplace_disputes").insert(
        {"order_id": order_id, "user_id": user_id, "reason": reason, "status": "open"}).execute()


def create_price_alert(user_id, crop, max_price):
    supabase = get_service()
    supabase.table("marketplace_price_alerts").insert(
        {"user_id": user_id, "crop": crop, "max_price": max_price}).execute()


def get_price_alerts(user_id):
    supabase = get_service()
    res = supabase.table("marketplace_price_alerts").select(
        "*").eq("user_id", user_id).execute()
    return res.data if res.data else []


def get_wallet_balance(user_id):
    supabase = get_service()
    try:
        res = supabase.table("seller_wallets").select(
            "*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]
    except:
        pass
    # Return safe default if table doesn't exist
    return {"balance": 0, "pending_escrow": 0, "user_id": user_id}


def request_withdrawal(user_id, amount):
    supabase = get_service()
    try:
        supabase.table("seller_withdrawals").insert(
            {"user_id": user_id, "amount": amount, "status": "pending"}).execute()
        return True, None
    except Exception as e:
        return False, str(e)


def get_price_trends(crop):
    supabase = get_service()
    res = supabase.table("marketplace_listings").select(
        "price, created_at").eq("crop", crop).eq("status", "active").execute()
    return res.data if res.data else []


# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div style="font-size:2.5rem;font-weight:800;text-align:center;color:#2e7d32;">🌍 GAIA Marketplace</div>
<div style="text-align:center;color:#607d8b;margin-bottom:2rem;">Buy and sell farm produce securely</div>
""", unsafe_allow_html=True)

# ============================================================
# FETCH LISTINGS
# ============================================================
all_listings = service.table("marketplace_listings").select(
    "*").eq("status", "active").order("created_at", desc=True).execute().data or []

# ============================================================
# TABS
# ============================================================
tab_browse, tab_orders, tab_sell, tab_store, tab_wallet, tab_alerts, tab_trends = st.tabs([
    "🛒 Browse", "📦 Orders", "📝 Sell", "👤 Store", "💰 Wallet", "🔔 Alerts", "📊 Trends"
])

# BROWSE TAB
with tab_browse:
    col_search, col_crop, col_state, col_price, col_org = st.columns([
                                                                     3, 2, 2, 2, 1])
    with col_search:
        search_query = st.text_input(
    "Search",
    placeholder="crop, variety, location...",
     label_visibility="collapsed")
    with col_crop:
        crop_filter = st.selectbox(
            "Crop", ["All"] + sorted(set(l.get("crop", "") for l in all_listings)))
    with col_state:
        state_filter = st.selectbox(
            "State", ["All"] + sorted(set(l.get("state", "") for l in all_listings)))
    with col_price:
        price_filter = st.selectbox(
    "Price", [
        "Any", "Under ₦50k", "₦50k–₦200k", "₦200k–₦500k", "Over ₦500k"])
    with col_org:
        organic_filter = st.checkbox("Organic", value=False)

    filtered = all_listings.copy()
    if search_query:
        filtered = [
    l for l in filtered if search_query.lower() in (
        l.get(
            "crop",
            "") +
            " " +
            l.get(
                "variety",
                "") +
                " " +
                l.get(
                    "location",
                     "")).lower()]
    if crop_filter != "All":
        filtered = [l for l in filtered if l.get("crop") == crop_filter]
    if state_filter != "All":
        filtered = [l for l in filtered if l.get("state") == state_filter]
    if organic_filter:
        filtered = [l for l in filtered if l.get("organic", False)]

    st.write(f"**{len(filtered)} listings found**")
    if not filtered:
        st.info("No listings match your filters.")
    else:
        cols = st.columns(3)
        for i, listing in enumerate(filtered):
            with cols[i % 3]:
                crop = listing.get("crop", "")
                variety = listing.get("variety", "")
                price_ngn = listing.get("price", 0)
                location = listing.get("location", "")
                state = listing.get("state", "")
                rating, count = get_seller_rating(listing.get("user_id"))
                trust = get_seller_trust_score(listing.get("user_id"))
                stars = "⭐" * int(rating)
                st.markdown(f"""
                <div style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:16px;">
                    <div style="height:160px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#e8f5e9,#c8e6c9);font-size:3rem;">🌱</div>
                    <div style="padding:12px;">
                        <div style="font-weight:600;color:#222;">{crop} {variety}</div>
                        <div style="font-size:1.2rem;font-weight:800;color:#2e7d32;">₦{price_ngn:,} <small style="font-size:0.7rem;color:#888;">/ {listing.get("unit", "tonne")}</small></div>
                        <div style="font-size:0.8rem;color:#888;">📍 {location}, {state}</div>
                        <div style="margin-top:4px;">{stars} {rating}({count}) <span style="background:#e8f5e9;color:#2e7d32;padding:2px 8px;border-radius:4px;font-size:0.75rem;">Trust {trust}/100</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                col_btn, col_fav = st.columns([4, 1])
                with col_btn:
                    if st.button(
    "Details",
    key=f"view_{
        listing['id']}",
         use_container_width=True):
                        st.session_state.selected_listing = listing
                        st.rerun()
                with col_fav:
                    fav = is_favorite(user.id, listing["id"])
                    if st.button(
    "❤️" if fav else "🤍", key=f"fav_{
        listing['id']}"):
                        toggle_favorite(user.id, listing["id"])
                        st.rerun()

    if st.session_state.selected_listing:
        listing = st.session_state.selected_listing
        st.markdown("---")
        st.markdown("## Listing Details")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(
                f"**Description:** {listing.get('description', 'No description')}")
            st.markdown("### Reviews")
            reviews = get_reviews(listing["id"])
            if not reviews:
                st.info("No reviews yet.")
            for rev in reviews:
                st.markdown(
    f'<div style="background:#fff;border-radius:8px;padding:10px;margin:5px 0;">{
        "⭐" *
        rev.get(
            "rating",
            0)}<br>{
                rev.get(
                    "comment",
                    "")}</div>',
                     unsafe_allow_html=True)
        with c2:
            seller_profile = get_seller_profile(listing.get("user_id"))
            seller_name = f"{
    seller_profile.get(
        'first_name',
        '')} {
            seller_profile.get(
                'last_name',
                 '')}".strip() or "Seller"
            st.markdown(f"**Seller:** {seller_name}")
            rating, count = get_seller_rating(listing.get("user_id"))
            trust = get_seller_trust_score(listing.get("user_id"))
            st.markdown(f"**Rating:** ⭐ {rating} ({count})")
            st.markdown(f"**Trust Score:** {trust}/100")
            seller_phone = seller_profile.get("phone", "")
            if seller_phone:
                st.markdown(
    f'<a href="tel:{seller_phone}" style="background:#2196f3;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none;display:inline-block;font-weight:600;">📞 Call</a>',
     unsafe_allow_html=True)
                st.markdown(
    f'<a href="https://wa.me/{
        # 25d366;color:#fff;padding:10px
        # 20px;border-radius:8px;text-decoration:none;display:inline-block;font-weight:600;">💬
        # WhatsApp</a>',
        normalize_phone(seller_phone)}" style="background:
         unsafe_allow_html=True)
            qty = st.number_input("Quantity", min_value=1, value=1)
            unit_price = listing.get("price", 0)
            total = unit_price * qty
            if qty >= 10:
                total *= 0.95
                st.info("Bulk discount applied: 5% off")
            st.markdown(f"**Total: ₦{total:,.0f}**")
            if st.button("Add to Cart", use_container_width=True):
                st.session_state.cart.append({
                    "listing_id": listing["id"],
                    "crop": listing.get("crop"),
                    "variety": listing.get("variety"),
                    "price": unit_price,
                    "quantity": qty,
                    "seller_id": listing.get("user_id"),
                    "total_price": total
                })
                st.success("Added to cart!")
                st.rerun()
            if st.button("Close"):
                st.session_state.selected_listing = None
                st.rerun()

    # CART & CHECKOUT
    st.markdown("---")
    st.markdown("## Cart & Checkout")
    if not st.session_state.cart:
        st.info("Your cart is empty.")
    else:
        total = sum(item.get("total_price", 0)
                    for item in st.session_state.cart)
        delivery = st.radio("Delivery Method", ["Pickup", "Home Delivery"])
        delivery_fee = 0 if delivery == "Pickup" else 1000
        final_total = total + delivery_fee
        st.markdown(f"**Subtotal:** ₦{total:,.0f}")
        st.markdown(f"**Delivery:** ₦{delivery_fee:,.0f}")
        st.markdown(f"### **Total: ₦{final_total:,.0f}**")
        ref = f"GAIA_MKT_{user.id[:8]}_{uuid.uuid4().hex[:6]}"
        seller_id = st.session_state.cart[0]["seller_id"]
        listing_id = st.session_state.cart[0]["listing_id"]
        order_data = {
            "listing_id": listing_id, "buyer_id": user.id, "seller_id": seller_id,
            "quantity": sum(item["quantity"] for item in st.session_state.cart),
            "total_amount": final_total, "status": "pending", "payment_reference": ref,
            "delivery_method": delivery.lower(), "delivery_fee": delivery_fee
        }
        service.table("marketplace_orders").insert(order_data).execute()
        order_id = service.table("marketplace_orders").select(
            "*").eq("payment_reference", ref).execute().data[0]["id"]
        create_escrow(order_id, final_total)
        components.html(f"""
        <!DOCTYPE html>
        <html><head><script src="https://js.paystack.co/v1/inline.js"></script></head>
        <body>
            <button onclick="payWithPaystack()" style="background:linear-gradient(135deg,#2e7d32,#4caf50);color:#fff;border:none;padding:18px 50px;border-radius:50px;font-weight:700;font-size:1.2rem;cursor:pointer;width:100%;">💳 Pay ₦{final_total:,.0f} with Paystack</button>
            <script>
                function payWithPaystack() {{
                    PaystackPop.setup({{
                        key: '{PAYSTACK_PUBLIC}', email: '{user.email}', amount: {final_total * 100},
                        currency: 'NGN', ref: '{ref}', label: 'GAIA Market',
                        onClose: function() {{ window.location.reload(); }},
                        callback: function(response) {{ window.location.href = '/~/payment_callback?reference=' + response.reference + '&order_type=market'; }}
                    }}).openIframe();
                }}
            </script>
        </body></html>
        """, height=200)
        if st.button("Clear Cart"):
            st.session_state.cart = []
            st.rerun()

# ORDERS TAB
with tab_orders:
    st.markdown("## My Orders")
    orders = service.table("marketplace_orders").select("*").or_(
    f"buyer_id.eq.{
        user.id},seller_id.eq.{
            user.id}").order(
                "created_at",
                 desc=True).execute().data or []
    if not orders:
        st.info("No orders yet.")
    else:
        for order in orders:
            if user and order.get("buyer_id") == user.id:
                        role = "Buyer"
                    else:
                        role = "Seller"
            status = order.get("status", "pending")
            status_emoji = {"pending": "🟡", "paid": "🟢", "completed": "✅", "cancelled": "❌"}.get(status, "⚪")
            listing = get_listing_by_id(order.get("listing_id"))
            crop_info = f"{listing.get('crop','')} {listing.get('variety','')}" if listing else "Item"
            with st.expander(f"{status_emoji} {crop_info} — {role} — {status.upper()}"):
                st.write(f"**Order ID:** {order['id'][:12]}")
                st.write(f"**Amount:** ₦{order.get('total_amount', 0):,}")
                st.write(f"**Quantity:** {order.get('quantity', 0)}")
                st.write(f"**Delivery:** {order.get('delivery_method', 'pickup')}")
                st.write(f"**Status:** {status.upper()}")
                st.write(f"**Reference:** {order.get('payment_reference','')[:20]}")
                try:
                    escrow = service.table("marketplace_escrow").select("*").eq("order_id", order["id"]).execute().data
                    if escrow:
                        esc = escrow[0]
                        esc_status = esc.get("status", "held")
                        st.write(f"**Escrow:** {esc_status.upper()}")
                        if esc_status == "held" and order.get("buyer_id") == user.id and status == "paid":
                            if st.button("Confirm Delivery — Release Payment", key=f"confirm_{order['id']}"):
                                release_escrow(order["id"])
                                st.success("Payment released!")
                                st.rerun()
                except:
                    pass
                with st.expander("Raise Dispute"):
                    with st.form(f"dispute_{order['id']}"):
                        reason = st.text_area("Reason")
                        if st.form_submit_button("Submit Dispute"):
                            create_dispute(order["id"], user.id, reason)
                            st.success("Dispute raised.")
                            st.rerun()

# SELL TAB
with tab_sell:
    st.markdown("## Sell Your Produce")
    if not is_verified_seller(user.id):
        st.warning("You must verify your identity before selling.")
        st.page_link("pages/11_Verify_Farmer.py", label="Verify Now")
    else:
        with st.form("sell_form"):
            crop = st.text_input("Crop *")
            variety = st.text_input("Variety")
            quantity = st.number_input("Quantity", min_value=1.0, value=1.0)
            unit = st.selectbox("Unit", ["tonne", "kg", "bag", "bunch", "piece"])
            price = st.number_input("Price per unit (₦)", min_value=0.0, value=0.0)
            location = st.text_input("Location *")
            state = st.text_input("State *")
            organic = st.checkbox("Organic")
            description = st.text_area("Description")
            uploaded_images = st.file_uploader("Photos", type=["jpg","jpeg","png"], accept_multiple_files=True)
            if st.form_submit_button("Publish Listing"):
                if not crop or not price or not location or not state:
                    st.error("Required fields missing.")
                else:
                    image_urls = []
                    for img_file in uploaded_images:
                        url, _ = upload_listing_image(img_file.read(), img_file.name)
                        if url:
                            image_urls.append(url)
                    service.table("marketplace_listings").insert({
                        "user_id": user.id, "crop": crop, "variety": variety,
                        "quantity": quantity, "unit": unit, "price": price,
                        "location": location, "state": state,
                        "description": description, "organic": organic,
                        "image_urls": image_urls, "status": "active"
                    }).execute()
                    st.success("Listing published!")
                    st.rerun()

# STORE TAB
with tab_store:
    st.markdown("## My Store")
    my_listings = service.table("marketplace_listings").select("*").eq("user_id", user.id).execute().data or []
    if not my_listings:
        st.info("No listings yet.")
    else:
        for listing in my_listings:
            with st.expander(f"{listing.get('crop','')} {listing.get('variety','')} — ₦{listing.get('price',0):,} ({listing.get('status')})"):
                st.write(f"Views: {listing.get('view_count', 0)}")
                if st.button("Delete", key=f"del_{listing['id']}"):
                    service.table("marketplace_listings").delete().eq("id", listing["id"]).execute()
                    st.rerun()

# WALLET TAB
with tab_wallet:
    st.markdown("## Seller Wallet")
    wallet = get_wallet_balance(user.id)
    st.metric("Available Balance", f"₦{wallet.get('balance', 0):,.2f}")
    st.metric("Pending Escrow", f"₦{wallet.get('pending_escrow', 0):,.2f}")
    with st.form("withdraw_form"):
        amount = st.number_input("Amount (₦)", min_value=1000.0, value=1000.0)
        if st.form_submit_button("Request Withdrawal"):
            ok, err = request_withdrawal(user.id, amount)
            if ok:
                st.success("Withdrawal requested.")
            else:
                st.warning("Withdrawal unavailable. Contact support.")

# ALERTS TAB
with tab_alerts:
    st.markdown("## Price Alerts")
    with st.form("alert_form"):
        alert_crop = st.text_input("Crop")
        alert_price = st.number_input("Max Price (₦)", min_value=0.0, value=0.0)
        if st.form_submit_button("Set Alert"):
            create_price_alert(user.id, alert_crop, alert_price)
            st.success("Alert set!")
            st.rerun()
    for alert in get_price_alerts(user.id):
        st.write(f"🔔 {alert.get('crop')} — ₦{alert.get('max_price', 0):,}")

# TRENDS TAB
with tab_trends:
    st.markdown("## Market Price Trends")
    crop_for_trend = st.selectbox("Crop", sorted(set(l.get("crop","") for l in all_listings)))
    trends = get_price_trends(crop_for_trend)
    if trends:
        df = pd.DataFrame(trends)
        df["date"] = pd.to_datetime(df["created_at"]).dt.date
        avg_by_date = df.groupby("date")["price"].mean().reset_index()
        if px:
            fig = px.line(avg_by_date, x="date", y="price", title=f"Average Price — {crop_for_trend}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.line_chart(avg_by_date.set_index("date"))
    else:
        st.info("No data yet.")

# NAVIGATION
st.markdown("---")
st.markdown("### Quick Navigation")
cols = st.columns(10)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[6]: st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[7]: st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[9]: st.page_link("pages/20_Marketplace.py", label="🌍 Market")
