from PIL import Image, ImageDraw
from supabase import create_client, Client
import streamlit as st
import datetime
import json
import os
import sys
import requests
import re
import calendar as calendar_lib
from geopy.geocoders import Nominatim
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))


# ---------- Config ----------
SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)


@st.cache_data(ttl=3600)
def geocode_location(location):
    """Geocode a location string to lat/lon."""
    try:
        geolocator = Nominatim(user_agent="gaia_farming_calendar")
        loc = geolocator.geocode(location, timeout=10)
        if loc:
            return loc.latitude, loc.longitude
        return None, None
    except BaseException:
        return None, None


@st.cache_data(ttl=3600)
def fetch_climate_data(lat, lon, start_date, end_date):
    """Fetch monthly climate data from Open-Meteo Climate API."""
    url = "https://climate-api.open-meteo.com/v1/climate"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_mean", "precipitation_sum"],
        "models": "EC_Earth3P_HR",
        "timezone": "auto",
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            temps = daily.get("temperature_2m_mean", [])
            precips = daily.get("precipitation_sum", [])
            return {"dates": dates, "temps": temps, "precips": precips}
    except BaseException:
        pass
    return None


def build_climate_summary(climate_data):
    """Convert climate data to a text summary."""
    if not climate_data or not climate_data.get("dates"):
        return "Climate data unavailable."
    dates = climate_data["dates"]
    temps = climate_data["temps"]
    precips = climate_data["precips"]

    # Group by month
    monthly = {}
    for d, t, p in zip(dates, temps, precips):
        month = d[:7]  # YYYY-MM
        if month not in monthly:
            monthly[month] = {"temps": [], "precips": []}
        monthly[month]["temps"].append(t)
        monthly[month]["precips"].append(p)

    summary = []
    for month, values in monthly.items():
        avg_temp = sum(values["temps"]) / len(values["temps"])
        total_precip = sum(values["precips"])
        summary.append(f"{month}: avg {
                avg_temp:.1f}°C, {
                total_precip:.1f} mm rain")
    return "\n".join(summary)


# ---------- Crop Groups & Crops ----------
CROP_GROUPS = {
    "🌾 Cereals": {
        "icon": "🌾",
        "crops": [
            "Maize",
            "Rice",
            "Wheat",
            "Sorghum",
            "Millet",
            "Barley",
            "Oats",
            "Fonio",
            "Teff",
        ],
        "color": "#ffb300",
    },
    "🥬 Vegetables": {
        "icon": "🥬",
        "crops": [
            "Tomato",
            "Pepper",
            "Cabbage",
            "Lettuce",
            "Spinach",
            "Onion",
            "Carrot",
            "Cucumber",
            "Okra",
            "Amaranth",
            "Broccoli",
            "Cauliflower",
        ],
        "color": "#4caf50",
    },
    "🍉 Fruits": {
        "icon": "🍉",
        "crops": [
            "Banana",
            "Mango",
            "Pineapple",
            "Watermelon",
            "Papaya",
            "Guava",
            "Orange",
            "Grape",
            "Apple",
            "Avocado",
        ],
        "color": "#e91e63",
    },
    "🫘 Legumes": {
        "icon": "🫘",
        "crops": [
            "Beans",
            "Cowpea",
            "Soybean",
            "Groundnut",
            "Pigeon Pea",
            "Chickpea",
            "Lentil",
        ],
        "color": "#795548",
    },
    "🥔 Roots & Tubers": {
        "icon": "🥔",
        "crops": [
            "Cassava",
            "Yam",
            "Potato",
            "Sweet Potato",
            "Cocoyam",
            "Ginger",
            "Turmeric",
        ],
        "color": "#ff9800",
    },
    "🌻 Oil Crops": {
        "icon": "🌻",
        "crops": [
            "Sunflower",
            "Sesame",
            "Oil Palm",
            "Coconut",
            "Castor Bean",
            "Safflower",
        ],
        "color": "#fdd835",
    },
    "🧵 Fiber Crops": {
        "icon": "🧵",
        "crops": ["Cotton", "Jute", "Kenaf", "Sisal", "Hemp"],
        "color": "#9e9e9e",
    },
    "🌿 Spices & Herbs": {
        "icon": "🌿",
        "crops": [
            "Basil",
            "Mint",
            "Thyme",
            "Rosemary",
            "Coriander",
            "Parsley",
            "Lemongrass",
        ],
        "color": "#689f38",
    },
}

