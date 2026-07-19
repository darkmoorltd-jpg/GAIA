
import streamlit as st
import requests
from datetime import datetime, date, timedelta
import numpy as np
import json
import os

# ---------- Optional geolocation imports ----------
try:
    from streamlit_folium import st_folium
    import folium
    FOLIUM_AVAILABLE = True
except:
    FOLIUM_AVAILABLE = False

# ---------- Page config ----------
st.set_page_config(page_title="GAIA – Early Warning", page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")

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

# ---------- Nigeria administrative data ----------
NIGERIA_DATA = {
    "Abia": ["Aba North", "Aba South", "Arochukwu", "Bende", "Ikwuano", "Isiala Ngwa North", "Isiala Ngwa South", "Isuikwuato", "Obi Ngwa", "Ohafia", "Osisioma", "Ugwunagbo", "Ukwa East", "Ukwa West", "Umuahia North", "Umuahia South", "Umu Nneochi"],
    "Adamawa": ["Demsa", "Fufure", "Ganye", "Gayuk", "Gombi", "Grie", "Hong", "Jada", "Lamurde", "Madagali", "Maiha", "Mayo Belwa", "Michika", "Mubi North", "Mubi South", "Numan", "Shelleng", "Song", "Toungo", "Yola North", "Yola South"],
    "FCT": ["Abaji", "Bwari", "Gwagwalada", "Kuje", "Kwali", "Municipal Area Council"],
    "Lagos": ["Agege", "Ajeromi-Ifelodun", "Alimosho", "Amuwo-Odofin", "Apapa", "Badagry", "Epe", "Eti Osa", "Ibeju-Lekki", "Ifako-Ijaiye", "Ikeja", "Ikorodu", "Kosofe", "Lagos Island", "Lagos Mainland", "Mushin", "Ojo", "Oshodi-Isolo", "Shomolu", "Surulere"],
    "Kano": ["Ajingi", "Albasu", "Bagwai", "Bebeji", "Bichi", "Bunkure", "Dala", "Dambatta", "Dawakin Kudu", "Dawakin Tofa", "Doguwa", "Fagge", "Gabasawa", "Garko", "Garun Mallam", "Gaya", "Gezawa", "Gwale", "Gwarzo", "Kabo", "Kano Municipal", "Karaye", "Kibiya", "Kiru", "Kumbotso", "Kunchi", "Kura", "Madobi", "Makoda", "Minjibir", "Nasarawa", "Rano", "Rimin Gado", "Rogo", "Shanono", "Sumaila", "Takai", "Tarauni", "Tofa", "Tsanyawa", "Tudun Wada", "Ungogo", "Warawa", "Wudil"]
}
COUNTRIES = ["Nigeria"]
STATES = list(NIGERIA_DATA.keys())

# ---------- Enhanced weather API ----------
def fetch_precision_weather(lat, lon):
    """Fetch 14-day forecast with leaf wetness, soil moisture, solar radiation."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "daily": [
            "temperature_2m_max", "temperature_2m_min",
            "relative_humidity_2m_max", "relative_humidity_2m_min",
            "precipitation_sum", "precipitation_hours",
            "shortwave_radiation_sum",
            "wind_speed_10m_max",
            "soil_temperature_0cm",
            "soil_moisture_0_to_10cm"
        ],
        "hourly": ["leaf_wetness_probability"],
        "forecast_days": 14,
        "past_days": 3,
        "timezone": "auto",
        "models": "best_match"
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if "hourly" in data:
                daily = data["daily"]
                lw = data["hourly"]["leaf_wetness_probability"]
                daily["leaf_wetness_hours"] = []
                for day_start in range(0, len(lw), 24):
                    day_vals = lw[day_start:day_start+24]
                    wet_hours = sum(1 for v in day_vals if v and v > 50)
                    daily["leaf_wetness_hours"].append(wet_hours)
            return data
    except:
        pass
    return None

# ---------- Complete crop-disease encyclopedia ----------
CROP_DISEASE_MAP = {
    "maize": [
        {"name": "Northern Leaf Blight", "temp_min": 18, "temp_max": 27, "humidity_min": 80, "leaf_wetness_hours": 10, "rainfall_weekly": 30},
        {"name": "Common Rust", "temp_min": 15, "temp_max": 25, "humidity_min": 90, "leaf_wetness_hours": 8, "rainfall_weekly": 15},
        {"name": "Gray Leaf Spot", "temp_min": 22, "temp_max": 30, "humidity_min": 85, "leaf_wetness_hours": 12, "rainfall_weekly": 35},
    ],
    "rice": [
        {"name": "Rice Blast", "temp_min": 20, "temp_max": 30, "humidity_min": 85, "leaf_wetness_hours": 10, "rainfall_weekly": 20},
        {"name": "Brown Spot", "temp_min": 25, "temp_max": 35, "humidity_min": 80, "leaf_wetness_hours": 8, "rainfall_weekly": 10},
        {"name": "Bacterial Leaf Blight", "temp_min": 25, "temp_max": 34, "humidity_min": 70, "leaf_wetness_hours": 0, "rainfall_weekly": 40},
    ],
    "wheat": [
        {"name": "Yellow Rust", "temp_min": 10, "temp_max": 20, "humidity_min": 80, "leaf_wetness_hours": 8, "rainfall_weekly": 10},
        {"name": "Septoria Tritici Blotch", "temp_min": 15, "temp_max": 25, "humidity_min": 85, "leaf_wetness_hours": 12, "rainfall_weekly": 20},
    ],
    "beans": [
        {"name": "Angular Leaf Spot", "temp_min": 20, "temp_max": 28, "humidity_min": 85, "leaf_wetness_hours": 10, "rainfall_weekly": 20},
        {"name": "Bean Rust", "temp_min": 15, "temp_max": 25, "humidity_min": 90, "leaf_wetness_hours": 8, "rainfall_weekly": 15},
    ],
    "potato": [
        {"name": "Late Blight", "temp_min": 10, "temp_max": 24, "humidity_min": 90, "leaf_wetness_hours": 12, "rainfall_weekly": 30},
        {"name": "Early Blight", "temp_min": 20, "temp_max": 30, "humidity_min": 70, "leaf_wetness_hours": 6, "rainfall_weekly": 10},
    ],
    "tomato": [
        {"name": "Late Blight", "temp_min": 10, "temp_max": 24, "humidity_min": 90, "leaf_wetness_hours": 12, "rainfall_weekly": 30},
        {"name": "Early Blight", "temp_min": 20, "temp_max": 30, "humidity_min": 70, "leaf_wetness_hours": 6, "rainfall_weekly": 10},
        {"name": "Bacterial Spot", "temp_min": 24, "temp_max": 30, "humidity_min": 80, "leaf_wetness_hours": 8, "rainfall_weekly": 20},
    ],
    "banana": [
        {"name": "Black Sigatoka", "temp_min": 22, "temp_max": 30, "humidity_min": 85, "leaf_wetness_hours": 12, "rainfall_weekly": 25},
        {"name": "Fusarium Wilt", "temp_min": 25, "temp_max": 35, "humidity_min": 75, "leaf_wetness_hours": 4, "rainfall_weekly": 15},
    ],
    "cassava": [
        {"name": "Cassava Mosaic Disease", "temp_min": 25, "temp_max": 35, "humidity_min": 60, "leaf_wetness_hours": 0, "rainfall_weekly": 20},
        {"name": "Cassava Bacterial Blight", "temp_min": 25, "temp_max": 35, "humidity_min": 80, "leaf_wetness_hours": 8, "rainfall_weekly": 30},
    ],
    "coffee": [
        {"name": "Coffee Leaf Rust", "temp_min": 15, "temp_max": 28, "humidity_min": 80, "leaf_wetness_hours": 10, "rainfall_weekly": 25},
    ],
    "sorghum": [
        {"name": "Anthracnose", "temp_min": 22, "temp_max": 30, "humidity_min": 85, "leaf_wetness_hours": 10, "rainfall_weekly": 25},
    ],
    "groundnut": [
        {"name": "Early Leaf Spot", "temp_min": 20, "temp_max": 30, "humidity_min": 85, "leaf_wetness_hours": 10, "rainfall_weekly": 20},
    ],
}

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

def calculate_precision_risk(weather_data, crop, growth_stage):
    if not weather_data or "daily" not in weather_data:
        return []
    daily = weather_data["daily"]
    diseases = CROP_DISEASE_MAP.get(crop, [])
    if not diseases:
        return []
    forecast_days = len(daily["time"])
    risks = []
    for day_idx in range(forecast_days):
        day_risks = []
        for disease in diseases:
            score = 0
            t_max = daily["temperature_2m_max"][day_idx]
            t_min = daily["temperature_2m_min"][day_idx]
            if disease["temp_min"] <= t_max <= disease["temp_max"]:
                score += 25
            if disease["temp_min"] <= t_min <= disease["temp_max"]:
                score += 15
            humidity = max(daily.get("relative_humidity_2m_max", [0]*forecast_days)[day_idx],
                          daily.get("relative_humidity_2m_min", [0]*forecast_days)[day_idx])
            if humidity >= disease["humidity_min"]:
                score += 30
            lw_hours = daily.get("leaf_wetness_hours", [0]*forecast_days)[day_idx]
            if lw_hours >= disease.get("leaf_wetness_hours", 6):
                score += 20
            rainfall = sum(daily.get("precipitation_sum", [0]*forecast_days)[max(0,day_idx-6):day_idx+1])
            if rainfall >= disease.get("rainfall_weekly", 20):
                score += 10
            if growth_stage in ["Seedling", "Vegetative"]:
                score = min(100, score + 10)
            day_risks.append({"disease": disease["name"], "risk": min(100, score), "date": daily["time"][day_idx]})
        risks.append(day_risks)
    return risks

# ---------- Main UI ----------
st.markdown('<div class="title">🛰️ EARLY WARNING SYSTEM</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Precision disease alerts based on your exact farm location</div>', unsafe_allow_html=True)

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in to use the Early Warning System.")
    st.stop()

# ---------- Location selection ----------
st.subheader("📍 Pinpoint Your Farm")
col1, col2, col3 = st.columns(3)
with col1:
    country = st.selectbox("Country", COUNTRIES, index=0)
with col2:
    state = st.selectbox("State", [""] + STATES)
with col3:
    lgas = NIGERIA_DATA.get(state, []) if state else []
    lga = st.selectbox("LGA", [""] + lgas)

# ---------- Interactive map ----------
lat, lon = 9.082, 8.675
if FOLIUM_AVAILABLE:
    st.write("**Click on the map to mark your exact farm location**")
    m = folium.Map(location=[lat, lon], zoom_start=6)
    m.add_child(folium.LatLngPopup())
    map_data = st_folium(m, width=700, height=400)
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.success(f"Selected coordinates: {lat:.4f}, {lon:.4f}")
else:
    lat = st.number_input("Latitude", value=lat)
    lon = st.number_input("Longitude", value=lon)

# ---------- Crop & planting date ----------
col1, col2 = st.columns(2)
with col1:
    crop = st.selectbox("Current Crop", list(CROP_DISEASE_MAP.keys()))
with col2:
    planting_date = st.date_input("Planting Date", max_value=date.today())

if st.button("🔍 Get Disease Risk Forecast"):
    weather = fetch_precision_weather(lat, lon)
    growth_stage = get_growth_stage(planting_date.strftime("%Y-%m-%d") if planting_date else "")
    
    if weather:
        risks = calculate_precision_risk(weather, crop, growth_stage)
        st.success(f"Forecast for coordinates ({lat:.4f}, {lon:.4f})")
        
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
        st.error("Unable to fetch weather data. Please check your coordinates.")
