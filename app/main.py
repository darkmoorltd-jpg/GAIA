
import streamlit as st
from app.utils.auth import sign_up, sign_in, sign_in_with_google, sign_out, reset_password, get_current_user

st.set_page_config(page_title="GAIA", page_icon="🌱", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.session_state.user = get_current_user()

if st.session_state.user is None:
    st.title("🌱 GAIA – Sign In / Create Account")
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Sign Up", "🅶 Google"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Login"):
                    user, error = sign_in(email, password)
                    if error:
                        st.error(f"Login failed: {error}")
                    else:
                        st.session_state.user = user
                        st.rerun()
            with col2:
                if st.form_submit_button("Forgot Password?"):
                    if email:
                        err = reset_password(email)
                        if err:
                            st.error(err)
                        else:
                            st.success("Password reset email sent (if email is registered).")
                    else:
                        st.warning("Enter your email first.")

    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email")
            new_password = st.text_input("Password (min 6 characters)", type="password")
            if st.form_submit_button("Create Account"):
                if len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    user, error = sign_up(new_email, new_password)
                    if error:
                        st.error(f"Sign up failed: {error}")
                    else:
                        st.session_state.user = user
                        st.success("Account created! You are now logged in.")
                        st.rerun()

    with tab3:
        st.write("Sign in instantly with your Google account (no rate limits).")
        if st.button("Sign in with Google"):
            url, error = sign_in_with_google()
            if error:
                st.error(f"Google sign‑in failed: {error}")
            else:
                st.markdown(f'<meta http-equiv="refresh" content="0; url={url}">', unsafe_allow_html=True)
                st.stop()

    st.stop()

st.sidebar.write(f"👤 {st.session_state.user.email}")
if st.sidebar.button("Logout"):
    sign_out()
    st.session_state.user = None
    st.rerun()

dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard", icon="🏠")
crops_page     = st.Page("pages/2_Crops.py", title="Crop Disease", icon="🌿")
pests_page     = st.Page("pages/3_Pests.py", title="Pest Detection", icon="🐛")
soil_page      = st.Page("pages/4_Soil.py", title="Soil Analysis", icon="🏞️")
livestock_page = st.Page("pages/5_Livestock.py", title="Livestock Health", icon="🐄")

pg = st.navigation({
    "GAIA": [dashboard_page],
    "Diagnose": [crops_page, pests_page, soil_page, livestock_page],
})
pg.run()
