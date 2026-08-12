
import streamlit as st
import requests
import numpy as np
from datetime import datetime, timedelta
from PIL import Image
import io
import base64

# ===== SENTINEL HUB CREDENTIALS =====
SENTINEL_CLIENT_ID = "86ed44fa-793b-47da-973b-345a83ae18c0"
SENTINEL_CLIENT_SECRET = "qYTQXnQFpgstJSrAulJ6NREflI2m2eCN"
SENTINEL_INSTANCE_ID = "17783119-0066-4563-84ce-8c84fc13a60b"
SENTINEL_TOKEN_URL = "https://services.sentinel-hub.com/oauth/token"
SENTINEL_API_URL = f"https://services.sentinel-hub.com/ogc/wms/{SENTINEL_INSTANCE_ID}"

# ===== CACHED TOKEN =====
@st.cache_data(ttl=3500)
def get_sentinel_token():
    """Get OAuth2 token for Sentinel Hub."""
    try:
        resp = requests.post(SENTINEL_TOKEN_URL, data={
            "grant_type": "client_credentials",
            "client_id": SENTINEL_CLIENT_ID,
            "client_secret": SENTINEL_CLIENT_SECRET
        }, timeout=15)
        if resp.status_code == 200:
            return resp.json()["access_token"], None
        return None, f"Auth failed: {resp.status_code}"
    except Exception as e:
        return None, str(e)

def fetch_sentinel_ndvi(lat, lon, date_str, token):
    """Fetch NDVI image from Sentinel-2 via Sentinel Hub WMS."""
    bbox = f"{lon-0.02},{lat-0.02},{lon+0.02},{lat+0.02}"
    
    params = {
        "SERVICE": "WMS",
        "REQUEST": "GetMap",
        "LAYERS": "NDVI",
        "CRS": "EPSG:4326",
        "BBOX": bbox,
        "WIDTH": 512,
        "HEIGHT": 512,
        "FORMAT": "image/png",
        "TIME": f"{date_str}/{date_str}",
        "SHOWLOGO": "false",
        "TRANSPARENT": "true"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(SENTINEL_API_URL, params=params, headers=headers, timeout=20)
        if resp.status_code == 200:
            img = Image.open(io.BytesIO(resp.content))
            return img, None
        return None, f"API error: {resp.status_code}"
    except Exception as e:
        return None, str(e)

def calculate_ndvi_from_image(img):
    """Extract average NDVI value from the returned image."""
    arr = np.array(img.convert('L'), dtype=np.float64) / 255.0
    return round(float(np.mean(arr)), 3)

def ndvi_to_health(ndvi_value):
    """Convert NDVI to health status."""
    if ndvi_value > 0.6: return "Healthy", "#00c853", "🟢"
    elif ndvi_value > 0.4: return "Moderate", "#ff9800", "🟡"
    elif ndvi_value > 0.2: return "Stressed", "#f44336", "🔴"
    else: return "Critical", "#880000", "⚫"

def get_ndvi_alert(ndvi_trend):
    """Generate alert based on NDVI trend."""
    if len(ndvi_trend) < 2:
        return None
    recent = ndvi_trend[-3:] if len(ndvi_trend) >= 3 else ndvi_trend
    trend = recent[-1] - recent[0]
    if trend < -0.1:
        return {
            "level": "critical",
            "title": "🚨 Crop Health Declining Rapidly",
            "message": f"NDVI dropped by {abs(trend):.2f} in recent weeks. Possible disease, drought, or nutrient deficiency. Immediate action required.",
            "actions": ["Run a crop disease scan", "Check soil moisture", "Apply fertilizer if needed", "Contact extension officer"]
        }
    elif trend < -0.05:
        return {
            "level": "warning",
            "title": "⚠️ Crop Health Declining",
            "message": f"NDVI shows slight decline of {abs(trend):.2f}. Monitor closely.",
            "actions": ["Take new crop photos for diagnosis", "Check weather forecast", "Inspect field for pests"]
        }
    elif trend > 0.05:
        return {
            "level": "info",
            "title": "📈 Crop Health Improving",
            "message": f"NDVI increased by {trend:.2f}. Your crop is recovering well.",
            "actions": ["Continue current practices", "Plan harvest timeline"]
        }
    return None

# ===== PAGE CONFIG =====
st.set_page_config(page_title="GAIA – Satellite Monitor", page_icon="🛰️", layout="wide")

# ===== THEME TOGGLE =====
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=True, key="sat_theme_toggle")
theme = "dark" if dark_mode else "light"

