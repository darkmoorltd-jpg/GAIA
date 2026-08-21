import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="Loan Management", page_icon="🏦", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["service_key"])

st.markdown("<h1 style='color:#2e7d32;'>🏦 Loan Management</h1>", unsafe_allow_html=True)
st.markdown("Apply for loans, track applications, and view repayment status.")

tab1, tab2 = st.tabs(["📝 Apply for Loan", "📋 My Loans"])

with tab1:
    with st.form("loan_form"):
        col1, col2 = st.columns(2)
        with col1:
            loan_amount = st.number_input("Loan Amount (₦)", min_value=10000, value=50000, step=10000)
            crop = st.selectbox("Crop to Finance", ["Maize", "Rice", "Beans", "Tomato", "Pepper", "Cabbage"])
        with col2:
            farm_location = st.text_input("Farm Location (LGA/State)")
            purpose = st.text_area("Purpose of Loan")
        if st.form_submit_button("Submit Application"):
            if farm_location and purpose:
                supabase.table("loan_applications").insert({
                    "user_id": st.session_state.user.id,
                    "loan_amount": loan_amount,
                    "crop": crop,
                    "farm_location": farm_location,
                    "purpose": purpose,
                    "status": "pending",
                    "created_at": "now()"
                }).execute()
                st.success("Loan application submitted!")
                st.rerun()
            else:
                st.error("Farm location and purpose are required.")

with tab2:
    res = supabase.table("loan_applications").select("*").eq("user_id", st.session_state.user.id).order("created_at", desc=True).execute()
    loans = res.data if res.data else []
    if loans:
        df = pd.DataFrame(loans)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No loan applications yet.")