# ---------- Fallback templates ----------
FALLBACK_TEMPLATES = {
    "Maize": [
        {"week": 0, "activity": "Land preparation: plough and harrow", "type": "land"},
        {
            "week": 0,
            "activity": "Apply basal NPK 15:15:15 at 200 kg/ha",
            "type": "fertilizer",
        },
        {
            "week": 0,
            "activity": "Plant seeds 25 cm apart, 2 seeds per hole",
            "type": "planting",
        },
        {"week": 2, "activity": "First weeding", "type": "weed"},
        {"week": 3, "activity": "Thin to 1 plant per stand", "type": "crop"},
        {
            "week": 4,
            "activity": "Apply Urea top-dressing at 100 kg/ha",
            "type": "fertilizer",
        },
        {
            "week": 5,
            "activity": "Scout for fall armyworm and stem borers",
            "type": "pest",
        },
        {
            "week": 6,
            "activity": "Spray Emamectin benzoate if pest pressure high",
            "type": "pest",
        },
        {"week": 8, "activity": "Second weeding", "type": "weed"},
        {
            "week": 9,
            "activity": "Apply Urea second top-dress at 50 kg/ha",
            "type": "fertilizer",
        },
        {
            "week": 12,
            "activity": "Monitor for Northern Leaf Blight and rust",
            "type": "disease",
        },
        {
            "week": 14,
            "activity": "Harvest when husks dry and kernels hard",
            "type": "harvest",
        },
        {
            "week": 14,
            "activity": "Dry maize to 13% moisture and store",
            "type": "postharvest",
        },
    ],
    "Rice": [
        {"week": 0, "activity": "Prepare nursery and sow seeds", "type": "planting"},
        {"week": 2, "activity": "Flood field and puddle", "type": "land"},
        {"week": 3, "activity": "Transplant seedlings 20 cm apart", "type": "planting"},
        {
            "week": 4,
            "activity": "Apply NPK 15:15:15 at 200 kg/ha",
            "type": "fertilizer",
        },
        {"week": 6, "activity": "Apply Urea 50 kg/ha", "type": "fertilizer"},
        {
            "week": 8,
            "activity": "Scout for rice blast and brown spot",
            "type": "disease",
        },
        {
            "week": 9,
            "activity": "Spray Propiconazole if blast symptoms appear",
            "type": "disease",
        },
        {"week": 12, "activity": "Drain field before harvest", "type": "land"},
        {
            "week": 14,
            "activity": "Harvest when 80% of grains are golden",
            "type": "harvest",
        },
        {
            "week": 14,
            "activity": "Thresh and dry to 14% moisture",
            "type": "postharvest",
        },
    ],
    "Beans": [
        {
            "week": 0,
            "activity": "Prepare land and make ridges 60 cm apart",
            "type": "land",
        },
        {
            "week": 0,
            "activity": "Plant seeds 10 cm apart, 2 seeds per hole",
            "type": "planting",
        },
        {"week": 2, "activity": "First weeding", "type": "weed"},
        {
            "week": 3,
            "activity": "Apply NPK 15:15:15 at 100 kg/ha",
            "type": "fertilizer",
        },
        {"week": 4, "activity": "Scout for aphids and leaf spot", "type": "pest"},
        {"week": 5, "activity": "Spray neem oil if aphids present", "type": "pest"},
        {"week": 6, "activity": "Second weeding", "type": "weed"},
        {"week": 8, "activity": "Monitor for angular leaf spot", "type": "disease"},
        {
            "week": 10,
            "activity": "Harvest when pods turn yellow and dry",
            "type": "harvest",
        },
        {
            "week": 10,
            "activity": "Thresh and store in cool, dry place",
            "type": "postharvest",
        },
    ],
    "Tomato": [
        {
            "week": 0,
            "activity": "Prepare nursery and sow tomato seeds",
            "type": "planting",
        },
        {"week": 3, "activity": "Transplant seedlings to field", "type": "planting"},
        {
            "week": 4,
            "activity": "Apply NPK 15:15:15 at 200 kg/ha",
            "type": "fertilizer",
        },
        {"week": 5, "activity": "Stake plants", "type": "crop"},
        {
            "week": 6,
            "activity": "Scout for early blight and spider mites",
            "type": "pest",
        },
        {"week": 7, "activity": "Spray Mancozeb if blight appears", "type": "disease"},
        {
            "week": 9,
            "activity": "Top-dress with Calcium nitrate 100 kg/ha",
            "type": "fertilizer",
        },
        {"week": 12, "activity": "Harvest ripe fruits", "type": "harvest"},
        {"week": 12, "activity": "Sort and pack for market", "type": "postharvest"},
    ],
    "Pepper": [
        {
            "week": 0,
            "activity": "Prepare nursery and sow pepper seeds",
            "type": "planting",
        },
        {"week": 4, "activity": "Transplant seedlings", "type": "planting"},
        {
            "week": 5,
            "activity": "Apply NPK 15:15:15 at 200 kg/ha",
            "type": "fertilizer",
        },
        {"week": 6, "activity": "Mulch to conserve moisture", "type": "crop"},
        {"week": 8, "activity": "Scout for aphids and bacterial spot", "type": "pest"},
        {
            "week": 9,
            "activity": "Spray copper-based fungicide if bacterial spot",
            "type": "disease",
        },
        {
            "week": 14,
            "activity": "Harvest peppers when firm and colorful",
            "type": "harvest",
        },
        {"week": 14, "activity": "Sort and pack", "type": "postharvest"},
    ],
    "Cabbage": [
        {
            "week": 0,
            "activity": "Prepare nursery beds and sow seeds",
            "type": "planting",
        },
        {"week": 4, "activity": "Transplant seedlings", "type": "planting"},
        {
            "week": 5,
            "activity": "Apply NPK 15:15:15 at 200 kg/ha",
            "type": "fertilizer",
        },
        {"week": 6, "activity": "Irrigate regularly", "type": "water"},
        {
            "week": 8,
            "activity": "Scout for diamondback moth and aphids",
            "type": "pest",
        },
        {"week": 9, "activity": "Spray Bt or neem oil for pests", "type": "pest"},
        {"week": 12, "activity": "Monitor for black rot", "type": "disease"},
        {"week": 16, "activity": "Harvest heads when firm", "type": "harvest"},
        {"week": 16, "activity": "Store in cool place", "type": "postharvest"},
    ],
}

