import streamlit as st
from supabase import create_client
import pandas as pd
import folium
from streamlit_folium import st_folium
import datetime
import uuid as uuid_lib

st.set_page_config(page_title="Farmer Database", page_icon="🌍", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

supabase = create_client(
    st.secrets["supabase"]["url"], st.secrets["supabase"]["service_key"]
)

st.markdown(
    "<h1 style='color:#2e7d32;text-align:center;'>🌍 National Farmer Database</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;'>Digital backbone for agricultural finance and extension</p>",
    unsafe_allow_html=True,
)

# ── Fetch data ──
farmers_res = supabase.table("farmer_registry").select("*").execute()
farmers = farmers_res.data if farmers_res.data else []
profiles_res = supabase.table("user_profiles").select("*").execute()
profiles = profiles_res.data if profiles_res.data else []
profile_map = {p["user_id"]: p for p in profiles}

# ── Build dataframe ──
df = pd.DataFrame(farmers) if farmers else pd.DataFrame()
if not df.empty:

    def get_name(uid):
        p = profile_map.get(uid, {})
        return f"{
            p.get(
                'first_name',
                '')} {
            p.get(
                'last_name',
                '')}".strip() or "Unknown"

    def get_phone(uid):
        return profile_map.get(uid, {}).get("phone", "")

    def get_verification(uid):
        return profile_map.get(uid, {}).get("verification_status", "pending")

    df["full_name"] = df["user_id"].apply(get_name)
    df["phone"] = df["user_id"].apply(get_phone)
    df["verification_status"] = df["user_id"].apply(get_verification)

# ── Metrics ──
if not df.empty:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Farmers", len(df))
    col2.metric("States", df["state"].nunique())
    col3.metric("Crops", df["crop"].nunique())
    col4.metric("Verified", len(df[df["verification_status"] == "approved"]))

# ── Tabs ──
tab_table, tab_analytics, tab_map, tab_detail, tab_register = st.tabs(
    ["📋 Table", "📊 Analytics", "🗺️ Map", "🔍 Farmer Detail", "➕ Register"]
)

