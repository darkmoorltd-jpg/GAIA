import streamlit as st
import requests
import uuid
from datetime import datetime
from supabase import create_client, Client

def get_service_client():
    url = st.secrets["supabase"]["url"]
    service_key = st.secrets["supabase"]["service_key"]
    return create_client(url, service_key)

def upload_listing_image(file_bytes, filename):
    supabase = get_service_client()
    unique_name = f"{uuid.uuid4().hex[:12]}_{filename}"
    bucket = "listing-images"
    try:
        supabase.storage.from_(bucket).upload(unique_name, file_bytes, {"content-type": "image/jpeg"})
        return supabase.storage.from_(bucket).get_public_url(unique_name), None
    except Exception as e:
        return None, str(e)[:200]

def verify_payment(reference):
    paystack_secret = st.secrets["paystack"]["secret_key"]
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {paystack_secret}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") and data["data"]["status"] == "success":
                return data["data"]
    except:
        pass
    return None

def get_listing_by_id(listing_id):
    supabase = get_service_client()
    try:
        res = supabase.table("marketplace_listings").select("*").eq("id", listing_id).execute()
        return res.data[0] if res.data else None
    except:
        return None

def get_seller_profile(seller_id):
    supabase = get_service_client()
    try:
        res = supabase.table("user_profiles").select("*").eq("user_id", seller_id).execute()
        return res.data[0] if res.data else {}
    except:
        return {}

def add_review(listing_id, seller_id, reviewer_id, rating, comment):
    supabase = get_service_client()
    supabase.table("marketplace_reviews").insert({
        "listing_id": listing_id,
        "seller_id": seller_id,
        "reviewer_id": reviewer_id,
        "rating": rating,
        "comment": comment
    }).execute()

def get_reviews(listing_id):
    supabase = get_service_client()
    res = supabase.table("marketplace_reviews").select("*").eq("listing_id", listing_id).order("created_at", desc=True).execute()
    return res.data if res.data else []

def get_seller_rating(seller_id):
    supabase = get_service_client()
    res = supabase.table("marketplace_reviews").select("rating").eq("seller_id", seller_id).execute()
    if res.data:
        avg = sum(r["rating"] for r in res.data) / len(res.data)
        return round(avg, 1), len(res.data)
    return 0, 0

def toggle_favorite(user_id, listing_id):
    supabase = get_service_client()
    res = supabase.table("marketplace_favorites").select("*").eq("user_id", user_id).eq("listing_id", listing_id).execute()
    if res.data:
        supabase.table("marketplace_favorites").delete().eq("user_id", user_id).eq("listing_id", listing_id).execute()
        return False
    else:
        supabase.table("marketplace_favorites").insert({"user_id": user_id, "listing_id": listing_id}).execute()
        return True

def is_favorite(user_id, listing_id):
    supabase = get_service_client()
    res = supabase.table("marketplace_favorites").select("*").eq("user_id", user_id).eq("listing_id", listing_id).execute()
    return len(res.data) > 0

def get_favorites(user_id):
    supabase = get_service_client()
    res = supabase.table("marketplace_favorites").select("listing_id").eq("user_id", user_id).execute()
    ids = [r["listing_id"] for r in res.data] if res.data else []
    if not ids:
        return []
    listings = supabase.table("marketplace_listings").select("*").in_("id", ids).execute()
    return listings.data if listings.data else []

def create_escrow(order_id, amount):
    supabase = get_service_client()
    supabase.table("marketplace_escrow").insert({
        "order_id": order_id,
        "amount": amount,
        "status": "held"
    }).execute()

def release_escrow(order_id):
    supabase = get_service_client()
    supabase.table("marketplace_escrow").update({
        "status": "released",
        "released_at": datetime.now().isoformat()
    }).eq("order_id", order_id).execute()
    supabase.table("marketplace_orders").update({"status": "paid"}).eq("id", order_id).execute()

def create_dispute(order_id, user_id, reason):
    supabase = get_service_client()
    supabase.table("marketplace_disputes").insert({
        "order_id": order_id,
        "raised_by": user_id,
        "reason": reason,
        "status": "open"
    }).execute()

def get_dispute(order_id):
    supabase = get_service_client()
    res = supabase.table("marketplace_disputes").select("*").eq("order_id", order_id).execute()
    return res.data[0] if res.data else None

def create_negotiation(listing_id, buyer_id, seller_id, proposed_price, proposed_quantity, message):
    supabase = get_service_client()
    supabase.table("marketplace_negotiations").insert({
        "listing_id": listing_id,
        "buyer_id": buyer_id,
        "seller_id": seller_id,
        "proposed_price": proposed_price,
        "proposed_quantity": proposed_quantity,
        "message": message
    }).execute()

def get_negotiations(user_id):
    supabase = get_service_client()
    res = supabase.table("marketplace_negotiations").select("*").or_(f"buyer_id.eq.{user_id},seller_id.eq.{user_id}").order("created_at", desc=True).execute()
    return res.data if res.data else []

def save_search(user_id, query):
    supabase = get_service_client()
    supabase.table("marketplace_saved_searches").insert({
        "user_id": user_id,
        "query": query
    }).execute()

def get_saved_searches(user_id):
    supabase = get_service_client()
    res = supabase.table("marketplace_saved_searches").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data if res.data else []

def get_price_index(crop=None, state=None):
    supabase = get_service_client()
    query = supabase.table("marketplace_price_index").select("*")
    if crop:
        query = query.eq("crop", crop)
    if state:
        query = query.eq("state", state)
    res = query.execute()
    return res.data if res.data else []

def update_price_index(crop, state, avg_price, count):
    supabase = get_service_client()
    supabase.table("marketplace_price_index").upsert({
        "crop": crop,
        "state": state,
        "avg_price": avg_price,
        "sample_count": count,
        "updated_at": datetime.now().isoformat()
    }).execute()

def get_notifications(user_id):
    supabase = get_service_client()
    res = supabase.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(20).execute()
    return res.data if res.data else []

def create_notification(user_id, title, body, notif_type):
    supabase = get_service_client()
    supabase.table("notifications").insert({
        "user_id": user_id,
        "title": title,
        "body": body,
        "type": notif_type
    }).execute()

def get_currency_rates():
    supabase = get_service_client()
    res = supabase.table("currency_rates").select("*").execute()
    return res.data if res.data else []

def get_delivery_partners():
    supabase = get_service_client()
    res = supabase.table("delivery_partners").select("*").execute()
    return res.data if res.data else []
