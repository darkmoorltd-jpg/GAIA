
import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
ADMIN_EMAIL = "darkmoorltd@gmail.com"

@st.cache_resource
def init_service_client():
    return create_client(SUPABASE_URL, SERVICE_KEY)

@st.cache_resource
def init_anon_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def safe_crops(val):
    if not val: return 'None'
    if isinstance(val, list): return ', '.join(val)
    return str(val).strip('{}').replace('"', '')

st.set_page_config(page_title="GAIA – Admin", page_icon="🔐", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.stop()
if st.session_state.user.email != ADMIN_EMAIL:
    st.error("Access denied. Admin only.")
    st.stop()

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); color: #fff; }
    header, footer { visibility: hidden; }
    .admin-title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #4caf50; }
    .user-card { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; border: 1px solid rgba(255,255,255,0.1); }
    .verified { color: #4caf50; font-weight: 600; }
    .pending { color: #ff9800; font-weight: 600; }
    .rejected { color: #f44336; font-weight: 600; }
    .stat-box { background: rgba(255,255,255,0.08); border-radius: 12px; padding: 1rem; text-align: center; }
    .stat-number { font-size: 2rem; font-weight: 800; color: #4caf50; }
    .stat-label { font-size: 0.8rem; color: #aaa; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="admin-title">🔐 GAIA Admin Dashboard</div>', unsafe_allow_html=True)

supabase = init_service_client()

# ===== FETCH REAL DATA =====
def fetch_all_users():
    """Fetch all auth users."""
    try:
        resp = supabase.auth.admin.list_users()
        if hasattr(resp, 'users'):
            return resp.users
        return []
    except Exception as e:
        st.error(f"Error fetching users: {e}")
        return []

def fetch_user_profiles():
    """Fetch all user profiles."""
    try:
        resp = supabase.table("user_profiles").select("*").execute()
        return resp.data if resp.data else []
    except:
        return []

def fetch_user_scans():
    """Fetch all user scans."""
    try:
        resp = supabase.table("user_scans").select("*").execute()
        return resp.data if resp.data else []
    except:
        return []

def fetch_payments():
    """Fetch all payment history."""
    try:
        resp = supabase.table("payment_history").select("*").execute()
        return resp.data if resp.data else []
    except:
        return []

def fetch_verifications():
    """Fetch all farmer verifications."""
    try:
        resp = supabase.table("farmer_verifications").select("*").execute()
        return resp.data if resp.data else []
    except:
        return []

def fetch_insurance_policies():
    """Fetch all insurance policies."""
    try:
        resp = supabase.table("insurance_policies").select("*").execute()
        return resp.data if resp.data else []
    except:
        return []

def fetch_insurance_claims():
    """Fetch all insurance claims."""
    try:
        resp = supabase.table("insurance_claims").select("*").execute()
        return resp.data if resp.data else []
    except:
        return []

def fetch_marketplace_listings():
    """Fetch all marketplace listings."""
    try:
        resp = supabase.table("marketplace_listings").select("*").execute()
        return resp.data if resp.data else []
    except:
        return []

def fetch_feedback():
    """Fetch all user feedback."""
    try:
        resp = supabase.table("user_feedback").select("*").execute()
        return resp.data if resp.data else []
    except:
        return []

def fetch_messages():
    """Fetch all support messages."""
    try:
        resp = supabase.table("messages").select("*").execute()
        return resp.data if resp.data else []
    except:
        return []

# ===== LOAD ALL DATA =====
auth_users = fetch_all_users()
profiles = fetch_user_profiles()
scans_data = fetch_user_scans()
payments = fetch_payments()
verifications = fetch_verifications()
insurance_policies = fetch_insurance_policies()
insurance_claims = fetch_insurance_claims()
marketplace_listings = fetch_marketplace_listings()
feedback_data = fetch_feedback()
messages_data = fetch_messages()

# Build profile and scan maps
profile_map = {p["user_id"]: p for p in profiles}
scan_map = {s["user_id"]: s for s in scans_data}

# ===== STATS =====
total_users = len(auth_users)
total_profiles = len(profiles)
verified_count = sum(1 for p in profiles if p.get("verification_status") == "approved")
pending_count = sum(1 for p in profiles if p.get("verification_status") == "pending")
total_payments = len(payments)
total_revenue = sum(p.get("amount", 0) for p in payments)
total_policies = len(insurance_policies)
total_claims = len(insurance_claims)
total_listings = len(marketplace_listings)

# ===== TABS =====
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Overview", "👥 Users", "🛡️ KYC", "💳 Payments", "🏦 Insurance", "🌍 Marketplace", "💬 Feedback", "✏️ Edit/Delete"
])

# ===== TAB 1: OVERVIEW =====
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f'<div class="stat-box"><div class="stat-number">{total_users}</div><div class="stat-label">Total Users</div></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="stat-box"><div class="stat-number">{verified_count}</div><div class="stat-label">Verified</div></div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="stat-box"><div class="stat-number">{total_payments}</div><div class="stat-label">Payments</div></div>', unsafe_allow_html=True)
    col4.markdown(f'<div class="stat-box"><div class="stat-number">₦{total_revenue:,.0f}</div><div class="stat-label">Total Revenue</div></div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f'<div class="stat-box"><div class="stat-number">{total_policies}</div><div class="stat-label">Insurance Policies</div></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="stat-box"><div class="stat-number">{total_claims}</div><div class="stat-label">Insurance Claims</div></div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="stat-box"><div class="stat-number">{total_listings}</div><div class="stat-label">Marketplace Listings</div></div>', unsafe_allow_html=True)
    col4.markdown(f'<div class="stat-box"><div class="stat-number">{pending_count}</div><div class="stat-label">Pending KYC</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Recent Users")
    
    if auth_users:
        recent = []
        for u in auth_users[:20]:
            uid = u.id
            p = profile_map.get(uid, {})
            recent.append({
                "Email": u.email,
                "Name": f"{p.get('first_name','')} {p.get('last_name','')}".strip(),
                "Phone": p.get("phone", ""),
                "State": p.get("state", ""),
                "KYC": p.get("verification_status", "N/A"),
                "Created": u.created_at[:10] if u.created_at else "",
            })
        st.dataframe(pd.DataFrame(recent), use_container_width=True)
    else:
        st.info("No users found in the database.")

# ===== TAB 2: USERS =====
with tab2:
    st.markdown("### 👥 All Users")
    
    if not auth_users:
        st.warning("⚠️ No users found. Check if the service_role key is correct in Streamlit secrets.")
        st.code("""
        [supabase]
        url = "your_url"
        key = "anon_key"
        service_key = "service_role_key"
        """)
    else:
        st.success(f"✅ Found {total_users} users")
        
        for u in auth_users:
            uid = u.id
            p = profile_map.get(uid, {})
            s = scan_map.get(uid, {})
            
            status = p.get("verification_status", "N/A")
            status_emoji = "✅" if status == "approved" else ("⏳" if status == "pending" else "❌")
            
            with st.expander(f"{status_emoji} {p.get('first_name','')} {p.get('last_name','')} — {u.email}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**User ID:** {uid[:16]}...")
                    st.write(f"**Email:** {u.email}")
                    st.write(f"**Phone:** {p.get('phone','N/A')}")
                    st.write(f"**WhatsApp:** {p.get('whatsapp','N/A')}")
                with col2:
                    st.write(f"**State:** {p.get('state','N/A')}")
                    st.write(f"**LGA:** {p.get('lga','N/A')}")
                    st.write(f"**City:** {p.get('city','N/A')}")
                    st.write(f"**Address:** {p.get('street_address','N/A')}")
                with col3:
                    st.write(f"**Scans:** {s.get('scans_remaining', 0)}")
                    st.write(f"**Plan:** {s.get('plan', 'free')}")
                    st.write(f"**BVN:** {p.get('bvn','N/A')}")
                    st.write(f"**NIN:** {p.get('nin','N/A')}")
                
                # Farm info
                with st.expander("🌾 Farm Info"):
                    st.write(f"**Farm State:** {p.get('farm_state','N/A')}")
                    st.write(f"**Farm Size:** {p.get('farm_size_acres','N/A')} acres")
                    st.write(f"**Primary Crops:** {p.get('primary_crops','N/A')}")
                    st.write(f"**Experience:** {p.get('years_experience','N/A')} years")
                
                # Banking
                with st.expander("🏦 Banking"):
                    st.write(f"**Account Name:** {p.get('account_name','N/A')}")
                    st.write(f"**Account Number:** {p.get('account_number','N/A')}")
                    st.write(f"**Bank:** {p.get('bank_name','N/A')}")
                
                # Emergency
                with st.expander("🚨 Emergency Contact"):
                    st.write(f"**Name:** {p.get('emergency_contact_name','N/A')}")
                    st.write(f"**Phone:** {p.get('emergency_contact_phone','N/A')}")
                    st.write(f"**Relationship:** {p.get('emergency_relationship','N/A')}")

# ===== TAB 3: KYC =====
with tab3:
    st.markdown("### 🛡️ KYC Verification")
    
    pending_kyc = [p for p in profiles if p.get("verification_status") == "pending" and p.get("bvn")]
    
    if not pending_kyc:
        st.info("No pending KYC verifications.")
    else:
        st.success(f"Found {len(pending_kyc)} pending verifications")
        
        for p in pending_kyc:
            with st.expander(f"⏳ {p.get('first_name','')} {p.get('last_name','')} — {p.get('email','N/A')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**BVN:** {p.get('bvn','N/A')}")
                    st.write(f"**NIN:** {p.get('nin','N/A')}")
                    st.write(f"**ID Type:** {p.get('govt_id_type','N/A')}")
                with col2:
                    st.write(f"**ID Number:** {p.get('govt_id_number','N/A')}")
                    st.write(f"**Phone:** {p.get('phone','N/A')}")
                    st.write(f"**State:** {p.get('state','N/A')}")
                
                col1, col2, col3 = st.columns(3)
                if col1.button("✅ Approve", key=f"approve_{p['user_id']}"):
                    supabase.table("user_profiles").update({"verification_status": "approved", "kyc_level": 2}).eq("user_id", p["user_id"]).execute()
                    st.success("Approved!")
                    st.rerun()
                if col2.button("❌ Reject", key=f"reject_{p['user_id']}"):
                    supabase.table("user_profiles").update({"verification_status": "rejected"}).eq("user_id", p["user_id"]).execute()
                    st.error("Rejected.")
                    st.rerun()
                if col3.button("🗑️ Delete", key=f"del_kyc_{p['user_id']}"):
                    supabase.table("user_profiles").delete().eq("user_id", p["user_id"]).execute()
                    st.warning("Deleted.")
                    st.rerun()

# ===== TAB 4: PAYMENTS =====
with tab4:
    st.markdown("### 💳 Payment History")
    
    if not payments:
        st.info("No payments yet.")
    else:
        payment_data = []
        for p in payments:
            payment_data.append({
                "User": p.get("user_id", "")[:12],
                "Amount": f"₦{p.get('amount', 0):,.2f}",
                "Scans": p.get("scans_added", 0),
                "Plan": p.get("plan", ""),
                "Reference": p.get("reference", ""),
                "Date": p.get("paid_at", "")[:16],
            })
        st.dataframe(pd.DataFrame(payment_data), use_container_width=True)

# ===== TAB 5: INSURANCE =====
with tab5:
    st.markdown("### 🏦 Insurance Policies")
    
    if insurance_policies:
        for pol in insurance_policies:
            with st.expander(f"Policy #{pol.get('policy_number','?')} — {pol.get('crop','')} — {pol.get('status','')}"):
                st.write(f"**User:** {pol.get('user_id','')[:16]}...")
                st.write(f"**Coverage:** ₦{pol.get('coverage_amount',0):,}")
                st.write(f"**Premium:** ₦{pol.get('premium_monthly',0):,}/month")
                st.write(f"**Location:** {pol.get('field_location','N/A')}")
    else:
        st.info("No insurance policies yet.")
    
    st.markdown("---")
    st.markdown("### 📝 Insurance Claims")
    
    if insurance_claims:
        for claim in insurance_claims:
            status = claim.get("status", "pending")
            with st.expander(f"Claim #{claim.get('id','?')} — {claim.get('claim_type','')} — {status}"):
                st.write(f"**User:** {claim.get('user_id','')[:16]}...")
                st.write(f"**Description:** {claim.get('description','')[:200]}")
                
                if status == "pending":
                    col1, col2 = st.columns(2)
                    if col1.button("✅ Approve", key=f"app_claim_{claim['id']}"):
                        supabase.table("insurance_claims").update({"status": "approved"}).eq("id", claim["id"]).execute()
                        st.rerun()
                    if col2.button("❌ Reject", key=f"rej_claim_{claim['id']}"):
                        supabase.table("insurance_claims").update({"status": "rejected"}).eq("id", claim["id"]).execute()
                        st.rerun()
    else:
        st.info("No insurance claims yet.")

# ===== TAB 6: MARKETPLACE =====
with tab6:
    st.markdown("### 🌍 Marketplace Listings")
    
    if marketplace_listings:
        for listing in marketplace_listings:
            with st.expander(f"{listing.get('crop','')} — ₦{listing.get('price',0):,} — {listing.get('status','')}"):
                st.write(f"**Seller:** {listing.get('farmer','N/A')}")
                st.write(f"**Location:** {listing.get('location','')}, {listing.get('state','')}")
                st.write(f"**Quantity:** {listing.get('quantity','')} {listing.get('unit','tonnes')}")
                
                col1, col2 = st.columns(2)
                if listing.get("status") == "active":
                    if col1.button("🔴 Deactivate", key=f"deact_list_{listing['id']}"):
                        supabase.table("marketplace_listings").update({"status": "inactive"}).eq("id", listing["id"]).execute()
                        st.rerun()
                if col2.button("🗑️ Delete", key=f"del_list_{listing['id']}"):
                    supabase.table("marketplace_listings").delete().eq("id", listing["id"]).execute()
                    st.rerun()
    else:
        st.info("No marketplace listings yet.")

# ===== TAB 7: FEEDBACK =====
with tab7:
    st.markdown("### 💬 User Feedback")
    
    if feedback_data:
        for fb in feedback_data:
            with st.expander(f"{'👍' if fb.get('helpful') else '👎'} {fb.get('predicted_class','')} — {fb.get('created_at','')[:16]}"):
                st.write(f"**User:** {fb.get('user_id','')[:16]}...")
                st.write(f"**Image:** {fb.get('image_name','')}")
    else:
        st.info("No feedback yet.")

# ===== TAB 8: EDIT/DELETE =====
with tab8:
    st.markdown("### ✏️ Edit or Delete User")
    
    if auth_users:
        user_emails = [u.email for u in auth_users]
        selected_email = st.selectbox("Select User", user_emails, key="edit_user_select")
        
        selected_user = next((u for u in auth_users if u.email == selected_email), None)
        
        if selected_user:
            uid = selected_user.id
            p = profile_map.get(uid, {})
            s = scan_map.get(uid, {})
            
            st.markdown(f"### Editing: {selected_email}")
            
            with st.form("edit_user_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_first = st.text_input("First Name", value=p.get("first_name", ""))
                    new_last = st.text_input("Last Name", value=p.get("last_name", ""))
                    new_phone = st.text_input("Phone", value=p.get("phone", ""))
                with col2:
                    new_bvn = st.text_input("BVN", value=p.get("bvn", ""))
                    new_nin = st.text_input("NIN", value=p.get("nin", ""))
                    new_state = st.text_input("State", value=p.get("state", ""))
                with col3:
                    new_status = st.selectbox("KYC Status", ["pending", "approved", "rejected"],
                                              index=["pending", "approved", "rejected"].index(p.get("verification_status", "pending")))
                    scans_add = st.number_input("Add Scans", min_value=0, value=0)
                    new_password = st.text_input("New Password (optional)", type="password")
                
                if st.form_submit_button("💾 Update User"):
                    updates = {}
                    if new_first != p.get("first_name", ""): updates["first_name"] = new_first
                    if new_last != p.get("last_name", ""): updates["last_name"] = new_last
                    if new_phone != p.get("phone", ""): updates["phone"] = new_phone
                    if new_bvn != p.get("bvn", ""): updates["bvn"] = new_bvn
                    if new_nin != p.get("nin", ""): updates["nin"] = new_nin
                    if new_state != p.get("state", ""): updates["state"] = new_state
                    if new_status != p.get("verification_status", ""): updates["verification_status"] = new_status
                    
                    if updates:
                        try:
                            supabase.table("user_profiles").update(updates).eq("user_id", uid).execute()
                        except:
                            supabase.table("user_profiles").insert({"user_id": uid, **updates}).execute()
                    
                    if scans_add > 0:
                        current = s.get("scans_remaining", 0)
                        supabase.table("user_scans").update({"scans_remaining": current + scans_add}).eq("user_id", uid).execute()
                    
                    if new_password and len(new_password) >= 6:
                        supabase.auth.admin.update_user(uid, {"password": new_password})
                    
                    st.success("✅ User updated!")
                    st.rerun()
            
            # Delete user
            st.markdown("---")
            st.markdown("### 🗑️ Danger Zone")
            confirm_delete = st.checkbox("I understand this will permanently delete the user and all their data.")
            
            if st.button("🗑️ Delete User", type="secondary"):
                if not confirm_delete:
                    st.warning("Please confirm the checkbox first.")
                else:
                    try:
                        for table in ["payment_history", "messages", "farmer_verifications", "user_profiles", "user_scans", "marketplace_listings", "insurance_policies", "insurance_claims", "field_monitoring", "seller_profiles", "badge_subscriptions", "farmer_wallets", "user_feedback"]:
                            try:
                                supabase.table(table).delete().eq("user_id", uid).execute()
                            except:
                                pass
                        supabase.auth.admin.delete_user(uid)
                        st.success(f"User {selected_email} deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")

# ===== NAVIGATION =====
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(9)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/8_Profile.py", label="👤 Profile")
with cols[6]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[7]: st.page_link("pages/20_Marketplace.py", label="🌍 Market")
with cols[8]: st.page_link("pages/21_Crop_Insurance.py", label="🏦 Insurance")
