
import streamlit as st
import requests
from datetime import datetime, date, timedelta
import numpy as np

st.set_page_config(page_title="GAIA – Early Warning", page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")

# ---------- Theme ----------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
    section[data-testid="stSidebar"] { display: block !important; }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=st.session_state.theme == "dark", key="ew_theme_toggle")
st.session_state.theme = "dark" if dark_mode else "light"
theme = st.session_state.theme

# ---------- CSS ----------
if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(145deg, #0a0a0a 0%, #1a1a2e 50%, #0d0d0d 100%); color: #e0e0e0; }
        header, footer {visibility: hidden;}
        .title { font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #00c853, #69f0ae, #00c853); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 30px rgba(0,200,83,0.6); margin-bottom: 0.5rem; animation: glow 2s ease-in-out infinite alternate; }
        @keyframes glow { from { text-shadow: 0 0 20px rgba(0,200,83,0.6); } to { text-shadow: 0 0 40px rgba(0,200,83,1), 0 0 80px rgba(0,200,83,0.8); } }
        .subtitle { text-align: center; font-size: 1.2rem; color: #90a4ae; margin-bottom: 2rem; }
        .farm-card { background: rgba(0,0,0,0.6); backdrop-filter: blur(20px); border: 1px solid rgba(0,200,83,0.2); border-radius: 20px; padding: 1.5rem; margin: 1rem 0; }
        .risk-card { background: rgba(0,0,0,0.6); backdrop-filter: blur(20px); border-radius: 20px; padding: 1.5rem; margin: 0.5rem 0; display: flex; align-items: center; justify-content: space-between; }
        .risk-low { border: 2px solid #00c853; box-shadow: 0 0 20px rgba(0,200,83,0.3); }
        .risk-moderate { border: 2px solid #ff9800; box-shadow: 0 0 20px rgba(255,152,0,0.3); }
        .risk-high { border: 2px solid #ff1744; box-shadow: 0 0 30px rgba(255,23,68,0.5); animation: pulse 1.5s ease-in-out infinite; }
        @keyframes pulse { 0%, 100% { box-shadow: 0 0 30px rgba(255,23,68,0.5); } 50% { box-shadow: 0 0 60px rgba(255,23,68,0.8); } }
        .risk-label { font-weight: 700; font-size: 1.2rem; }
        .risk-label.low { color: #00c853; }
        .risk-label.moderate { color: #ff9800; }
        .risk-label.high { color: #ff1744; }
        .action-btn { padding: 12px 25px; border-radius: 30px; font-weight: 600; text-decoration: none; display: inline-block; margin-top: 0.5rem; }
        .action-btn.green { background: #00c853; color: #000; }
        .action-btn.orange { background: #ff9800; color: #000; }
        .action-btn.red { background: #ff1744; color: #fff; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); color: #1b5e20; }
        header, footer {visibility: hidden;}
        .title { font-size: 3rem; font-weight: 900; text-align: center; color: #2e7d32; }
        .subtitle { text-align: center; font-size: 1.2rem; color: #33691e; margin-bottom: 2rem; }
        .farm-card { background: rgba(255,255,255,0.9); border-radius: 20px; padding: 1.5rem; margin: 1rem 0; }
        .risk-card { background: rgba(255,255,255,0.9); border-radius: 20px; padding: 1.5rem; margin: 0.5rem 0; display: flex; align-items: center; justify-content: space-between; }
        .risk-low { border: 2px solid #4caf50; }
        .risk-moderate { border: 2px solid #ff9800; }
        .risk-high { border: 2px solid #f44336; }
        .risk-label { font-weight: 700; font-size: 1.2rem; }
        .risk-label.low { color: #4caf50; }
        .risk-label.moderate { color: #ff9800; }
        .risk-label.high { color: #f44336; }
        .action-btn { padding: 12px 25px; border-radius: 30px; font-weight: 600; text-decoration: none; display: inline-block; margin-top: 0.5rem; }
        .action-btn.green { background: #4caf50; color: #fff; }
        .action-btn.orange { background: #ff9800; color: #000; }
        .action-btn.red { background: #f44336; color: #fff; }
    </style>
    """, unsafe_allow_html=True)

# ---------- Helper functions ----------
def fetch_weather_forecast(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "relative_humidity_2m_max", "relative_humidity_2m_min"],
        "forecast_days": 7, "timezone": "Africa/Lagos"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def get_growth_stage(planting_date_str):
    if not planting_date_str:
        return "Unknown"
    try:
        planting = datetime.strptime(planting_date_str, "%Y-%m-%d")
        days_since = (datetime.now() - planting).days
        if days_since < 0: return "Not planted yet"
        elif days_since <= 21: return "Seedling"
        elif days_since <= 50: return "Vegetative"
        elif days_since <= 80: return "Flowering"
        elif days_since <= 120: return "Grain-fill / Maturity"
        else: return "Harvest-ready"
    except:
        return "Unknown"

def calculate_risk(weather_data, crop, growth_stage):
    if not weather_data or "daily" not in weather_data:
        return []
    daily = weather_data["daily"]
    dates = daily["time"]
    risks = []
    disease_map = {
        "maize": [
            {"name": "Northern Leaf Blight", "temp_range": (18, 27), "humidity_min": 80, "rainfall_min": 5},
            {"name": "Common Rust", "temp_range": (15, 25), "humidity_min": 90, "rainfall_min": 2},
        ],
        "rice": [
            {"name": "Rice Blast", "temp_range": (20, 30), "humidity_min": 85, "rainfall_min": 3},
            {"name": "Brown Spot", "temp_range": (25, 35), "humidity_min": 80, "rainfall_min": 0},
        ],
        "beans": [
            {"name": "Angular Leaf Spot", "temp_range": (20, 28), "humidity_min": 85, "rainfall_min": 2},
        ],
        "potato": [
            {"name": "Late Blight", "temp_range": (10, 24), "humidity_min": 90, "rainfall_min": 5},
            {"name": "Early Blight", "temp_range": (20, 30), "humidity_min": 70, "rainfall_min": 0},
        ],
        "wheat": [
            {"name": "Yellow Rust", "temp_range": (10, 20), "humidity_min": 80, "rainfall_min": 1},
        ],
        "banana": [
            {"name": "Fusarium Wilt", "temp_range": (25, 35), "humidity_min": 75, "rainfall_min": 0},
        ],
        "tomato": [
            {"name": "Late Blight", "temp_range": (10, 24), "humidity_min": 90, "rainfall_min": 5},
            {"name": "Early Blight", "temp_range": (20, 30), "humidity_min": 70, "rainfall_min": 0},
        ]
    }
    if crop not in disease_map:
        return []
    diseases = disease_map[crop]
    for i, date_str in enumerate(dates):
        day_risks = []
        for disease in diseases:
            temp_max = daily["temperature_2m_max"][i]
            temp_min = daily["temperature_2m_min"][i]
            humidity = max(daily["relative_humidity_2m_max"][i], daily["relative_humidity_2m_min"][i])
            rainfall = daily["precipitation_sum"][i]
            risk_score = 0
            if disease["temp_range"][0] <= temp_max <= disease["temp_range"][1]:
                risk_score += 30
            if disease["temp_range"][0] <= temp_min <= disease["temp_range"][1]:
                risk_score += 20
            if humidity >= disease["humidity_min"]:
                risk_score += 35
            if rainfall >= disease["rainfall_min"]:
                risk_score += 15
            if growth_stage in ["Seedling", "Vegetative"]:
                risk_score = min(100, risk_score + 10)
            day_risks.append({"disease": disease["name"], "risk": min(100, risk_score), "date": date_str})
        risks.append(day_risks)
    return risks

# ---------- Main UI ----------
st.markdown('<div class="title">🛰️ EARLY WARNING SYSTEM</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Predictive disease alerts based on weather, crop stage, and regional data</div>', unsafe_allow_html=True)

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in to use the Early Warning System.")
    st.stop()

user_id = st.session_state.user.id

from supabase import create_client, Client
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_service_client():
    SERVICE_KEY = st.secrets["supabase"]["service_key"]
    return create_client(SUPABASE_URL, SERVICE_KEY)

supabase = get_supabase()
service_client = get_service_client()
res = service_client.table("user_profiles").select("*").eq("user_id", user_id).execute()
profile = res.data[0] if res.data else {}

with st.expander("🌍 Farm Settings", expanded=not profile.get("farm_location")):
    with st.form("farm_settings"):
        col1, col2 = st.columns(2)
        with col1:
            farm_location = st.text_input("Farm Location (City)", value=profile.get("farm_location", ""), placeholder="e.g., Gwagwalada, Abuja")
        with col2:
            crop = st.selectbox("Current Crop", ["maize", "rice", "beans", "potato", "wheat", "banana", "tomato"])
        planting_date = st.date_input("Planting Date", 
                                      value=datetime.strptime(profile.get("planting_date", ""), "%Y-%m-%d") if profile.get("planting_date") else None,
                                      max_value=date.today())
        if st.form_submit_button("Save Settings"):
            try:
                service_client.table("user_profiles").upsert({
                    "user_id": user_id,
                    "farm_location": farm_location.strip(),
                    "planting_date": planting_date.strftime("%Y-%m-%d") if planting_date else None
                }).execute()
                st.success("Farm settings saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Could not save: {e}")

if profile.get("farm_location"):
    lat, lon = 9.05785, 7.49508  # Default: Abuja
    city_coords = {
        "abuja": (9.05785, 7.49508), "lagos": (6.5244, 3.3792), "kano": (12.0, 8.5167),
        "ibadan": (7.3775, 3.9470), "kaduna": (10.5264, 7.4388), "port harcourt": (4.8156, 7.0498),
        "gwagwalada": (8.9333, 7.0833), "accra": (5.6037, -0.1870), "nairobi": (-1.2921, 36.8219),
        "london": (51.5074, -0.1278),
    }
    for city, coords in city_coords.items():
        if city in profile["farm_location"].lower():
            lat, lon = coords
            break

    weather = fetch_weather_forecast(lat, lon)
    growth_stage = get_growth_stage(profile.get("planting_date", ""))

    st.markdown(f"""
    <div class="farm-card">
        <h3>📍 {profile['farm_location']}</h3>
        <p>🌾 Crop: <b>{crop.title()}</b> | 🌱 Stage: <b>{growth_stage}</b></p>
        <p>📅 Planted: {profile.get('planting_date', 'Not set')}</p>
    </div>
    """, unsafe_allow_html=True)

    if weather:
        risks = calculate_risk(weather, crop, growth_stage)
        if risks and any(any(r["risk"] > 0 for r in day) for day in risks):
            st.markdown("### 📊 7‑Day Disease Risk Forecast")
            for day_idx, day_risks in enumerate(risks):
                if not day_risks:
                    continue
                date_str = weather["daily"]["time"][day_idx]
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                day_name = date_obj.strftime("%a %d %b")
                for risk_data in day_risks:
                    risk = risk_data["risk"]
                    if risk < 30:
                        card_class, label_class, badge, action_text, action_class = "risk-low", "low", "🟢 LOW", "Monitor conditions", "green"
                    elif risk < 60:
                        card_class, label_class, badge, action_text, action_class = "risk-moderate", "moderate", "🟡 MODERATE", "Prepare preventive spray", "orange"
                    else:
                        card_class, label_class, badge, action_text, action_class = "risk-high", "high", "🔴 HIGH", "Apply treatment NOW", "red"
                    st.markdown(f"""
                    <div class="risk-card {card_class}">
                        <div>
                            <strong>{risk_data['disease']}</strong> — {day_name}
                            <p style="margin:0;color:#78909c;">Temp: {weather['daily']['temperature_2m_min'][day_idx]}°C – {weather['daily']['temperature_2m_max'][day_idx]}°C | Humidity: {max(weather['daily']['relative_humidity_2m_max'][day_idx], weather['daily']['relative_humidity_2m_min'][day_idx])}% | Rain: {weather['daily']['precipitation_sum'][day_idx]}mm</p>
                        </div>
                        <div style="text-align:right;">
                            <div class="risk-label {label_class}">{badge} — {risk}%</div>
                            <span class="action-btn {action_class}">{action_text}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No significant disease risk detected for the next 7 days.")
    else:
        st.warning("Unable to fetch weather data. Check your farm location.")
else:
    st.info("👆 Set your farm location and crop above to see disease risk predictions.")
