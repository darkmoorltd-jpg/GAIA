import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

st.set_page_config(page_title="Loan Management", page_icon="🏦", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.warning("Please log in first.")
    st.stop()

supabase = create_client(
    st.secrets["supabase"]["url"],
    st.secrets["supabase"]["service_key"])

st.markdown(
    "<h1 style='color:#2e7d32;'>🏦 Loan Management</h1>",
    unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 Apply", "📋 Applications", "💵 Repayments"])

with tab1:
    with st.form("loan_form"):
        col1, col2 = st.columns(2)
        with col1:
            loan_amount = st.number_input(
                "Loan Amount (₦)", min_value=10000, value=50000, step=10000)
            crop = st.selectbox(
                "Crop to Finance", [
                    "Maize", "Rice", "Beans", "Tomato", "Pepper", "Cabbage"])
            duration = st.number_input(
                "Duration (months)", min_value=3, max_value=24, value=6)
        with col2:
            farm_location = st.text_input("Farm Location (LGA/State)")
            purpose = st.text_area("Purpose of Loan")
            interest_rate = st.number_input(
                "Interest Rate (% annual)",
                min_value=0.0,
                max_value=30.0,
                value=12.0)
        if st.form_submit_button("Submit Application"):
            if farm_location and purpose:
                supabase.table("loan_applications").insert({
                    "user_id": st.session_state.user.id,
                    "loan_amount": loan_amount,
                    "crop": crop,
                    "farm_location": farm_location,
                    "purpose": purpose,
                    "duration_months": duration,
                    "interest_rate": interest_rate,
                    "status": "pending",
                    "due_date": (datetime.datetime.now() + datetime.timedelta(days=30 * duration)).isoformat(),
                    "outstanding_balance": loan_amount,
                    "created_at": "now()"
                }).execute()
                st.success("Loan application submitted!")
                st.rerun()
            else:
                st.error("Farm location and purpose are required.")

with tab2:
    res = supabase.table("loan_applications").select(
        "*").order("created_at", desc=True).execute()
    loans = res.data if res.data else []
    if loans:
        df = pd.DataFrame(loans)
        # Summary
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Applications", len(df))
        col2.metric("Approved", len(df[df["status"] == "approved"]))
        col3.metric("Pending", len(df[df["status"] == "pending"]))
        total_disbursed = df[df["status"] ==
                             "approved"]["loan_amount"].astype(float).sum()
        col4.metric("Total Disbursed (₦)", f"{total_disbursed:,.0f}")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No loan applications yet.")

with tab3:
    repayments_res = supabase.table("loan_repayments").select(
        "*").order("paid_at", desc=True).execute()
    repayments = repayments_res.data if repayments_res.data else []
    if repayments:
        df_rep = pd.DataFrame(repayments)
        st.dataframe(df_rep, use_container_width=True)
    else:
        st.info("No repayments recorded yet.")
