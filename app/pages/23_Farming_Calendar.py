
import streamlit as st
import datetime
import json
import os
import sys
import requests
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from supabase import create_client, Client

# ---------- Config ----------
SUPABASE_URL = st.secrets["supabase"]["url"]
SERVICE_KEY = st.secrets["supabase"]["service_key"]
DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

@st.cache_resource
def get_service():
    return create_client(SUPABASE_URL, SERVICE_KEY)

# ---------- Fallback Templates (used if DeepSeek fails) ----------
FALLBACK_TEMPLATES = {
    "Maize": [
        {"week": 0, "activity": "Land preparation: plough and harrow", "type": "land"},
        {"week": 0, "activity": "Apply basal NPK 15:15:15 at 200 kg/ha", "type": "fertilizer"},
        {"week": 0, "activity": "Plant seeds 25 cm apart, 2 seeds per hole", "type": "planting"},
        {"week": 2, "activity": "First weeding", "type": "weed"},
        {"week": 3, "activity": "Thin to 1 plant per stand", "type": "crop"},
        {"week": 4, "activity": "Apply Urea top-dressing at 100 kg/ha", "type": "fertilizer"},
        {"week": 5, "activity": "Scout for fall armyworm and stem borers", "type": "pest"},
        {"week": 6, "activity": "Spray Emamectin benzoate if pest pressure high", "type": "pest"},
        {"week": 8, "activity": "Second weeding", "type": "weed"},
        {"week": 9, "activity": "Apply Urea second top-dress at 50 kg/ha", "type": "fertilizer"},
        {"week": 12, "activity": "Monitor for Northern Leaf Blight and rust", "type": "disease"},
        {"week": 14, "activity": "Harvest when husks dry and kernels hard", "type": "harvest"},
        {"week": 14, "activity": "Dry maize to 13% moisture and store", "type": "postharvest"},
    ],
    "Rice": [
        {"week": 0, "activity": "Prepare nursery and sow seeds", "type": "planting"},
        {"week": 2, "activity": "Flood field and puddle", "type": "land"},
        {"week": 3, "activity": "Transplant seedlings 20 cm apart", "type": "planting"},
        {"week": 4, "activity": "Apply NPK 15:15:15 at 200 kg/ha", "type": "fertilizer"},
        {"week": 6, "activity": "Apply Urea 50 kg/ha", "type": "fertilizer"},
        {"week": 8, "activity": "Scout for rice blast and brown spot", "type": "disease"},
        {"week": 9, "activity": "Spray Propiconazole if blast symptoms appear", "type": "disease"},
        {"week": 12, "activity": "Drain field before harvest", "type": "land"},
        {"week": 14, "activity": "Harvest when 80% of grains are golden", "type": "harvest"},
        {"week": 14, "activity": "Thresh and dry to 14% moisture", "type": "postharvest"},
    ],
    "Beans": [
        {"week": 0, "activity": "Prepare land and make ridges 60 cm apart", "type": "land"},
        {"week": 0, "activity": "Plant seeds 10 cm apart, 2 seeds per hole", "type": "planting"},
        {"week": 2, "activity": "First weeding", "type": "weed"},
        {"week": 3, "activity": "Apply NPK 15:15:15 at 100 kg/ha", "type": "fertilizer"},
        {"week": 4, "activity": "Scout for aphids and leaf spot", "type": "pest"},
        {"week": 5, "activity": "Spray neem oil if aphids present", "type": "pest"},
        {"week": 6, "activity": "Second weeding", "type": "weed"},
        {"week": 8, "activity": "Monitor for angular leaf spot", "type": "disease"},
        {"week": 10, "activity": "Harvest when pods turn yellow and dry", "type": "harvest"},
        {"week": 10, "activity": "Thresh and store in cool, dry place", "type": "postharvest"},
    ],
    "Tomato": [
        {"week": 0, "activity": "Prepare nursery and sow tomato seeds", "type": "planting"},
        {"week": 3, "activity": "Transplant seedlings to field", "type": "planting"},
        {"week": 4, "activity": "Apply NPK 15:15:15 at 200 kg/ha", "type": "fertilizer"},
        {"week": 5, "activity": "Stake plants", "type": "crop"},
        {"week": 6, "activity": "Scout for early blight and spider mites", "type": "pest"},
        {"week": 7, "activity": "Spray Mancozeb if blight appears", "type": "disease"},
        {"week": 9, "activity": "Top-dress with Calcium nitrate 100 kg/ha", "type": "fertilizer"},
        {"week": 12, "activity": "Harvest ripe fruits", "type": "harvest"},
        {"week": 12, "activity": "Sort and pack for market", "type": "postharvest"},
    ],
    "Pepper": [
        {"week": 0, "activity": "Prepare nursery and sow pepper seeds", "type": "planting"},
        {"week": 4, "activity": "Transplant seedlings", "type": "planting"},
        {"week": 5, "activity": "Apply NPK 15:15:15 at 200 kg/ha", "type": "fertilizer"},
        {"week": 6, "activity": "Mulch to conserve moisture", "type": "crop"},
        {"week": 8, "activity": "Scout for aphids and bacterial spot", "type": "pest"},
        {"week": 9, "activity": "Spray copper-based fungicide if bacterial spot", "type": "disease"},
        {"week": 14, "activity": "Harvest peppers when firm and colorful", "type": "harvest"},
        {"week": 14, "activity": "Sort and pack", "type": "postharvest"},
    ],
    "Cabbage": [
        {"week": 0, "activity": "Prepare nursery beds and sow seeds", "type": "planting"},
        {"week": 4, "activity": "Transplant seedlings", "type": "planting"},
        {"week": 5, "activity": "Apply NPK 15:15:15 at 200 kg/ha", "type": "fertilizer"},
        {"week": 6, "activity": "Irrigate regularly", "type": "water"},
        {"week": 8, "activity": "Scout for diamondback moth and aphids", "type": "pest"},
        {"week": 9, "activity": "Spray Bt or neem oil for pests", "type": "pest"},
        {"week": 12, "activity": "Monitor for black rot", "type": "disease"},
        {"week": 16, "activity": "Harvest heads when firm", "type": "harvest"},
        {"week": 16, "activity": "Store in cool place", "type": "postharvest"},
    ],
}

