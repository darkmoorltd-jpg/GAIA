
import streamlit as st
import requests
import numpy as np
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium

# ===== SENTINEL HUB CONFIG (from Streamlit Secrets) =====
try:
    CLIENT_ID = st.secrets["sentinel"]["client_id"]
    CLIENT_SECRET = st.secrets["sentinel"]["client_secret"]
except:
    CLIENT_ID = "86ed44fa-793b-47da-973b-345a83ae18c0"
    CLIENT_SECRET = "qYTQXnQFpgstJSrAulJ6NREflI2m2eCN"
TOKEN_URL = "https://services.sentinel-hub.com/oauth/token"
PROCESS_URL = "https://services.sentinel-hub.com/api/v1/process"

# Cache the OAuth token (valid for 1 hour)
@st.cache_data(ttl=3500)
def get_access_token():
    """Get OAuth2 token from Sentinel Hub."""
    import base64
    # Sentinel Hub uses Basic Auth with client_id:client_secret
    credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(TOKEN_URL, data={"grant_type": "client_credentials"}, headers=headers)
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None

def fetch_satellite_image(lat, lon, width=512, height=512, layers="TRUE_COLOR", date_from=None, date_to=None):
    """Fetch satellite imagery from Sentinel Hub."""
    token = get_access_token()
    if not token:
        return None, "Failed to authenticate with Sentinel Hub"

    if not date_from:
        date_from = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")

    # Evalscript for true color
    if layers == "TRUE_COLOR":
        evalscript = """
        //VERSION=3
        function setup() {
            return { input: ["B04","B03","B02"], output: { bands: 3 } };
        }
        function evaluatePixel(sample) {
            // L1C values are 0-10000, normalize to 0-1
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
            // Normalize L1C values
            let b04 = sample.B04 / 10000;
            let b08 = sample.B08 / 10000;
            let ndvi = (b08 - b04) / (b08 + b04 + 0.001);
            // Map to 0-255 for display
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
            // Classify into health categories
            if (ndvi > 0.6) return [0, 1, 0];       // Green - healthy
            else if (ndvi > 0.4) return [0.6, 0.8, 0.2]; // Yellow-green - moderate
            else if (ndvi > 0.2) return [1, 0.7, 0];     // Orange - stressed
            else return [1, 0, 0];                    // Red - critical
        }
        """

    # Calculate bounding box (roughly 500m x 500m area)
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
        return None, f"API error: {resp.status_code} - {resp.text[:200]}"
    except Exception as e:
        return None, str(e)

def calculate_vegetation_health(ndvi_img):
    """Calculate vegetation health statistics from NDVI image."""
    arr = np.array(ndvi_img.convert("L"), dtype=float) / 255.0
    # Values are in [0,1] range from evalscript
    # Convert to NDVI range [-1, 1]
    arr = (arr * 2) - 1
    # Clamp to valid NDVI range
    arr = np.clip(arr, -1, 1)
    
    healthy = (arr > 0.4).mean() * 100
    moderate = ((arr > 0.2) & (arr <= 0.4)).mean() * 100
    stressed = ((arr > 0) & (arr <= 0.2)).mean() * 100
    barren = (arr <= 0).mean() * 100
    
    avg_ndvi = arr.mean()
    health_status = "🟢 Excellent" if avg_ndvi > 0.6 else ("🟡 Good" if avg_ndvi > 0.4 else ("🟠 Moderate" if avg_ndvi > 0.2 else "🔴 Poor"))
    
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

# ===== THEME TOGGLE =====

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
