
import streamlit as st
import requests
import os
import tempfile
import time

DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

def explain_diagnosis(diagnosis, confidence, crop_or_type, context_type="crop"):
    """Use DeepSeek to explain a GAIA diagnosis with retry and longer timeout."""
    if context_type == "crop":
        prompt = f"""GAIA diagnosed: {diagnosis} on {crop_or_type} with {confidence:.1f}% confidence.

Please provide a comprehensive farmer-friendly guide covering:
1. **What This Means:** Explain the disease in simple terms
2. **Organic Treatment:** Natural remedies with exact recipes and dosages
3. **Chemical Treatment:** Specific product names, exact dosages per liter/hectare, application method
4. **Water Management:** Irrigation advice specific to this condition
5. **Ridges/Bed Preparation:** How to prepare land to prevent recurrence
6. **Yield Impact:** Expected yield loss if untreated vs treated
7. **Cost Estimate:** Approximate cost of treatment per hectare
8. **Prevention:** How to prevent this in future seasons
9. **Safety:** Protective gear and waiting period before harvest

Be practical, specific, and use Nigerian/local context. Mention exact product names available in Nigerian agro-dealers."""
    elif context_type == "pest":
        prompt = f"""GAIA identified: {diagnosis} with {confidence:.1f}% confidence.

Please provide a comprehensive pest management guide covering:
1. **About This Pest:** Lifecycle, damage pattern, crops affected
2. **Organic Control:** Natural predators, neem oil recipes, trap crops
3. **Chemical Pesticides:** Specific products, exact dosages, application timing
4. **Water & Irrigation:** How watering affects this pest
5. **Field Management:** Ridges, spacing, intercropping to reduce pest pressure
6. **Yield Protection:** Expected damage if untreated vs treated
7. **Cost-Benefit:** Treatment cost vs potential loss
8. **Prevention:** Seasonal planning to avoid recurrence
9. **Safety:** Protective equipment, re-entry interval, pre-harvest interval"""
    elif context_type == "soil":
        prompt = f"""GAIA identified soil type: {diagnosis} with {confidence:.1f}% confidence.

Please provide a comprehensive soil management guide covering:
1. **Soil Characteristics:** pH, drainage, nutrient profile
2. **Organic Improvement:** Compost, green manure, cover crops
3. **Fertilizer Guide:** Exact NPK ratios, application rates per hectare, timing
4. **Best Crops:** Top 5 crops for this soil with expected yields
5. **Water Management:** Irrigation frequency, drainage needs
6. **Land Preparation:** Ridges, beds, or flat planting recommendations
7. **Yield Potential:** Expected yields for major crops in this soil
8. **Input Cost:** Fertilizer and amendment costs per hectare
9. **Soil Conservation:** Preventing erosion and degradation
10. **Common Mistakes:** What farmers often do wrong with this soil"""
    elif context_type == "livestock":
        prompt = f"""GAIA diagnosed: {diagnosis} in livestock with {confidence:.1f}% confidence.

Please provide a comprehensive farmer-friendly guide covering:
1. **What This Means:** Explain the disease in simple terms
2. **Symptoms:** How to recognise it
3. **Isolation:** Should the animal be separated?
4. **Treatment:** Specific medicines, dosages, and administration
5. **Prevention:** Vaccinations, hygiene, and management
6. **Feeding:** Special nutrition during recovery
7. **Cost Estimate:** Approximate treatment cost
8. **Safety:** Handling sick animals, milk/meat withdrawal periods
Be practical, specific, and use Nigerian/local context. Mention exact product names available in Nigerian veterinary stores."""
    else:
        prompt = f"""GAIA diagnosis: {diagnosis}. Explain and give actionable advice."""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are GAIA, an expert agricultural advisor built by Darkmoor Ltd in Nigeria. Give practical, specific, Nigerian-context answers. Never mention DeepSeek or any other AI company. You ARE GAIA."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }

    # Retry up to 3 times with longer timeout
    for attempt in range(3):
        try:
            response = requests.post(
                DEEPSEEK_URL,
                headers=headers,
                json=payload,
                timeout=120  # increased from 30 to 120 seconds
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"], None
            else:
                return None, f"API error: {response.status_code}"
        except requests.exceptions.Timeout:
            if attempt < 2:
                time.sleep(2)
                continue
            return None, "DeepSeek timed out. Please try again."
        except Exception as e:
            return None, str(e)

    return None, "Failed after retries."


def text_to_speech(text, language="en"):
    """Convert text to speech using Edge TTS (free) with local voice selection."""
    import asyncio
    import edge_tts

    voices = {
        "en-GB": "en-GB-SoniaNeural",
        "en-US": "en-US-JennyNeural",
        "pcm": "en-GB-RyanNeural",     # Nigerian Pidgin
        "ha": "ha-NG-MuhammedNeural",  # Hausa
        "yo": "yo-NG-AbimbolaNeural",  # Yoruba
        "ig": "ig-NG-ChidinmaNeural",  # Igbo
    }
    voice = voices.get(language, "en-GB-SoniaNeural")

    gtts_lang = {
        "en-GB": "en",
        "en-US": "en",
        "pcm": "en",
        "ha": "ha",
        "yo": "yo",
        "ig": "ig",
    }.get(language, "en")

    async def generate_with_edge():
        communicate = edge_tts.Communicate(text, voice)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        await communicate.save(tmp.name)
        return tmp.name, None

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_path, error = loop.run_until_complete(generate_with_edge())
        loop.close()

        if error:
            from gtts import gTTS
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            tts.save(tmp.name)
            with open(tmp.name, "rb") as f:
                audio_bytes = f.read()
            os.unlink(tmp.name)
            return audio_bytes, None

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        os.unlink(audio_path)
        return audio_bytes, None

    except Exception as e:
        try:
            from gtts import gTTS
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            tts.save(tmp.name)
            with open(tmp.name, "rb") as f:
                audio_bytes = f.read()
            os.unlink(tmp.name)
            return audio_bytes, None
        except Exception as e2:
            return None, str(e2)