# ---------- Activity type colors/icons ----------
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

def generate_calendar_with_deepseek(crop, planting_date, location):
    """Use DeepSeek to generate a personalized farming calendar."""
    prompt = f"""
You are an expert agricultural advisor. Generate a detailed farming calendar for {crop} in {location or 'Nigeria'}.
Planting date: {planting_date}.

Return a JSON array of activities. Each activity must have:
- "week": integer (week number from planting, 0 = planting week)
- "activity": string (clear instruction)
- "type": one of ["land", "planting", "fertilizer", "pest", "disease", "water", "weed", "harvest", "postharvest", "crop"]

Make it practical, specific, and appropriate for smallholder farmers. Use exact product names available in Nigerian agro-dealers where possible. Provide 10-15 activities covering the full season.

Return ONLY valid JSON array, no extra text.
"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are GAIA, an expert Nigerian agricultural assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,
        "max_tokens": 1500
    }
    try:
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                activities = json.loads(match.group())
                return activities
    except:
        pass
    return None

# ---------- Page Config ----------
st.set_page_config(page_title="GAIA – Farming Calendar", page_icon="📅", layout="wide")

st.markdown("""
<style>
    .stToggle > label { display: none !important; }
    .stToggle { display: flex; justify-content: center; margin-bottom: 1rem; }
    .stToggle > div { transform: scale(1.3); }
