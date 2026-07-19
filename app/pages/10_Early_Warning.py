
import streamlit as st
import requests
from datetime import datetime, date, timedelta
import numpy as np
import json
import os

# ---------- Optional geolocation imports ----------
try:
    from geopy.geocoders import Nominatim
    GEO_AVAILABLE = True
except:
    GEO_AVAILABLE = False

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

# ---------- Nigeria administrative data (states → LGAs) ----------
NIGERIA_DATA = {
    "Abia": ["Aba North", "Aba South", "Arochukwu", "Bende", "Ikwuano", "Isiala Ngwa North", "Isiala Ngwa South", "Isuikwuato", "Obi Ngwa", "Ohafia", "Osisioma", "Ugwunagbo", "Ukwa East", "Ukwa West", "Umuahia North", "Umuahia South", "Umu Nneochi"],
    "Adamawa": ["Demsa", "Fufure", "Ganye", "Gayuk", "Gombi", "Grie", "Hong", "Jada", "Lamurde", "Madagali", "Maiha", "Mayo Belwa", "Michika", "Mubi North", "Mubi South", "Numan", "Shelleng", "Song", "Toungo", "Yola North", "Yola South"],
    "Akwa Ibom": ["Abak", "Eastern Obolo", "Eket", "Esit Eket", "Essien Udim", "Etim Ekpo", "Etinan", "Ibeno", "Ibesikpo Asutan", "Ibiono-Ibom", "Ika", "Ikono", "Ikot Abasi", "Ikot Ekpene", "Ini", "Itu", "Mbo", "Mkpat-Enin", "Nsit-Atai", "Nsit-Ibom", "Nsit-Ubium", "Obot Akara", "Okobo", "Onna", "Oron", "Oruk Anam", "Udung-Uko", "Ukanafun", "Uruan", "Urue-Offong/Oruko", "Uyo"],
    "Anambra": ["Aguata", "Anambra East", "Anambra West", "Anaocha", "Awka North", "Awka South", "Ayamelum", "Dunukofia", "Ekwusigo", "Idemili North", "Idemili South", "Ihiala", "Njikoka", "Nnewi North", "Nnewi South", "Ogbaru", "Onitsha North", "Onitsha South", "Orumba North", "Orumba South", "Oyi"],
    "Bauchi": ["Alkaleri", "Bauchi", "Bogoro", "Damban", "Darazo", "Dass", "Gamawa", "Ganjuwa", "Giade", "Itas/Gadau", "Jama'are", "Katagum", "Kirfi", "Misau", "Ningi", "Shira", "Tafawa Balewa", "Toro", "Warji", "Zaki"],
    "Bayelsa": ["Brass", "Ekeremor", "Kolokuma/Opokuma", "Nembe", "Ogbia", "Sagbama", "Southern Ijaw", "Yenagoa"],
    "Benue": ["Ado", "Agatu", "Apa", "Buruku", "Gboko", "Guma", "Gwer East", "Gwer West", "Katsina-Ala", "Konshisha", "Kwande", "Logo", "Makurdi", "Obi", "Ogbadibo", "Ohimini", "Oju", "Okpokwu", "Oturkpo", "Tarka", "Ukum", "Ushongo", "Vandeikya"],
    "Borno": ["Abadam", "Askira/Uba", "Bama", "Bayo", "Biu", "Chibok", "Damboa", "Dikwa", "Gubio", "Guzamala", "Gwoza", "Hawul", "Jere", "Kaga", "Kala/Balge", "Konduga", "Kukawa", "Kwaya Kusar", "Mafa", "Magumeri", "Maiduguri", "Marte", "Mobbar", "Monguno", "Ngala", "Nganzai", "Shani"],
    "Cross River": ["Abi", "Akamkpa", "Akpabuyo", "Bakassi", "Bekwarra", "Biase", "Boki", "Calabar Municipal", "Calabar South", "Etung", "Ikom", "Obanliku", "Obubra", "Obudu", "Odukpani", "Ogoja", "Yakuur", "Yala"],
    "Delta": ["Aniocha North", "Aniocha South", "Bomadi", "Burutu", "Ethiope East", "Ethiope West", "Ika North East", "Ika South", "Isoko North", "Isoko South", "Ndokwa East", "Ndokwa West", "Okpe", "Oshimili North", "Oshimili South", "Patani", "Sapele", "Udu", "Ughelli North", "Ughelli South", "Ukwuani", "Uvwie", "Warri North", "Warri South", "Warri South West"],
    "Ebonyi": ["Abakaliki", "Afikpo North", "Afikpo South", "Ebonyi", "Ezza North", "Ezza South", "Ikwo", "Ishielu", "Ivo", "Izzi", "Ohaozara", "Ohaukwu", "Onicha"],
    "Edo": ["Akoko-Edo", "Egor", "Esan Central", "Esan North-East", "Esan South-East", "Esan West", "Etsako Central", "Etsako East", "Etsako West", "Igueben", "Ikpoba Okha", "Orhionmwon", "Oredo", "Ovia North-East", "Ovia South-West", "Owan East", "Owan West", "Uhunmwonde"],
    "Ekiti": ["Ado Ekiti", "Efon", "Ekiti East", "Ekiti South-West", "Ekiti West", "Emure", "Gbonyin", "Ido Osi", "Ijero", "Ikere", "Ikole", "Ilejemeje", "Irepodun/Ifelodun", "Ise/Orun", "Moba", "Oye"],
    "Enugu": ["Aninri", "Awgu", "Enugu East", "Enugu North", "Enugu South", "Ezeagu", "Igbo Etiti", "Igbo Eze North", "Igbo Eze South", "Isi Uzo", "Nkanu East", "Nkanu West", "Nsukka", "Oji River", "Udenu", "Udi", "Uzo Uwani"],
    "FCT": ["Abaji", "Bwari", "Gwagwalada", "Kuje", "Kwali", "Municipal Area Council"],
    "Gombe": ["Akko", "Balanga", "Billiri", "Dukku", "Funakaye", "Gombe", "Kaltungo", "Kwami", "Nafada", "Shongom", "Yamaltu/Deba"],
    "Imo": ["Aboh Mbaise", "Ahiazu Mbaise", "Ehime Mbano", "Ezinihitte", "Ideato North", "Ideato South", "Ihitte/Uboma", "Ikeduru", "Isiala Mbano", "Isu", "Mbaitoli", "Ngor Okpala", "Njaba", "Nkwerre", "Nwangele", "Obowo", "Oguta", "Ohaji/Egbema", "Okigwe", "Orlu", "Orsu", "Oru East", "Oru West", "Owerri Municipal", "Owerri North", "Owerri West", "Unuimo"],
    "Jigawa": ["Auyo", "Babura", "Biriniwa", "Birnin Kudu", "Buji", "Dutse", "Gagarawa", "Garki", "Gumel", "Guri", "Gwaram", "Gwiwa", "Hadejia", "Jahun", "Kafin Hausa", "Kazaure", "Kiri Kasama", "Kiyawa", "Kaugama", "Maigatari", "Malam Madori", "Miga", "Ringim", "Roni", "Sule Tankarkar", "Taura", "Yankwashi"],
    "Kaduna": ["Birnin Gwari", "Chikun", "Giwa", "Igabi", "Ikara", "Jaba", "Jema'a", "Kachia", "Kaduna North", "Kaduna South", "Kagarko", "Kajuru", "Kaura", "Kauru", "Kubau", "Kudan", "Lere", "Makarfi", "Sabon Gari", "Sanga", "Soba", "Zangon Kataf", "Zaria"],
    "Kano": ["Ajingi", "Albasu", "Bagwai", "Bebeji", "Bichi", "Bunkure", "Dala", "Dambatta", "Dawakin Kudu", "Dawakin Tofa", "Doguwa", "Fagge", "Gabasawa", "Garko", "Garun Mallam", "Gaya", "Gezawa", "Gwale", "Gwarzo", "Kabo", "Kano Municipal", "Karaye", "Kibiya", "Kiru", "Kumbotso", "Kunchi", "Kura", "Madobi", "Makoda", "Minjibir", "Nasarawa", "Rano", "Rimin Gado", "Rogo", "Shanono", "Sumaila", "Takai", "Tarauni", "Tofa", "Tsanyawa", "Tudun Wada", "Ungogo", "Warawa", "Wudil"],
    "Katsina": ["Bakori", "Batagarawa", "Batsari", "Baure", "Bindawa", "Charanchi", "Dandume", "Danja", "Dan Musa", "Daura", "Dutsi", "Dutsin Ma", "Faskari", "Funtua", "Ingawa", "Jibia", "Kafur", "Kaita", "Kankara", "Kankia", "Katsina", "Kurfi", "Kusada", "Mai'Adua", "Malumfashi", "Mani", "Mashi", "Matazu", "Musawa", "Rimi", "Sabuwa", "Safana", "Sandamu", "Zango"],
    "Kebbi": ["Aleiro", "Arewa Dandi", "Argungu", "Augie", "Bagudo", "Birnin Kebbi", "Bunza", "Dandi", "Fakai", "Gwandu", "Jega", "Kalgo", "Koko/Besse", "Maiyama", "Ngaski", "Sakaba", "Shanga", "Suru", "Wasagu/Danko", "Yauri", "Zuru"],
    "Kogi": ["Adavi", "Ajaokuta", "Ankpa", "Bassa", "Dekina", "Ibaji", "Idah", "Igalamela Odolu", "Ijumu", "Kabba/Bunu", "Kogi", "Lokoja", "Mopa Muro", "Ofu", "Ogori/Magongo", "Okehi", "Okene", "Olamaboro", "Omala", "Yagba East", "Yagba West"],
    "Kwara": ["Asa", "Baruten", "Edu", "Ekiti", "Ifelodun", "Ilorin East", "Ilorin South", "Ilorin West", "Irepodun", "Isin", "Kaiama", "Moro", "Offa", "Oke Ero", "Oyun", "Pategi"],
    "Lagos": ["Agege", "Ajeromi-Ifelodun", "Alimosho", "Amuwo-Odofin", "Apapa", "Badagry", "Epe", "Eti Osa", "Ibeju-Lekki", "Ifako-Ijaiye", "Ikeja", "Ikorodu", "Kosofe", "Lagos Island", "Lagos Mainland", "Mushin", "Ojo", "Oshodi-Isolo", "Shomolu", "Surulere"],
    "Nasarawa": ["Akwanga", "Awe", "Doma", "Karu", "Keana", "Keffi", "Kokona", "Lafia", "Nasarawa", "Nasarawa Egon", "Obi", "Toto", "Wamba"],
    "Niger": ["Agaie", "Agwara", "Bida", "Borgu", "Bosso", "Chanchaga", "Edati", "Gbako", "Gurara", "Katcha", "Kontagora", "Lapai", "Lavun", "Magama", "Mariga", "Mashegu", "Mokwa", "Moya", "Paikoro", "Rafi", "Rijau", "Shiroro", "Suleja", "Tafa", "Wushishi"],
    "Ogun": ["Abeokuta North", "Abeokuta South", "Ado-Odo/Ota", "Egbado North", "Egbado South", "Ewekoro", "Ifo", "Ijebu East", "Ijebu North", "Ijebu North East", "Ijebu Ode", "Ikenne", "Imeko Afon", "Ipokia", "Obafemi Owode", "Odeda", "Odogbolu", "Remo North", "Sagamu"],
    "Ondo": ["Akoko North-East", "Akoko North-West", "Akoko South-West", "Akoko South-East", "Akure North", "Akure South", "Ese Odo", "Idanre", "Ifedore", "Ilaje", "Ile Oluji/Okeigbo", "Irele", "Odigbo", "Okitipupa", "Ondo East", "Ondo West", "Ose", "Owo"],
    "Osun": ["Atakunmosa East", "Atakunmosa West", "Aiyedaade", "Aiyedire", "Boluwaduro", "Boripe", "Ede North", "Ede South", "Egbedore", "Ejigbo", "Ife Central", "Ife East", "Ife North", "Ife South", "Ifedayo", "Ifelodun", "Ila", "Ilesa East", "Ilesa West", "Irepodun", "Irewole", "Isokan", "Iwo", "Obokun", "Odo Otin", "Ola Oluwa", "Olorunda", "Oriade", "Orolu", "Osogbo"],
    "Oyo": ["Afijio", "Akinyele", "Atiba", "Atisbo", "Egbeda", "Ibadan North", "Ibadan North-East", "Ibadan North-West", "Ibadan South-East", "Ibadan South-West", "Ibarapa Central", "Ibarapa East", "Ibarapa North", "Ido", "Irepo", "Iseyin", "Itesiwaju", "Iwajowa", "Kajola", "Lagelu", "Ogbomosho North", "Ogbomosho South", "Ogo Oluwa", "Olorunsogo", "Oluyole", "Ona Ara", "Orelope", "Ori Ire", "Oyo East", "Oyo West", "Saki East", "Saki West", "Surulere"],
    "Plateau": ["Barkin Ladi", "Bassa", "Jos East", "Jos North", "Jos South", "Kanam", "Kanke", "Langtang North", "Langtang South", "Mangu", "Mikang", "Pankshin", "Qua'an Pan", "Riyom", "Shendam", "Wase"],
    "Rivers": ["Abua/Odual", "Ahoada East", "Ahoada West", "Akuku-Toru", "Andoni", "Asari-Toru", "Bonny", "Degema", "Eleme", "Emuoha", "Etche", "Gokana", "Ikwerre", "Khana", "Obio/Akpor", "Ogba/Egbema/Ndoni", "Ogu/Bolo", "Okrika", "Omuma", "Opobo/Nkoro", "Oyigbo", "Port Harcourt", "Tai"],
    "Sokoto": ["Binji", "Bodinga", "Dange Shuni", "Gada", "Goronyo", "Gudu", "Gwadabawa", "Illela", "Isa", "Kebbe", "Kware", "Rabah", "Sabon Birni", "Shagari", "Silame", "Sokoto North", "Sokoto South", "Tambuwal", "Tangaza", "Tureta", "Wamako", "Wurno", "Yabo"],
    "Taraba": ["Ardo Kola", "Bali", "Donga", "Gashaka", "Gassol", "Ibi", "Jalingo", "Karim Lamido", "Kumi", "Lau", "Sardauna", "Takum", "Ussa", "Wukari", "Yorro", "Zing"],
    "Yobe": ["Bade", "Bursari", "Damaturu", "Fika", "Fune", "Geidam", "Gujba", "Gulani", "Jakusko", "Karasuwa", "Machina", "Nangere", "Nguru", "Potiskum", "Tarmuwa", "Yunusari", "Yusufari"],
    "Zamfara": ["Anka", "Bakura", "Birnin Magaji/Kiyaw", "Bukkuyum", "Bungudu", "Gummi", "Gusau", "Kaura Namoda", "Maradun", "Maru", "Shinkafi", "Talata Mafara", "Tsafe", "Zurmi"]
}

