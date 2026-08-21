import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="Extension Dashboard", page_icon="🧑‍🌾", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["service_key"])

st.markdown("<h1 style='color:#2e7d32;'>🧑‍🌾 Extension Dashboard</h1>", unsafe_allow_html=True)
st.markdown("Assign farmers to extension officers and view field reports.")

tab1, tab2 = st.tabs(["📋 Assign Farmers", "📊 Field Reports"])

with tab1:
    st.markdown("### Assign farmers to extension officers")
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
            else:
                st.error("Farmer email not found.")

with tab2:
    st.markdown("### Field Reports")
    res = supabase.table("field_reports").select("*").order("created_at", desc=True).limit(20).execute()
    reports = res.data if res.data else []
    if reports:
        for rep in reports:
            st.markdown(f"**{rep.get('report_type','')}** — {rep.get('location','')}")
            st.write(rep.get('description',''))
            st.caption(rep.get('created_at',''))
            st.divider()
    else:
        st.info("No field reports yet.")