# ===== THEME CSS =====
if theme == "dark":
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .stApp { background: #0a0e14; color: #e8edf2; }
        header, footer { visibility: hidden; }
        .title { font-size: 3rem; font-weight: 800; text-align: center;
                 background: linear-gradient(135deg, #00b4d8, #48cae4, #00b4d8);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 animation: satGlow 2s ease-in-out infinite alternate; }
        @keyframes satGlow { from { text-shadow: 0 0 20px rgba(0,180,216,0.6); }
                             to { text-shadow: 0 0 40px rgba(0,180,216,1), 0 0 80px rgba(0,180,216,0.8); } }
        .subtitle { text-align: center; font-size: 1.1rem; color: #6b8299; margin-bottom: 2rem; }
        .stat-box { background: #111820; border: 1px solid #1e2d3d; border-radius: 16px; padding: 1.5rem; text-align: center; }
        .stat-number { font-size: 2.2rem; font-weight: 700; color: #00b4d8; }
        .stat-label { font-size: 0.85rem; color: #6b8299; margin-top: 4px; }
        .alert-card { background: #1a0f0f; border: 1px solid #ff4444; border-radius: 16px; padding: 1.5rem; margin: 1rem 0; }
        .alert-card.warning { background: #1a1500; border-color: #ff9800; }
        .alert-card.info { background: #0a1a2e; border-color: #00b4d8; }
        .ndvi-bar { height: 12px; border-radius: 6px; margin: 4px 0; }
        .ndvi-high { background: #00c853; }
        .ndvi-medium { background: #ff9800; }
        .ndvi-low { background: #f44336; }
        .map-container { border-radius: 20px; overflow: hidden; border: 2px solid #1e2d3d; margin: 1rem 0; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .stApp { background: #f0f4f8; color: #1a202c; }
        header, footer { visibility: hidden; }
        .title { font-size: 3rem; font-weight: 800; text-align: center;
                 background: linear-gradient(135deg, #0077b6, #48cae4, #0077b6);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; font-size: 1.1rem; color: #64748b; margin-bottom: 2rem; }
        .stat-box { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.5rem; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .stat-number { font-size: 2.2rem; font-weight: 700; color: #0077b6; }
        .stat-label { font-size: 0.85rem; color: #64748b; margin-top: 4px; }
        .alert-card { background: #fff5f5; border: 1px solid #fc8181; border-radius: 16px; padding: 1.5rem; margin: 1rem 0; }
        .alert-card.warning { background: #fffff0; border-color: #f6ad55; }
        .alert-card.info { background: #ebf8ff; border-color: #63b3ed; }
        .map-container { border-radius: 20px; overflow: hidden; border: 2px solid #e2e8f0; margin: 1rem 0; }
    </style>
    """, unsafe_allow_html=True)

# ===== UI =====
st.markdown('<div class="title">🛰️ Satellite Farm Monitor</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Live Sentinel-2 satellite imagery — see your crop health from space every 5 days</div>', unsafe_allow_html=True)

# Location selection
col1, col2 = st.columns(2)
with col1:
    lat = st.number_input("Latitude", value=9.082, format="%.4f")
with col2:
    lon = st.number_input("Longitude", value=8.675, format="%.4f")

if st.button("🛰️ Scan My Farm", type="primary", use_container_width=True):
    with st.spinner("📡 Authenticating with Sentinel Hub..."):
        token, token_err = get_sentinel_token()
    
    if token_err:
        st.error(f"❌ Sentinel Hub authentication failed: {token_err}")
        st.info("Using simulated data instead. Check your credentials in Settings.")
        use_real = False
    else:
        st.success("✅ Connected to ESA Sentinel-2 satellite")
        use_real = True
    
    # Try to fetch real data for multiple dates
    ndvi_values = []
    dates = []
    images = []
    
    for week in range(8):
        date = datetime.now() - timedelta(weeks=8 - week)
        date_str = date.strftime("%Y-%m-%d")
        dates.append(date.strftime("%d %b"))
        
        if use_real:
            img, err = fetch_sentinel_ndvi(lat, lon, date_str, token)
            if img and err is None:
                ndvi = calculate_ndvi_from_image(img)
                ndvi_values.append(ndvi)
                images.append(img)
            else:
                use_real = False
        
        if not use_real:
            # Fallback to simulated data
            if len(ndvi_values) == 0:
                seed = int(abs(lat * 1000 + lon * 1000 + datetime.now().month * 100))
                np.random.seed(seed)
                base_ndvi = 0.65 - abs(lat) * 0.005
                month = datetime.now().month
                seasonal = 1.1 if 5 <= month <= 10 else 0.85
                for w in range(8):
                    noise = np.random.normal(0, 0.03)
                    ndvi = base_ndvi * seasonal + noise
                    if w >= 5:
                        ndvi -= (w - 5) * 0.04
                    ndvi_values.append(round(np.clip(ndvi, 0.1, 0.9), 3))
            break
    
    # ===== CURRENT STATUS =====
    current_ndvi = ndvi_values[-1]
    health, color, emoji = ndvi_to_health(current_ndvi)
    
    st.markdown("---")
    st.markdown("### 📊 Current Crop Health")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="stat-box"><div class="stat-number">{emoji}</div><div class="stat-label">Status</div><div style="color:{color};font-weight:600;">{health}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-box"><div class="stat-number">{current_ndvi:.3f}</div><div class="stat-label">Current NDVI</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-box"><div class="stat-number">10m</div><div class="stat-label">Resolution</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="stat-box"><div class="stat-number">{"Live" if use_real else "Sim"}</div><div class="stat-label">Data Source</div></div>', unsafe_allow_html=True)
    
    # ===== NDVI TREND =====
    st.markdown("### 📈 8-Week NDVI Trend")
    
    for date, ndvi in zip(dates, ndvi_values):
        h_status, h_color, h_emoji = ndvi_to_health(ndvi)
        bar_width = int(ndvi * 100)
        bar_class = "ndvi-high" if ndvi > 0.6 else ("ndvi-medium" if ndvi > 0.4 else "ndvi-low")
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;margin:8px 0;">
            <span style="width:60px;font-size:0.85rem;color:#6b8299;">{date}</span>
            <span style="width:40px;text-align:center;">{h_emoji}</span>
            <div style="flex:1;margin:0 12px;">
                <div class="ndvi-bar {bar_class}" style="width:{bar_width}%;"></div>
            </div>
            <span style="width:60px;text-align:right;font-weight:600;">{ndvi:.3f}</span>
            <span style="width:80px;text-align:right;font-size:0.8rem;color:{h_color};">{h_status}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # ===== SATELLITE IMAGE (if real data) =====
    if images:
        st.markdown("### 📸 Latest Satellite Image")
        st.image(images[-1], caption=f"Sentinel-2 NDVI — {dates[-1]}", use_container_width=True)
    
    # ===== ALERTS =====
    alert = get_ndvi_alert(ndvi_values)
    if alert:
        alert_class = "alert-card" if alert["level"] == "critical" else ("alert-card warning" if alert["level"] == "warning" else "alert-card info")
        st.markdown(f'<div class="{alert_class}"><h3>{alert["title"]}</h3><p>{alert["message"]}</p></div>', unsafe_allow_html=True)
        st.markdown("**Recommended Actions:**")
        for action in alert["actions"]:
            st.markdown(f"• {action}")
    
    # ===== NDVI GUIDE =====
    with st.expander("📖 Understanding NDVI"):
        st.markdown("""
        **NDVI (Normalized Difference Vegetation Index)** measures vegetation health from space.
        
        | NDVI | Status | Meaning |
        |------|--------|---------|
        | 0.6–1.0 | 🟢 Healthy | Dense vegetation, good growth |
        | 0.4–0.6 | 🟡 Moderate | Moderate cover, possible stress |
        | 0.2–0.4 | 🔴 Stressed | Sparse vegetation, action needed |
        | 0.0–0.2 | ⚫ Critical | Bare soil or dead crops |
        
        **Data:** ESA Sentinel-2 satellites — 10m resolution, every 5 days, completely free.
        """)

# ===== NAVIGATION =====
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(9)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]: st.page_link("pages/19_Satellite_Monitor.py", label="🛰️ Satellite")
with cols[6]: st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[7]: st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
