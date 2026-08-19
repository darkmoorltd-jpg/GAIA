
import streamlit as st
import requests
import uuid
from supabase import create_client, Client

def get_service_client():
    """Return a Supabase client with service role (bypasses RLS)."""
    url = st.secrets["supabase"]["url"]
    service_key = st.secrets["supabase"]["service_key"]
    return create_client(url, service_key)

def upload_listing_image(file_bytes, filename):
    """Upload an image to Supabase Storage and return its public URL."""
    supabase = get_service_client()
    unique_name = f"{uuid.uuid4().hex[:12]}_{filename}"
    bucket = "listing-images"
    try:
        supabase.storage.from_(bucket).upload(
            unique_name,
            file_bytes,
            {"content-type": "image/jpeg"}
        )
        return supabase.storage.from_(bucket).get_public_url(unique_name), None
    except Exception as e:
        return None, str(e)[:200]

def verify_payment(reference):
    """Verify a Paystack transaction."""
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
    """Fetch a single listing by ID."""
    supabase = get_service_client()
    try:
        res = supabase.table("marketplace_listings").select("*").eq("id", listing_id).execute()
        return res.data[0] if res.data else None
    except:
        return None

def get_seller_profile(seller_id):
    """Fetch seller profile from user_profiles."""
    supabase = get_service_client()
    try:
        res = supabase.table("user_profiles").select("*").eq("user_id", seller_id).execute()
        return res.data[0] if res.data else {}
    except:
        return {}

def add_review(listing_id, seller_id, reviewer_id, rating, comment):
    """Insert a review for a listing."""
    supabase = get_service_client()
    supabase.table("marketplace_reviews").insert({
        "listing_id": listing_id,
        "seller_id": seller_id,
        "reviewer_id": reviewer_id,
        "rating": rating,
        "comment": comment
    }).execute()

def get_reviews(listing_id):
    """Fetch reviews for a listing."""
    supabase = get_service_client()
    res = supabase.table("marketplace_reviews").select("*").eq("listing_id", listing_id).order("created_at", desc=True).execute()
    return res.data if res.data else []

def toggle_favorite(user_id, listing_id):
    """Toggle favorite status for a listing. Returns True if now favorite, False otherwise."""
    supabase = get_service_client()
    res = supabase.table("marketplace_favorites").select("*").eq("user_id", user_id).eq("listing_id", listing_id).execute()
    if res.data:
        supabase.table("marketplace_favorites").delete().eq("user_id", user_id).eq("listing_id", listing_id).execute()
        return False
    else:
        supabase.table("marketplace_favorites").insert({"user_id": user_id, "listing_id": listing_id}).execute()
        return True

def is_favorite(user_id, listing_id):
    """Check if a listing is in user's favorites."""
    supabase = get_service_client()
    res = supabase.table("marketplace_favorites").select("*").eq("user_id", user_id).eq("listing_id", listing_id).execute()
    return len(res.data) > 0

def get_favorites(user_id):
    """Fetch all favorite listings for a user."""
    supabase = get_service_client()
    res = supabase.table("marketplace_favorites").select("listing_id").eq("user_id", user_id).execute()
    ids = [r["listing_id"] for r in res.data] if res.data else []
    if not ids:
        return []
    listings = supabase.table("marketplace_listings").select("*").in_("id", ids).execute()
    return listings.data if listings.data else []