GENERIC_ACTIVITIES = [
    {"week": 0, "activity": "Prepare land and plant seeds", "type": "planting"},
    {"week": 2, "activity": "First weeding", "type": "weed"},
    {"week": 4, "activity": "Apply balanced fertilizer", "type": "fertilizer"},
    {"week": 6, "activity": "Monitor for pests and diseases", "type": "pest"},
    {"week": 8, "activity": "Second weeding", "type": "weed"},
    {
        "week": 10,
        "activity": "Apply fertilizer top-dress if needed",
        "type": "fertilizer",
    },
    {"week": 14, "activity": "Harvest when mature", "type": "harvest"},
    {
        "week": 14,
        "activity": "Post-harvest handling and storage",
        "type": "postharvest",
    },
]

ACTIVITY_META = {
    "land": {"icon": "🚜", "color": "#8d6e63"},
    "planting": {"icon": "🌱", "color": "#2e7d32"},
    "fertilizer": {"icon": "💩", "color": "#ff9800"},
    "pest": {"icon": "🐛", "color": "#f44336"},
    "disease": {"icon": "🦠", "color": "#e91e63"},
    "water": {"icon": "💧", "color": "#2196f3"},
    "weed": {"icon": "🌿", "color": "#4caf50"},
    "harvest": {"icon": "🌾", "color": "#ffb300"},
    "postharvest": {"icon": "📦", "color": "#795548"},
    "crop": {"icon": "🌽", "color": "#689f38"},
    "tip": {"icon": "💡", "color": "#7c4dff"},
}