</style>
""", unsafe_allow_html=True)

dark_mode = st.toggle("", value=False, key="calendar_theme_toggle")
theme = "dark" if dark_mode else "light"

if theme == "dark":
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); color: #fff; }
        header, footer { visibility: hidden; }
        .title { font-size: 3rem; font-weight: 900; text-align: center;
                 background: linear-gradient(135deg, #00c853, #69f0ae);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 text-shadow: 0 0 25px rgba(0,200,83,0.7); }
        .subtitle { text-align: center; color: #b0bec5; font-size: 1.2rem; margin-bottom: 2rem; }
        .activity-card {
            background: rgba(255,255,255,0.05);
            border-left: 5px solid var(--accent);
            border-radius: 15px;
            padding: 1rem 1.5rem;
            margin: 0.7rem 0;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        .activity-card:hover {
            transform: translateX(5px);
            background: rgba(255,255,255,0.08);
        }
        .week-label {
            font-size: 0.85rem; font-weight: 700;
            text-transform: uppercase; letter-spacing: 0.05em;
        }
        .activity-type {
            font-size: 0.75rem; opacity: 0.8;
            text-transform: uppercase; letter-spacing: 0.08em;
        }
        .timeline-dot {
            display: inline-block; width: 12px; height: 12px;
            border-radius: 50%; margin-right: 8px;
        }
        .stButton button {
            background: linear-gradient(135deg, #00c853, #4caf50);
            color: #fff; border: none; border-radius: 10px;
            padding: 12px 30px; font-weight: 700;
        }
        .delete-btn {
            background: #f44336; color: #fff; border: none;
            border-radius: 8px; padding: 5px 15px;
            font-weight: 600; cursor: pointer;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9, #f1f8e9); color: #1b5e20; }
        header, footer { visibility: hidden; }
        .title { font-size: 3rem; font-weight: 900; text-align: center;
                 background: linear-gradient(135deg, #2e7d32, #4caf50);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; color: #33691e; font-size: 1.2rem; margin-bottom: 2rem; }
        .activity-card {
            background: rgba(255,255,255,0.9);
            border-left: 5px solid var(--accent);
            border-radius: 15px;
            padding: 1rem 1.5rem;
            margin: 0.7rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }
        .activity-card:hover {
            transform: translateX(5px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .week-label {
            font-size: 0.85rem; font-weight: 700;
            text-transform: uppercase; letter-spacing: 0.05em;
        }
        .activity-type {
            font-size: 0.75rem; opacity: 0.8;
            text-transform: uppercase; letter-spacing: 0.08em;
        }
        .timeline-dot {
            display: inline-block; width: 12px; height: 12px;
            border-radius: 50%; margin-right: 8px;
        }
        .stButton button {
            background: linear-gradient(135deg, #2e7d32, #4caf50);
            color: #fff; border: none; border-radius: 10px;
            padding: 12px 30px; font-weight: 700;
        }
        .delete-btn {
            background: #f44336; color: #fff; border: none;
            border-radius: 8px; padding: 5px 15px;
            font-weight: 600; cursor: pointer;
        }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="title">📅 AI Farming Calendar</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your personalized season‑long action plan — generated by GAIA AI</div>', unsafe_allow_html=True)

# ---------- Input Form ----------
col1, col2 = st.columns(2)
with col1:
    crop = st.selectbox("🌾 Select Crop", list(FALLBACK_TEMPLATES.keys()))
with col2:
    planting_date = st.date_input("📅 Planting Date", value=datetime.date.today())

location = st.text_input("📍 Location (optional)", placeholder="e.g., Kaduna")

# ---------- Generate Calendar ----------
if st.button("Generate My Calendar", type="primary"):
    if "user" not in st.session_state or not st.session_state.user:
        st.warning("Please log in first.")
        st.stop()

    user_id = st.session_state.user.id

    with st.spinner("🧠 GAIA is generating your personalized farming calendar..."):
        activities = generate_calendar_with_deepseek(crop, planting_date.isoformat(), location)

        if activities is None:
            st.warning("GAIA is using standard template.")
            template = FALLBACK_TEMPLATES[crop]
            activities = []
            for item in template:
                week = item["week"]
                activity_date = planting_date + datetime.timedelta(weeks=week)
                activities.append({
                    "week": week,
                    "date": activity_date.isoformat(),
                    "activity": item["activity"],
                    "type": item["type"]
                })
        else:
            for act in activities:
                week = int(act.get("week", 0))
                act["date"] = (planting_date + datetime.timedelta(weeks=week)).isoformat()

        supabase = get_service()
        supabase.table("farming_calendar").insert({
            "user_id": user_id,
            "crop": crop,
            "planting_date": planting_date.isoformat(),
            "location": location,
            "activities": json.dumps(activities)
        }).execute()

        st.success("✅ Calendar saved!")
        st.markdown(f"### Your {crop} Farming Calendar")
        st.markdown(f"**Planting Date:** {planting_date.strftime('%d %b %Y')}")

        for act in activities:
            week = act.get("week", 0)
            date_str = act.get("date", "")
            if date_str:
                date_obj = datetime.date.fromisoformat(date_str)
                date_str = date_obj.strftime('%d %b %Y')
            act_type = act.get("type", "crop")
            act_text = act.get("activity", "")
            meta = ACTIVITY_META.get(act_type, {"icon": "🌱", "color": "#00c853"})
            icon = meta["icon"]
            color = meta["color"]

            st.markdown(f"""
            <div class="activity-card" style="--accent:{color};">
                <div class="week-label">
                    <span class="timeline-dot" style="background:{color};"></span>
                    {icon} Week {week} — {date_str}
                </div>
                <div class="activity-type" style="color:{color};">{act_type.upper()}</div>
                <p style="margin:0.3rem 0 0 0;">{act_text}</p>
            </div>
            """, unsafe_allow_html=True)

# ---------- Show Saved Calendars with Delete ----------
st.markdown("---")
st.subheader("📂 My Saved Calendars")

if "user" in st.session_state and st.session_state.user:
    supabase = get_service()
    res = supabase.table("farming_calendar").select("*").eq("user_id", st.session_state.user.id).order("created_at", desc=True).execute()
    if res.data:
        for cal in res.data:
            with st.expander(f"🌾 {cal['crop']} — planted {cal['planting_date']}"):
                activities = json.loads(cal.get("activities", "[]"))
                for act in activities:
                    week = act.get("week", 0)
                    act_type = act.get("type", "crop")
                    act_text = act.get("activity", "")
                    date_str = act.get("date", "")
                    if date_str:
                        date_obj = datetime.date.fromisoformat(date_str)
                        date_str = date_obj.strftime('%d %b')
                    meta = ACTIVITY_META.get(act_type, {"icon": "🌱", "color": "#00c853"})
                    icon = meta["icon"]
                    st.write(f"{icon} Week {week} ({date_str}): **{act_text}**")
                if cal.get("location"):
                    st.write(f"📍 {cal['location']}")
                
                # Delete button
                if st.button("🗑️ Delete Calendar", key=f"delete_{cal['id']}", use_container_width=False):
                    supabase.table("farming_calendar").delete().eq("id", cal["id"]).execute()
                    st.success("Calendar deleted.")
                    st.rerun()
    else:
        st.info("No saved calendars yet.")
else:
    st.info("Log in to see your saved calendars.")