# ---------- Table ----------
with tab_table:
    if df.empty:
        st.info("No farmers registered yet.")
    else:
        search = st.text_input(
            "Search by name, phone, state, crop",
            placeholder="e.g., Ibrahim, 0803, Kano, Maize",
        )
        filtered = df
        if search:
            q = search.lower()
            filtered = df[
                df["full_name"].str.lower().str.contains(q)
                | df["phone"].astype(str).str.contains(q)
                | df["state"].str.lower().str.contains(q)
                | df["crop"].str.lower().str.contains(q)
            ]
        st.dataframe(
            filtered[
                [
                    "full_name",
                    "phone",
                    "state",
                    "lga",
                    "crop",
                    "farm_size_acres",
                    "verification_status",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "📥 Export CSV", filtered.to_csv(index=False), "farmers.csv", "text/csv"
        )

# ---------- Analytics ----------
with tab_analytics:
    if df.empty:
        st.info("No data for analytics.")
    else:
        st.subheader("Farmers by State")
        st.bar_chart(df["state"].value_counts())
        st.subheader("Crop Adoption")
        st.bar_chart(df["crop"].value_counts())
        st.subheader("Verification Status")
        st.bar_chart(df["verification_status"].value_counts())

# ---------- Map ----------
with tab_map:
    if df.empty:
        st.info("No farmers to plot.")
    else:
        farmers_with_gps = df[
            df.get("gps_lat", pd.Series()).notna()
            & df.get("gps_lon", pd.Series()).notna()
        ]
        if farmers_with_gps.empty:
            st.warning("No GPS coordinates available. Add GPS in Register.")
        else:
            m = folium.Map(location=[9.0765, 7.3986], zoom_start=6)
            for _, row in farmers_with_gps.iterrows():
                folium.Marker(
                    [row["gps_lat"], row["gps_lon"]],
                    popup=f"{row['full_name']} - {row['crop']}",
                    tooltip=row["full_name"],
                ).add_to(m)
            st_folium(m, width=700, height=500)

# ---------- Detail ----------
with tab_detail:
    if df.empty:
        st.info("No farmers to show.")
    else:
        selected_name = st.selectbox("Select Farmer", df["full_name"])
        farmer = df[df["full_name"] == selected_name].iloc[0]
        uid = farmer["user_id"]
        st.markdown(f"### 👤 {farmer['full_name']}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Phone:** {farmer['phone'] or 'N/A'}")
            st.write(f"**State:** {farmer['state']}")
            st.write(f"**LGA:** {farmer['lga']}")
        with col2:
            st.write(f"**Primary Crop:** {farmer['crop']}")
            st.write(f"**Farm Size:** {farmer['farm_size_acres']} acres")
            st.write(f"**Verification:** {farmer['verification_status']}")
        with col3:
            st.write(f"**Farmer Type:** {farmer.get('farmer_type', 'N/A')}")
            st.write(f"**Gender:** {farmer.get('gender', 'N/A')}")
            st.write(f"**Youth:** {'Yes' if farmer.get('youth') else 'No'}")
        st.markdown("---")
        st.subheader("💰 Loan History")
        loans_res = (
            supabase.table("farmer_loan_history")
            .select("*")
            .eq("user_id", uid)
            .execute()
        )
        loans = loans_res.data if loans_res.data else []
        if loans:
            st.dataframe(pd.DataFrame(loans), use_container_width=True)
        else:
            st.info("No loan history.")
        st.subheader("🌿 Recent Diagnoses")
        diag_res = (
            supabase.table("farmer_diagnoses")
            .select("*")
            .eq("user_id", uid)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )
        diagnoses = diag_res.data if diag_res.data else []
        if diagnoses:
            for d in diagnoses:
                st.write(f"- **{d['diagnosis_type']}**: {d['result']}")
        else:
            st.info("No diagnoses yet.")

# ---------- Register New Farmer ----------
with tab_register:
    st.subheader("Create Farmer Account")
    with st.form("register_new_farmer"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name *")
            last_name = st.text_input("Last Name *")
            email = st.text_input("Email *")
            password = st.text_input("Password *", type="password")
            phone = st.text_input("Phone")
        with col2:
            state = st.text_input("State *")
            lga = st.text_input("LGA *")
            crop = st.text_input("Primary Crop *")
            farm_size = st.number_input("Farm Size (acres)", min_value=0.0, value=1.0)
            farmer_type = st.selectbox(
                "Farmer Type",
                ["Smallholder", "Commercial", "Cooperative", "Youth", "Woman"],
            )
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            youth = st.checkbox("Youth?")
            gps_lat = st.number_input("GPS Latitude (optional)", value=0.0)
            gps_lon = st.number_input("GPS Longitude (optional)", value=0.0)

        if st.form_submit_button("Register Farmer"):
            if not (
                first_name
                and last_name
                and email
                and password
                and state
                and lga
                and crop
            ):
                st.error("Please fill all required fields marked with *")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                try:
                    auth_user = supabase.auth.admin.create_user(
                        {"email": email, "password": password, "email_confirm": True}
                    )
                    if auth_user.user:
                        new_uid = auth_user.user.id
                        supabase.table("user_profiles").insert(
                            {
                                "user_id": new_uid,
                                "first_name": first_name,
                                "last_name": last_name,
                                "phone": phone,
                                "verification_status": "pending",
                            }
                        ).execute()
                        unique_id = f"GAIA-{uuid_lib.uuid4().hex[:8].upper()}"
                        supabase.table("farmer_registry").insert(
                            {
                                "user_id": new_uid,
                                "state": state,
                                "lga": lga,
                                "phone": phone,
                                "crop": crop,
                                "farm_size_acres": farm_size,
                                "farmer_type": farmer_type,
                                "gender": gender,
                                "youth": youth,
                                "gps_lat": gps_lat if gps_lat != 0 else None,
                                "gps_lon": gps_lon if gps_lon != 0 else None,
                                "unique_farmer_id": unique_id,
                            }
                        ).execute()
                        st.success(
                            f"Farmer account created! Email: {email} | Farmer ID: {unique_id}"
                        )
                    else:
                        st.error("Failed to create user.")
                except Exception as e:
                    st.error(f"Error: {str(e)[:200]}")