# Default to Nigeria for now; extend with other countries as needed
COUNTRIES = ["Nigeria"]
STATES = list(NIGERIA_DATA.keys())

# ---------- Helper functions ----------
def fetch_weather_forecast(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum",
                  "relative_humidity_2m_max", "relative_humidity_2m_min"],
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
st.markdown('<div class="subtitle">Precision disease alerts based on your exact farm location</div>', unsafe_allow_html=True)

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in to use the Early Warning System.")
    st.stop()

user_id = st.session_state.user.id

# Supabase (service client for profile)
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

service_client = get_service_client()
res = service_client.table("user_profiles").select("*").eq("user_id", user_id).execute()
profile = res.data[0] if res.data else {}

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
lat, lon = 9.082, 8.675  # default center Nigeria
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
    crop = st.selectbox("Current Crop", ["maize", "rice", "beans", "potato", "wheat", "banana", "tomato"])
with col2:
    planting_date = st.date_input("Planting Date", max_value=date.today())

if st.button("🔍 Get Disease Risk Forecast"):
    weather = fetch_weather_forecast(lat, lon)
    growth_stage = get_growth_stage(planting_date.strftime("%Y-%m-%d") if planting_date else "")
    
    if weather:
        risks = calculate_risk(weather, crop, growth_stage)
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
