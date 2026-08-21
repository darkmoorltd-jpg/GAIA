import streamlit as st
user = st.session_state.get("user", None)
import requests
import numpy as np
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium

# ===== SENTINEL HUB CONFIG =====
try:
    CLIENT_ID = st.secrets["sentinel"]["client_id"]
    CLIENT_SECRET = st.secrets["sentinel"]["client_secret"]
except:
    CLIENT_ID = "86ed44fa-793b-47da-973b-345a83ae18c0"
    CLIENT_SECRET = "qYTQXnQFpgstJSrAulJ6NREflI2m2eCN"
TOKEN_URL = "https://services.sentinel-hub.com/oauth/token"
PROCESS_URL = "https://services.sentinel-hub.com/api/v1/process"

@st.cache_data(ttl=3500)
def get_access_token():
    import base64
    credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(TOKEN_URL, data={"grant_type": "client_credentials"}, headers=headers)
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None

def fetch_satellite_image(lat, lon, width=512, height=512, layers="TRUE_COLOR", date_from=None, date_to=None):
    token = get_access_token()
    if not token:
        return None, "Failed to authenticate with Sentinel Hub"
    if not date_from:
        date_from = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")

    if layers == "TRUE_COLOR":
        evalscript = """
        //VERSION=3
        function setup() {
            return { input: ["B04","B03","B02"], output: { bands: 3 } };
        }
        function evaluatePixel(sample) {
            return [sample.B04/10000, sample.B03/10000, sample.B02/10000];
        }
        """
    elif layers == "NDVI":
        evalscript = """
        //VERSION=3
        function setup() {
            return { input: ["B04","B08"], output: { bands: 1 } };
        }
        function evaluatePixel(sample) {
            let b04 = sample.B04 / 10000;
            let b08 = sample.B08 / 10000;
            let ndvi = (b08 - b04) / (b08 + b04 + 0.001);
            return [(ndvi + 1) / 2 * 255];
        }
        """
    elif layers == "MOISTURE":
        evalscript = """
        //VERSION=3
        function setup() {
            return { input: ["B08","B11"], output: { bands: 1 } };
        }
        function evaluatePixel(sample) {
            let b08 = sample.B08 / 10000;
            let b11 = sample.B11 / 10000;
            let ndmi = (b08 - b11) / (b08 + b11 + 0.001);
            return [(ndmi + 1) / 2 * 255];
        }
        """
    else:
        evalscript = """
        //VERSION=3
        function setup() {
            return { input: ["B04","B08"], output: { bands: 1 } };
        }
        function evaluatePixel(sample) {
            let b04 = sample.B04 / 10000;
            let b08 = sample.B08 / 10000;
            let ndvi = (b08 - b04) / (b08 + b04 + 0.001);
            if (ndvi > 0.6) return [0, 1, 0];
            else if (ndvi > 0.4) return [0.6, 0.8, 0.2];
            else if (ndvi > 0.2) return [1, 0.7, 0];
            else return [1, 0, 0];
        }
        """

    delta = 0.0025
    bbox = [lon - delta, lat - delta, lon + delta, lat + delta]

    payload = {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
            },
            "data": [{
                "type": "sentinel-2-l1c",
                "dataFilter": {
                    "timeRange": {"from": f"{date_from}T00:00:00Z", "to": f"{date_to}T23:59:59Z"},
                    "maxCloudCoverage": 50,
                    "mosaickingOrder": "leastCC"
                }
            }]
        },
        "output": {"width": width, "height": height, "responses": [{"identifier": "default", "format": {"type": "image/png"}}]},
        "evalscript": evalscript
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        resp = requests.post(PROCESS_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            return img, None
        return None, f"API error: {resp.status_code}"
    except Exception as e:
        return None, str(e)

def calculate_vegetation_health(ndvi_img):
    arr = np.array(ndvi_img.convert("L"), dtype=float) / 255.0
    arr = (arr * 2) - 1
    arr = np.clip(arr, -1, 1)
    healthy = (arr > 0.4).mean() * 100
    moderate = ((arr > 0.2) & (arr <= 0.4)).mean() * 100
    stressed = ((arr > 0) & (arr <= 0.2)).mean() * 100
    barren = (arr <= 0).mean() * 100
    avg_ndvi = arr.mean()
    health_status = "Excellent" if avg_ndvi > 0.6 else ("Good" if avg_ndvi > 0.4 else ("Moderate" if avg_ndvi > 0.2 else "Poor"))
    return {
        "healthy_pct": healthy,
        "moderate_pct": moderate,
        "stressed_pct": stressed,
        "barren_pct": barren,
        "avg_ndvi": avg_ndvi,
        "health_status": health_status
    }

# ===== PAGE CONFIG =====
st.set_page_config(page_title="GAIA – Satellite Monitoring", page_icon="🛰️", layout="wide")

# Theme toggle
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="satellite_theme_toggle")
theme = "dark" if dark_mode else "light"

