import streamlit as st
from supabase import create_client, Client


def get_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["service_key"]
    return create_client(url, key)


def deduct_scans(user_id, amount, feature_name):
    """Deduct scans and show a small clean box."""
    supabase = get_supabase()

    # Ensure row exists
    try:
        supabase.table("user_scans").insert(
            {"user_id": user_id, "scans_remaining": 30, "plan": "free"}
        ).execute()
    except BaseException:
        pass

    # Fetch current
    res = (
        supabase.table("user_scans")
        .select("scans_remaining")
        .eq("user_id", user_id)
        .execute()
    )
    current = res.data[0]["scans_remaining"] if res.data else 30

    if current < amount:
        st.error(f"⚠️ Not enough scans! Need {amount}, have {current}.")
        return False, current

    new_total = current - amount
    supabase.table("user_scans").update({"scans_remaining": new_total}).eq(
        "user_id", user_id
    ).execute()

    # Small rectangular box — like Buy Scans counter but smaller
    st.markdown(
        f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 8px;
        background: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 6px 12px;
        margin: 4px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        width: fit-content;
    ">
        <span style="font-size: 0.85rem; color: #666;">📉</span>
        <span style="font-size: 0.85rem; font-weight: 600; color: #2e7d32;">{new_total}</span>
        <span style="font-size: 0.75rem; color: #999;">scans left</span>
        <span style="font-size: 0.7rem; color: #bbb; margin-left: 4px;">(-{amount} {feature_name})</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    return True, new_total