def generate_calendar_with_deepseek(crop, planting_date, location, climate_summary):
    prompt = f"""
You are an expert agricultural advisor. Generate a detailed farming calendar for {crop} in {location}.
Planting date: {planting_date}.

Climate information for the location:
{climate_summary}

Return a JSON array of activities. Each activity must have:
- "week": integer (week number from planting, 0 = planting week)
- "activity": string (clear instruction)
- "type": one of ["land", "planting", "fertilizer", "pest", "disease", "water", "weed", "harvest", "postharvest", "crop"]

Use the climate data to adjust timing, irrigation, and pest control. Make it practical, specific, and appropriate for smallholder farmers. Use exact product names available in Nigerian agro-dealers. Provide 10-15 activities covering the full season.

Return ONLY valid JSON array, no extra text.
"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are GAIA, an expert Nigerian agricultural assistant.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6,
        "max_tokens": 1500,
    }
    try:
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                return json.loads(match.group())
    except BaseException:
        pass
    return None


# ---------- Calendar Image Generator ----------


def generate_calendar_image(planting_date, activities, theme):
    max_week = max((act.get("week", 0) for act in activities), default=0)
    final_date = planting_date + datetime.timedelta(weeks=max_week)
    start_year, start_month = planting_date.year, planting_date.month
    end_year, end_month = final_date.year, final_date.month

    months = []
    y, m = start_year, start_month
    while (y, m) <= (end_year, end_month):
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1

    images = []
    bg_color = (30, 30, 30) if theme == "dark" else (255, 255, 255)
    text_color = (255, 255, 255) if theme == "dark" else (30, 30, 30)
    header_color = (0, 200, 83) if theme == "dark" else (46, 125, 50)
    cell_color = (60, 60, 60) if theme == "dark" else (220, 220, 220)
    highlight_color = (0, 200, 83, 150) if theme == "dark" else (46, 125, 50, 150)

    for year, month in months:
        cal_obj = calendar_lib.Calendar(firstweekday=6)
        month_days = cal_obj.monthdayscalendar(year, month)

        img_width = 600
        img_height = 450
        img = Image.new("RGBA", (img_width, img_height), bg_color + (255,))
        draw = ImageDraw.Draw(img)

        month_name = datetime.date(year, month, 1).strftime("%B %Y")
        draw.text((img_width // 2, 20), month_name, fill=header_color, anchor="mm")

        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        cell_width = img_width // 7
        cell_height = 50
        start_y = 60
        for i, day in enumerate(days):
            x = i * cell_width + cell_width // 2
            draw.text((x, start_y), day, fill=header_color, anchor="mm")

        for week_idx, week in enumerate(month_days):
            for day_idx, day in enumerate(week):
                x0 = day_idx * cell_width
                y0 = start_y + 30 + week_idx * cell_height
                x1 = x0 + cell_width
                y1 = y0 + cell_height
                draw.rectangle([x0, y0, x1, y1], outline=cell_color, width=1)
                if day == 0:
                    continue
                draw.text((x0 + 5, y0 + 2), str(day), fill=text_color)
                if (
                    year == planting_date.year
                    and month == planting_date.month
                    and day == planting_date.day
                ):
                    draw.rectangle([x0, y0, x1, y1], fill=highlight_color)

                y_dot = y0 + cell_height - 12
                for act in activities:
                    week = act.get("week", 0)
                    act_date = planting_date + datetime.timedelta(weeks=week)
                    if (
                        act_date.year == year
                        and act_date.month == month
                        and act_date.day == day
                    ):
                        act_type = act.get("type", "crop")
                        color_hex = ACTIVITY_META.get(act_type, {"color": "#ccc"})[
                            "color"
                        ]
                        color_rgb = tuple(
                            int(color_hex[i : i + 2], 16) for i in (1, 3, 5)
                        )
                        draw.ellipse(
                            [x0 + 5, y_dot, x0 + 10, y_dot + 5], fill=color_rgb
                        )

        images.append(img)
    return images


# ---------- Page Config ----------
st.set_page_config(page_title="GAIA – Farming Calendar", page_icon="📅", layout="wide")
st.markdown(
    "<style>.stToggle>label{display:none}.stToggle{display:flex;justify-content:center;margin-bottom:1rem}.stToggle>div{transform:scale(1.3)}</style>",
    unsafe_allow_html=True,
)
dark_mode = st.toggle("", value=False, key="calendar_theme_toggle")
theme = "dark" if dark_mode else "light"

if theme == "dark":
    st.markdown(
        """<style>
        @keyframes glow {0%,100%{text-shadow:0 0 25px rgba(0,200,83,0.7);}50%{text-shadow:0 0 50px rgba(0,200,83,1),0 0 80px rgba(0,200,83,0.6);}}
        .stApp {background: linear-gradient(rgba(0,0,0,0.65),rgba(0,0,0,0.65)),url('https://images.unsplash.com/photo-1500382017468-9049fed747ef?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80');background-size:cover;background-attachment:fixed;background-position:center;color:#fff;}
        header,footer{visibility:hidden;}
        .title{font-size:3rem;font-weight:900;text-align:center;background:linear-gradient(135deg,#00c853,#69f0ae);-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:glow 2s ease-in-out infinite alternate;}
        .subtitle{text-align:center;color:#b0bec5;font-size:1.2rem;margin-bottom:2rem;}
        .group-card{background:rgba(255,255,255,0.05);border:2px solid transparent;border-radius:20px;padding:1.5rem;text-align:center;cursor:pointer;transition:all 0.3s;backdrop-filter:blur(10px);}
        .group-card:hover{transform:translateY(-5px);border-color:var(--accent);box-shadow:0 8px 25px rgba(0,0,0,0.3);}
        .group-icon{font-size:2.5rem;margin-bottom:0.5rem;}
        .group-name{font-weight:700;font-size:1.1rem;}
        .crop-chip{display:inline-block;background:rgba(255,255,255,0.1);border-radius:50px;padding:0.5rem 1rem;margin:0.3rem;font-weight:600;cursor:pointer;}
        .crop-chip:hover{background:rgba(0,200,83,0.3);}
        .activity-card{background:rgba(255,255,255,0.05);border-left:5px solid var(--accent);border-radius:15px;padding:1rem 1.5rem;margin:0.7rem 0;backdrop-filter:blur(10px);transition:all 0.3s;}
        .activity-card:hover{transform:translateX(5px);background:rgba(255,255,255,0.08);}
        .week-label{font-size:0.85rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;}
        .activity-type{font-size:0.75rem;opacity:0.8;text-transform:uppercase;}
        .timeline-dot{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:8px;}
        .stButton button{background:linear-gradient(135deg,#00c853,#4caf50);color:#fff;border:none;border-radius:10px;padding:12px 30px;font-weight:700;}
    </style>""",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """<style>
        @keyframes glowLight {0%,100%{text-shadow:0 0 15px rgba(46,125,50,0.5);}50%{text-shadow:0 0 30px rgba(46,125,50,1),0 0 60px rgba(46,125,50,0.7);}}
        .stApp{background:linear-gradient(rgba(255,255,255,0.75),rgba(255,255,255,0.75)),url('https://images.unsplash.com/photo-1500382017468-9049fed747ef?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80');background-size:cover;background-attachment:fixed;background-position:center;color:#1b5e20;}
        header,footer{visibility:hidden;}
        .title{font-size:3rem;font-weight:900;text-align:center;background:linear-gradient(135deg,#2e7d32,#4caf50);-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:glowLight 2s ease-in-out infinite alternate;}
        .subtitle{text-align:center;color:#33691e;font-size:1.2rem;margin-bottom:2rem;}
        .group-card{background:rgba(255,255,255,0.9);border:2px solid transparent;border-radius:20px;padding:1.5rem;text-align:center;cursor:pointer;transition:all 0.3s;box-shadow:0 2px 10px rgba(0,0,0,0.05);}
        .group-card:hover{transform:translateY(-5px);border-color:var(--accent);box-shadow:0 8px 25px rgba(0,0,0,0.1);}
        .group-icon{font-size:2.5rem;margin-bottom:0.5rem;}
        .group-name{font-weight:700;font-size:1.1rem;color:#1b5e20;}
        .crop-chip{display:inline-block;background:#fff;border:1px solid #c8e6c9;border-radius:50px;padding:0.5rem 1rem;margin:0.3rem;font-weight:600;cursor:pointer;}
        .crop-chip:hover{background:#e8f5e9;}
        .activity-card{background:rgba(255,255,255,0.9);border-left:5px solid var(--accent);border-radius:15px;padding:1rem 1.5rem;margin:0.7rem 0;box-shadow:0 2px 8px rgba(0,0,0,0.05);transition:all 0.3s;}
        .activity-card:hover{transform:translateX(5px);box-shadow:0 4px 15px rgba(0,0,0,0.1);}
        .week-label{font-size:0.85rem;font-weight:700;text-transform:uppercase;}
        .activity-type{font-size:0.75rem;opacity:0.8;text-transform:uppercase;}
        .timeline-dot{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:8px;}
        .stButton button{background:linear-gradient(135deg,#2e7d32,#4caf50);color:#fff;border:none;border-radius:10px;padding:12px 30px;font-weight:700;}
    </style>""",
        unsafe_allow_html=True,
    )

st.markdown('<div class="title">📅 AI Farming Calendar</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Select a crop group, choose your crop, and GAIA will generate a personalized season plan</div>',
    unsafe_allow_html=True,
)

# ---------- Session state ----------
if "selected_group" not in st.session_state:
    st.session_state.selected_group = None
if "selected_crop" not in st.session_state:
    st.session_state.selected_crop = None

# ---------- Step 1: Group selection ----------
if st.session_state.selected_group is None:
    st.markdown("### Choose a Crop Group")
    cols = st.columns(4)
    for i, (group_name, group_data) in enumerate(CROP_GROUPS.items()):
        with cols[i % 4]:
            if st.button(
                f"{group_data['icon']}\n\n{group_name}",
                key=f"group_{group_name}",
                use_container_width=True,
            ):
                st.session_state.selected_group = group_name
                st.rerun()

# ---------- Step 2: Crop selection ----------
elif st.session_state.selected_crop is None:
    group_name = st.session_state.selected_group
    group_data = CROP_GROUPS[group_name]
    st.markdown(f"### {group_data['icon']} {group_name}")
    st.markdown("Select a crop:")
    cols = st.columns(3)
    for i, crop in enumerate(group_data["crops"]):
        with cols[i % 3]:
            if st.button(crop, key=f"crop_{crop}", use_container_width=True):
                st.session_state.selected_crop = crop
                st.rerun()
    if st.button("← Back to Groups"):
        st.session_state.selected_group = None
        st.rerun()

# ---------- Step 3: Generate ----------
else:
    group_name = st.session_state.selected_group
    crop = st.session_state.selected_crop
    group_data = CROP_GROUPS[group_name]
    st.markdown(f"### {group_data['icon']} {crop}")
    col1, col2 = st.columns(2)
    with col1:
        planting_date = st.date_input("📅 Planting Date", value=datetime.date.today())
    with col2:
        location = st.text_input("📍 Location *", placeholder="e.g., Kaduna, Nigeria")

    if st.button("Generate My Calendar", type="primary"):
        if not location.strip():
            st.error("Location is required. Please enter your farm location.")
        elif "user" not in st.session_state or not st.session_state.user:
            st.warning("Please log in first.")
        else:
            user_id = st.session_state.user.id
            with st.spinner("🌍 Geocoding location and fetching climate..."):
                lat, lon = geocode_location(location)
                if lat is None:
                    st.error("Could not find that location. Please be more specific.")
                else:
                    # Display map
                    map_df = pd.DataFrame({"lat": [lat], "lon": [lon]})
                    st.map(map_df, zoom=8)

                    # Fetch climate data for the growing season
                    max_week = (
                        24  # rough maximum, will refine after activities generated
                    )
                    start_date = planting_date.strftime("%Y-%m-%d")
                    end_date = (
                        planting_date + datetime.timedelta(weeks=max_week)
                    ).strftime("%Y-%m-%d")
                    climate_data = fetch_climate_data(lat, lon, start_date, end_date)
                    climate_summary = build_climate_summary(climate_data)

            with st.spinner(
                "🧠 GAIA is generating your personalized farming calendar..."
            ):
                activities = generate_calendar_with_deepseek(
                    crop, planting_date.isoformat(), location, climate_summary
                )
                if activities is None:
                    if crop in FALLBACK_TEMPLATES:
                        activities = FALLBACK_TEMPLATES[crop].copy()
                    else:
                        activities = GENERIC_ACTIVITIES.copy()
                    final_activities = []
                    for item in activities:
                        week = item["week"]
                        activity_date = planting_date + datetime.timedelta(weeks=week)
                        final_activities.append(
                            {
                                "week": week,
                                "date": activity_date.isoformat(),
                                "activity": item["activity"],
                                "type": item["type"],
                            }
                        )
                    activities = final_activities
                else:
                    for act in activities:
                        week = int(act.get("week", 0))
                        act["date"] = (
                            planting_date + datetime.timedelta(weeks=week)
                        ).isoformat()

                supabase = get_service()
                supabase.table("farming_calendar").insert(
                    {
                        "user_id": user_id,
                        "crop": crop,
                        "planting_date": planting_date.isoformat(),
                        "location": location,
                        "activities": json.dumps(activities),
                    }
                ).execute()
                st.success("✅ Calendar saved!")
                # Display real calendar images
                for cal_img in generate_calendar_image(
                    planting_date, activities, theme
                ):
                    st.image(cal_img, use_container_width=True)
                st.markdown(f"### Your {crop} Farming Calendar")
                st.markdown(
                    f"**Planting Date:** {planting_date.strftime('%d %b %Y')} | **Location:** {location}"
                )
                for act in activities:
                    week = act.get("week", 0)
                    date_str = act.get("date", "")
                    if date_str:
                        date_obj = datetime.date.fromisoformat(date_str)
                        date_str = date_obj.strftime("%d %b %Y")
                    act_type = act.get("type", "crop")
                    act_text = act.get("activity", "")
                    meta = ACTIVITY_META.get(
                        act_type, {"icon": "🌱", "color": "#00c853"}
                    )
                    icon = meta["icon"]
                    color = meta["color"]
                    st.markdown(
                        f"""
                    <div class="activity-card" style="--accent:{color};">
                        <div class="week-label"><span class="timeline-dot" style="background:{color};"></span>{icon} Week {week} — {date_str}</div>
                        <div class="activity-type" style="color:{color};">{act_type.upper()}</div>
                        <p style="margin:0.3rem 0 0 0;">{act_text}</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

    if st.button("← Change Crop"):
        st.session_state.selected_crop = None
        st.rerun()

# ---------- Saved Calendars ----------
st.markdown("---")
st.subheader("📂 My Saved Calendars")
if "user" in st.session_state and st.session_state.user:
    supabase = get_service()
    res = (
        supabase.table("farming_calendar")
        .select("*")
        .eq("user_id", st.session_state.user.id)
        .order("created_at", desc=True)
        .execute()
    )
    if res.data:
        for cal_entry in res.data:
            crop = cal_entry["crop"]
            group_color = "#00c853"
            for gname, gdata in CROP_GROUPS.items():
                if crop in gdata["crops"]:
                    group_color = gdata["color"]
                    break
            with st.expander(f"🌾 {crop} — planted {cal_entry['planting_date']}"):
                cal_date = datetime.date.fromisoformat(cal_entry["planting_date"])
                saved_acts = json.loads(cal_entry.get("activities", "[]"))
                for cal_img in generate_calendar_image(cal_date, saved_acts, theme):
                    st.image(cal_img, use_container_width=True)
                for act in saved_acts:
                    week = act.get("week", 0)
                    act_type = act.get("type", "crop")
                    act_text = act.get("activity", "")
                    date_str = act.get("date", "")
                    if date_str:
                        date_obj = datetime.date.fromisoformat(date_str)
                        date_str = date_obj.strftime("%d %b")
                    meta = ACTIVITY_META.get(
                        act_type, {"icon": "🌱", "color": "#00c853"}
                    )
                    icon = meta["icon"]
                    color = meta["color"]
                    st.markdown(
                        f"""
                    <div class="activity-card" style="--accent:{color};">
                        <div class="week-label"><span class="timeline-dot" style="background:{color};"></span>{icon} Week {week} ({date_str})</div>
                        <div class="activity-type" style="color:{color};">{act_type.upper()}</div>
                        <p style="margin:0.3rem 0 0 0;">{act_text}</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                if cal_entry.get("location"):
                    st.write(f"📍 {cal_entry['location']}")
                if st.button("🗑️ Delete Calendar", key=f"delete_{
                        cal_entry['id']}"):
                    supabase.table("farming_calendar").delete().eq(
                        "id", cal_entry["id"]
                    ).execute()
                    st.success("Calendar deleted.")
                    st.rerun()
    else:
        st.info("No saved calendars yet.")
else:
    st.info("Log in to see your saved calendars.")


# ============================================================
# NAVIGATION
# ============================================================
st.markdown("---")
st.markdown("### 🔗 Quick Navigation")
cols = st.columns(10)
with cols[0]:
    st.page_link("pages/1_Dashboard.py", label="🏠 Dashboard")
with cols[1]:
    st.page_link("pages/2_Crops.py", label="🌿 Crops")
with cols[2]:
    st.page_link("pages/3_Pests.py", label="🐛 Pests")
with cols[3]:
    st.page_link("pages/4_Soil.py", label="🏞️ Soil")
with cols[4]:
    st.page_link("pages/5_Livestock.py", label="🐄 Livestock")
with cols[5]:
    st.page_link("pages/17_Video_Scan.py", label="🎥 Video Scan")
with cols[6]:
    st.page_link("pages/19_Satellite.py", label="🛰️ Satellite")
with cols[7]:
    st.page_link("pages/18_Voice_Agronomist.py", label="🎙️ Voice AI")
with cols[8]:
    st.page_link("pages/9_Buy_Scans.py", label="💳 Buy Scans")
with cols[9]:
    st.page_link("pages/20_Marketplace.py", label="🌍 Market")

st.markdown("### 📱 More Features")
cols2 = st.columns(10)
with cols2[0]:
    st.page_link("pages/11_Verify_Farmer.py", label="🛡️ Verify")
with cols2[1]:
    st.page_link("pages/12_Verification_History.py", label="📋 History")
with cols2[2]:
    st.page_link("pages/14_Wallet.py", label="💰 Wallet")
with cols2[3]:
    st.page_link("pages/15_Badges.py", label="🏅 Badges")
with cols2[4]:
    st.page_link("pages/16_Chat.py", label="💬 Chat")
with cols2[5]:
    st.page_link("pages/20_Marketplace.py", label="🌍 Market")
with cols2[6]:
    st.page_link("pages/21_Crop_Insurance.py", label="🏦 Insurance")
with cols2[7]:
    st.page_link("pages/6_Payment_History.py", label="💳 Payments")
with cols2[8]:
    st.page_link("pages/8_Profile.py", label="👤 Profile")
with cols2[9]:
    st.page_link("pages/13_Help.py", label="🆘 Help")
