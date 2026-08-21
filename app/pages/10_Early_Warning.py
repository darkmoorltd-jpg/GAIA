import os
import json
import numpy as np
from datetime import datetime, date, timedelta
import streamlit as st
# Allow demo mode
from supabase import create_client

user = st.session_state.get("user", None)
if user is None:
    st.warning("Please log in first.")
    st.stop()
supabase = create_client(
    st.secrets["supabase"]["url"],
    st.secrets["supabase"]["key"])
try:
    session = supabase.auth.get_session()
    user = session.user if session else None
except BaseException:
    import requests

try:
    from streamlit_folium import st_folium
    import folium
    FOLIUM_AVAILABLE = True
except BaseException:
    FOLIUM_AVAILABLE = False

st.set_page_config(
    page_title="GAIA – Early Warning",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); color: #1b5e20; }
    header, footer { visibility: hidden; }
    .title { font-size: 3rem; font-weight: 900; text-align: center; color: #2e7d32; }
    .subtitle { text-align: center; font-size: 1.2rem; color: #33691e; margin-bottom: 2rem; }
    .risk-card { background: rgba(255,255,255,0.9); border-radius: 20px; padding: 1.5rem; margin: 0.5rem 0; }
    .risk-low { border: 2px solid #4caf50; }
    .risk-moderate { border: 2px solid #ff9800; }
    .risk-high { border: 2px solid #f44336; }
    .risk-label { font-weight: 700; font-size: 1.2rem; }
    .risk-label.low { color: #4caf50; }
    .risk-label.moderate { color: #ff9800; }
    .risk-label.high { color: #f44336; }
</style>
""", unsafe_allow_html=True)

NIGERIA_DATA = {
    "Lagos": ["Agege", "Alimosho", "Ikeja", "Surulere", "Eti Osa"],
    "Kano": ["Dala", "Fagge", "Gwale", "Kano Municipal", "Nassarawa", "Tarauni"],
    "Kaduna": ["Kaduna North", "Kaduna South", "Zaria", "Kafanchan"],
    "FCT": ["Abaji", "Bwari", "Gwagwalada", "Kuje", "Kwali"],
    "Oyo": ["Ibadan North", "Ibadan South", "Ogbomoso", "Oyo"],
    "Rivers": ["Port Harcourt", "Obio-Akpor", "Eleme"],
    "Benue": ["Makurdi", "Gboko", "Otukpo"],
    "Plateau": ["Jos North", "Jos South", "Barkin Ladi"],
}

STATES = list(NIGERIA_DATA.keys())

CROP_DISEASE_MAP = {
    "maize": [
        {"name": "Northern Leaf Blight", "temp_min": 18, "temp_max": 27, "humidity_min": 80},
        {"name": "Common Rust", "temp_min": 15, "temp_max": 25, "humidity_min": 90},
    ],
    "rice": [
        {"name": "Rice Blast", "temp_min": 20, "temp_max": 30, "humidity_min": 85},
        {"name": "Brown Spot", "temp_min": 25, "temp_max": 35, "humidity_min": 80},
    ],
    "wheat": [
        {"name": "Yellow Rust", "temp_min": 10, "temp_max": 20, "humidity_min": 80},
    ],
    "beans": [
        {"name": "Angular Leaf Spot", "temp_min": 20, "temp_max": 28, "humidity_min": 85},
    ],
    "tomato": [
        {"name": "Late Blight", "temp_min": 10, "temp_max": 24, "humidity_min": 90},
        {"name": "Early Blight", "temp_min": 20, "temp_max": 30, "humidity_min": 70},
    ],
    "cassava": [
        {"name": "Cassava Mosaic Disease", "temp_min": 25, "temp_max": 35, "humidity_min": 60},
    ],
}


def fetch_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "relative_humidity_2m_max",
            "precipitation_sum"],
        "forecast_days": 14,
        "timezone": "auto"}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            return r.json(), None
        return None, "HTTP " + str(r.status_code)
    except Exception as e:
        return None, str(e)


def calculate_risk(weather_data, crop):
    if not weather_data or "daily" not in weather_data:
        return []
    daily = weather_data["daily"]
    diseases = CROP_DISEASE_MAP.get(crop, [])
    if not diseases:
        return []
    risks = []
    for day_idx in range(min(7, len(daily["time"]))):
        for disease in diseases:
            score = 0
            t_max = daily["temperature_2m_max"][day_idx]
            t_min = daily["temperature_2m_min"][day_idx]
            humidity = daily["relative_humidity_2m_max"][day_idx]
            if disease["temp_min"] <= t_max <= disease["temp_max"]:
                score += 40
            if disease["humidity_min"] <= humidity:
                score += 40
            if daily["precipitation_sum"][day_idx] > 0:
                score += 20
            risk_level = "low" if score < 50 else (
                "moderate" if score < 75 else "high")
            risks.append({
                "disease": disease["name"],
                "score": score,
                "level": risk_level,
                "date": daily["time"][day_idx]
            })
    return risks


st.markdown(
    '<div class="title">🛰️ Early Warning System</div>',
    unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Weather-based disease risk alerts for your farm</div>',
    unsafe_allow_html=True)

st.markdown("### 📍 Your Farm Location")
col1, col2 = st.columns(2)
with col1:
    state = st.selectbox("State", STATES)
with col2:
    lga = st.selectbox("LGA", NIGERIA_DATA.get(state, ["--"]))

st.markdown("### 🌾 Select Crop")
crop = st.selectbox("Crop", list(CROP_DISEASE_MAP.keys()))

st.markdown("### 📅 Planting Date")
planting_date = st.date_input(
    "When did you plant?",
    value=date.today() -
    timedelta(
        days=30))

if st.button("🔍 Check Disease Risk", type="primary", use_container_width=True):
    state_coords = {
        "Lagos": (6.5244, 3.3792),
        "Kano": (12.0022, 8.5920),
        "Kaduna": (10.5105, 7.4165),
        "FCT": (9.0765, 7.3986),
        "Oyo": (7.3775, 3.9470),
        "Rivers": (4.8156, 7.0498),
        "Benue": (7.7275, 8.5391),
        "Plateau": (9.8965, 8.8583),
    }
    lat, lon = state_coords.get(state, (9.0765, 7.3986))

    with st.spinner("📡 Fetching weather data..."):
        weather, err = fetch_weather(lat, lon)

    if err:
        st.error("Failed to fetch weather: " + str(err))
    else:
        risks = calculate_risk(weather, crop)
        st.markdown("---")
        st.markdown("### 📊 Disease Risk Report")

        if not risks:
            st.info("No disease risk data available for this crop.")
        else:
            for risk in risks[:10]:
                level = risk["level"]
                level_emoji = {
                    "low": "🟢",
                    "moderate": "🟡",
                    "high": "🔴"}.get(
                    level,
                    "⚪")
                card_class = "risk-card risk-" + level
                risk_label_class = "risk-label " + level

                st.markdown(
                    '<div class="' + card_class + '">',
                    unsafe_allow_html=True)
                st.markdown(
                    '<span class="' +
                    risk_label_class +
                    '">' +
                    level_emoji +
                    ' ' +
                    risk["disease"] +
                    '</span>',
                    unsafe_allow_html=True)
                st.markdown(
                    '<span style="float: right; color: #888;">' +
                    risk["date"] +
                    '</span>',
                    unsafe_allow_html=True)
                st.markdown(
                    '<p style="margin-top: 8px;">Risk Score: ' +
                    str(
                        risk["score"]) +
                    '%</p>',
                    unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        if "user" in st.session_state and user is not None:
            from app.utils.scan_util import deduct_scans
            deduct_scans(user.id, 1, "Early Warning")

st.markdown("---")
st.caption("Powered by Darkmoor Ltd")

st.markdown("---")
st.markdown("### Quick Navigation")
cols = st.columns(10)
with cols[0]:
    st.page_link("pages/1_Dashboard.py", label="Dashboard")
with cols[1]:
   st.page_link("pages/2_Crops.py", label="Crops")
with cols[2]:
    st.page_link("pages/3_Pests.py", label="Pests")
with cols[3]:
   st.page_link("pages/4_Soil.py", label="Soil")
with cols[4]:
    st.page_link("pages/5_Livestock.py", label="Livestock")
with cols[5]:
   st.page_link("pages/17_Video_Scan.py", label="Video Scan")
with cols[6]:
    st.page_link("pages/19_Satellite.py", label="Satellite")
with cols[7]:
   st.page_link("pages/18_Voice_Agronomist.py", label="Voice AI")
with cols[8]:
    st.page_link("pages/9_Buy_Scans.py", label="Buy Scans")
with cols[9]:
   st.page_link("pages/10_Early_Warning.py", label="Alerts")

st.markdown("### More Features")
cols2 = st.columns(10)
with cols2[0]:
    st.page_link("pages/11_Verify_Farmer.py", label="Verify")
with cols2[1]:
   st.page_link("pages/12_Verification_History.py", label="History")
with cols2[2]:
    st.page_link("pages/14_Wallet.py", label="Wallet")
with cols2[3]:
   st.page_link("pages/15_Badges.py", label="Badges")
with cols2[4]:
    st.page_link("pages/16_Chat.py", label="Chat")
with cols2[5]:
   st.page_link("pages/20_Marketplace.py", label="Market")
with cols2[6]:
    st.page_link("pages/21_Crop_Insurance.py", label="Insurance")
with cols2[7]:
   st.page_link("pages/6_Payment_History.py", label="Payments")
with cols2[8]:
    st.page_link("pages/8_Profile.py", label="Profile")
with cols2[9]:
   st.page_link("pages/13_Help.py", label="Help")
