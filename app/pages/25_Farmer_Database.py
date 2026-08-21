import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="Farmer Database", page_icon="🌍", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["service_key"])

st.markdown("<h1 style='color:#2e7d32;'>🌍 National Farmer Database</h1>", unsafe_allow_html=True)

# Fetch farmer registry and profiles
res = supabase.table("farmer_registry").select("*").execute()
farmers = res.data if res.data else []
profiles_res = supabase.table("user_profiles").select("*").execute()
profiles = profiles_res.data if profiles_res.data else []
profile_map = {p["user_id"]: p for p in profiles}

if farmers:
    df = pd.DataFrame(farmers)
    # Merge profile data
    def get_name(uid):
        p = profile_map.get(uid, {})
        first = p.get("first_name", "")
        last = p.get("last_name", "")
        return f"{first} {last}".strip() or "Unknown"
    df["full_name"] = df["user_id"].apply(get_name)
    df["phone"] = df["user_id"].apply(lambda u: profile_map.get(u, {}).get("phone", ""))
    df["verification_status"] = df["user_id"].apply(lambda u: profile_map.get(u, {}).get("verification_status", "pending"))

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Farmers", len(df))
    col2.metric("States", df["state"].nunique())
    col3.metric("Crops", df["crop"].nunique())
    col4.metric("Verified", len(df[df["verification_status"] == "approved"]))

    # Search
    search = st.text_input("Search by name, phone, state, or crop", placeholder="e.g., Ibrahim, 0803, Kano, Maize")

    filtered = df
    if search:
        q = search.lower()
        filtered = df[
            df["full_name"].str.lower().str.contains(q) |
            df["phone"].str.contains(q) |
            df["state"].str.lower().str.contains(q) |
            df["crop"].str.lower().str.contains(q)
        ]

    st.dataframe(
        filtered[["full_name", "phone", "state", "lga", "crop", "farm_size_acres", "verification_status"]],
        use_container_width=True,
        hide_index=True
    )

    # Export CSV
    csv = filtered.to_csv(index=False)
    st.download_button("📥 Export CSV", csv, "farmers.csv", "text/csv")
else:
    st.info("No farmers registered yet.")

# Register new farmer
st.markdown("---")
st.markdown("### ➕ Register New Farmer")
with st.form("register_farmer"):
    col1, col2 = st.columns(2)
    with col1:
        state = st.text_input("State")
        lga = st.text_input("LGA")
        phone = st.text_input("Phone")
    with col2:
        crop = st.text_input("Primary Crop")
        farm_size = st.number_input("Farm Size (acres)", min_value=0.0, value=1.0)
    if st.form_submit_button("Register"):
        if state and lga and crop:
            supabase.table("farmer_registry").insert({
                "user_id": st.session_state.user.id,
                "state": state,
                "lga": lga,
                "phone": phone,
                "crop": crop,
                "farm_size_acres": farm_size
            }).execute()
            st.success("Farmer registered!")
            st.rerun()
        else:
            st.error("State, LGA, and Crop are required.")
