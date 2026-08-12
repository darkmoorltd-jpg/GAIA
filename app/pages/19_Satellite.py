
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
        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
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
                    "maxCloudCoverage": 30,
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
st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="satellite_theme_toggle")
theme = "dark" if dark_mode else "light"

# ===== THEME CSS =====
if theme == "dark":
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .stApp { background: linear-gradient(135deg, #0a0e1a 0%, #111827 50%, #0a0e1a 100%); color: #e2e8f0; }
        header, footer { visibility: hidden; }
        .title { font-size: 3rem; font-weight: 800; text-align: center; background: linear-gradient(135deg, #6366f1, #818cf8, #6366f1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.3rem; }
        .subtitle { text-align: center; font-size: 1.1rem; color: #94a3b8; margin-bottom: 2rem; }
        .stat-box { background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2); border-radius: 16px; padding: 1.5rem; text-align: center; }
        .stat-number { font-size: 2rem; font-weight: 700; color: #818cf8; }
        .stat-label { font-size: 0.85rem; color: #94a3b8; margin-top: 4px; }
        .satellite-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 1.5rem; margin: 1rem 0; backdrop-filter: blur(20px); }
        .stButton button { background: linear-gradient(135deg, #6366f1, #818cf8) !important; color: #fff !important; border: none !important; border-radius: 12px !important; padding: 12px 28px !important; font-weight: 600 !important; font-size: 1rem !important; transition: all 0.3s !important; }
        .stButton button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(99,102,241,0.4); }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .stApp { background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); color: #1e293b; }
        header, footer { visibility: hidden; }
        .title { font-size: 3rem; font-weight: 800; text-align: center; background: linear-gradient(135deg, #4f46e5, #6366f1, #4f46e5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.3rem; }
        .subtitle { text-align: center; font-size: 1.1rem; color: #64748b; margin-bottom: 2rem; }
        .stat-box { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.5rem; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .stat-number { font-size: 2rem; font-weight: 700; color: #4f46e5; }
        .stat-label { font-size: 0.85rem; color: #64748b; margin-top: 4px; }
        .satellite-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 20px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .stButton button { background: #4f46e5 !important; color: #fff !important; border: none !important; border-radius: 12px !important; padding: 12px 28px !important; font-weight: 600 !important; font-size: 1rem !important; }
        .stButton button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(79,70,229,0.3); }
    </style>
    """, unsafe_allow_html=True)

# ===== UI =====
st.markdown('<div class="title">🛰️ Satellite Field Monitor</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">See your farm from space — vegetation health, crop stress, and field conditions updated every 5 days</div>', unsafe_allow_html=True)

# ===== LOCATION INPUT =====
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    lat = st.number_input("📍 Latitude", value=9.0820, format="%.4f", help="Enter your farm's latitude")
with col2:
    lon = st.number_input("📍 Longitude", value=8.6753, format="%.4f", help="Enter your farm's longitude")
with col3:
    layer_type = st.selectbox("🔬 Analysis Type", ["TRUE_COLOR", "NDVI", "MOISTURE", "CROP_STRESS"], 
                              help="TRUE_COLOR: Natural photo | NDVI: Plant health | MOISTURE: Water content | CROP_STRESS: Problem areas")

# ===== INTERACTIVE MAP =====
st.markdown("### 🗺️ Click on the Map to Select Your Farm")
m = folium.Map(location=[lat, lon], zoom_start=14)
m.add_child(folium.LatLngPopup())
folium.Marker([lat, lon], popup="Your Farm", tooltip="Selected Location").add_to(m)
map_data = st_folium(m, width=700, height=350)

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"📍 Selected: {lat:.4f}, {lon:.4f}")

# ===== FETCH IMAGERY =====
if st.button("🛰️ Capture Satellite Image", type="primary"):
    with st.spinner("📡 Tasking Sentinel-2 satellite... This may take 10-15 seconds."):
        img, error = fetch_satellite_image(lat, lon, layers=layer_type)
    
    if error:
        st.error(f"❌ Satellite data unavailable: {error}")
        st.info("💡 Try: 1) Adjusting location slightly  2) Waiting for cloud-free day  3) Using demo mode below")
        
        # DEMO MODE — show sample imagery
        st.markdown("---")
        st.markdown("### 🎨 Demo Mode — Sample Satellite View")
        demo_urls = {
            "TRUE_COLOR": "https://images.unsplash.com/photo-1488747279002-c8523379faaa?w=800",
            "NDVI": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/NDVI_example.jpg/800px-NDVI_example.jpg",
            "MOISTURE": "https://images.unsplash.com/photo-1586771107445-b3f0a0a0e1a5?w=800",
            "CROP_STRESS": "https://images.unsplash.com/photo-1574943320219-553eb213f72d?w=800"
        }
        st.image(demo_urls.get(layer_type, demo_urls["TRUE_COLOR"]), caption=f"Sample {layer_type} imagery", use_container_width=True)
    else:
        st.markdown('<div class="satellite-card">', unsafe_allow_html=True)
        st.image(img, caption=f"Sentinel-2 {layer_type} — {lat:.4f}, {lon:.4f}", use_container_width=True)
        
        # If NDVI, calculate vegetation health
        if layer_type == "NDVI":
            health = calculate_vegetation_health(img)
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.markdown(f'<div class="stat-box"><div class="stat-number">{health["avg_ndvi"]:.3f}</div><div class="stat-label">Average NDVI</div></div>', unsafe_allow_html=True)
            col2.markdown(f'<div class="stat-box"><div class="stat-number">{health["healthy_pct"]:.0f}%</div><div class="stat-label">Healthy Vegetation</div></div>', unsafe_allow_html=True)
            col3.markdown(f'<div class="stat-box"><div class="stat-number">{health["moderate_pct"]:.0f}%</div><div class="stat-label">Moderate</div></div>', unsafe_allow_html=True)
            col4.markdown(f'<div class="stat-box"><div class="stat-number">{health["stressed_pct"]:.0f}%</div><div class="stat-label">Stressed</div></div>', unsafe_allow_html=True)
            col5.markdown(f'<div class="stat-box"><div class="stat-number">{health["health_status"]}</div><div class="stat-label">Overall Health</div></div>', unsafe_allow_html=True)
            
            # Recommendations based on health
            if health["avg_ndvi"] < 0.2:
                st.warning("⚠️ Your field shows significant stress. Consider: 1) Soil testing 2) Irrigation check 3) Pest/disease inspection")
            elif health["avg_ndvi"] < 0.4:
                st.info("💡 Your field is doing okay but could improve. Check fertilizer application and irrigation timing.")
            else:
                st.success("✅ Your field looks healthy! Continue your current practices.")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ===== NDVI SCALE EXPLANATION =====
with st.expander("📊 Understanding NDVI Values", expanded=False):
    st.markdown("""
    | NDVI Range | Health Status | What It Means |
    |------------|---------------|---------------|
    | **0.6 – 1.0** | 🟢 Excellent | Dense, healthy vegetation. Crops thriving. |
    | **0.4 – 0.6** | 🟡 Good | Moderate vegetation. Some areas may need attention. |
    | **0.2 – 0.4** | 🟠 Stressed | Sparse or stressed vegetation. Possible nutrient/water issues. |
    | **0.0 – 0.2** | 🔴 Poor | Very little vegetation. Bare soil or severely stressed crops. |
    | **< 0.0** | ⚫ Barren | No vegetation. Water, rock, or bare soil. |
    
    **NDVI** (Normalized Difference Vegetation Index) is the gold standard for measuring crop health from space.
    Healthy plants reflect near-infrared light and absorb red light. NDVI captures this difference.
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
with cols[5]: st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[6]: st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[7]: st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[8]: st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
