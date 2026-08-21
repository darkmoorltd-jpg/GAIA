import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="Extension Dashboard", page_icon="🧑‍🌾", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["service_key"])

st.markdown("<h1 style='color:#2e7d32;'>🧑‍🌾 Extension Dashboard</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📋 Assign Farmers", "📊 Field Reports", "📈 Performance"])

with tab1:
    st.markdown("### Assign farmers to extension officers")
    # Fetch assignments
    assignments_res = supabase.table("extension_assignments").select("*").execute()
    assignments = assignments_res.data if assignments_res.data else []
    if assignments:
        df_a = pd.DataFrame(assignments)
        st.dataframe(df_a, use_container_width=True)
    with st.form("assign_form"):
        user_email = st.text_input("Farmer Email")
        officer_name = st.text_input("Extension Officer Name")
        crops = st.text_input("Crops (comma separated)")
        if st.form_submit_button("Assign"):
            # Find user by email
            auth_res = supabase.auth.admin.list_users()
            target_user = None
            for u in auth_res:
                if u.email == user_email:
                    target_user = u
                    break
            if target_user:
                supabase.table("extension_assignments").insert({
                    "user_id": target_user.id,
                    "officer_name": officer_name,
                    "assigned_crops": crops
                }).execute()
                st.success("Farmer assigned.")
                st.rerun()
            else:
                st.error("Farmer email not found.")

with tab2:
    st.markdown("### Field Reports")
    # Submit new report
    with st.form("report_form"):
        report_type = st.selectbox("Report Type", ["Crop disease", "Pest outbreak", "Soil issue", "General advisory"])
        location = st.text_input("Location (LGA/State)")
        description = st.text_area("Description")
        if st.form_submit_button("Submit Report"):
            if location and description:
                supabase.table("field_reports").insert({
                    "user_id": st.session_state.user.id,
                    "report_type": report_type,
                    "description": description,
                    "location": location,
                    "created_at": "now()"
                }).execute()
                st.success("Report submitted.")
                st.rerun()
    # View reports
    reports_res = supabase.table("field_reports").select("*").order("created_at", desc=True).limit(50).execute()
    reports = reports_res.data if reports_res.data else []
    if reports:
        for rep in reports:
            st.markdown(f"**{rep.get('report_type','')}** — {rep.get('location','')}")
            st.write(rep.get('description',''))
            st.caption(rep.get('created_at',''))
            st.divider()
    else:
        st.info("No field reports yet.")

with tab3:
    st.markdown("### Performance")
    officers = supabase.table("extension_assignments").select("officer_name").execute()
    df_off = pd.DataFrame(officers.data) if officers.data else pd.DataFrame()
    if not df_off.empty:
        perf = df_off["officer_name"].value_counts().reset_index()
        perf.columns = ["Officer", "Farmers Assigned"]
        st.dataframe(perf, use_container_width=True)
    else:
        st.info("No assignments yet.")