if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0a0e1a 0%, #111827 50%, #0a0e1a 100%); color: #e2e8f0; }
        header, footer { visibility: hidden; }
        .title { font-size: 3rem; font-weight: 800; text-align: center; color: #818cf8; margin-bottom: 0.3rem; }
        .subtitle { text-align: center; font-size: 1.1rem; color: #94a3b8; margin-bottom: 2rem; }
        .stat-box { background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2); border-radius: 16px; padding: 1.5rem; text-align: center; }
        .stat-number { font-size: 2rem; font-weight: 700; color: #818cf8; }
        .stat-label { font-size: 0.85rem; color: #94a3b8; }
        .satellite-card { background: rgba(255,255,255,0.03); border-radius: 20px; padding: 1.5rem; margin: 1rem 0; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%); color: #1e1b4b; }
        header, footer { visibility: hidden; }
        .title { font-size: 3rem; font-weight: 800; text-align: center; color: #4f46e5; margin-bottom: 0.3rem; }
        .subtitle { text-align: center; font-size: 1.1rem; color: #64748b; margin-bottom: 2rem; }
        .stat-box { background: #fff; border: 1px solid #e0e0e0; border-radius: 16px; padding: 1.5rem; text-align: center; }
        .stat-number { font-size: 2rem; font-weight: 700; color: #4f46e5; }
        .stat-label { font-size: 0.85rem; color: #64748b; }
        .satellite-card { background: #fff; border-radius: 20px; padding: 1.5rem; margin: 1rem 0; }
    </style>
    """, unsafe_allow_html=True)

# ===== HEADER =====
st.markdown('<div class="title">🛰️ Satellite Monitor</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Monitor your farm health from space</div>', unsafe_allow_html=True)

# ===== LOCATION INPUT =====
st.markdown("### 📍 Enter Your Farm Location")
col1, col2 = st.columns(2)
with col1:
    lat = st.number_input("Latitude", value=9.0765, format="%.4f", step=0.001)
with col2:
    lon = st.number_input("Longitude", value=7.3986, format="%.4f", step=0.001)

# ===== LAYER SELECTION =====
st.markdown("### 🎨 Select Analysis Type")
layer = st.selectbox("Layer", ["TRUE_COLOR", "NDVI", "MOISTURE"])

if st.button("🛰️ Fetch Satellite Image", type="primary", use_container_width=True):
    with st.spinner("📡 Fetching satellite imagery..."):
        img, err = fetch_satellite_image(lat, lon, layers=layer)
    
    if err:
        st.error(f"Failed to fetch image: {err}")
    else:
        st.image(img, caption=f"{layer} — {lat:.4f}, {lon:.4f}", use_container_width=True)
        
        if layer == "NDVI":
            health = calculate_vegetation_health(img)
            
            st.markdown("---")
            st.markdown("### 📊 Vegetation Health Report")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f'<div class="stat-box"><div class="stat-number">{health["healthy_pct"]:.1f}%</div><div class="stat-label">Healthy</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="stat-box"><div class="stat-number">{health["moderate_pct"]:.1f}%</div><div class="stat-label">Moderate</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="stat-box"><div class="stat-number">{health["stressed_pct"]:.1f}%</div><div class="stat-label">Stressed</div></div>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<div class="stat-box"><div class="stat-number">{health["health_status"]}</div><div class="stat-label">Status</div></div>', unsafe_allow_html=True)
        
        if "user" in st.session_state and user is not None:
            from app.utils.scan_util import deduct_scans
            deduct_scans(user.id, 2, "Satellite Monitor")

st.markdown("---")
st.caption("Powered by Darkmoor Ltd")

# ============================================
# FULL NAVIGATION
# ============================================
st.markdown("---")
st.markdown("### Quick Navigation")
cols = st.columns(10)
with cols[0]: st.page_link("pages/1_Dashboard.py", label="Dashboard")
with cols[1]: st.page_link("pages/2_Crops.py", label="Crops")
with cols[2]: st.page_link("pages/3_Pests.py", label="Pests")
with cols[3]: st.page_link("pages/4_Soil.py", label="Soil")
with cols[4]: st.page_link("pages/5_Livestock.py", label="Livestock")
with cols[5]: st.page_link("pages/17_Video_Scan.py", label="Video Scan")
with cols[6]: st.page_link("pages/19_Satellite.py", label="Satellite")
with cols[7]: st.page_link("pages/18_Voice_Agronomist.py", label="Voice AI")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="Buy Scans")
with cols[9]: st.page_link("pages/10_Early_Warning.py", label="Alerts")

st.markdown("### More Features")
cols2 = st.columns(10)
with cols2[0]: st.page_link("pages/11_Verify_Farmer.py", label="Verify")
with cols2[1]: st.page_link("pages/12_Verification_History.py", label="History")
with cols2[2]: st.page_link("pages/14_Wallet.py", label="Wallet")
with cols2[3]: st.page_link("pages/15_Badges.py", label="Badges")
with cols2[4]: st.page_link("pages/16_Chat.py", label="Chat")
with cols2[5]: st.page_link("pages/20_Marketplace.py", label="Market")
with cols2[6]: st.page_link("pages/21_Crop_Insurance.py", label="Insurance")
with cols2[7]: st.page_link("pages/6_Payment_History.py", label="Payments")
with cols2[8]: st.page_link("pages/8_Profile.py", label="Profile")
with cols2[9]: st.page_link("pages/13_Help.py", label="Help")
